# Database Schema Specification & DDL

**Sistem:** AI Vision Workforce Monitoring Engine  
**Database Engine:** PostgreSQL 15+  
**ORM & Migrations:** SQLAlchemy 2.0 + Alembic (`packages/db`)  
**Dokumen:** Database Schema & DDL Blueprint  
**Versi:** 1.1  
**Tanggal:** 20 Agustus 2026  

---

## 1. Entity Relationship Diagram (Conceptual Overview)

```
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│  buildings   ├────────►│    floors    ├────────►│    rooms     │
└──────────────┘         └──────────────┘         └──────┬───────┘
                                                         │
                         ┌──────────────┐                │
                         │   cameras    ├────────────────┤
                         └──────┬───────┘                │
                                │                        ▼
                                │                 ┌──────────────┐
                                ├────────────────►│    zones     │
                                │                 └──────┬───────┘
                                │                        │
                                │                        ▼
                                │                 ┌──────────────┐
                                └────────────────►│ workstations │
                                                  └──────────────┘

┌──────────────┐         ┌────────────────────────┐         ┌───────────────────────┐
│  employees   ├────────►│  identity_associations ├────────►│   tracking_sessions   │
└──────┬───────┘         └────────────────────────┘         └───────────┬───────────┘
       │                                                                │
       │                                                                ▼
       │                 ┌──────────────────────────────────────────────────────────┐
       │                 │                Partitioned Event Layer                   │
       │                 │  - location_events                                       │
       │                 │  - activity_events                                       │
       │                 │  - state_events                                          │
       │                 └──────────────────────────────┬───────────────────────────┘
       │                                                │
       ▼                                                ▼
┌────────────────────────┐                   ┌────────────────────────┐
│ daily_work_summaries   │◄──────────────────┤     work_sessions      │
└────────────────────────┘                   └───────────┬────────────┘
                                                         │
                                                         ▼
                                             ┌────────────────────────┐
                                             │    event_overrides     │
                                             └────────────────────────┘
```

---

## 2. PostgreSQL DDL Specification

