# PRD — AI Vision Workforce Monitoring Engine

**Versi:** 1.1  
**Tanggal:** 20 Agustus 2026  
**Status:** Approved  
**Jenis:** AI Computer Vision + Workforce Analytics  

---

## 1. Ringkasan Produk

AI Vision Workforce Monitoring Engine adalah sistem computer vision yang memanfaatkan **CCTV/RTSP** dan sistem **face attendance** perusahaan untuk membangun timeline keberadaan dan aktivitas pegawai secara otomatis.

Sistem tidak hanya menghitung apakah seorang pegawai hadir, tetapi berusaha mengetahui:

- kapan pegawai masuk;
- kapan pegawai keluar;
- lokasi pegawai;
- perpindahan antar-ruangan;
- perpindahan workstation;
- aktivitas/state pegawai;
- periode bekerja;
- meeting;
- break;
- away;
- periode yang tidak dapat ditentukan;
- total durasi kerja berdasarkan event yang terobservasi.

Sistem dirancang menggunakan pendekatan **event-driven**, sehingga hasil AI mentah dipisahkan dari interpretasi bisnis.

---

# 2. Problem Statement

Sistem absensi konvensional dapat mengetahui:

```text
08:03 → Clock In
17:04 → Clock Out
```

Tetapi tidak dapat menjawab:

> Apa yang terjadi selama periode tersebut?

Contohnya:

```text
08:03  Clock In
08:05  Working
10:15  Meeting
11:02  Working
12:01  Break
13:02  Working
15:30  Away
15:42  Working
17:04  Clock Out
```

Perusahaan membutuhkan sistem yang dapat membangun informasi tersebut dari CCTV secara otomatis tanpa mengharuskan pegawai melakukan input manual.

---

# 3. Tujuan Produk

## Primary Goal

Membangun engine yang mampu mengubah:

```text
CCTV + Attendance
```

menjadi:

```text
Employee Timeline
        ↓
Location Timeline
        ↓
Activity/State Timeline
        ↓
Work Session
        ↓
Work Duration
```

## Secondary Goals

Sistem diharapkan mampu:

1. melakukan person detection secara realtime;
2. melakukan multi-object tracking;
3. mempertahankan identitas sementara manusia;
4. menghubungkan track dengan Employee ID;
5. mendeteksi perpindahan zona;
6. mendukung beberapa kamera;
7. mendukung perpindahan workstation;
8. membedakan official break dan observed break;
9. menangani kondisi `UNKNOWN`;
10. menyimpan evidence untuk setiap keputusan AI.

---

# 4. Non-Goals

Versi awal sistem **tidak bertujuan**:

- melakukan pengawasan isi layar komputer;
- membaca isi monitor;
- merekam keyboard;
- menilai produktivitas pegawai secara subjektif;
- menentukan apakah pegawai "malas";
- memberikan sanksi otomatis;
- menggantikan sistem absensi;
- memastikan aktivitas manusia 100% akurat;
- mengidentifikasi manusia hanya berdasarkan workstation.

Work duration adalah **hasil observasi sistem**, bukan penilaian subjektif terhadap produktivitas.

---

# 5. Konsep Identitas

Sistem menggunakan beberapa jenis ID.

### Employee ID

Identitas resmi dari sistem kepegawaian/attendance.

```text
EMP001
```

### Global Track ID

Identitas manusia pada level global tracking.

```text
GTRK-001
```

### Local Track ID

Identitas tracking pada kamera tertentu.

```text
CAM02/TRK-83
```

### Workstation ID

Identitas tempat kerja.

```text
WS-017
```

Hubungannya:

```text
EMP001
   │
   └── GTRK-001
          │
          ├── CAM01/TRK17
          ├── CAM02/TRK83
          └── CAM03/TRK144
                     │
                     ▼
                  WS-017
```

**Workstation tidak digunakan sebagai Employee Identifier.**

---

# 6. Arsitektur Sistem

