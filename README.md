# ColdChain IoT – Backend (Django + DRF + Docker)

This repo contains the **IoT ColdChain backend** (Django REST + PostgreSQL + MQTT + Telegram).  
It exposes JWT‑protected APIs for **devices, measurements, tickets, dashboard and users**.

---

## ⚙️ Prerequisites

- Docker & Docker Compose
- (Optional) `mosquitto_pub` CLI if you want to publish MQTT messages from your host

---

## 🚀 Quick Start

### 1) Configure environment

Copy the sample env if you have it, then adjust values (DB, Telegram, JWT, etc.)

```bash
cp .env.example .env   # if your repo has one; otherwise ensure these vars exist in compose
```

**Important envs commonly used in this project:**

```
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*

POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=coldchain
POSTGRES_USER=coldchain
POSTGRES_PASSWORD=coldchain

MQTT_HOST=mosquitto
MQTT_PORT=1883
MQTT_TOPIC=coldchain/+/telemetry

TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=xxxxxxxx:yyyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

> If Telegram is not required, set `TELEGRAM_ENABLED=false` or remove the bot service from the `docker compose up` command.

---

### 2) Start the stack

```bash
docker compose up -d db mosquitto web worker telegram-bot
# or without telegram:
# docker compose up -d db mosquitto web worker
```

The `web` container will run migrations automatically if your entrypoint is wired that way.  
If not, just do:

```bash
docker compose exec web python manage.py migrate
```

Check logs:

```bash
docker compose logs -f web
```

---

### 3) Create the **first admin** (non‑interactive, safe one‑liner)

Run this once to seed an admin user. It will **create or update** the password if the user exists.

```bash
docker compose exec web python - <<'PY'
from django.contrib.auth import get_user_model
User = get_user_model()
email = "admin@example.com"
password = "AdminPass123"  # change me
u, created = User.objects.get_or_create(email=email, defaults={"is_staff": True, "is_superuser": True})
if not created:
    u.is_staff = True
    if hasattr(u, "is_superuser"):
        u.is_superuser = True
    u.set_password(password)
    u.save()
print("Admin ready ->", email)
PY
```

*(If your project uses username instead of email, adapt the fields accordingly.)*

> Alternative (interactive):
> ```bash
> docker compose exec web python manage.py createsuperuser
> ```

---

### 4) Get a JWT access token

```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"AdminPass123"}'
```

Response (example):
```json
{ "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6..." }
```

Use it in all subsequent calls:
```
Authorization: Bearer <access_token>
```

---

## ✅ Smoke Test

### Health check
```bash
curl -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/api/hello
```

### Devices
- **List**: `GET /api/devices`
- **Create** (admin only): `POST /api/devices`
  ```json
  {
    "code": "fridge-ARZAK-001",
    "name": "Arzak – 1",
    "location": "ARZAK",
    "active": true
  }
  ```
- **Get one**: `GET /api/devices/{code}`
- **Update** (admin only): `PATCH /api/devices/{code}`
- **Delete** (admin only): `DELETE /api/devices/{code}`
- **Metrics**: `GET /api/devices/{code}/metrics?range=day|week|month|year&bucket=hour`  
  Returns time‑bucketed `temp` + `humidity` series with min/max.

> **Note:** The public API fields map to the actual model fields like this:  
> `name -> label`, `location -> site`, `active -> is_active` (handled in the service layer).

### Measurements
- **Ingest (HTTP)**: `POST /api/measurements/ingest`
  ```json
  {
    "deviceId": "fridge-ARZAK-001",
    "ts": "2025-11-04T18:40:00Z",
    "tempC": 6.2,
    "humidity": 55
  }
  ```
- **Recent**: `GET /api/measurements/recent?device=fridge-ARZAK-001&limit=50`
- **Range**: `GET /api/measurements/range?device=fridge-ARZAK-001&from=2025-11-01T00:00:00Z&to=2025-11-05T23:59:59Z&limit=200`
- **Export CSV**: `GET /api/measurements/export.csv?device=fridge-ARZAK-001&from=...&to=...`

### MQTT Simulation (optional)
Inside the compose project:
```bash
docker compose exec mosquitto mosquitto_pub \
  -h mosquitto -p 1883 \
  -t coldchain/fridge-ARZAK-001/telemetry \
  -m '{"deviceId":"fridge-ARZAK-001","ts":"2025-11-04T18:40:00Z","tempC":4.0,"humidity":54}'
```

### Tickets
- **Open tickets**: `GET /api/tickets/open`
- **Get one**: `GET /api/tickets/{id}`
- **Acknowledge**: `POST /api/tickets/{id}/ack` `{ "name": "Admin Operator" }`
- **Comment**: `POST /api/tickets/{id}/comment` `{ "message": "Technician on the way." }`
- **Resolve**: `POST /api/tickets/{id}/resolve` `{ "resolution": "Door closed; temp stable." }`

### Users (admin only)
- **List**: `GET /api/users`
- **Create**: `POST /api/users`
- **Get/Update/Delete**: `/api/users/{id}`

---

## 🔐 Permissions (default)

- **Read** (GET) → any authenticated user
- **Write** (POST/PUT/PATCH/DELETE) → **admin (`is_staff=True`) only**  
- This is enforced in views and/or with a reusable permission (`ReadOnlyOrAdmin`).

---

## 🧩 Troubleshooting

- **401 Unauthorized** → Missing/expired token
- **403 Forbidden** → Logged user is not admin; set `is_staff=True` for admins
- **405 Method Not Allowed** → Wrong HTTP method (e.g., POST on a GET‑only endpoint)
- **500 on device create** → Fixed by service: unknown fields are ignored/mapped (API uses `name/location/active`; model uses `label/site/is_active`)
- **ModuleNotFoundError: `app.core`** → Use `from core.models import ...` (app is named `core`)

---

## 🧭 Project Map (containers)

- `web` – Django + DRF (REST API / JWT)
- `db` – PostgreSQL
- `mosquitto` – MQTT broker
- `worker` – background jobs / MQTT consumers
- `telegram-bot` – optional Telegram alerting bot

---

## 📄 License & Contact

Internal academic/industrial project.  
Owner: ColdChain IoT Team.  
For questions ping the backend owner or open an issue.