```sql
-- ============================================================================
-- AI VISION WORKFORCE MONITORING ENGINE - DATABASE SCHEMA DDL
-- Compatible with PostgreSQL 15+
-- ============================================================================

-- Ekstensi yang Diperlukan
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================================
-- 1. ENUM TYPES
-- ============================================================================

CREATE TYPE identity_status_enum AS ENUM (
    'UNASSIGNED',
    'CANDIDATE',
    'PROBABLE',
    'CONFIRMED',
    'UNKNOWN'
);

CREATE TYPE observed_activity_enum AS ENUM (
    'SITTING',
    'STANDING',
    'WALKING',
    'MOVING',
    'STATIONARY',
    'PERSON_INTERACTION',
    'OBJECT_INTERACTION',
    'UNKNOWN'
);

CREATE TYPE business_state_enum AS ENUM (
    'WORKING',
    'MEETING',
    'BREAK',
    'AWAY',
    'UNKNOWN'
);

CREATE TYPE attendance_type_enum AS ENUM (
    'CLOCK_IN',
    'CLOCK_OUT',
    'BREAK_OUT',
    'BREAK_IN'
);

CREATE TYPE zone_type_enum AS ENUM (
    'WORK_AREA',
    'MEETING_ROOM',
    'PANTRY',
    'CORRIDOR',
    'ENTRANCE',
    'EXIT',
    'RESTRICTED'
);

-- ============================================================================
-- 2. MASTER DATA ENTITIES (ORGANIZATION & PHYSICAL SPACES)
-- ============================================================================

CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_code VARCHAR(100) UNIQUE NOT NULL, -- e.g. EMP001
    full_name VARCHAR(255) NOT NULL,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    email VARCHAR(255) UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    face_embedding_encrypted BYTEA, -- Enkripsi biometrik AES-256
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS buildings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    address TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS floors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,
    floor_number INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(building_id, floor_number)
);

CREATE TABLE IF NOT EXISTS rooms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    floor_id UUID NOT NULL REFERENCES floors(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(255) NOT NULL,
    room_type VARCHAR(50) DEFAULT 'OFFICE_SPACE',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(floor_id, code)
);

CREATE TABLE IF NOT EXISTS cameras (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_code VARCHAR(50) UNIQUE NOT NULL, -- e.g. CAM01
    name VARCHAR(255) NOT NULL,
    room_id UUID REFERENCES rooms(id) ON DELETE SET NULL,
    rtsp_url TEXT NOT NULL,
    ip_address INET,
    fps INT DEFAULT 25,
    resolution VARCHAR(20) DEFAULT '1920x1080',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    zone_code VARCHAR(50) NOT NULL, -- e.g. WORK_AREA_01
    zone_name VARCHAR(255) NOT NULL,
    zone_type zone_type_enum NOT NULL DEFAULT 'WORK_AREA',
    polygon_points JSONB NOT NULL, -- Array of points: [[x1, y1], [x2, y2], ...]
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(camera_id, zone_code)
);

CREATE TABLE IF NOT EXISTS workstations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    zone_id UUID NOT NULL REFERENCES zones(id) ON DELETE CASCADE,
    workstation_code VARCHAR(50) NOT NULL, -- e.g. WS-017
    polygon_points JSONB NOT NULL,
    default_assigned_employee_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(zone_id, workstation_code)
);

CREATE TABLE IF NOT EXISTS camera_topologies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    target_camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    transit_time_min_seconds INT NOT NULL DEFAULT 1,
    transit_time_max_seconds INT NOT NULL DEFAULT 30,
    reid_similarity_threshold FLOAT NOT NULL DEFAULT 0.75,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(source_camera_id, target_camera_id)
);

-- ============================================================================
-- 3. TRACKING & IDENTITY SESSIONS
-- ============================================================================

CREATE TABLE IF NOT EXISTS tracking_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    camera_id UUID NOT NULL REFERENCES cameras(id) ON DELETE CASCADE,
    local_track_id INT NOT NULL, -- e.g. 17
    global_track_id VARCHAR(100), -- e.g. GTRK-001
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ,
    last_seen_at TIMESTAMPTZ NOT NULL,
    total_frames_tracked INT NOT NULL DEFAULT 1,
    status VARCHAR(50) DEFAULT 'ACTIVE', -- ACTIVE, TERMINATED, MERGED
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS identity_associations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracking_session_id UUID NOT NULL REFERENCES tracking_sessions(id) ON DELETE CASCADE,
    employee_id UUID REFERENCES employees(id) ON DELETE SET NULL,
    identity_status identity_status_enum NOT NULL DEFAULT 'UNASSIGNED',
    confidence FLOAT NOT NULL DEFAULT 0.0,
    association_method VARCHAR(50) NOT NULL, -- FACE_ANCHOR, REID_TOPOLOGY, MANUAL
    associated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    evidence_payload JSONB
);

-- ============================================================================
-- 4. TIME-SERIES EVENT TABLES (PARTITIONED BY TIMESTAMP)
-- ============================================================================

-- 4.1. Location Events (Partitioned)
CREATE TABLE IF NOT EXISTS location_events (
    id UUID DEFAULT uuid_generate_v4(),
    tracking_session_id UUID NOT NULL,
    employee_id UUID,
    camera_id UUID NOT NULL,
    zone_id UUID,
    workstation_id UUID,
    event_type VARCHAR(50) NOT NULL, -- ZONE_ENTER, ZONE_EXIT, WS_ENTER, WS_EXIT
    foot_x FLOAT NOT NULL,
    foot_y FLOAT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- 4.2. Activity Events (Partitioned)
CREATE TABLE IF NOT EXISTS activity_events (
    id UUID DEFAULT uuid_generate_v4(),
    tracking_session_id UUID NOT NULL,
    activity observed_activity_enum NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 1.0,
    timestamp TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- 4.3. State Events (Partitioned)
CREATE TABLE IF NOT EXISTS state_events (
    id UUID DEFAULT uuid_generate_v4(),
    employee_id UUID,
    tracking_session_id UUID,
    state business_state_enum NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 1.0,
    timestamp TIMESTAMPTZ NOT NULL,
    evidence JSONB,
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Inisialisasi Partisi Harian Awal (Contoh untuk Agustus 2026)
CREATE TABLE IF NOT EXISTS location_events_2026_08 PARTITION OF location_events
    FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS activity_events_2026_08 PARTITION OF activity_events
    FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00');

CREATE TABLE IF NOT EXISTS state_events_2026_08 PARTITION OF state_events
    FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00');

-- ============================================================================
-- 5. ATTENDANCE & WORK SESSIONS (BUSINESS LAYER)
-- ============================================================================

CREATE TABLE IF NOT EXISTS attendance_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    attendance_type attendance_type_enum NOT NULL,
    source_terminal VARCHAR(100) DEFAULT 'FACE_TERMINAL_MAIN',
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS work_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    state business_state_enum NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_seconds INT GENERATED ALWAYS AS (
        EXTRACT(EPOCH FROM (end_time - start_time))::INT
    ) STORED,
    dominant_zone_id UUID REFERENCES zones(id) ON DELETE SET NULL,
    confidence_score FLOAT NOT NULL DEFAULT 1.0,
    is_overridden BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS daily_work_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    clock_in_time TIMESTAMPTZ,
    clock_out_time TIMESTAMPTZ,
    total_presence_seconds INT NOT NULL DEFAULT 0,
    total_working_seconds INT NOT NULL DEFAULT 0,
    total_meeting_seconds INT NOT NULL DEFAULT 0,
    total_break_seconds INT NOT NULL DEFAULT 0,
    total_away_seconds INT NOT NULL DEFAULT 0,
    total_unknown_seconds INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(employee_id, date)
);

-- ============================================================================
-- 6. AUDIT & HUMAN-IN-THE-LOOP OVERRIDES
-- ============================================================================

CREATE TABLE IF NOT EXISTS event_overrides (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    work_session_id UUID NOT NULL REFERENCES work_sessions(id) ON DELETE CASCADE,
    operator_user_id UUID NOT NULL, -- User yang melakukan koreksi
    original_state business_state_enum NOT NULL,
    new_state business_state_enum NOT NULL,
    reason TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    actor_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- 7. INDEXING STRATEGY FOR HIGH PERFORMANCE
-- ============================================================================

-- B-Tree Indexes for Master & Lookup
CREATE INDEX IF NOT EXISTS idx_employees_code ON employees(employee_code);
CREATE INDEX IF NOT EXISTS idx_tracking_sessions_cam_track ON tracking_sessions(camera_id, local_track_id);
CREATE INDEX IF NOT EXISTS idx_identity_assoc_employee ON identity_associations(employee_id);
CREATE INDEX IF NOT EXISTS idx_work_sessions_emp_time ON work_sessions(employee_id, start_time, end_time);
CREATE INDEX IF NOT EXISTS idx_daily_summaries_date ON daily_work_summaries(date, employee_id);

-- BRIN & B-Tree Indexes on Partitioned Time-Series Events
CREATE INDEX IF NOT EXISTS idx_loc_events_time ON location_events USING BRIN(timestamp);
CREATE INDEX IF NOT EXISTS idx_loc_events_session ON location_events(tracking_session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_act_events_time ON activity_events USING BRIN(timestamp);
CREATE INDEX IF NOT EXISTS idx_state_events_time ON state_events USING BRIN(timestamp);
CREATE INDEX IF NOT EXISTS idx_state_events_emp_time ON state_events(employee_id, timestamp);
```