```text
                    ┌──────────────────────┐
                    │ Attendance System    │
                    │ Face Recognition     │
                    └──────────┬───────────┘
                               │
                         Employee ID
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Identity Engine      │
                    └──────────┬───────────┘
                               ▲
                               │
CCTV ──RTSP──► Video Ingestion (NVDEC/HW)
                    │
                    ▼
              Frame Processing (Drop-oldest Queue)
                    │
                    ▼
              Person Detection (YOLO)
                    │
                    ▼
            Multi-Object Tracking (ByteTrack)
                    │
                    ▼
              Track Management
                    │
                    ▼
             Identity Association (Spatio-Temporal Graph)
                    │
                    ▼
              Spatial Engine (Bottom-Center ROI)
                    │
                    ▼
             Activity Engine
                    │
                    ▼
               State Engine (Temporal Validation)
                    │
                    ▼
               Event Engine
                    │
                    ▼
              Session Engine
                    │
                    ▼
           Work Duration Engine
                    │
             ┌──────┴──────┐
             ▼             ▼
        PostgreSQL      Analytics API
      (Partitioned)        │
                           ▼
                       Dashboard
```

---

# 7. CCTV / Video Ingestion

## Input

Sistem harus mendukung sumber video berbasis:

```text
RTSP
```

Contoh:

```text
rtsp://camera-address/stream
```

## Requirements

Video ingestion harus:

- menerima stream CCTV secara simultan dari banyak kamera;
- melakukan decoding terakselerasi hardware (e.g. NVIDIA NVDEC / GStreamer / PyAV);
- menyediakan frame untuk inference dengan antrean *non-blocking / drop-oldest policy* agar tidak terjadi latensi kumulatif (*latency creep*);
- menangani reconnect otomatis ketika jaringan atau RTSP terputus;
- mendeteksi camera disconnect dan menghasilkan event `CAMERA_OFFLINE`;
- menyediakan sinkronisasi timestamp yang akurat (lihat Bagian 8.1);
- menjaga buffer memory tetap terkendali.

Sistem tidak mengirim setiap frame melalui HTTP API.

---

# 8. Frame Processing & Time Synchronization

CCTV dapat menghasilkan:

```text
25 FPS
```

Namun inference tidak harus dilakukan pada seluruh frame.

Konsep pipeline:

```text
25 FPS Video Stream
     ↓
Hardware Decode (NVDEC)
     ↓
Frame Sampling (5–10 FPS)
     ↓
Batch Detection Queue
     ↓
Tracking & Spatial Projection
```

Tujuannya mengurangi beban GPU tanpa kehilangan stabilitas tracking. Nilai FPS final akan ditentukan melalui benchmark footage aktual.

## 8.1. Time Synchronization & Clock Drift Mitigation

1. **NTP Standard:** Seluruh IP Camera, mesin absensi (*face attendance*), dan server AI wajib terhubung ke server **NTP (Network Time Protocol)** lokal yang sama.
2. **Ingestion Timestamping:** Jika kamera tidak menyediakan timestamp RTP/PTS yang andal, worker ingestion akan menyematkan **Server Arrival Wall-Clock Timestamp (UTC)** berpresisi milidetik pada saat frame didecode.

---

# 9. Person Detection

Sistem mendeteksi manusia dari frame CCTV.

Output minimal:

```json
{
  "bbox": [x1, y1, x2, y2],
  "confidence": 0.94,
  "timestamp": "2026-08-20T08:05:00.120Z",
  "foot_point": [cx, y2]
}
```

Model awal dapat menggunakan keluarga model object detection modern seperti YOLO (v8/v11).

Model final harus ditentukan berdasarkan:

- detection accuracy (mAP);
- small-person detection;
- occlusion resistance;
- robustness terhadap variasi pencahayaan & sudut kamera;
- FPS throughput & efisiensi utilisasi GPU.

---

# 10. Multi-Object Tracking

Detector menghasilkan detection bounding box.

Tracker mengubahnya menjadi continuous trajectory:

```text
Detection
    ↓
Tracker (ByteTrack / BoT-SORT)
    ↓
Track ID
```

Contoh:

```text
CAM01/TRK-17
CAM01/TRK-18
CAM01/TRK-19
```

Tracker harus mampu menangani:

- orang berjalan;
- orang berhenti / diam lama;
- occlusion (tertutup sejenak oleh orang lain atau perabot);
- crossing (dua orang bersilangan);
- temporary disappearance;
- track creation & termination yang bersih.

---

# 11. Identity Association

Tracker hanya mengetahui:

> "Ini manusia yang sama."

Identity Engine harus menentukan:

> "Manusia ini adalah EMP001."

