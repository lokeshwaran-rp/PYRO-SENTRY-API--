# PYRO-SENTRY — Backend Services & Realtime Engine (Lokesh's Module)

This repository contains the backend implementation for **Lokesh's Role** in the **PYRO-SENTRY** wildfire surveillance platform.

---

## 1. Project Purpose

The purpose of this module is to serve as the **central API and communication hub** for PYRO-SENTRY:
- Provide **modular REST APIs** for querying thermal hotspots, wildfire targets, threat escalations, GIS layers, satellite evidence, system status, and dashboard analytics.
- Provide a **Realtime WebSocket engine (`/ws`)** to stream live event envelopes (e.g. newly detected hotspots, threat updates, and simulation steps) to frontend clients.
- Provide a **Simulation Engine (`/api/v1/simulation`)** for running isolated, non-destructive fire spread and classification calculations.
- Operate in a **self-contained environment** using in-memory mock datasets without requiring external databases.

---

## 2. REST APIs

All REST endpoints are grouped logically under `/api/v1` and return standard JSON payloads.

| Category | Method | Endpoint | Description |
|---|---|---|---|
| **Health** | `GET` | `/api/v1/health` | Service health status, UTC timestamp, active WebSocket count |
| **Hotspots** | `GET` | `/api/v1/hotspots` | List active thermal hotspots (supports `min_frp`, `min_confidence`, `limit`) |
| **Targets** | `GET` | `/api/v1/targets` | List wildfire target clusters (supports `status`, `threat_level`) |
| | `GET` | `/api/v1/targets/{id}` | Target metadata and summary |
| | `GET` | `/api/v1/targets/{id}/observations` | Sensor observation passes |
| | `GET` | `/api/v1/targets/{id}/history` | Lifecycle audit trail and history logs |
| | `GET` | `/api/v1/targets/{id}/classification` | Model classification probabilities |
| | `GET` | `/api/v1/targets/{id}/risk` | Composite risk score and threatened assets |
| | `GET` | `/api/v1/targets/{id}/evidence` | Multi-source sensor & environmental evidence |
| | `GET` | `/api/v1/targets/{id}/satellite` | Satellite pass info and imagery URLs |
| **Threats** | `GET` | `/api/v1/threats` | List active and historical threats |
| | `GET` | `/api/v1/threats/{id}` | Specific threat details |
| | `PATCH`| `/api/v1/threats/{id}` | Update threat severity, status, or operator notes |
| | `POST` | `/api/v1/threats/{id}/acknowledge`| Acknowledge an active threat |
| | `POST` | `/api/v1/threats/{id}/resolve` | Mark a threat as resolved |
| **Analytics** | `GET` | `/api/v1/analytics/summary` | High-level dashboard counters |
| | `GET` | `/api/v1/analytics/frp-trends` | Fire Radiative Power (MW) time-series trends |
| | `GET` | `/api/v1/analytics/classification-distribution` | Class breakdown (Wildfire, Prescribed, Flare, etc.) |
| | `GET` | `/api/v1/analytics/hourly-activity` | 24-hour diurnal detection frequency |
| **GIS Layers** | `GET` | `/api/v1/gis/hotspots` | GeoJSON FeatureCollection of hotspots |
| | `GET` | `/api/v1/gis/targets` | GeoJSON FeatureCollection of targets |
| | `GET` | `/api/v1/gis/industrial-assets` | GeoJSON FeatureCollection of critical infrastructure |
| | `GET` | `/api/v1/gis/clusters` | GeoJSON FeatureCollection of fire cluster polygons |
| | `GET` | `/api/v1/gis/risk-zones` | GeoJSON FeatureCollection of calculated threat buffer zones |
| **Satellite** | `GET` | `/api/v1/satellite/evidence/{target_id}`| High-resolution SWIR anomaly analysis |
| **Search** | `GET` | `/api/v1/search?q={query}` | Search across targets, threats, and assets |
| **System** | `GET` | `/api/v1/system/data-sources` | External satellite & weather ingestion feed status |
| | `GET` | `/api/v1/system/status` | System runtime telemetry, memory, and CPU metrics |
| **Events** | `GET` | `/api/v1/events` | List recently recorded wildfire alerts |
| | `POST` | `/api/v1/events` | Ingest and broadcast a new wildfire alert |

