# System Architecture & Technical Design Document

**Sistem:** AI Vision Workforce Monitoring Engine  
**Dokumen:** System Architecture & Technical Specification  
**Versi:** 1.0  
**Tanggal:** 20 Agustus 2026  
**Status:** Approved Technical Blueprint  

---

## 1. Ikhtisar Arsitektur Sistem

AI Vision Workforce Monitoring Engine dirancang menggunakan arsitektur **modular, decoupled, dan event-driven**. Sistem memisahkan proses komputasi computer vision intensif (*heavy GPU inference*) dari pemrosesan logika bisnis, state machine, dan agregasi analitik.

```
┌────────────────────────────────────────────────────────────────────────┐
│                              EDGE / ON-PREMISE                         │
│                                                                        │
│  ┌──────────────┐      RTSP       ┌─────────────────────────────────┐  │
│  │  CCTV IP CAM ├────────────────►│       Vision Worker             │  │
│  └──────────────┘                 │  - Hardware NVDEC Decode        │  │
│  ┌──────────────┐      RTSP       │  - Drop-Oldest Frame Queue      │  │
│  │  CCTV IP CAM ├────────────────►│  - YOLO Person Detection (GPU)  │  │
│  └──────────────┘                 │  - ByteTrack MOT Engine         │  │
│                                   │  - Foot-Point Spatial Engine    │  │
│                                   └───────────────┬─────────────────┘  │
│  ┌──────────────┐      Webhook/HTTP               │ Raw Vision Events  │
│  │ Face Attend. ├─────────────────┐               ▼                    │
│  └──────────────┘                 │     ┌───────────────────┐          │
│                                   └────►│   Redis Streams   │          │
│                                         │  (Message Broker) │          │
│                                         └─────────┬─────────┘          │
│                                                   │ Ingestion Stream   │
│                                                   ▼                    │
│                                   ┌─────────────────────────────────┐  │
│                                   │        Event Processor          │  │
│                                   │  - Identity Associator          │  │
│                                   │  - Spatio-Temporal Graph Gating │  │
│                                   │  - Temporal State Machine       │  │
│                                   │  - Session & Duration Engine    │  │
│                                   └───────┬─────────────────┬───────┘  │
│                                           │                 │          │
│                           State Events &  │                 │ Realtime │
│                           Work Sessions   │                 │ Broadcast│
│                                           ▼                 ▼          │
│                              ┌─────────────────┐   ┌─────────────────┐ │
│                              │   PostgreSQL    │   │  FastAPI Server │ │
│                              │  (Partitioned)  │   │  (REST & WS)    │ │
│                              └─────────────────┘   └────────┬────────┘ │
│                                                             │          │
│                                                             ▼          │
│                                                    ┌─────────────────┐ │
│                                                    │ SvelteKit UI    │ │
│                                                    │ (Dashboard)     │ │
│                                                    └─────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Rincian Komponen Arsitektur

### 2.1. Vision Worker (`apps/vision-worker`)
Worker independen yang menangani akuisisi video stream dan inferensi model AI.

* **Tanggung Jawab:**
  1. Melakukan koneksi RTSP berkelanjutan dengan mekanisme *auto-reconnect*.
  2. Melakukan decoding frame menggunakan akselerasi GPU (NVIDIA NVDEC melalui PyAV / GStreamer / OpenCV).
  3. Mengelola antrean frame berbasis *drop-oldest queue* (maksimal buffer 1 frame) untuk menjamin latensi streaming selalu nol (*zero cumulative latency*).
  4. Menjalankan *batch detection* dengan model YOLO (FP16 / TensorRT).
  5. Menjalankan algoritma tracking *ByteTrack* untuk menjaga stabilitas Track ID lokal per kamera.
  6. Menghitung koordinat tumpuan kaki (*Foot Point*: $[(x_1 + x_2)/2, y_2]$) dan melakukan evaluasi spasial *Point-in-Polygon (PiP)* terhadap ROI Zone.
  7. Mempublikasikan *Raw Vision Events* ke Redis Streams.

### 2.2. Event Broker (`Redis Streams`)
Lapisan perantara pesan asinkron berkecepatan tinggi.

* **Channel/Stream Utama:**
  - `stream:vision:events` : Menerima raw detections, track updates, dan zone crossings dari seluruh Vision Worker.
  - `stream:attendance:events` : Menerima log absensi masuk/keluar dari sistem face attendance.
  - `stream:system:health` : Heartbeat dan status koneksi kamera dari setiap worker.

### 2.3. Event & State Processor (`apps/event-processor`)
Engine cerdas berbasis aturan (*rule engine*) dan mesin status berjangka waktu (*temporal state machine*).

* **Tanggung Jawab:**
  1. **Identity Association:** Menghubungkan log Face Attendance dengan Track ID di kamera entrance (*Identity Anchor*), lalu menyebarkan identitas melalui *Spatio-Temporal Graph Gating*.
  2. **Temporal Validation (Debounce & Hysteresis):** Memastikan transisi state (misal `WORKING` $\to$ `AWAY`) hanya terpicu jika subjek konsisten berada pada kondisi tersebut selama periode minimum (default: 30–60 detik).
  3. **Work Session Engine:** Menggabungkan transisi status menjadi rentang sesi kerja yang kontinu.
  4. **Work Duration Engine:** Menghitung total durasi kehadiran, kerja, meeting, break, away, dan unknown per hari.
  5. **Database Persistence:** Menuliskan event perubahan state, sesi kerja, dan agregasi harian ke PostgreSQL.
  6. **WebSocket Relay:** Meneruskan event yang telah divalidasi ke FastAPI untuk ditampilkan secara realtime di dashboard.

### 2.4. Backend API & WebSocket Hub (`apps/api`)
Layanan API RESTful dan gateway komunikasi dua arah berbasis WebSocket.

* **Tanggung Jawab:**
  1. Menyediakan REST endpoints untuk konfigurasi kamera, poligon ROI, master data pegawai, dan riwayat analitik.
  2. Mengelola koneksi WebSocket untuk live streaming event, bounding box coordinates, dan status spasial ke frontend.
  3. Menyediakan API untuk koreksi manual (*Human-in-the-Loop Override*).
  4. Mengelola autentikasi dan kontrol akses berbasis peran (RBAC).

### 2.5. Frontend Dashboard (`apps/dashboard`)
Aplikasi web modern berbasis SvelteKit untuk visualisasi operasional.

* **Tanggung Jawab:**
  1. Menampilkan *Live Floor Plan / Spatial View* secara interaktif.
  2. Menampilkan *Employee Daily Timeline* (Gantt-chart view aktivitas kerja harian).
  3. Menyediakan antarmuka editor poligon ROI kamera secara visual (*drag & drop polygon editor*).
  4. Menyediakan modul audit trail dan form koreksi status bagi supervisor/HR.

### 2.6. Database & ORM Layer (`packages/db`)
Package terpusat untuk model data modular dan manajemen siklus hidup skema database PostgreSQL.

* **Tanggung Jawab:**
  1. Menyediakan model domain modular berbasis **SQLAlchemy 2.0** (`organization`, `spatial`, `tracking`, `events`, `business`, `audit`, `enums`).
  2. Mengelola koneksi asynchronous (`AsyncEngine`, `AsyncSession`) dan dependency injection untuk FastAPI & Event Processor.
  3. Mengelola versioning dan eksekusi migrasi skema database menggunakan **Alembic** (`0001_initial_schema.py` dan `uv run alembic upgrade head`).
  4. Menyediakan dukungan native untuk tabel berpartisi time-series (`location_events`, `activity_events`, `state_events`) dan stored computed column.

---

## 3. Detail Pipeline Teknis

### 3.1. Ingestion Pipeline & Resiliency Matrix

```
[RTSP Stream] ──► [Decoded Packet] ──► [Frame Buffer (Capacity=1)] ──► [Inference Queue]
                         │                         ▲
                         │ (If Buffer Full)        │
                         └─────────────────────────┘ (Drop Old Frame)
