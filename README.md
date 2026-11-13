# 🤖 Enterprise Telegram Bot & Bot Manager

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-aiogram%20v3.28+-0088cc.svg?style=flat-square&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![Database](https://img.shields.io/badge/database-PostgreSQL%20%7C%20Neon-336791.svg?style=flat-square&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Async Engine](https://img.shields.io/badge/async-asyncpg%20%7C%20aiohttp-4ba064.svg?style=flat-square)](https://github.com/MagicStack/asyncpg)
[![FSM Storage](https://img.shields.io/badge/FSM-Redis%20%7C%20Memory-DC382D.svg?style=flat-square&logo=redis&logoColor=white)](https://redis.io/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)
[![Linter](https://img.shields.io/badge/linter-ruff-orange.svg?style=flat-square)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-22%20passed-brightgreen.svg?style=flat-square&logo=pytest&logoColor=white)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)

> **A high-performance, asynchronous Telegram bot platform built with aiogram v3, asyncpg, Redis, and PostgreSQL.**  
> Features a dynamic, in-bot **Bot Manager** (an integrated @BotFather alternative) allowing users to register, configure, and diagnose secondary bot tokens, paired with an enterprise middleware pipeline, natural language reminders, stateful AI chat, live weather, and dual execution modes (Webhook & Long Polling).

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Key Features](#-key-features)
  - [1. Dynamic Bot Manager (BotFather Clone) & Diagnostics](#1-dynamic-bot-manager-botfather-clone--diagnostics)
  - [2. Enterprise Middlewares Pipeline](#2-enterprise-middlewares-pipeline)
  - [3. Dual Engine: Production Webhook & Polling](#3-dual-engine-production-webhook--polling)
  - [4. Distributed Redis FSM with Auto-Fallback](#4-distributed-redis-fsm-with-auto-fallback)
  - [5. Smart Reminders Engine](#5-smart-reminders-engine)
  - [6. Conversational AI Assistant](#6-conversational-ai-assistant)
  - [7. Live Weather & Forecasts](#7-live-weather--forecasts)
  - [8. Interactive FAQ Database](#8-interactive-faq-database)
  - [9. Enterprise Administration & Broadcast](#9-enterprise-administration--broadcast)
  - [10. Resilient Multi-Tier Storage with Auto-Indexing](#10-resilient-multi-tier-storage-with-auto-indexing)
- [Project Structure](#-project-structure)
- [Command Reference](#-command-reference)
- [Technology Stack](#-technology-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Configuration](#environment-configuration)
  - [Running the Bot](#running-the-bot)
- [Health Monitoring & Diagnostics](#-health-monitoring--diagnostics)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Production Deployment](#-production-deployment)
  - [Systemd Service (Linux)](#systemd-service-linux)
  - [Docker Containerization](#docker-containerization)
- [Security & Reliability](#-security--reliability)
- [Contributing & License](#-contributing--license)

---

## 💡 Overview

The **Enterprise Telegram Bot** is built for mission-critical productivity, multi-tenant bot management, and seamless end-user workflows. Rather than functioning as a standard single-purpose bot, it incorporates a comprehensive **Bot Manager Dashboard** where users can register their own bots via Bot API tokens, modify public profile data (name, description, bio, commands, profile photos) without leaving Telegram, run automated **health and delivery diagnostics**, and securely inspect credentials behind spoiler protections.

Backed by **asynchronous connection pooling** via PostgreSQL (`asyncpg`), **Redis-backed FSM state persistence**, **enterprise rate-limiting and error-sanitization middlewares**, and dual **Webhook / Long Polling** runtimes, this repository provides a resilient, modern standard for Telegram applications.

---

## 🏗 Architecture

The system is designed following modern asynchronous Python paradigms with clean decoupling between event routers, middleware pipelines, business logic, and data persistence:

```mermaid
flowchart TD
    User([Telegram User]) <-->|Updates / Commands / Callbacks| TGAPI[Telegram Bot API]
    TGAPI <-->|Webhook or Long Polling| Main[main.py: App Engine]
    
    subgraph Middlewares Pipeline
        Main --> MW_LOG[Logging & Latency Middleware]
        MW_LOG --> MW_ERR[Error Sanitizer & Exception Boundary]
        MW_ERR --> MW_THR[Anti-Flood Throttling Middleware]
        MW_THR --> MW_DB[Database & User Sync Middleware]
    end

    subgraph Handlers Layer
        MW_DB --> H_BM[Bot Manager & Diagnostics Router]
        MW_DB --> H_REM[Reminders Router]
        MW_DB --> H_AI[AI Chat Router]
        MW_DB --> H_WEA[Weather Router]
        MW_DB --> H_FAQ[FAQ Router]
        MW_DB --> H_ADM[Admin Panel Router]
        MW_DB --> H_CB[Callback Router]
        MW_DB --> H_ST[Start & Stats Router]
    end

    subgraph Service & Storage Layer
        H_BM <-->|API Calls: setMyName, getWebhookInfo, etc.| TGAPI_EXT[Managed Telegram Bots]
        H_AI <-->|OpenAI Chat Completions| OpenAI[OpenAI API]
        H_WEA <-->|Geo & Forecast Queries| OWM[OpenWeatherMap API]
        
        Handlers Layer <--> FSM{FSM State Storage}
        FSM -->|Distributed| REDIS[(Redis FSM Storage)]
        FSM -.->|Local Dev| MEM_FSM[(In-Memory FSM)]

        Handlers Layer <--> DB_ADAPT{Database Layer}
        DB_ADAPT -->|Production asyncpg Pool| PG[(PostgreSQL / Neon)]
        DB_ADAPT -.->|Dev Fallback| MEM_DB[(In-Memory Mock Storage)]
    end

    subgraph Background Workers & Webhook Server
        PG -->|Load Active on Startup| SCHED[Asyncio Reminder Scheduler]
        SCHED -->|Fire Notifications| TGAPI
        Main -->|Optional Mode| WEBHOOK[Aiohttp Webhook Server + /health API]
    end
```

---

## ✨ Key Features

### 1. Dynamic Bot Manager (BotFather Clone) & Diagnostics
- **Token Registration & Instant Handshake**: Register any Telegram bot token generated via [@BotFather](https://t.me/botfather). Automatically verifies credentials using `getMe` before committing to the registry.
- **Dynamic Profile Mutation**: Update managed bot properties in real time directly from inline keyboard menus:
  - ✍️ **Display Name** (`setMyName`)
  - 📝 **Welcome Description** (`setMyDescription`)
  - ℹ️ **About Text / Short Bio** (`setMyShortDescription`)
  - 📜 **Commands Directory** (`setMyCommands`) with formatted multi-line parsing
  - 🖼️ **Profile Picture Avatar** (`setMyProfilePhoto`) via direct image upload
- **📜 Live Command Directory Inspector**: Query and review all active commands currently registered on the managed bot via `getMyCommands`.
- **🔔 Live Connection Ping**: Dispatch a live end-to-end verification ping from the managed bot directly to the owner to verify dispatch privileges.
- **🌐 Webhook Reset & Conflict Resolver**: Clear external webhooks and flush pending update queues with one click to resolve `409 Conflict` errors and restore long polling.
- **🔍 Automated Health & Delivery Diagnostics**: Inspect live bot health in one click:
  - Real-time API reachability
  - Delivery mode (`Webhook` with URL vs `Long Polling`)
  - Pending update counts & Telegram delivery error reports
  - Group permissions (`can_join_groups`, `can_read_all_group_messages`, privacy mode status)
  - Inline queries capability
- **Credential Protection**: View active tokens protected behind Telegram `<tg-spoiler>` tags to prevent shoulder surfing or recording leaks.
- **Bot De-registration**: Clean deletion lifecycle removing bot ownership from database tables.

### 2. Enterprise Middlewares Pipeline
- **⏳ Anti-Flood Throttling Middleware**: Prevents rapid command flooding and Telegram `429 Too Many Requests` bans with configurable cooldown windows (default: 0.6s, heavy commands: 2.0s).
- **🗃️ Database & Auto-Registration Middleware**: Injects active database connection pools into handlers and automatically synchronizes user profiles and `last_active` timestamps on every update.
- **⏱️ Latency & Performance Logging**: Monitors and outputs precision execution duration (in milliseconds) for every message and callback query.
- **🛡️ Exception Boundary & Token Redaction**: Catches unexpected handler exceptions and scrubs sensitive tokens, passwords, and API keys before logging, while sending a friendly error prompt to the user.

### 3. Dual Engine: Production Webhook & Polling
- **Production Webhook Server**: High-throughput `aiohttp` web server supporting custom paths (`/webhook`), secret token validation (`X-Telegram-Bot-Api-Secret-Token`), and SSL termination.
- **`/health` Health-Check Endpoint**: Exposes standard health metrics (`status`, `bot`, `database`, `timestamp`) for Docker, Kubernetes, and uptime monitoring services.
- **Resilient Long Polling**: Automatic reconnection and signal management (`SIGINT`, `SIGTERM`) for zero-configuration local development.

### 4. Distributed Redis FSM with Auto-Fallback
- Connects to **Redis** via `RedisStorage.from_url(REDIS_URL)` to support multi-process deployments and state persistence across server restarts.
- Intelligently degrades to `MemoryStorage` when `REDIS_URL` is omitted.

### 5. Smart Reminders Engine
- **Natural Language Parsing**: Recognizes relative and shorthand time phrases (e.g., `in 15 minutes`, `2 hours`, `tomorrow at 9am`, `3d`).
- **Interactive Reminders Directory**: Review active scheduled tasks via `/reminders` or `/myreminders` with instant cancellation buttons.
- **🔁 Recurring Daily Scheduling**: Understands natural recurrence schedules (e.g., `every day at 9am Standup` or `daily at 8pm Review goals`).
- **Interactive Inline Actions**: Delivered reminders feature interactive inline action buttons:
  - ✅ **Mark Done**: Dismisses the reminder and logs task completion.
  - ⏰ **Snooze**: Reschedules notifications for later follow-up (+5 min, +10 min).
  - ❌ **Delete**: Purges the reminder from database storage.
- **Persistent Reboot Recovery**: When the bot server starts, active reminders stored in PostgreSQL are automatically recovered and rescheduled into asyncio background tasks.

### 6. Conversational AI Assistant & Persona Engine
- **Context-Aware Dialogue**: Powered by OpenAI's `gpt-3.5-turbo` with stateful FSM chat memory.
- **🎭 Multi-Persona Switching**: Switch between specialized personas on the fly:
  - 🧑‍💼 **Productivity Assistant**: Structured, friendly, and comprehensive.
  - 💻 **Senior Software Engineer**: Clean, typed, idiomatic code with error handling.
  - ⚡ **Ultra-Concise Executive**: Direct bullet points, zero filler.
- **Graceful Fallback Mode**: If `OPENAI_API_KEY` is not configured, the bot automatically switches to an informative mock intelligence responder tailored to the active persona.

### 7. Live Weather & Forecasts
- **Current Conditions**: Real-time temperature, humidity, atmospheric pressure, and wind speed via OpenWeatherMap API.
- **5-Day Extended Projections**: Formatted weather outlook cards with weather emojis.
- **⚡ Quick-Tap World Cities**: One-click weather cards for London, New York, Tokyo, and Dubai.
- **Flexible Location Input**: Accepts city name queries (`/weather Tokyo`) or Telegram location pin shares.

### 8. Interactive FAQ Database
- **Categorized Knowledgebase**: Organized into General, Features, Technical, and Account categories.
- **Instant Search Index**: Query keywords to pull matching guides and help articles directly in chat.

### 9. Enterprise Administration & Broadcast
- **Role-Based Access Control**: Strict access verification via `ADMIN_IDS` configuration.
- **Real-Time Analytics Dashboard**: Tracks total onboarded users, daily active users (DAU), command invocation frequency, and service loads.
- **📈 Live Engine Telemetry**: Monitored runtime metrics: memory consumption (RSS), update throughput, average and p95 latencies, and uptime.
- **Mass Broadcast Engine**: Real-time dispatcher iterating across all registered database users with delivery and failure metrics.
- **Audit Logs Inspector**: View the last 20 runtime log entries with formatting and live refresh.
- **System Environment Inspector**: Review active runtime configuration, modes, and database connection pools.

### 10. Resilient Multi-Tier Storage with Auto-Indexing
- **PostgreSQL Connection Pool**: High-speed, connection-pooled execution using `asyncpg`.
- **Automatic High-Performance Indexes**: Indexes created on startup for `users(last_active)`, `reminders(status, remind_time)`, `usage_stats(user_id, command)`, and `managed_bots(owner_id)`.
- **Zero-Setup In-Memory Mode**: If `DB_URL` is omitted, the bot initializes an in-memory fallback layer, allowing instant testing without database setup.

### 11. Global Inline Mode Engine
- **Any-Chat Accessibility**: Use the bot from inside any group, channel, or direct message by typing `@your_bot_username [query]`.
- **Instant Search Cards**:
  - `faq [query]`: Searches categorized FAQs and delivers shareable answer articles.
  - `weather [city]`: Renders real-time weather cards with temperatures and conditions.
  - `ai [prompt]`: Generates inline AI completions and code snippets.
  - `share`: Creates an interactive invitation card.

### 12. User Profiles, Timezones & Referral Program
- **Personal Identity Dashboard (`/profile`)**: Displays membership rank, registration age, commands count, and current timezone.
- **Configurable Timezones**: Select from world timezones (`UTC`, `EST`, `CET`, `EAT`, `IST`, `PST`) so reminder triggers always match local schedules.
- **Deep-Linked Referral System (`/referral`)**: Unique shareable invite links (`https://t.me/<bot>?start=ref_<id>`) with automated referral crediting.

---

## 📁 Project Structure

```text
telegrambot/
├── config/
│   ├── __init__.py          # Exposes package configuration settings
│   └── settings.py          # Validates environment parameters (.env)
│
├── database/
│   ├── __init__.py
│   └── models.py            # PostgreSQL asyncpg schema, connection pool & indexing
│
├── handlers/
│   ├── __init__.py          # Consolidates and provides master setup_routers()
│   ├── admin.py             # Administrative dashboard, stats & mass broadcast
│   ├── ai_chat.py           # Stateful conversational AI assistant
│   ├── bot_manager.py       # BotFather clone (token registration & profile editor)
│   ├── callback.py          # Central navigation callbacks & inline queries
│   ├── faq.py               # Categorized FAQ search and display
│   ├── inline.py            # Global inline query engine (@bot queries)
│   ├── reminders.py         # Natural language reminder parser & background scheduler
│   ├── start.py             # User onboarding, deep-linking & usage tracking
│   └── weather.py           # Weather metrics and 5-day predictive forecasts
│
├── middlewares/
│   ├── __init__.py          # Exports complete middleware pipeline
│   ├── throttling.py        # Anti-flood rate-limiting middleware
│   ├── database.py          # Database dependency injection & auto-registration
│   ├── logging.py           # Latency metrics & execution logger
│   └── error.py             # Global exception boundary & credential sanitizer
│
├── utils/
│   ├── __init__.py
│   ├── keyboards.py         # Main reply keyboards & dynamic inline menus
│   └── telemetry.py         # Real-time metrics, latency & memory observer
│
├── tests/
│   ├── test_bot.py          # System environment, module imports & config tests
│   ├── test_bot_manager.py  # Bot manager CRUD, token regex & router tests
│   └── test_advanced.py     # Middleware, router consolidation & sanitizer tests
│
├── logs/                    # Daily rotated execution logs (runtime generated)
├── .env                     # Local environment secrets (ignored by Git)
├── .gitignore               # Ignored files, cache directories, and secrets
├── main.py                  # Dual-engine entry point (Webhook & Polling runner)
└── requirements.txt         # Production and development dependencies
```

---

## 📜 Command Reference

### 👤 User Commands

| Command | Shorthand | Description |
| :--- | :--- | :--- |
| `/start` | — | Initialize user profile, handle deep-links, and display main menu |
| `/help` | `Help` | Comprehensive guide explaining all bot features and syntax |
| `/menu` | — | Display the primary reply keyboard navigation |
| `/faq` | `FAQ` | Search and explore categorized frequently asked questions |
| `/remind` | `Reminder` | Create a time-based task reminder (`/remind 15m Call client`) |
| `/ai` | `AI Chat` | Start an interactive conversation with the AI assistant |
| `/weather` | `Weather` | Get current weather or 5-day forecast for any city |
| `/stats` | `Stats` | View personal usage metrics and commands executed |
| `/profile` | — | Display personal account details and change timezone |
| `/referral` | — | View referral statistics and share invitation link |
| `/feedback` | `Feedback` | Submit comments or issue reports directly to administrators |
| `/cancel` | `Cancel` | Cancel any active FSM dialogue or multi-step wizard |

### 🤖 Bot Manager Commands

| Command | Action Target | Description |
| :--- | :--- | :--- |
| `/bot_manager` | Dashboard | Open the interactive Bot Manager dashboard |
| `/newbot` | Registration | Register a new bot token into the manager |
| `/mybots` | Inventory | View all bots registered under your Telegram ID |
| `/setname` | Profile | Change the display name of a managed bot |
| `/setdescription` | Profile | Update the start description of a managed bot |
| `/setabouttext` | Profile | Update the profile bio / about text of a managed bot |
| `/setuserpic` | Avatar | Upload a new profile picture for a managed bot |
| `/setcommands` | Commands | Configure the bot command directory for user menus |
| `/deletebot` | Removal | Unregister and remove a bot from the manager |

### 🔐 Administrator Commands

| Command | Access Level | Description |
| :--- | :--- | :--- |
| `/admin` | Admin IDs | Access the administrative control center |
| `admin_stats` | Admin IDs | Inspect global bot metrics (active users, total commands, queries) |
| `admin_broadcast` | Admin IDs | Dispatch announcements to all registered users |
| `admin_logs` | Admin IDs | Inspect system logs from runtime sessions |

---

## 🛠 Technology Stack

- **Runtime**: [Python 3.11+](https://www.python.org/) (tested on Python 3.12 & 3.13)
- **Telegram Bot Framework**: [aiogram v3.28+](https://docs.aiogram.dev/)
- **Database Engine**: [asyncpg v0.31+](https://github.com/MagicStack/asyncpg) (PostgreSQL connection pool)
- **FSM Storage**: [redis-py](https://redis.io/) & [aiogram.fsm.storage.redis](https://docs.aiogram.dev/en/latest/dispatcher/finite_state_machine/index.html)
- **HTTP Engine**: [aiohttp v3.13+](https://docs.aiohttp.org/) (Webhook server & asynchronous HTTP client)
- **Configuration**: [python-dotenv](https://github.com/theskumar/python-dotenv)
- **Code Quality & Testing**:
  - [pytest](https://docs.pytest.org/) & [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
  - [Black](https://github.com/psf/black) code formatter
  - [Ruff](https://github.com/astral-sh/ruff) high-speed linter

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.11** or higher.
- A **Telegram Bot Token** obtained from [@BotFather](https://t.me/botfather).
- *(Optional)* A **PostgreSQL Database** instance (local or hosted on [Neon](https://neon.tech/), Supabase, or AWS RDS).
- *(Optional)* A **Redis Database** instance (for distributed state storage).
- *(Optional)* An **OpenAI API Key** (for conversational AI features).
- *(Optional)* An **OpenWeatherMap API Key** (for live weather updates).

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/kenenisabeyan/telegrambot.git
   cd telegrambot
   ```

2. **Create and activate a virtual environment**:
   
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   
   - **Linux / macOS (Bash)**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

### Environment Configuration

Create a `.env` file in the root directory:

```env
# ==========================================
# Telegram Bot Credentials (Required)
# ==========================================
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ

# ==========================================
# Administrator Access (Required for /admin)
# Comma-separated list of Telegram User IDs
# ==========================================
ADMIN_IDS=123456789,987654321

# ==========================================
# Storage & Database (Optional)
# Falls back to in-memory store if omitted
# ==========================================
DB_URL=postgresql://user:password@ep-sample-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
REDIS_URL=redis://localhost:6379/0

# ==========================================
# External Service APIs (Optional)
# ==========================================
OPENAI_API_KEY=sk-proj-yourOpenAiApiKeyHere
OPENWEATHER_API_KEY=yourOpenWeatherApiKeyHere

# ==========================================
# Webhook Server Configuration (Optional)
# Leave WEBHOOK_URL blank to use Long Polling
# ==========================================
WEBHOOK_URL=https://your-domain.com
WEBHOOK_PATH=/webhook
WEBHOOK_SECRET=your_super_secret_webhook_token
WEBAPP_HOST=0.0.0.0
WEBAPP_PORT=8080

# ==========================================
# Anti-Flood Rate Limiting (Seconds)
# ==========================================
RATE_LIMIT_DEFAULT=0.6
RATE_LIMIT_HEAVY=2.0

# ==========================================
# Logging Configuration
# DEBUG, INFO, WARNING, ERROR, CRITICAL
# ==========================================
LOG_LEVEL=INFO
```

### Running the Bot

Start the bot:

```bash
python main.py
```

- When `WEBHOOK_URL` is omitted: Operates in **Resilient Long Polling** mode.
- When `WEBHOOK_URL` is configured: Launches high-performance **Aiohttp Webhook Server**.

---

## 🩺 Health Monitoring & Diagnostics

When running in webhook mode, the bot serves an automated health probe at:

```http
GET http://0.0.0.0:8080/health
```

Sample JSON response:
```json
{
  "status": "healthy",
  "bot": "online",
  "database": "connected",
  "timestamp": "2026-11-12T04:16:00.123456"
}
```

---

## 🧪 Testing & Quality Assurance

The project features automated unit tests covering imports, configuration, Bot Manager CRUD, rate-limiting, and error redaction.

### Running Unit Tests

```bash
pytest -v
```

### Code Formatting & Linting

```bash
# Lint checks with Ruff
ruff check .

# Format code with Black
black .
```

---

## 🚢 Production Deployment

### Systemd Service (Linux)

```ini
[Unit]
Description=Enterprise Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/telegrambot
ExecStart=/home/ubuntu/telegrambot/venv/bin/python main.py
Restart=always
RestartSec=5
EnvironmentFile=/home/ubuntu/telegrambot/.env

[Install]
WantedBy=multi-user.target
```

### Docker Containerization

```dockerfile
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["python", "main.py"]
```

---

## 🔒 Security & Reliability

- **Enterprise Middleware Boundary**: Intercepts uncaught exceptions and strips sensitive keys and credentials before logging.
- **Rate-Limiting Protection**: Anti-flood token bucket algorithm prevents flood bans and ensures equitable server usage.
- **SQL Injection Prevention**: All queries execute through parameterized `asyncpg` queries (`$1, $2, ...`).
- **Spoiler Protection**: Telegram credentials presented in chat are enveloped within `<tg-spoiler>` tags.
- **Auto Re-connect**: Connection pool recovery with auto-indexing for optimized query latency.

---

## 📄 License & Contributing

Distributed under the **MIT License**.

**Author**: Kenenisa Beyan  
**Repository**: [github.com/kenenisabeyan/telegrambot](https://github.com/kenenisabeyan/telegrambot)
