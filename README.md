# WorkVision AI — AI Vision Workforce Monitoring Engine

AI Vision Workforce Monitoring Engine adalah platform computer vision dan analytics tenaga kerja modern yang memanfaatkan feed CCTV/RTSP dan sistem absensi wajah untuk merekonstruksi timeline lokasi, aktivitas, dan sesi kerja pegawai secara otomatis, transparan, dan terukur.

---

## Struktur Repositori (Monorepo UV Workspace)

Workspace dikelola secara modular menggunakan fitur native **[uv workspaces](https://docs.astral.sh/uv/concepts/workspaces/)**:

```
workvision-ai/
├── apps/
│   ├── api/                    # [workvision-api] FastAPI REST & WebSocket Gateway
│   ├── vision-worker/          # [workvision-worker] RTSP Video Ingestion, YOLO Detection, Tracking
│   └── event-processor/        # [workvision-processor] Temporal State Machine & Analytics Engine
│
├── packages/
│   ├── config/                 # [workvision-config] Centralized Configuration & Environment Loader
│   ├── db/                     # [workvision-db] SQLAlchemy 2.0 Models & Alembic Migrations
│   ├── schemas/                # [workvision-schemas] Shared Pydantic Data Contracts & DTOs
│   └── shared/                 # [workvision-shared] Spatial Math, Foot-Point & IoU Utilities
│
├── models/                     # Weights & Model configs (YOLO, Re-ID)
│   ├── detection/
│   └── reid/
│
├── infrastructure/
│   └── docker/                 # Docker Compose & Container Configurations
│
├── pyproject.toml              # Root Workspace Configuration (tool.uv.workspace)
└── docs/                       # PRD, Architecture, Database Schema, API Docs
```

---

## Dokumentasi Utama

- **Product Requirements Document (PRD):** [`docs/PRD.md`](file:///c:/Users/dev%20perusahaan%20pst/workspaces/pst/workvision-ai/docs/PRD.md)
- **System Architecture & Technical Design:** [`docs/SYSTEM_ARCHITECTURE.md`](file:///c:/Users/dev%20perusahaan%20pst/workspaces/pst/workvision-ai/docs/SYSTEM_ARCHITECTURE.md)
- **Database Schema & DDL Specification:** [`docs/DATABASE_SCHEMA.md`](file:///c:/Users/dev%20perusahaan%20pst/workspaces/pst/workvision-ai/docs/DATABASE_SCHEMA.md)

---

## Quick Start (Development dengan `uv`)

### 1. Prasyarat
- [uv](https://docs.astral.sh/uv/) (Package & Workspace Manager)
- Docker & Docker Compose (untuk database PostgreSQL & broker Redis)
- GPU NVIDIA dengan CUDA 12+ (Opsional, untuk akselerasi hardware NVDEC & YOLO)

### 2. Setup Environment & Sinkronisasi Workspace
```bash
# 1. Salin konfigurasi environment template
cp .env.example .env

# 2. Sinkronkan seluruh workspace members
uv sync
```

### 3. Menjalankan Seluruh Stack Layanan (Docker Compose)
Seluruh ekosistem layanan (PostgreSQL, Redis, API Gateway, Vision Worker, dan Event Processor) dapat dijalankan secara terpadu melalui satu perintah Docker Compose:

```bash
# 1. Jalankan seluruh container layanan
docker compose -f infrastructure/docker/docker-compose.yml up -d

# 2. Terapkan migrasi skema database terbaru
uv run alembic upgrade head
```

### 4. Pengujian & Validasi Monorepo (Pytest Suite)
Seluruh kontrak data, model database, konfigurasi, dan integrasi diuji secara komprehensif melalui native workspace runner:

```bash
# Menjalankan seluruh test suite
uv run pytest -v
```

---

## Author & Maintainer

- **Nama:** Riki Ruswandi
- **GitHub:** [@mikeu-dev](https://github.com/mikeu-dev)
- **Email:** [rikiruswandi28@gmail.com](mailto:rikiruswandi28@gmail.com)

---

## Lisensi

Proyek ini dilisensikan di bawah ketentuan **[MIT License](file:///c:/Users/dev%20perusahaan%20pst/workspaces/pst/workvision-ai/LICENSE)** — lihat berkas [LICENSE](file:///c:/Users/dev%20perusahaan%20pst/workspaces/pst/workvision-ai/LICENSE) untuk detail selengkapnya.
