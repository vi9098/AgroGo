# 🌾 AgriGo (AgroGo) — Precision Agriculture AI Platform & Farmer Intelligence Center

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SQLite WAL](https://img.shields.io/badge/Database-SQLite%203%20WAL-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Supabase](https://img.shields.io/badge/Cloud%20Dual--Write-Supabase%20PostgreSQL-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com/)
[![AI Models](https://img.shields.io/badge/AI%20Core-DeepSeek%20%2B%20OpenAI%20%2B%20RAG-7C3AED?style=for-the-badge)](https://deepseek.com)
[![Frontend](https://img.shields.io/badge/Frontend-Vanilla%20HTML5%20%2F%20CSS3%20%2F%20ES6-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

**AgriGo** is a dual-core precision agricultural intelligence platform engineered to bridge the digital divide for Indian farmers while providing agricultural administrators with telemetry, governance, and real-time market analytics.

[Features](#-key-features) • [Tech Stack](#-technology-stack--architecture) • [Getting Started](#-quickstart--installation) • [API Reference](#-api-endpoints-reference) • [Architecture](#-system-architecture)

</div>

---

## 📖 Table of Contents
- [Executive Overview](#-executive-overview)
- [Key Features](#-key-features)
- [Technology Stack & Architecture](#-technology-stack--architecture)
- [Project Directory Structure](#-project-directory-structure)
- [Quickstart & Installation](#-quickstart--installation)
- [API Endpoints Reference](#-api-endpoints-reference)
- [Dynamic Weather & Crop Reminder Engine](#-dynamic-weather--crop-reminder-engine)
- [Security & Session Management](#-security--session-management)
- [Automated Testing Suite](#-automated-testing-suite)
- [Deployment Options](#-deployment-options)
- [License & Acknowledgments](#-license--acknowledgments)

---

## 🌟 Executive Overview

Indian agriculture faces critical challenges: fragmented market information, lack of localized weather advice, unpredictable pest attacks, and complex digital interfaces that alienate rural users. 

**AgriGo solves these challenges with a dual-tier architecture:**
1. **Vernacular Farmer AI Companion (`farmer.html`, `index.html`)**: Mobile-first, low-bandwidth, WhatsApp-intuitive interface supporting Hindi and regional Indian languages. Features voice queries (STT/TTS), crop health diagnosis, real-time mandi prices, and dynamic date-based farming schedules.
2. **Admin Mission Control (`admin.html`)**: A cybernetic dark-mode telemetry operations center for agricultural officers and system administrators featuring live CTE database metrics, user lifecycle management, cascade account deletion, and immutable security audit logging.

---

## 🚀 Key Features

### 1. 🌾 Multilingual Farmer AI Advisor (`farmer.html`)
* **Conversational AI in Regional Languages**: Hindi, English, Punjabi, Tamil, and Telugu.
* **Dual LLM Architecture**:
  * **DeepSeek (`deepseek-chat`)**: Powers farmer queries with deep agronomic context.
  * **OpenAI (`gpt-4o-mini`)**: Powers smart natural language reminder scheduling.
* **ICAR RAG Knowledge Base**: Direct semantic retrieval from Indian Council of Agricultural Research (ICAR) packages of practices and university advisories.
* **Voice-Enabled Interface**: Full Web Speech API Speech-to-Text (STT) and Text-to-Speech (TTS) for hands-free advisory in local dialects.
* **Crop Disease & Insect Identification**: Image upload pipeline with automated diagnostic advisories for timely disease interception.

### 2. ⏰ Smart Agricultural Reminders & Crop Lifecycle Scheduler (`reminders.html`)
* **32+ ICAR Crop Baselines**: Comprehensive timelines for Wheat, Mustard, Paddy, Tomato, Potato, Sugarcane, Cotton, Gram, Maize, Soybean, and more.
* **Automatic Calendar Date Calculation**: Converts a single **Sowing Date** into exact future calendar dates for every milestone:
  * Basal fertilization & seed treatment
  * Crown Root Initiation (CRI) irrigation
  * Tillering, jointing, and flowering top-dressing (Urea/DAP)
  * Rust, blight, and pest surveillance intervals
  * Physiological maturity and harvest window
* **Acreage Dosage Scaling**: Automatically calculates exact kilogram dosages of fertilizer (Urea, DAP, MOP) scaled to the farmer's specific acreage.
* **Open-Meteo Dynamic Weather Adaptation**: Postpones irrigation if $>5\text{ mm}$ rain is forecasted or if root-zone soil moisture is saturated ($>0.35\text{ m}^3/\text{m}^3$). Issues spray drift cautions if wind speeds exceed $16\text{ km/h}$.
* **Browser Web Alerts & Push Countdown**: Real-time notifications and notification bell integration directly in the universal taskbar.

### 3. 💰 Live Mandi Market Prices (`mandi.html`)
* **455,359+ Historical & Live Records**: Sourced from data.gov.in / Agmarknet across wholesale APMC mandis nationwide.
* **Multi-Tier Filtering**: Filter instantaneously by State, District, and Commodity.
* **Crop Revenue Calculator**: Calculates estimated gross revenue and net profit based on land acreage, expected yield (quintals), and current live modal prices.

### 4. 🌤️ Material 3 Agromet Weather Hub (`weather.html`)
* **Real-Time Agromet Telemetry**: Temperature, humidity, wind velocity, precipitation probability, and solar radiation.
* **Multi-Layer Root Zone Soil Telemetry**: Measures soil moisture and temperature across 5 depth intervals ($0\text{--}1\text{ cm}$, $1\text{--}3\text{ cm}$, $3\text{--}9\text{ cm}$, $9\text{--}27\text{ cm}$, $27\text{--}81\text{ cm}$).
* **Actionable Farm Advisories**: Rain alerts, frost warnings, heat stress indexes, and chemical spray suitability ratings.

### 5. 🛡️ Admin Mission Control (`admin.html`, `admin-login.html`)
* **Live System Telemetry**: Sub-10ms composite CTE queries monitoring active users, crop distribution, storage size, and API latency.
* **User & Farm Lifecycle Management**: View, search, toggle status (Active/Suspended), and perform cascade deletion (user + farms + crops + reminders).
* **Immutable Security Audit Trail**: Complete log of login attempts, privilege escalation, data modifications, client IP, and timestamps.
* **TOTP Two-Factor Authentication (2FA)**: Argon2id password verification combined with time-based one-time password security for admin accounts.

### 6. 🔐 Simple & Positive Authentication (`farmer-login.html`)
* **Rectangular & Elliptical Agriculture Theme**: Warm sunrise green aesthetic (`#15803D`, `#22C55E`, `#FEFCE8`) designed to be inviting, simple, and stress-free.
* **1-Click Frictionless Entry (Quick Login)**: Zero OTP wait time and zero password barrier; enter 10-digit mobile number and access the farm immediately.
* **Optional Password Mode**: Allows password entry for users who want credential security.
* **Self-Service Password Recovery**: Security question-based reset mechanism.

---

## 🛠️ Technology Stack & Architecture

### Architectural Overview

```
+-----------------------------------------------------------------------------------+
|                                 AGRIGO PLATFORM                                   |
+-----------------------------------------+-----------------------------------------+
|          FARMER COMPANION TIER          |       ADMIN INTELLIGENCE CENTER         |
| • Mobile-First Responsive PWA           | • Cybernetic Dark Telemetry Dashboard   |
| • Vernacular Voice & AI RAG Chat        | • Real-Time Database Metrics & CTEs     |
| • Dynamic Crop Calendar & Reminders     | • Argon2id Passwords + TOTP 2FA         |
| • Open-Meteo Weather & Mandi Prices     | • Cascade Account & Farm Data Deletion  |
| • Zero-Friction 1-Click Mobile Auth     | • Immutable Security Audit Trail        |
+-----------------------------------------+-----------------------------------------+
|                APPLICATION CORE: Python 3.11+ / FastAPI ASGI Server               |
|      STORAGE & PERSISTENCE: SQLite 3 (WAL Mode) + Supabase PostgreSQL Dual-Sync  |
+-----------------------------------------------------------------------------------+
```

### Detailed Tech Stack Matrix

| Layer | Technology | Key Capabilities & Rationale |
| :--- | :--- | :--- |
| **Backend Core** | **Python 3.11+ / FastAPI (ASGI)** | Async concurrency, native type safety with Pydantic v2, Swagger documentation, and high-throughput ASGI execution via Uvicorn. |
| **Presentation Tier** | **Vanilla HTML5, CSS3, ES6+ JS** | **Zero Node.js dependency in production.** Pure web standards, blazing-fast cold starts, offline PWA capability, and minimal bandwidth consumption. |
| **Primary Database** | **SQLite 3 (WAL Mode)** | `PRAGMA journal_mode = WAL;`, `PRAGMA synchronous = NORMAL;`, `PRAGMA busy_timeout = 5000;`. Extreme read performance with zero server management overhead. |
| **Cloud Dual-Write** | **Supabase (PostgreSQL / PostGIS)** | REST-based cloud replication with automatic offline fallback to local SQLite cache if network connectivity drops. |
| **AI & LLM Services** | **DeepSeek + OpenAI + ChromaDB** | DeepSeek (`deepseek-chat`) for multilingual farming advice; OpenAI (`gpt-4o-mini`) for reminder scheduling; ChromaDB for ICAR RAG embeddings. |
| **Weather & Soil Telemetry** | **Open-Meteo High-Resolution API** | `openmeteo-requests`, cached session via `requests_cache`, retry backoff via `retry_requests`, and `pandas` for 5-band root-zone soil analysis. |
| **Security & Auth** | **HttpOnly Sessions + Argon2id** | Cryptographic session cookies (`SameSite=Lax`), Argon2id / bcrypt password hashing, sliding-window rate limiting, and IDOR protection. |
| **Mobile Access** | **Cloudflare Tunnel (`cloudflared`)** | Secure zero-trust public tunnel allowing any smartphone to access the local development server instantly via HTTPS. |

---

## 📁 Project Directory Structure

```
agri-go/
├── .env.example                 # Comprehensive environment variable template
├── ARCHITECTURE.md              # In-depth architectural blueprint and security specification
├── Procfile                     # Deployment configuration for Heroku / Dokku
├── README.md                    # Primary project documentation (this file)
├── docker-compose.yml           # Multi-container orchestration
├── netlify.toml                 # Netlify deployment configuration
├── package.json                 # Project build and utility scripts
├── requirements.txt             # Python backend dependencies
├── run_site.py                  # One-command server and Cloudflare tunnel launcher
├── test_production_suite.py     # Comprehensive automated test suite (13 test cases)
├── vercel.json                  # Vercel serverless deployment specification
│
├── backend/                     # Python FastAPI application core
│   ├── agrigo.db                # SQLite database with Write-Ahead Logging (WAL)
│   ├── app/
│   │   ├── main.py              # Application entrypoint & static mount
│   │   ├── config.py            # Pydantic Settings configuration loader
│   │   ├── database.py          # Database connection manager, SQLite WAL & Supabase
│   │   ├── supabase_client.py   # Resilient Supabase REST client with pooling
│   │   ├── adapters/            # External service adapters
│   │   │   ├── weather.py       # Open-Meteo client with caching and retry
│   │   │   ├── mandi.py         # Agmarknet market price pipeline
│   │   │   └── llm/             # DeepSeek & OpenAI API adapters
│   │   ├── middleware/          # Security, authentication, and rate limiting
│   │   │   ├── auth.py          # Session validation & IDOR protection
│   │   │   └── security.py      # Helmet-equivalent HTTP security headers
│   │   ├── routes/              # Modular REST API endpoints
│   │   │   ├── auth.py          # Login, quick-login, register, logout, security questions
│   │   │   ├── admin.py         # Admin telemetry, user management, audit trails
│   │   │   ├── agri.py          # Direct weather, mandi, and revenue endpoints
│   │   │   ├── chat.py          # Farmer AI chat (DeepSeek + ICAR RAG)
│   │   │   ├── farm.py          # Farm and crop management endpoints
│   │   │   ├── health.py        # System health checks
│   │   │   ├── knowledge.py     # Agronomic knowledge base endpoints
│   │   │   ├── media.py         # Image uploads for disease diagnosis
│   │   │   ├── reminders.py     # Crop reminder generation and schedules
│   │   │   └── voice.py         # Speech-to-Text and Text-to-Speech endpoints
│   │   ├── services/            # Core business logic services
│   │   │   ├── reminder_engine.py # 32-crop ICAR schedule calculation engine
│   │   │   ├── session_service.py # Cryptographic session manager
│   │   │   ├── audit_service.py   # Security audit logging service
│   │   │   └── agri_rag.py        # Vector search & context retrieval
│   │   └── scripts/             # Seeding and database migration scripts
│   │       └── seed_data.py     # Seeds test farmers, crops, and knowledge chunks
│
├── frontend-html/               # Pure zero-dependency presentation tier
│   ├── admin-login.html         # Admin login gateway (Argon2id + 2FA)
│   ├── admin.html               # Cybernetic Admin Mission Control Center
│   ├── farmer-login.html        # Simple & positive farmer login (Rectangular-Elliptical)
│   ├── farmer.html              # Farmer operational dashboard & AI chat
│   ├── index.html               # Public landing page & platform gateway
│   ├── mandi.html               # Wholesale market prices & revenue calculator
│   ├── register.html            # 1-minute farmer registration
│   ├── reminders.html           # Crop management reminder timeline hub
│   ├── weather.html             # Material 3 Agromet weather hub
│   ├── css/
│   │   └── styles.css           # Core design system & CSS custom properties
│   └── js/
│       ├── admin.js             # Admin dashboard controller
│       ├── api.js               # Centralized vanilla API client
│       ├── gateway.js           # Auth & modal helper logic
│       ├── header.js            # Universal taskbar & notification manager
│       ├── i18n.js              # Multilingual translations (Hindi, English, etc.)
│       └── reminders.js         # Dynamic reminder UI controller
│
└── uploads/                     # Storage directory for crop photos and diagnosis media
```

---

## ⚡ Quickstart & Installation

### Prerequisites
* **Python 3.11** or higher
* **Git** installed on your machine
* Modern web browser (Chrome, Firefox, Edge, Safari)

### 1. Clone the Repository
```bash
git clone https://github.com/vi9098/AgroGo.git
cd AgroGo
```

### 2. Set Up a Python Virtual Environment
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Backend Dependencies
```bash
pip install -r requirements.txt
pip install openmeteo-requests requests-cache retry-requests pandas
```

### 4. Configure Environment Variables
Copy the example environment configuration to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to supply your API keys (optional for local testing; baseline fallback modes work out-of-the-box):
* `OPENAI_API_KEY`: For OpenAI `gpt-4o-mini` smart reminder parsing.
* `DEEPSEEK_API_KEY`: For DeepSeek `deepseek-chat` Farmer AI queries.
* `SUPABASE_URL` & `SUPABASE_KEY`: If synchronizing to Supabase cloud PostgreSQL.

### 5. Launch the Platform
Run the unified launcher script:
```bash
python run_site.py
```

The system will automatically initialize the SQLite WAL database, apply indexes, seed baseline records, and serve the application:
* **Local Web URL**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Farmer Companion**: [http://127.0.0.1:8000/farmer.html](http://127.0.0.1:8000/farmer.html)
* **Farmer Login**: [http://127.0.0.1:8000/farmer-login.html](http://127.0.0.1:8000/farmer-login.html)
* **Crop Reminders**: [http://127.0.0.1:8000/reminders.html](http://127.0.0.1:8000/reminders.html)
* **Mandi Prices**: [http://127.0.0.1:8000/mandi.html](http://127.0.0.1:8000/mandi.html)
* **Admin Mission Control**: [http://127.0.0.1:8000/admin.html](http://127.0.0.1:8000/admin.html)
* **Interactive API Docs (Swagger)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

> **Mobile Access**: If `cloudflared.exe` is present in the `backend/` folder, `run_site.py` will print a public HTTPS Cloudflare Tunnel URL allowing you to test on any smartphone without port forwarding!

---

## 📡 API Endpoints Reference

### Authentication & Sessions
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login` | Public | Authenticates farmer or admin via phone/email and password. Sets HttpOnly cookie. |
| `POST` | `/api/auth/quick-login` | Public | 1-click login using 10-digit mobile number; auto-registers new farmers. |
| `POST` | `/api/auth/register` | Public | Registers a new farmer account with farm area, soil type, and primary crop. |
| `GET` | `/api/auth/me` | Authenticated | Retrieves current authenticated session user details. |
| `POST` | `/api/auth/logout` | Authenticated | Destroys server session in database and expires session cookies. |
| `GET` | `/api/auth/security-question` | Public | Retrieves registered security question for password recovery. |
| `POST` | `/api/auth/reset-password-security`| Public | Resets account password using security question verification. |

### Crop Management & Reminders
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/farmer/reminders/{farmer_id}` | Authenticated | Returns active reminders and schedules for a specific farmer. |
| `POST` | `/api/v1/farmer/reminders/generate-schedule` | Authenticated | Generates standard chronological farming schedule from sowing date. |
| `POST` | `/api/v1/farmer/reminders/natural` | Authenticated | Parses natural language farmer input into structured reminders (OpenAI). |
| `PATCH`| `/api/v1/farmer/reminders/{id}/complete` | Authenticated | Marks a scheduled farming task as completed. |

### Weather & Mandi Intelligence
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/weather` | Public | Live Open-Meteo agromet weather and 5-band root-zone soil moisture. |
| `GET` | `/agriculture/market/live` | Public | Live APMC mandi prices with State, District, and Commodity search. |
| `POST`| `/agriculture/market/calculate-revenue` | Public | Calculates expected gross revenue based on live modal commodity price. |
| `POST`| `/agriculture/market/sync` | Admin | Synchronizes wholesale mandi data from data.gov.in Agmarknet. |

### Admin Mission Control
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/admin/telemetry` | Admin Only | High-speed composite CTE metrics (users, crops, storage, audits). |
| `GET` | `/api/admin/users` | Admin Only | Directory of registered farmers and administrators with search & pagination. |
| `PATCH`| `/api/admin/users/{id}/status` | Admin Only | Toggles farmer account status between `active` and `suspended`. |
| `DELETE`| `/api/admin/users/{id}` | Admin Only | Cascading deletion of farmer, farms, crop cycles, and reminders with audit trail. |
| `GET` | `/api/admin/audits` | Admin Only | Immutable security audit trail with IP address and action timestamps. |

---

## 🌦️ Dynamic Weather & Crop Reminder Engine

AgriGo integrates **Open-Meteo High-Resolution Agromet APIs** with client caching and exponential retry backoff. When a task is marked as `weather_dependent = true`, the system evaluates telemetry before firing notifications:

```python
# Open-Meteo telemetry client with caching and retry backoff
import openmeteo_requests
import requests_cache
from retry_requests import retry

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)
```

### Agronomic Decision Logic
1. **Irrigation Milestones (e.g. CRI at 21 days)**:
   * If upcoming 48-hour rainfall forecast $> 5.0\text{ mm}$ $\rightarrow$ **Postpone irrigation by 3 days** to conserve groundwater and prevent waterlogging.
   * If root-zone soil moisture ($0\text{--}9\text{ cm}$) $> 0.35\text{ m}^3/\text{m}^3$ $\rightarrow$ **Delay irrigation** until soil moisture drops below field capacity.
2. **Pest & Disease Spray Intervals**:
   * If rainfall is expected within 24 hours $\rightarrow$ **Postpone spraying** to avoid chemical wash-off.
   * If surface wind speed $> 16\text{ km/h}$ $\rightarrow$ **Flag spray drift hazard**; recommend spraying only during early morning calm hours.

---

## 🔒 Security & Session Management

AgriGo adopts a zero-trust security architecture:

1. **HttpOnly Cookie Sessions**: Session identifiers are stored exclusively in cryptographic server-side sessions and transmitted via `HttpOnly`, `SameSite=Lax`, and `Secure` cookies. Zero JWTs or authentication tokens are stored in browser `localStorage` or `sessionStorage`, rendering Cross-Site Scripting (XSS) token theft impossible.
2. **IDOR & Multi-Tenant Isolation**: The authorization middleware (`require_auth`) cryptographically validates that the requesting session owner matches the resource's `farmer_id`. Farmers cannot view, modify, or delete another farmer's data under any condition.
3. **Sliding-Window Rate Limiting**: The authentication router monitors failed login attempts by IP and account identifier, automatically throttling brute-force attempts with `429 Too Many Requests` after 5 failures.
4. **Argon2id Password Hashing**: Passwords are saved using memory-hard Argon2id key derivation functions with random salts.
5. **Security Audit Ledger**: Every administrative action, privilege change, and login event is permanently written to the immutable `audit_logs` table.

---

## 🧪 Automated Testing Suite

The repository includes a comprehensive test suite validating all operational requirements:

```bash
python test_production_suite.py
```

### Verified Test Cases:
* **Test 1**: Unauthenticated requests to protected endpoints return `401 Unauthorized`.
* **Test 2**: Successful login creates a server session and issues a secure HttpOnly cookie.
* **Test 3**: Subsequent requests retain authenticated state across page refreshes.
* **Test 4**: Logout explicitly destroys the server session and clears client cookies.
* **Test 5**: Expired or idle sessions are rejected with `401`.
* **Test 6**: Farmers can access their own farm records (`200 OK`).
* **Test 7**: Farmers attempting to access another farmer's data are blocked (`403 Forbidden` - IDOR protection).
* **Test 8**: Farmers attempting to access `/api/admin` are blocked (`403 Forbidden`).
* **Test 9**: Administrators can access the admin control center (`200 OK`).
* **Test 10**: Administrator deletion enforces confirmation, cascade deletion, and audit logging, while preventing self-deletion.
* **Test 11**: Rate limiting triggers `429 Too Many Requests` after repeated failed logins.
* **Test 12**: Real Open-Meteo agromet weather returns live temperature, humidity, and soil moisture.
* **Test 13**: Manual Indian district coordinate lookup works with sub-second response times.

---

## 🚢 Deployment Options

### Docker Deployment
```bash
# Build and launch with Docker Compose
docker compose up -d --build
```

### Heroku / Dokku
The included [`Procfile`](file:///c:/Users/raika/Downloads/mynew/agri-go/Procfile) configures Uvicorn for production:
```procfile
web: uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT --workers 4
```

### Vercel / Netlify
* **Vercel**: Deploy directly using [`vercel.json`](file:///c:/Users/raika/Downloads/mynew/agri-go/vercel.json) configured with ASGI Mangum adapter.
* **Netlify**: Deploy using [`netlify.toml`](file:///c:/Users/raika/Downloads/mynew/agri-go/netlify.toml).

---

## 📄 License & Acknowledgments

This project is licensed under the **MIT License**.

### Special Acknowledgments:
* **Indian Council of Agricultural Research (ICAR)** for agronomic crop guidelines and milestone timelines.
* **Open-Meteo** for high-resolution agromet and multi-band soil telemetry data.
* **data.gov.in / Agmarknet** for wholesale mandi price records.
* **Google DeepMind Team** for guidance on agentic development and sustainable agricultural AI solutions.

---

<div align="center">
  <sub>जय जवान • जय किसान • समृद्ध भारत 🇮🇳</sub>
</div>