Evidence berasal dari multi-sinyal:

```text
Attendance Context (Clock-in timestamp + Entrance camera)
+
Person Re-ID Embedding
+
Temporal Consistency
+
Spatial Consistency (Camera Topology Graph)
```

Status identity:

```text
UNASSIGNED
     ↓
CANDIDATE
     ↓
PROBABLE
     ↓
CONFIRMED
```

Jika confidence tidak mencukupi:

```text
UNKNOWN
```

Sistem **tidak boleh memaksakan identitas** ketika confidence rendah.

---

# 12. Face Recognition

Face recognition digunakan terutama sebagai **identity anchor**, khususnya pada titik absensi/entrance.

Contoh:

```text
Face Attendance
      ↓
EMP001
      ↓
Presence Session
```

CCTV yang jauh atau sudut tinggi tidak harus mampu mengenali wajah setiap saat.

Setelah identity anchor terbentuk di pintu masuk, sistem mempertahankan identitas menggunakan:

```text
Tracking + Re-ID + Spatio-Temporal Graph
```

---

# 13. Multi-Camera Tracking & Spatio-Temporal Graph Gating

Sistem harus mampu menghubungkan track antar-kamera tanpa mengalami *identity drift* (terutama di lingkungan kantor dengan pakaian/seragam yang mirip).

### Camera Topology Graph

Topologi kamera dimodelkan sebagai graf berarah dengan batasan waktu transit fisik:

```text
CAM01 (Entrance) ──[2s - 15s]──► CAM02 (Corridor) ──[3s - 20s]──► CAM03 (Room A)
```

### Spatio-Temporal Gating Rule

- Pencarian Re-ID **tidak dilakukan secara global brute-force** ke seluruh kamera.
- Kandidat Re-ID dibatasi hanya pada kamera tetangga yang secara fisik terhubung jika seseorang keluar dari jangkauan kamera sebelumnya dalam jendela waktu transit yang realistis ($t_{min} \le \Delta t \le t_{max}$).
- Jika seseorang muncul di CAM03 tanpa melewati CAM02 dalam rentang waktu yang valid, pencocokan identitas memerlukan verifikasi ulang (*higher confidence threshold* atau *face anchor baru*).

---

# 14. Spatial Engine

Sistem menggunakan hierarki struktur fisik:

```text
Building
   ↓
Floor
   ↓
Room
   ↓
Zone
   ↓
Workstation
```

Contoh:

```text
Building A
└── Floor 2
    └── Engineering Room
        ├── Work Area
        │   ├── WS001
        │   ├── WS002
        │   └── WS003
        │
        ├── Meeting Area
        └── Exit
```

Workstation bersifat opsional dan pegawai dapat berpindah workstation secara dinamis.

---

# 15. Zone / ROI & Spatial Anchoring

Setiap kamera dapat memiliki polygon ROI 2D yang dikalibrasikan ke area lantai.

Contoh:

```text
CAM03
├── WORK_AREA
├── MEETING_AREA
├── PANTRY
└── EXIT
```

Event:

```text
ZONE_ENTER
ZONE_EXIT
```

### Standar Titik Acuan Spasial (Spatial Foot Anchor)

Untuk mencegah bias perspektif pada kamera bersudut tinggi, kalkulasi **Point-in-Polygon (PiP)** wajib menggunakan **titik tengah bawah bounding box (Foot Point)**:

$$\text{Foot Point} = \left( \frac{x_1 + x_2}{2}, y_2 \right)$$

Titik ini merepresentasikan posisi tumpuan kaki manusia di lantai.

---

# 16. Activity Engine

Activity merupakan observasi visual murni pada level frame/track.

Contoh:

```text
SITTING
STANDING
WALKING
MOVING
STATIONARY
PERSON_INTERACTION
OBJECT_INTERACTION
```

Activity tidak langsung dianggap sebagai state bisnis.

---

# 17. State Engine

State merupakan interpretasi business-level dari gabungan lokasi, aktivitas visual, dan status absensi.

State utama:

```text
WORKING
MEETING
BREAK
AWAY
UNKNOWN
```

Contoh inferensi state:

