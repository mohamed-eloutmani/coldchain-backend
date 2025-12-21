/****************************************************
 * ColdChain IoT - ESP8266 + DHT11 → MQTT (JSON)
 * topic:   coldchain/<DEVICE_ID>/telemetry
 * payload: {"deviceId","ts","tempC","humidity"}
 ****************************************************/

#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <DHT.h>
#include <time.h>  // NTP time

// ------------ USER CONFIG ------------
const char* WIFI_SSID     = "Et@ehei";
const char* WIFI_PASSWORD = "eheio2023";

const char* MQTT_HOST = "10.9.9.74";
const uint16_t MQTT_PORT = 1883;

const char* DEVICE_ID = "fridge-ARZAK-001";
#define  DHTPIN   D4                        // change if you wired to another pin (e.g., D2)
#define  DHTTYPE  DHT11                     // ✅ your sensor is DHT11
// ------------------------------------

WiFiClient espClient;
PubSubClient mqtt(espClient);
DHT dht(DHTPIN, DHTTYPE);

// For demo/testing: 1 minute. For prod: 20*60*1000.
const unsigned long PUBLISH_INTERVAL_MS = 60UL * 1000UL;  // 20UL*60UL*1000UL for 20 min
unsigned long lastPublish = 0;

// Forward declarations
void ensureWifi();
void ensureMqtt();
void publishTelemetry();
void initTime();
bool readDhtSafe(float &t, float &h);

void setup() {
  Serial.begin(115200);
  delay(200);
  Serial.println("\n[boot] ColdChain ESP8266");

  dht.begin();
  delay(2000);  // warm-up so first read isn't garbage

  ensureWifi();
  initTime();

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
}

void loop() {
  ensureWifi();
  ensureMqtt();
  mqtt.loop();

  unsigned long now = millis();
  if (now - lastPublish >= PUBLISH_INTERVAL_MS) {
    publishTelemetry();
    lastPublish = now;
  }

  delay(10);
}

void ensureWifi() {
  if (WiFi.status() == WL_CONNECTED) return;

  Serial.printf("[wifi] connecting to %s ...\n", WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  uint8_t tries = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (++tries > 60) { // ~30s timeout
      Serial.println("\n[wifi] failed, retrying...");
      WiFi.disconnect();
      delay(1000);
      WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
      tries = 0;
    }
  }
  Serial.printf("\n[wifi] connected, ip=%s\n", WiFi.localIP().toString().c_str());
}

void initTime() {
  // Set NTP (UTC)
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  Serial.print("[time] syncing NTP");
  for (int i = 0; i < 30 && time(nullptr) < 1700000000; i++) {
    Serial.print(".");
    delay(500);
  }
  Serial.println();
  time_t now = time(nullptr);
  if (now < 1700000000) Serial.println("[time] WARNING: NTP not ready; will send without ts");
  else Serial.println("[time] NTP ready");
}

void ensureMqtt() {
  if (mqtt.connected()) return;

  Serial.printf("[mqtt] connecting to %s:%u ...\n", MQTT_HOST, MQTT_PORT);
  String clientId = String("cc-esp8266-") + String(ESP.getChipId(), HEX);

  // LWT: publish "offline" if the device drops unexpectedly
  String lwtTopic = String("coldchain/") + DEVICE_ID + "/status";
  bool ok = mqtt.connect(
    clientId.c_str(),
    /*willTopic=*/ lwtTopic.c_str(),
    /*willQos=*/ 0,
    /*willRetain=*/ true,
    /*willMessage=*/ "offline"
  );

  if (ok) {
    Serial.println("[mqtt] connected");
    // Announce online (retained)
    mqtt.publish(lwtTopic.c_str(), "online", true);

    // Send one reading immediately on connect (handy for demos)
    publishTelemetry();
    lastPublish = millis();
  } else {
    Serial.printf("[mqtt] failed, rc=%d; retry in 3s\n", mqtt.state());
    delay(3000);
  }
}

void publishTelemetry() {
  float t, h;
  if (!readDhtSafe(t, h)) {
    Serial.println("[sensor] all retries failed, skipping publish");
    return;
  }

  // Build topic and JSON
  String topic = String("coldchain/") + DEVICE_ID + "/telemetry";

  // ISO timestamp via NTP (UTC). If NTP wasn't ready, omit ts.
  char payload[200];
  time_t now = time(nullptr);
  if (now >= 1700000000) {
    struct tm *tm_utc = gmtime(&now);
    char iso[25];
    strftime(iso, sizeof(iso), "%Y-%m-%dT%H:%M:%SZ", tm_utc);
    snprintf(payload, sizeof(payload),
             "{\"deviceId\":\"%s\",\"ts\":\"%s\",\"tempC\":%.2f,\"humidity\":%.2f}",
             DEVICE_ID, iso, t, h);
  } else {
    snprintf(payload, sizeof(payload),
             "{\"deviceId\":\"%s\",\"tempC\":%.2f,\"humidity\":%.2f}",
             DEVICE_ID, t, h);
  }

  bool ok = mqtt.publish(topic.c_str(), payload);
  Serial.printf("[mqtt] publish topic=%s ok=%s payload=%s\n",
                topic.c_str(), ok ? "true" : "false", payload);

  if (!ok) mqtt.disconnect(); // force reconnect next loop if publish failed
}

// Read DHT with retries + plausibility checks (DHT11 ranges)
bool readDhtSafe(float &t, float &h) {
  for (int i = 0; i < 3; i++) {        // up to 3 tries
    h = dht.readHumidity();
    t = dht.readTemperature();         // Celsius
    Serial.printf("[sensor] raw t=%.2f h=%.2f (try %d)\n", t, h, i+1);

    if (!isnan(t) && !isnan(h)) {
      // DHT11 typical valid ranges: temp 0..50°C, humidity 20..90%
      if (t >= 0.0 && t <= 50.0 && h >= 20.0 && h <= 90.0) return true;
    }
    delay(2000);                       // DHT requires ~2s between reads
  }
  return false;
}