```

1. **Drop Policy:** Antrean decoding menggunakan ring buffer dengan kapasitas ukuran = 1. Jika inference thread sedang sibuk memproses frame sebelumnya, frame baru yang masuk akan langsung menimpa frame lama di buffer. Ini mencegah *latency creep* di mana tampilan tertinggal beberapa detik dari waktu nyata.
2. **Auto-Reconnect Strategy:**
   - Deteksi stream putus melalui timeout pembacaan frame (threshold: 3 detik).
   - Pola reconnect menggunakan *Exponential Backoff with Jitter* ($1\text{s}, 2\text{s}, 4\text{s}, 8\text{s}, \dots, \max 30\text{s}$).
   - Saat terputus, worker menerbitkan event `CAMERA_OFFLINE` ke broker. Saat tersambung kembali, menerbitkan event `CAMERA_ONLINE`.
3. **Sinkronisasi Timestamp:**
   - Menggunakan format UTC ISO-8601 berpresisi milidetik.
   - Timestamp disematkan langsung oleh ingestion worker saat frame selesai didecode (`ingestion_timestamp`).

---

### 3.2. Vision & Tracking Pipeline (ByteTrack + Spatial Foot Point)

```
                       [Input Frame 1080p]
                                │
                                ▼ (Resize & Letterbox to 640x640)
                   [YOLOv8/v11 Person Detector]
                                │
                                ▼ Detections: [x1, y1, x2, y2, conf]
                     [ByteTrack Multi-Object Tracker]
                                │
                                ▼ Confirmed Tracks: [track_id, bbox]
                   [Foot-Point Extraction: cx, y2]
                                │
                                ▼
                   [Point-in-Polygon (PiP) ROI Gating]
                                │
                                ▼
              [Zone Events: ZONE_ENTER / ZONE_EXIT]