```text
WORK_AREA + SITTING + LOW_MOTION + DURATION > 2 MIN + CLOCKED_IN → WORKING
MEETING_ROOM + >= 2 PEOPLE + INTERACTION → MEETING
PANTRY / LOUNGE + STAY > 3 MIN → BREAK
EXIT_DETECTED / OUT_OF_VIEW > THRESHOLD → AWAY
POOR_CONFIDENCE / OCCLUSION → UNKNOWN
```

---

# 18. Temporal State Validation (Debounce & Hysteresis)

State tidak boleh berubah hanya karena fluktuasi 1 frame (e.g. berdiri mengambil pulpen tidak boleh langsung mengubah status `WORKING` menjadi `AWAY`).

Pipeline:

```text
Observation Ticks
       ↓
Candidate State (Rolling Window)
       ↓
Temporal Validation (Hysteresis Filter: e.g. min 30-60 detik konsisten)
       ↓
Confirmed State Transition
```

Hal ini mengeliminasi *false transition* dan kebisingan data (*jitter*).

---

# 19. Unknown State

`UNKNOWN` merupakan state resmi yang valid dan terhormat dalam sistem.

Kondisi `UNKNOWN` dipicu oleh:

- Track Lost / Blind Spot kamera;
- Occlusion parah dalam durasi tertentu;
- Pencahayaan buruk atau resolusi rendah;
- Identity confidence di bawah threshold ambang batas;
- Aktivitas ambigu.

Sistem tidak boleh menganggap:

```text
TRACK LOST = AWAY (Kecuali terkonfirmasi melewati pintu keluar/EXIT)
NO DETECTION = NOT WORKING
```

---

# 20. Attendance Integration

Attendance (mesin absensi wajah) menjadi sumber kebenaran (*ground truth*) untuk:

```text
CLOCK_IN
BREAK_OUT
BREAK_IN
CLOCK_OUT
```

CCTV melengkapi konteks:

```text
OBSERVED_LOCATION
OBSERVED_ACTIVITY
OBSERVED_STATE
```

Keduanya saling melengkapi dan tidak saling menimpa secara sepihak.

---

# 21. Official Break vs Observed Break

Sistem membedakan dengan jelas:

### Official Break

Berasal dari aksi resmi sistem absensi:

```text
12:01 BREAK_OUT
13:02 BREAK_IN
```

### Observed Break

Berasal dari observasi pergerakan CCTV:

```text
15:30 → Pindah ke PANTRY
15:42 → Kembali ke WORK_AREA
```

Observed break disimpan sebagai data analitik visual dan **tidak mengubah data absensi resmi secara otomatis**.

---

# 22. Event Engine

### Raw Events

```text
PERSON_DETECTED
TRACK_CREATED
TRACK_UPDATED
TRACK_LOST
FACE_MATCH
ZONE_ENTER
ZONE_EXIT
ATTENDANCE_IN
ATTENDANCE_OUT
```

### Derived / State Events

```text
WORK_STARTED / WORK_ENDED
MEETING_STARTED / MEETING_ENDED
BREAK_STARTED / BREAK_ENDED
AWAY_STARTED / AWAY_ENDED
SESSION_STARTED / SESSION_ENDED
```

---

# 23. Work Session Engine

Event transisi digunakan untuk membangun continuous session timeline:

```text
08:05 → 10:15 | WORK (2h 10m)
10:15 → 11:02 | MEETING (0h 47m)
11:02 → 12:01 | WORK (0h 59m)
12:01 → 13:02 | BREAK (1h 01m)
13:02 → 17:04 | WORK (4h 02m)
```

---

# 24. Work Duration Engine

Output agregasi harian:

```text
Presence       9h 01m
Working        6h 45m
Meeting        1h 02m
Break          0h 52m
Away           0h 21m
Unknown        0h 01m
```

Perhitungan total waktu produktif/kerja berbasis aturan bisnis:

$$\text{Work-related Duration} = \text{Total Working} + \text{Total Meeting}$$

---

# 25. Event Evidence & Audit Trail

Setiap kesimpulan state penting wajib menyimpan *structured evidence*:

```json
{
  "employee_id": "EMP001",
  "session_id": "SESS-20260820-001",
  "state": "WORKING",
  "confidence": 0.91,
  "start_time": "2026-08-20T08:05:00Z",
  "end_time": "2026-08-20T10:15:00Z",
  "evidence": {
    "camera_id": "CAM03",
    "zone": "WORK_AREA",
    "dominant_posture": "SITTING",
    "motion_level": "LOW",
    "track_id": "TRK-144",
    "attendance_state": "CLOCKED_IN"
  }
}
```