---

## 3. Implementasi ORM & Migrations (SQLAlchemy 2.0 + Alembic)

Skema database di atas diimplementasikan secara modular pada package `packages/db/workvision_db/models/` dan siklus hidup migrasinya dikelola sepenuhnya oleh **Alembic** (tanpa ketergantungan pada script SQL statis).

### 3.1. Struktur Modul Model Terpisah

```
packages/db/workvision_db/
├── __init__.py                              # Root exports (Base, engine, session, models)
├── base.py                                  # DeclarativeBase SQLAlchemy 2.0
├── session.py                               # AsyncEngine & AsyncSession factory
└── models/                                  # Modular domain models
    ├── __init__.py                          # Centralized model registry
    ├── enums.py                             # Enum types (IdentityStatus, ObservedActivity, dll.)
    ├── organization.py                      # Department, Employee (BYTEA face embedding)
    ├── spatial.py                           # Building, Floor, Room, Camera, Zone, Workstation, CameraTopology
    ├── tracking.py                          # TrackingSession, IdentityAssociation
    ├── events.py                            # LocationEvent, ActivityEvent, StateEvent (Partitioned)
    ├── business.py                          # AttendanceEvent, WorkSession, DailyWorkSummary, EventOverride
    └── audit.py                             # AuditLog
```

### 3.2. Perintah Eksekusi Migrasi Database

```bash
# Menjalankan migrasi ke versi skema terbaru
uv run alembic upgrade head

# Memeriksa status migrasi saat ini
uv run alembic current

# Membuat file revisi migrasi baru secara otomatis
uv run alembic revision --autogenerate -m "nama_perubahan"

# Melakukan inspeksi DDL SQL offline
uv run alembic upgrade head --sql
```