```

* **Foot-Point Formulation:**
  $$\text{Foot Point } P = \left( \frac{x_1 + x_2}{2}, y_2 \right)$$
* **Point-in-Polygon (PiP) Algorithm:** Menggunakan algoritma *Ray Casting* teroptimasi (vektorisasi C / Shapely) yang mengecek apakah titik $P$ berada di dalam poligon zona $[(x_a, y_a), (x_b, y_b), \dots]$.
* **Zone State Memory:** Worker menyimpan dictionary lokal `current_zones = {track_id: zone_id}`.
  - Jika $P \in \text{Zone } B$ dan sebelumnya $P \in \text{Zone } A$, terbitkan `ZONE_EXIT(Zone A)` lalu `ZONE_ENTER(Zone B)`.

---

### 3.3. Identity Association & Spatio-Temporal Graph

Untuk memitigasi *identity drift* pada lingkungan kerja di mana pegawai berpakaian serupa:

```
[Face Attendance @ Entrance] ──► Identity Anchor (EMP001 @ 08:03:00)
                                      │
                                      ▼
                        [CAM01 / Entrance Camera]
                        Match: Foot Point near Turnstile @ 08:03:00
                        Bind: EMP001 ──► CAM01/TRK-17 (CONFIRMED)
                                      │
                                      ▼ (Transition through Topology)
                        [CAM02 / Corridor Camera]
                        Condition: Transit time from CAM01 = [2s - 15s]
                        Re-ID Embedding Similarity + Topology Gating
                        Bind: EMP001 ──► CAM02/TRK-83 (CONFIRMED)