---

# 26. Database & Persistence Strategy

Sistem menggunakan **PostgreSQL** dengan strategi partisi time-series:

### Entitas Master
- `employees`
- `cameras`
- `zones`
- `workstations`
- `camera_topologies`

### Entitas Sesi & Asosiasi
- `tracking_sessions`
- `identity_associations`

### Entitas Time-Series (Declarative Partitioning by Range/Day)
- `location_events` (Partitioned)
- `activity_events` (Partitioned)
- `state_events` (Partitioned)

### Entitas Agregasi & Audit
- `work_sessions`
- `daily_work_summaries`
- `event_overrides` (*Human-in-the-loop corrections*)
- `audit_logs`

> **Prinsip Efisiensi Storage:** Inference ticks mentah (per-frame) diproses di in-memory stream (Redis Streams/Memory Queue). Hanya **state transitions**, **zone boundary crossing**, dan **heartbeat periodic snapshots (e.g. per 60s)** yang dipersistensikan ke database relasional.

---

# 27. Data Retention & Privacy Lifecycle

1. **Raw Video Stream:** Dikelola oleh NVR perusahaan (retensi pendek sesuai kapasitas lokal NVR, misal 7–14 hari). AI Engine tidak menyimpan continuous raw video.
2. **AI Frame Evidence (Crops):** Disimpan hanya saat terjadi incident/dispute dengan enkripsi at-rest, retensi maksimal 14–30 hari.
3. **Partitioned Events:** Disimpan selama 90–180 hari untuk keperluan audit dan penyesuaian model.
4. **Daily Aggregated Summaries:** Disimpan jangka panjang (> 1 tahun) untuk reporting dan tren analitik HR.

---

# 28. Realtime Architecture

```text
[RTSP Streams] 
     │
     ▼ (Hardware NVDEC Decode)
[Vision Workers] ──(In-memory Ring Buffer)──► [Detection + Tracking + Spatial]
     │
     ▼ (JSON Event Stream)
[Redis Streams / Broker]
     │
     ▼
[Event & State Processor] (Temporal Validation & State Machine)
     │
     ├──► [PostgreSQL Database] (Persist State Transitions & Sessions)
     └──► [FastAPI WebSocket Hub] ──► [SvelteKit Realtime Dashboard]
```

---

# 29. Teknologi

- **Vision & AI:** Python 3.10+, PyTorch, Ultralytics YOLO (v8/v11), ByteTrack / BoT-SORT, OSNet / FastReID, OpenCV / PyAV (NVDEC).
- **Backend API & WebSockets:** FastAPI, Uvicorn, Pydantic v2.
- **Database & ORM:** PostgreSQL 15+, SQLAlchemy 2.0 (Async/Sync), Alembic (Migrations), AsyncPG, Psycopg2-binary (`packages/db`).
- **Message Broker / Caching:** Redis Streams (atau In-Memory Asyncio Queue untuk single-node deployment).
- **Frontend Dashboard:** SvelteKit, TailwindCSS, Chart.js / LayerChart, WebSocket client.
- **Infrastruktur & Deployment:** Docker, Docker Compose, NVIDIA Container Toolkit (CUDA 12+).

---

# 30. Repository Structure

```text
workvision-ai/
├── apps/
│   ├── vision-worker/          # RTSP Ingestion, YOLO Detection, ByteTrack, Re-ID
│   ├── event-processor/        # State Machine, Spatial Analysis, Temporal Filter
│   ├── api/                    # FastAPI REST API & WebSocket Realtime Gateway
│   └── dashboard/              # SvelteKit Analytics & Management Dashboard
│
├── packages/
│   ├── config/                 # Centralized configuration & environment loader
│   ├── db/                     # SQLAlchemy 2.0 Modular Models & Alembic Migrations
│   ├── schemas/                # Shared Pydantic data contracts & DTOs
│   └── shared/                 # Shared utilities (logging, spatial math, crypto)
│
├── models/                     # Weights & Model configs (YOLO, Re-ID)
│   ├── detection/
│   └── reid/
│
├── infrastructure/
│   └── docker/                 # Dockerfile & docker-compose definitions
│
└── docs/                       # PRD, Architecture, Database Schema, API Spec
```