---

## 3. Simulation API

### Stateless Simulation Calculation
- **`POST /api/v1/simulation/run`**
  - **Inputs**: `frp`, `brightness`, `persistence`, `industrial_proximity`, `wind_speed`, `wind_direction`, `ndvi`, `nbr`, `swir_anomaly`.
  - **Outputs**: `classification`, `confidence`, `risk_score`, `risk_level`, `evidence`, `smoke_estimate`, `impact_estimate`, `is_simulated: true`, `status: "COMPLETED"`.
  - **Guaranteed Isolation**: Stateless calculation that **never** modifies or mutates existing targets, observations, or threats.

### Spatial Spread Simulation Orchestrator
- **`POST /api/v1/simulation/start`**: Launch a background simulation loop generating spreading perimeter steps.
- **`GET /api/v1/simulation/status`**: Check status and latest step of current simulation.
- **`POST /api/v1/simulation/stop`**: Gracefully stop the active simulation.

---

## 4. WebSocket (`/ws`)

### Realtime Stream Endpoint
- **URL**: `ws://localhost:8000/ws` (with `ws://localhost:8000/ws/realtime` supported as an alias)
- In-memory multi-client connection manager supporting concurrent subscribers without Redis.

### Supported Event Types
1. `hotspot.created`
2. `target.updated`
3. `classification.completed`
4. `risk.updated`
5. `threat.created`
6. `threat.updated`
7. `simulation.completed`
8. `system.status`

### Event Envelope Format
```json
{
  "event": "hotspot.created",
  "timestamp": "2026-08-26T21:40:27.758547+00:00",
  "data": {
    "hotspot_id": "hs-101",
    "latitude": 34.2439,
    "longitude": -118.1753,
    "frp": 124.5
  }
}
```

### Demo / Test Event Trigger
Trigger a live broadcast using the REST endpoint:
```bash
POST /api/v1/realtime/publish
{
  "event": "threat.created",
  "data": {"threat_id": "threat-99", "severity": "CRITICAL"}
}
```

---

## 5. How to Install

### Prerequisites
- Python 3.10+ installed.

### Setup Steps
```bash
# 1. Clone repository and navigate to workspace
cd "New folder (2)"

# 2. (Optional) Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 6. How to Run

Start the FastAPI application with Uvicorn:

```bash
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The application will be accessible at:
- **Base URL**: `http://127.0.0.1:8000`
- **Health Endpoint**: `http://127.0.0.1:8000/api/v1/health`

---

## 7. Swagger Documentation

Interactive OpenAPI documentation is automatically available when the app is running:
- **Interactive Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 8. How to Run Tests

Run the full automated test suite using `pytest`:

```bash
python -m pytest -v
```

The test suite contains **53 automated tests** covering:
- Every REST endpoint & subresource
- Stateless and spatial simulation runs
- WebSocket connection, disconnection, echo, and multi-client broadcast
- Pydantic input validation & 422 error rejection
- 404 error handling for non-existent entities
- Simulation isolation (ensuring existing records remain 100% immutable)

---

## 9. How to Run Docker

### Using Docker Compose (Recommended)
```bash
# Build and start the container in detached mode
docker compose up -d --build

# View container logs
docker compose logs -f

# Stop the container
docker compose down
```

### Using Plain Docker Commands
```bash
# Build Docker image
docker build -t pyro-sentry-api:latest .

# Run container mapping port 8000
docker run -d --name pyro-sentry-api -p 8000:8000 pyro-sentry-api:latest
```

Once running in Docker:
- **API URL**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/docs`
- **WebSocket URL**: `ws://localhost:8000/ws`
