# PYRO-SENTRY — Industrial Thermal Surveillance API & Realtime Gateway

Production-ready backend API service and realtime communication hub for the **PYRO-SENTRY Industrial Thermal Surveillance Platform**.

---

## 1. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI APPLICATION                             │
│                                                                             │
│  ┌──────────────┐   ┌────────────────────────┐   ┌───────────────────────┐  │
│  │ /auth/*      │   │ /api/v1/*              │   │ /ws (/ws/realtime)    │  │
│  │ JWT + RBAC   │   │ Surveillance & Threats │   │ WebSocket Broadcast   │  │
│  └──────┬───────┘   └───────────┬────────────┘   └───────────▲───────────┘  │
└─────────┼───────────────────────┼────────────────────────────┼──────────────┘
          │                       │                            │
          ▼                       ▼                            │
┌──────────────────┐    ┌──────────────────┐         ┌─────────┴──────────┐
│  PostgreSQL +    │    │ Intelligence     │         │ Redis Pub/Sub      │
│  SQLAlchemy ORM  │    │ Engine           │         │ Channel Broker     │
│  (Real DB Layer) │    │ Classifier/Risk  │         │ (Multi-Instance)   │
└──────────────────┘    └──────────────────┘         └────────────────────┘
```

- **Database Layer**: Full async SQLAlchemy 2.0 ORM with PostgreSQL + asyncpg (and in-memory SQLite support for automated tests).
- **Authentication & RBAC**: JWT access tokens (short-lived) + refresh tokens (stored as SHA-256 hashes in `refresh_tokens` table) with bcrypt password hashing and security audit logging.
- **Threat Lifecycle Engine**: PRD-enforced state machine graph (`NEW` → `ACKNOWLEDGED` → `INVESTIGATING` → `DISPATCHED` → `RESOLVED` + `FALSE_POSITIVE`).
- **Intelligence Engine**: Single source of truth for classifier & composite risk scoring (`app/intelligence/classifier.py` and `app/intelligence/risk.py`).
- **Realtime Gateway**: Redis Pub/Sub backend with WebSocket fan-out supporting multiple concurrent API instances.

---

## 2. API Endpoints & Backing Data Sources

### Authentication (`/auth`)
| Method | Endpoint | Description | Auth / RBAC |
|---|---|---|---|
| `POST` | `/auth/register` | Register new user account | Public |
| `POST` | `/auth/login` | Authenticate with email/password and obtain JWT pair | Public |
| `POST` | `/auth/refresh` | Exchange valid refresh token for fresh access token | Public |
| `GET` | `/auth/me` | Retrieve profile of authenticated user | Any Authenticated |
| `POST` | `/auth/logout` | Revoke active refresh token | Any Authenticated |

### Surveillance & Telemetry (`/api/v1`)
| Category | Method | Endpoint | Real Data Source / Logic | Auth / RBAC |
|---|---|---|---|---|
| **Health** | `GET` | `/api/v1/health` | Realtime connection counter & service status | Public |
| **Hotspots** | `GET` | `/api/v1/hotspots` | DB Query: `hotspots` table (filtered by FRP/confidence) | Authenticated |
| **Targets** | `GET` | `/api/v1/targets` | DB Query: `targets` table with embedded sub-resources | Authenticated |
| | `GET` | `/api/v1/targets/{id}` | DB Query: Target details + all 1-to-N / 1-to-1 relations | Authenticated |
| | `GET` | `/api/v1/targets/{id}/observations` | DB Query: `observations` table | Authenticated |
| | `GET` | `/api/v1/targets/{id}/history` | DB Query: `target_history` lifecycle audit logs | Authenticated |
| | `GET` | `/api/v1/targets/{id}/classification`| DB Query: `classifications` model evaluation | Authenticated |
| | `GET` | `/api/v1/targets/{id}/risk` | DB Query: `risk_assessments` composite risk | Authenticated |
| | `GET` | `/api/v1/targets/{id}/evidence` | DB Query: `evidence` multi-source items | Authenticated |
| | `GET` | `/api/v1/targets/{id}/satellite` | DB Query: `satellite_passes` high-resolution imagery | Authenticated |
| **Threats** | `GET` | `/api/v1/threats` | DB Query: `threats` table (filtered by status/severity) | Authenticated |
| | `GET` | `/api/v1/threats/{id}` | DB Query: Specific threat by ID | Authenticated |
| | `PATCH`| `/api/v1/threats/{id}` | DB Update + State Machine validation | `OPERATOR`, `ADMIN` |
| | `POST` | `/api/v1/threats/{id}/acknowledge`| Transition state `NEW` → `ACKNOWLEDGED` | `OPERATOR`, `ADMIN` |
| | `POST` | `/api/v1/threats/{id}/resolve` | Transition state `DISPATCHED` → `RESOLVED` | `OPERATOR`, `ADMIN` |
| **Analytics**| `GET` | `/api/v1/analytics/summary` | DB Aggregation (`COUNT`, `AVG`, `SUM`, `MAX`) | Authenticated |
| | `GET` | `/api/v1/analytics/frp-trends` | DB Time-series grouping by hour | Authenticated |
| | `GET` | `/api/v1/analytics/classification-distribution`| DB Group-by `primary_class` | Authenticated |
| | `GET` | `/api/v1/analytics/hourly-activity`| DB Diurnal 24h detection frequency | Authenticated |
| **GIS** | `GET` | `/api/v1/gis/hotspots` | GeoJSON FeatureCollection generated from `hotspots` | Authenticated |
| | `GET` | `/api/v1/gis/targets` | GeoJSON FeatureCollection generated from `targets` | Authenticated |
| | `GET` | `/api/v1/gis/industrial-assets` | GeoJSON FeatureCollection from `industrial_assets` | Authenticated |
| | `GET` | `/api/v1/gis/clusters` | GeoJSON polygon buffers from target clusters | Authenticated |
| | `GET` | `/api/v1/gis/risk-zones` | GeoJSON polygon zones with evacuation flags | Authenticated |
| **Satellite**| `GET` | `/api/v1/satellite/evidence/{target_id}` | DB Query: `satellite_passes` | Authenticated |
| **Search** | `GET` | `/api/v1/search?q={query}` | DB Full-text search across targets, threats & assets | Authenticated |
| **System** | `GET` | `/api/v1/system/data-sources` | DB Query: `data_sources` operational feed status | Authenticated |
| | `GET` | `/api/v1/system/status` | Live OS/runtime process telemetry (`psutil`) | Authenticated |
| **Events** | `GET` | `/api/v1/events` | DB Query: `events` alert log | Authenticated |
| | `POST` | `/api/v1/events` | DB Insert + Redis Pub/Sub Broadcast | `OPERATOR`, `ADMIN` |
| **Realtime** | `POST` | `/api/v1/realtime/publish` | Publish event envelope to Redis Pub/Sub channel | `OPERATOR`, `ADMIN` |

---

## 3. Threat Lifecycle State Machine

Server-side transition enforcement strictly prevents illegal state jumps (returns `409 Conflict` on invalid transitions):

```
       ┌───────────────────────────────┐
       │             NEW               │
       └───────┬───────────────┬───────┘
               │               │
       ┌───────▼───────┐       │
       │ ACKNOWLEDGED  │       │
       └───────┬───────┴──────┐│
               │              ││
       ┌───────▼───────┐      ││
       │ INVESTIGATING │      ││
       └───────┬───────┴─────┐││
               │             │││
       ┌───────▼───────┐     │││
       │  DISPATCHED   │     │││
       └───────┬───────┘     │││
               │             │││
       ┌───────▼───────┐     │││
       │   RESOLVED    │     ▼▼▼
       └───────────────┘  ┌────────────────┐
        (Terminal State)  │ FALSE_POSITIVE │
                          └────────────────┘
                           (Terminal State)
```

---

## 4. Realtime Redis Pub/Sub Architecture

1. When any background worker, pipeline event, or REST endpoint publishes an event envelope, it calls `publisher.publish(event_type, data)`.
2. The event is published to the Redis channel `pyrosentry:events`.
3. Every running API instance runs an async subscriber task (`start_subscriber`) listening to `pyrosentry:events`.
4. Upon receiving a Redis message, the subscriber fans out the envelope to all locally connected WebSocket clients on `/ws`.
5. If Redis is unavailable in single-instance local development, the publisher gracefully falls back to in-process broadcast.

---

## 5. Running the Application

### Environment Setup
Create a `.env` file based on `.env.example`:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://pyro:pyro@localhost:5432/pyrosentry

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_CHANNEL=pyrosentry:events

# JWT Security
PYRO_JWT_SECRET=your-secure-secret-key-min-32-chars
PYRO_JWT_ALGORITHM=HS256
PYRO_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
PYRO_JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Migrations
```bash
alembic upgrade head
```

### Start Application
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 6. Running Automated Tests

Run the complete test suite:
```bash
python -m pytest -v
```

The test suite runs with **70 tests (100% passing)** against real DB-backed behavior (in-memory SQLite with seed data), testing:
- **Authentication & RBAC**: Register, login, refresh, profile, logout token revocation, audit logging, role enforcement.
- **Threat Lifecycle**: Valid progression workflows, false positive branching, and 409 rejection of invalid skips.
- **Simulation Parity**: Verifies that `/simulation/run` outputs 100% match direct `classifier.classify()` and `risk.compute_risk()` calculations.
- **Redis Pub/Sub**: Cross-instance multi-server delivery and in-process fallback.
- **Surveillance REST APIs**: Hotspots, targets, observations, history, GIS GeoJSON, satellite evidence, analytics aggregations, search, system metrics, and WebSocket endpoints.
