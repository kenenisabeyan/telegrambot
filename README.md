# 🤖 Enterprise Telegram Bot & Bot Manager

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-aiogram%20v3.28+-0088cc.svg?style=flat-square&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![Database](https://img.shields.io/badge/database-PostgreSQL%20%7C%20Neon-336791.svg?style=flat-square&logo=postgresql&logoColor=white)](https://neon.tech/)
[![Async Engine](https://img.shields.io/badge/async-asyncpg%20%7C%20aiohttp-4ba064.svg?style=flat-square)](https://github.com/MagicStack/asyncpg)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat-square)](https://github.com/psf/black)
[![Linter](https://img.shields.io/badge/linter-ruff-orange.svg?style=flat-square)](https://github.com/astral-sh/ruff)
[![Tests](https://img.shields.io/badge/tests-8%20passed-brightgreen.svg?style=flat-square&logo=pytest&logoColor=white)](tests/)
[![License](https://img.shields.io/badge/license-MIT-green.svg?style=flat-square)](LICENSE)

> **A high-performance, asynchronous Telegram bot platform built with aiogram v3, asyncpg, and PostgreSQL.**  
> Features a dynamic, in-bot **Bot Manager** (an integrated @BotFather alternative) allowing users to register, configure, and manage secondary bot tokens, paired with natural language reminders, stateful AI chat, real-time weather analytics, and admin broadcast controls.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Key Features](#-key-features)
  - [1. Dynamic Bot Manager (BotFather Clone)](#1-dynamic-bot-manager-botfather-clone)
  - [2. Smart Reminders Engine](#2-smart-reminders-engine)
  - [3. Conversational AI Assistant](#3-conversational-ai-assistant)
  - [4. Live Weather & Forecasts](#4-live-weather--forecasts)
  - [5. Interactive FAQ Database](#5-interactive-faq-database)
  - [6. Enterprise Administration & Broadcast](#6-enterprise-administration--broadcast)
  - [7. Resilient Multi-Tier Storage](#7-resilient-multi-tier-storage)
- [Project Structure](#-project-structure)
- [Command Reference](#-command-reference)
- [Technology Stack](#-technology-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Configuration](#environment-configuration)
  - [Running the Bot](#running-the-bot)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Production Deployment](#-production-deployment)
  - [Systemd Service (Linux)](#systemd-service-linux)
  - [Docker Containerization](#docker-containerization)
- [Security & Reliability](#-security--reliability)
- [Contributing & License](#-contributing--license)

---

## 💡 Overview

The **Enterprise Telegram Bot** is built for mission-critical productivity, multi-tenant bot management, and seamless end-user workflows. Rather than functioning as a standard single-purpose bot, it incorporates a comprehensive **Bot Manager Dashboard** where users can register their own bots via Bot API tokens, modify public profile data (name, description, bio, commands, profile photos) without leaving Telegram, and securely inspect credentials behind spoiler protections.

Backed by **asynchronous connection pooling** via PostgreSQL (`asyncpg`), intelligent **in-memory fallbacks** for zero-dependency local development, and strict **Finite State Machine (FSM)** validation, this repository serves as both a turnkey enterprise utility and an extensible foundation for modern Telegram applications.

---

## 🏗 Architecture

The system is designed following modern asynchronous Python paradigms with clean decoupling between event routers, business logic, and data persistence:

```mermaid
flowchart TD
    User([Telegram User]) <-->|Updates / Commands / Callbacks| TGAPI[Telegram Bot API]
    TGAPI <-->|Long Polling / Webhook| Main[main.py: Dispatcher & Router Engine]
    
    subgraph Handlers Layer
        Main --> H_BM[Bot Manager Router]
        Main --> H_REM[Reminders Router]
        Main --> H_AI[AI Chat Router]
        Main --> H_WEA[Weather Router]
        Main --> H_FAQ[FAQ Router]
        Main --> H_ADM[Admin Panel Router]
        Main --> H_CB[Callback Router]
        Main --> H_ST[Start & Stats Router]
    end

    subgraph Service & Storage Layer
        H_BM <-->|API Calls: setMyName, setMyCommands, etc.| TGAPI_EXT[Managed Telegram Bots]
        H_AI <-->|OpenAI Chat Completions| OpenAI[OpenAI API]
        H_WEA <-->|Geo & Forecast Queries| OWM[OpenWeatherMap API]
        
        Handlers Layer <--> DB_ADAPT{Database Layer}
        DB_ADAPT -->|Production| PG[(PostgreSQL Pool / Neon)]
        DB_ADAPT -.->|Dev Fallback| MEM[(In-Memory Mock Storage)]
    end

    subgraph Background Workers
        PG -->|Load Active on Startup| SCHED[Asyncio Reminder Scheduler]
        SCHED -->|Fire Notifications| TGAPI
    end
```

---

## ✨ Key Features

### 1. Dynamic Bot Manager (BotFather Clone)
- **Token Registration & Instant Handshake**: Register any Telegram bot token generated via [@BotFather](https://t.me/botfather). Automatically verifies credentials using `getMe` before committing to the registry.
- **Dynamic Profile Mutation**: Update managed bot properties in real time directly from inline keyboard menus:
  - ✍️ **Display Name** (`setMyName`)
  - 📝 **Welcome Description** (`setMyDescription`)
  - ℹ️ **About Text / Short Bio** (`setMyShortDescription`)
  - 📜 **Commands Directory** (`setMyCommands`) with formatted multi-line parsing
  - 🖼️ **Profile Picture Avatar** (`setMyProfilePhoto`) via direct image upload
- **Credential Protection**: View active tokens protected behind Telegram `<tg-spoiler>` tags to prevent shoulder surfing or recording leaks.
- **Bot De-registration**: Clean deletion lifecycle removing bot ownership from database tables.

### 2. Smart Reminders Engine
- **Natural Language Parsing**: Recognizes relative and shorthand time phrases (e.g., `in 15 minutes`, `2 hours`, `tomorrow at 9am`, `3d`).
- **Interactive Inline Actions**: Delivered reminders feature interactive inline action buttons:
  - ✅ **Mark Done**: Dismisses the reminder and logs task completion.
  - ⏰ **Snooze**: Reschedules notifications for later follow-up (+10 min, +1 hour).
  - ❌ **Delete**: Purges the reminder from database storage.
- **Persistent Reboot Recovery**: When the bot server starts, active reminders stored in PostgreSQL are automatically recovered and rescheduled into asyncio background tasks.

### 3. Conversational AI Assistant
- **Context-Aware Dialogue**: Powered by OpenAI's `gpt-3.5-turbo` with stateful FSM chat memory.
- **Graceful Fallback Mode**: If `OPENAI_API_KEY` is not configured, the bot automatically switches to an informative mock intelligence responder to preserve user experience during offline evaluation.

### 4. Live Weather & Forecasts
- **Current Conditions**: Real-time temperature, humidity, atmospheric pressure, and wind speed via OpenWeatherMap API.
- **5-Day Extended Projections**: Formatted weather outlook cards with weather emojis.
- **Flexible Location Input**: Accepts city name queries (`/weather Tokyo`) or Telegram location pin shares.

### 5. Interactive FAQ Database
- **Categorized Knowledgebase**: Organized into General, Features, Technical, and Account categories.
- **Instant Search Index**: Query keywords to pull matching guides and help articles directly in chat.

### 6. Enterprise Administration & Broadcast
- **Role-Based Access Control**: Strict access verification via `ADMIN_IDS` configuration.
- **Real-Time Analytics Dashboard**: Tracks total onboarded users, daily active users (DAU), command invocation frequency, and service loads.
- **Mass Broadcast Engine**: Dispatch formatted announcements (HTML/Markdown) to all active users with error containment for blocked/inactive chats.
- **Audit Logs**: Inspect runtime log files directly within Telegram chat sessions.

### 7. Resilient Multi-Tier Storage
- **PostgreSQL Connection Pool**: High-speed, connection-pooled execution using `asyncpg`.
- **Zero-Setup In-Memory Mode**: If `DB_URL` is omitted, the bot initializes an in-memory fallback layer, allowing instant testing without database setup.

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
│   └── models.py            # PostgreSQL asyncpg schema, migrations & queries
│
├── handlers/
│   ├── __init__.py          # Central registry packaging handler routers
│   ├── admin.py             # Administrative dashboard, stats & mass broadcast
│   ├── ai_chat.py           # Stateful conversational AI assistant
│   ├── bot_manager.py       # BotFather clone (token registration & profile editor)
│   ├── callback.py          # Central navigation callbacks & inline queries
│   ├── faq.py               # Categorized FAQ search and display
│   ├── reminders.py         # Natural language reminder parser & background scheduler
│   ├── start.py             # User onboarding, deep-linking & usage tracking
│   └── weather.py           # Weather metrics and 5-day predictive forecasts
│
├── middlewares/
│   └── __init__.py          # Custom update and event processing pipelines
│
├── utils/
│   ├── __init__.py
│   └── keyboards.py         # Main reply keyboards & dynamic inline menus
│
├── tests/
│   ├── test_bot.py          # System environment, module imports & config tests
│   └── test_bot_manager.py  # Bot manager CRUD, token regex & router tests
│
├── logs/                    # Daily rotated execution logs (runtime generated)
├── .env                     # Local environment secrets (ignored by Git)
├── .gitignore               # Ignored files, cache directories, and secrets
├── main.py                  # Asynchronous bot entry point and lifecycle manager
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

- **Runtime**: [Python 3.11+](https://www.python.org/) (fully compatible with Python 3.12 & 3.13)
- **Telegram Bot Framework**: [aiogram v3.28+](https://docs.aiogram.dev/)
- **Database Driver**: [asyncpg v0.31+](https://github.com/MagicStack/asyncpg) (high-speed PostgreSQL interface)
- **HTTP Client**: [aiohttp v3.13+](https://docs.aiohttp.org/)
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

Create a `.env` file in the root directory (you can copy the template below):

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
# External Service APIs (Optional)
# Falls back to informative mock systems if empty
# ==========================================
OPENAI_API_KEY=sk-proj-yourOpenAiApiKeyHere
OPENWEATHER_API_KEY=yourOpenWeatherApiKeyHere

# ==========================================
# Database Connection (Optional)
# Falls back to in-memory store if omitted
# ==========================================
DB_URL=postgresql://user:password@ep-sample-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require

# ==========================================
# Logging Configuration
# DEBUG, INFO, WARNING, ERROR, CRITICAL
# ==========================================
LOG_LEVEL=INFO
```

#### Environment Variables Reference

| Variable | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `BOT_TOKEN` | String | **Yes** | Telegram Bot API token from [@BotFather](https://t.me/botfather). |
| `ADMIN_IDS` | String | No | Comma-separated integer IDs permitted to use `/admin`. |
| `DB_URL` | String | No | PostgreSQL DSN connection string (e.g. Neon serverless). |
| `OPENAI_API_KEY` | String | No | OpenAI API secret key for AI chat. |
| `OPENWEATHER_API_KEY` | String | No | OpenWeatherMap API key for weather reports. |
| `LOG_LEVEL` | String | No | Console & file logging verbosity (`INFO` by default). |

### Running the Bot

Start the bot polling process:

```bash
python main.py
```

Upon launch, the bot will:
1. Initialize UTF-8 stream handlers (Windows-compatible).
2. Configure logging to both `logs/bot_YYYYMMDD.log` and stdout.
3. Register official bot commands with the Telegram API.
4. Establish the PostgreSQL connection pool (or activate mock memory storage).
5. Recover and reschedule all pending reminders.
6. Dispatch a startup notification to administrators.

---

## 🧪 Testing & Quality Assurance

The project includes unit tests covering module imports, configuration integrity, Bot Manager CRUD routines, and token validation logic.

### Running Unit Tests

Run the full automated test suite with pytest:

```bash
pytest -v
```

To run a specific test suite:

```bash
pytest tests/test_bot.py
pytest tests/test_bot_manager.py
```

### Code Formatting & Linting

Enforce code formatting with **Black**:
```bash
black --check .
black .
```

Run static analysis with **Ruff**:
```bash
ruff check .
ruff check --fix .
```

---

## 🚢 Production Deployment

### Systemd Service (Linux)

To ensure the bot remains running continuously and automatically restarts after system reboots, configure a `systemd` service:

1. Create a service file:
   ```bash
   sudo nano /etc/systemd/system/telegrambot.service
   ```

2. Add the following unit configuration (adjusting paths and user):
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

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegrambot
   sudo systemctl start telegrambot
   sudo systemctl status telegrambot
   ```

### Docker Containerization

To run using Docker, build an image and start the container:

```dockerfile
# Dockerfile
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

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t enterprise-telegrambot .
docker run -d --name telegram_bot --env-file .env enterprise-telegrambot
```

---

## 🔒 Security & Reliability

- **UTF-8 Stream Enforcement**: Configures explicit UTF-8 stdout/stderr streams to prevent encoding exceptions on Windows environments.
- **SQL Injection Prevention**: All queries in `database/models.py` strictly execute through parameterized asyncpg queries (`$1, $2, ...`).
- **Spoiler-Protected Tokens**: Bot tokens accessed through the Bot Manager dashboard are delivered wrapped in `<tg-spoiler>` tags.
- **Graceful Lifecycle Handlers**: `on_startup` and `on_shutdown` hooks verify connection pools, close HTTP aiohttp sessions, and inform administrators of status transitions.
- **Fail-Safe Fallbacks**: Network or API omissions (OpenAI, OpenWeatherMap, PostgreSQL) gracefully drop into mock modes without terminating bot execution.

---

## 📄 License & Contributing

Distributed under the **MIT License**. See `LICENSE` for details.

### Contributing
Contributions, issues, and feature requests are welcome!
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

**Author**: Kenenisa Beyan  
**Repository**: [github.com/kenenisabeyan/telegrambot](https://github.com/kenenisabeyan/telegrambot)