```

* **Camera Topology Graph Matrix:**
  Setiap edge antara Kamera $A$ dan Kamera $B$ memiliki parameter:
  - $t_{\min}$: Waktu tempuh tercepat fisik manusia antar-kamera.
  - $t_{\max}$: Waktu tempuh maksimal yang wajar.
  - $S_{\text{threshold}}$: Ambang batas minimum kesamaan cosine embedding Re-ID.
* Jika seseorang muncul di Kamera $C$ tanpa melewati lintasan graf yang valid, sistem **tidak mengasumsikan identitas secara otomatis**, melainkan menandai status sebagai `CANDIDATE` atau `UNKNOWN`.

---

### 3.4. State Engine & Temporal Validation (Hysteresis Filter)

State bisnis tidak diubah secara instan berdasarkan observasi single frame.

```
Raw Ticks: [W, W, W, W, S, S, S, S, S, S, S, S, ...]  (W = Work, S = Stand/Walk)
Window:    [---------- 30 seconds -----------]
Filter:    Majority vote & Minimum Continuous Duration Threshold
Result:    State transition triggered ONLY when threshold is met.
```

* **State Priority Matrix:**
  1. `MEETING`: Jika subjek berada di dalam `MEETING_ROOM` dengan $\ge 2$ orang selama $\ge 2$ menit.
  2. `BREAK`: Jika subjek berada di `PANTRY`/`LOUNGE` selama $\ge 3$ menit, ATAU ada event absensi `BREAK_OUT`.
  3. `WORKING`: Jika subjek berada di `WORK_AREA` dengan posisi `SITTING`/`STATIONARY` dan status kehadiran `CLOCKED_IN`.
  4. `AWAY`: Jika subjek terdeteksi keluar gedung melalui `EXIT_ZONE` atau tidak terdeteksi pada kamera manapun selama $> 5$ menit tanpa ada occlusion flag.
  5. `UNKNOWN`: Kondisi default saat confidence identitas rendah atau subjek berada di area blind spot.

---

## 4. Hardware Sizing & Capacity Guidelines

| Komponen | Spesifikasi Minimum (1–4 Kamera) | Rekomendasi Production (8–16 Kamera) |
| :--- | :--- | :--- |
| **GPU** | NVIDIA RTX 3060 (12GB VRAM) / T4 | NVIDIA RTX 4080 (16GB) / A4000 / L4 |
| **CPU** | 8 Cores (Intel i7 Gen 12 / AMD Ryzen 7) | 16–32 Cores (Intel Xeon / AMD EPYC) |
| **RAM** | 16 GB DDR4/DDR5 | 32–64 GB DDR5 ECC |
| **Storage** | 512 GB NVMe SSD | 1 TB–2 TB NVMe SSD (PCIe Gen 4) |
| **Network** | 1 Gbps Ethernet Dedicated LAN | 10 Gbps Ethernet Dedicated CCTV LAN |
| **Throughput Target** | $\ge 15$ FPS per stream | $\ge 20$ FPS per stream |

---

## 5. Security & Privacy Architecture (UU PDP No. 27/2022)

1. **Zero Raw Video Persistence:** Stream CCTV didecode langsung di RAM/VRAM GPU. Tidak ada rekaman video mentah 24/7 yang disimpan di server AI.
2. **Encrypted Biometric Vectors:** Vektor representasi wajah (128d/512d) dan Re-ID features disimpan di database dengan enkripsi kolom simetris AES-256-GCM. Kunci enkripsi dikelola melalui *Environment Secret Management* (e.g. HashiCorp Vault / KMS).
3. **Non-Destructive Audit Trail:** Tabel `event_overrides` mencatat setiap perubahan manual yang dilakukan pengguna dengan atribut: `operator_id`, `reason`, `original_state`, `overridden_state`, dan `timestamp`.
4. **Role-Based Access Control (RBAC):**
   - **Viewer / Employee:** Hanya dapat melihat timeline dan ringkasan durasi miliknya sendiri.
   - **Supervisor / Manager:** Dapat melihat agregasi tim dan live spatial heatmap tanpa detail visual individual.
   - **HR Admin / Compliance:** Memiliki hak audit trail dan koreksi data *Human-in-the-Loop*.
   - **System Engineer:** Mengelola konfigurasi kamera dan hardware tanpa akses data analitik pegawai.