---

# 31. MVP Roadmap

## MVP 1 — Vision Foundation & Single-Camera Spatial Tracking
- Ingestion RTSP yang stabil dengan auto-reconnect.
- Deteksi manusia realtime menggunakan YOLO terakselerasi GPU.
- Multi-object tracking (ByteTrack) dengan Track ID stabil.
- Konfigurasi ROI Zone polygon dan deteksi `ZONE_ENTER` / `ZONE_EXIT` berbasis *bottom-center foot point*.
- Visualisasi realtime di dashboard lokal / video stream viewer.

## MVP 2 — Multi-Camera & Spatio-Temporal Topology
- Pengelolaan multiple RTSP streams simultan.
- Topologi graf antar-kamera dan spatio-temporal gating.
- Handover track antar-kamera di area koridor/pintu.

## MVP 3 — Attendance & Identity Association
- Integrasi webhook/API data kehadiran (*Face Attendance*).
- Asosiasi otomatis antara Clock-In event dengan Track ID di entrance camera (*Identity Anchor*).
- Pemeliharaan identitas Employee ID pada continuous track.

## MVP 4 — Activity & Posture Engine
- Ekstraksi aktivitas visual (Sitting, Standing, Moving, Walking, Stationary).
- Evaluasi interaksi dengan workstation / meeting table.

## MVP 5 — State Machine & Temporal Validation
- Transformasi activity + spatial context menjadi business states (`WORKING`, `MEETING`, `BREAK`, `AWAY`, `UNKNOWN`).
- Temporal filter (hysteresis & debounce) untuk mengeliminasi false state transitions.

## MVP 6 — Work Sessions, Duration Aggregator & Enterprise Analytics
- Rekonstruksi work session otomatis.
- Kalkulasi total durasi kerja harian.
- Dashboard analytics eksekutif & reporting timeline pegawai.

---

# 32. Success Metrics

### Vision & Tracking
- **Person Detection Recall:** $\ge 95\%$ pada kondisi pencahayaan normal.
- **MOTA (Multiple Object Tracking Accuracy):** $\ge 85\%$.
- **ID Switch Rate:** $\le 2$ switch per 10 menit per orang pada area tidak padat.

### Spatial & State
- **Zone Boundary Accuracy:** $\ge 98\%$ (menggunakan *bottom-center foot point*).
- **State Transition False Positive Rate:** $\le 3\%$ setelah temporal validation (30s window).
- **Unknown Resolution:** Status `UNKNOWN` terselesaikan dalam $< 10$ detik setelah visibilitas pulih.

### System Performance
- **Ingestion & Tracking Throughput:** $\ge 15$ FPS per kamera pada resolusi 1080p.
- **End-to-End Latency:** $\le 500$ ms dari frame RTSP hingga event diterima WebSocket dashboard.
- **Stream Reconnect Resiliency:** Reconnect otomatis dalam $< 5$ detik setelah RTSP drop tanpa crash memori.

---

# 33. Non-Functional Requirements

- **High Availability & Resiliency:** Worker mampu me-recover stream kamera yang terputus tanpa restart container.
- **Auditability:** Seluruh event transisi state memiliki metadata penjelas (*evidence payload*).
- **Scalability:** Arsitektur modular memisahkan proses berat (GPU vision inference) dari pemrosesan logika bisnis (event processor).
- **Replayability:** Sistem mampu melakukan replay event log historis untuk memverifikasi atau menguji ulang logika state machine baru.

---

# 34. Dashboard & User Experience

Dashboard menyediakan 3 tampilan utama:

1. **Live Spatial & Video View:** Visualisasi denah kantor / zona dengan posisi live avatar pegawai dan indikator status kamera.
2. **Employee Daily Timeline:** Tampilan bar chart horizontal interaktif yang memetakan aktivitas harian pegawai sejak Clock In hingga Clock Out.
3. **Department & Workforce Analytics:** Matriks agregasi total jam kerja, rasio waktu meeting vs fokus kerja, dan distribusi kehadiran per ruangan.

---

# 35. Privacy, Governance & UU PDP Compliance

