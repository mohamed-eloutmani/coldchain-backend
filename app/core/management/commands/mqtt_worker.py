# core/management/commands/mqtt_worker.py
import json, os, sys, time, threading
from datetime import datetime, timezone as dt_timezone

from django.core.management.base import BaseCommand
from django.db import transaction, close_old_connections

from paho.mqtt import client as mqtt

from core.serializers import IngestMeasurementSerializer
from core.alerts import on_violation, on_recovery
from core.reminders import send_open_ticket_reminders

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "coldchain/+/telemetry")

_reminder_started = False  # guard: ensure only one background loop


def _start_reminder_thread():
    """
    Background loop that calls send_open_ticket_reminders() every 60s.
    Runs inside this process (daemon thread), no Celery required.
    """
    def _loop():
        while True:
            try:
                # recycle stale DB connections in long-lived loops
                close_old_connections()
                send_open_ticket_reminders()
            except Exception as e:
                print(f"[reminder] error: {e}", flush=True)
            time.sleep(60)

    t = threading.Thread(target=_loop, daemon=True, name="reminder-thread")
    t.start()
    return t


def _normalize_ts_inplace(d: dict):
    """
    Accept:
      - ISO8601 string
      - integer/float epoch seconds or milliseconds
      - missing -> fill now (UTC)
    Mutates d["ts"] into ISO 8601 (Z).
    """
    if "ts" not in d or d["ts"] in (None, "", 0):
        d["ts"] = datetime.now(dt_timezone.utc).isoformat()
        return

    ts = d["ts"]
    # numeric? treat as epoch (ms or s)
    if isinstance(ts, (int, float)):
        # heuristics: ms if > 10^11
        if ts > 10**11:
            ts = ts / 1000.0
        d["ts"] = datetime.fromtimestamp(ts, tz=dt_timezone.utc).isoformat()
        return

    # string? if already ISO, keep; otherwise try parse a few formats
    if isinstance(ts, str):
        s = ts.strip()
        if s.endswith("Z"):
            return
        # allow "YYYY-mm-dd HH:MM:SS" (no tz) -> assume UTC
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=dt_timezone.utc)
            d["ts"] = dt.astimezone(dt_timezone.utc).isoformat()
            return
        except Exception:
            # fallback to now to avoid serializer errors
            d["ts"] = datetime.now(dt_timezone.utc).isoformat()
            return


class Command(BaseCommand):
    help = "MQTT consumer: subscribes to telemetry, ingests measurements, triggers alerts, runs reminders."

    def handle(self, *args, **options):
        global _reminder_started

        print(f"[mqtt_worker] starting… host={MQTT_HOST} port={MQTT_PORT} topic={MQTT_TOPIC}", flush=True)

        # ----- kick off reminders thread once -----
        if not _reminder_started:
            print("[mqtt_worker] launching reminder thread…", flush=True)
            _start_reminder_thread()
            _reminder_started = True

        # ----- set up MQTT client -----
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="coldchain-django-worker")

        def on_connect(cli, userdata, flags, reason_code, properties=None):
            rc_val = getattr(reason_code, "value", reason_code)
            print(f"[mqtt_worker] connected rc={rc_val}", flush=True)
            cli.subscribe(MQTT_TOPIC, qos=1)
            print(f"[mqtt_worker] subscribed to {MQTT_TOPIC}", flush=True)

        def on_message(cli, userdata, msg):
            try:
                payload = msg.payload.decode("utf-8", errors="replace")
                print(f"[mqtt_worker] message topic={msg.topic} payload={payload}", flush=True)

                data = json.loads(payload)
                _normalize_ts_inplace(data)

                # Validate & save
                ser = IngestMeasurementSerializer(data=data)
                ser.is_valid(raise_exception=True)

                with transaction.atomic():
                    m = ser.save()

                print(f"[mqtt_worker] ingested {m.device.code} {m.temp_c}C state={m.state}", flush=True)

                # ---- ALERT ENGINE HOOKS (no duplicates) ----
                try:
                    print(f"[mqtt_worker] dispatching alerts for state={m.state}", flush=True)
                    if m.state in ("SEVERE", "CRITICAL"):
                        on_violation(m.device, m.state)
                    else:
                        on_recovery(m.device)
                except Exception as e:
                    print(f"[mqtt_worker] alert handling error: {e}", flush=True)

            except Exception as e:
                print(f"[mqtt_worker] error: {e}", flush=True)

        def on_disconnect(cli, userdata, disconnect_flags, reason_code, properties=None):
            rc_val = getattr(reason_code, "value", reason_code)
            print(f"[mqtt_worker] disconnected rc={rc_val} flags={disconnect_flags}", flush=True)

        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect

        # ----- connect & loop forever with simple retry -----
        while True:
            try:
                print("[mqtt_worker] connecting…", flush=True)
                client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
                client.loop_forever()
            except KeyboardInterrupt:
                print("[mqtt_worker] stopping…", flush=True)
                try:
                    client.disconnect()
                except Exception:
                    pass
                sys.exit(0)
            except Exception as e:
                print(f"[mqtt_worker] connect error: {e}; retry in 3s", flush=True)
                time.sleep(3)