Sistem mengadopsi prinsip **Privacy by Design** dan mematuhi **UU Pelindungan Data Pribadi No. 27/2022 (UU PDP)**:

1. **Dasar Pemrosesan yang Sah (Legal Basis):** Pemrosesan data biometrik dan kehadiran dilakukan atas dasar kepatuhan operasional kerja dan kesepakatan Perjanjian Kerja Bersama (PKB).
2. **Enkripsi Data Biometrik:** Embedding wajah dan fitur Re-ID dienkripsi *at-rest* menggunakan AES-256 dan dilindungi kontrol akses berbasis peran (RBAC).
3. **Mekanisme Koreksi (Human-in-the-Loop Override):**
   - Hasil inferensi AI tidak langsung menjadi dasar sanksi atau tindakan disipliner tanpa tinjauan manusia.
   - Supervisor/HR dapat menambahkan layer `MANUAL_OVERRIDE` jika terjadi anomali atau kesalahan identifikasi. Raw event AI tetap dipertahankan untuk integritas audit trail.
4. **Data Minimization:** Tidak ada perekaman layar monitor, isi pesan, atau audio percakapan.

---

# 36. Matriks Risiko & Mitigasi

| Risiko | Dampak | Mitigasi Arsitektur |
| :--- | :---: | :--- |
| **Pakaian/Seragam Pegawai Mirip** | Tinggi | Terapkan *Spatio-Temporal Graph Gating* pada Re-ID (batasi pencocokan hanya pada kamera tetangga dan jendela waktu realistis). |
| **RTSP Latency Creep** | Sedang | Terapkan *drop-oldest queue policy* di thread decoding video worker. |
| **Kamera Mati / Jaringan Putus** | Sedang | Background thread auto-reconnect dengan exponential backoff dan penerbitan event `CAMERA_OFFLINE`. |
| **Perspektif Bounding Box Bias** | Sedang | Gunakan *bottom-center foot point* untuk seluruh perhitungan spatial ROI. |
| **Volume Event Membebani DB** | Tinggi | Persistensikan hanya event transisi state dan gunakan PostgreSQL time-range partitioning. |
| **Salah Menilai Pegawai Away** | Tinggi | Validasi temporal hysteresis (min 1-2 menit) dan klasifikasi ke state `UNKNOWN` sebelum `AWAY`. |
| **Salah Identifikasi Pegawai** | Tinggi | Confidence score threshold ketat; fallback ke `UNKNOWN` jika ragu; layer koreksi `MANUAL_OVERRIDE`. |

---

# 37. Prinsip Arsitektur Utama (Non-Negotiable)

```text
1. Employee ID ≠ Track ID
2. Track ID ≠ Workstation ID
3. Workstation bukan identity
4. Missing detection ≠ Away
5. Unknown ≠ Work failure
6. Activity ≠ State
7. CCTV ≠ Attendance System
8. Raw Event ≠ Derived Event
9. Frame ≠ Event
10. Work duration = hasil rekonstruksi timeline
```

> **Aturan Emas:** Sistem harus selalu lebih memilih menyatakan `UNKNOWN` daripada menghasilkan kesimpulan identitas atau status kerja yang keliru.

---

# 38. Definition of Done — MVP 1 (Vision Foundation)

MVP 1 dinyatakan selesai dan sukses apabila:

- [ ] Ingestion RTSP stabil menerima minimal 1 stream CCTV 1080p tanpa memory leak.
- [ ] Worker mampu reconnect otomatis dalam $< 5$ detik saat RTSP terputus secara sengaja selama 30 detik.
- [ ] Person detection berjalan realtime ($\ge 15$ FPS) terakselerasi GPU dengan model YOLO.
- [ ] Multi-object tracking (ByteTrack) menghasilkan Track ID yang konsisten saat subjek berjalan dan berhenti.
- [ ] Konfigurasi Polygon ROI dapat dimuat secara dinamis dari file konfigurasi/database.
- [ ] Titik tumpuan *bottom-center foot point* berhasil memicu event `ZONE_ENTER` dan `ZONE_EXIT` secara akurat.
- [ ] Event transisi zona dipublikasikan ke message broker / stream dalam format JSON terstandar.
- [ ] Tersedia visualizer/dashboard sederhana untuk memverifikasi stream video, bounding box, track ID, dan batas polygon ROI secara realtime.
