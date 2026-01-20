# Getting Started with Magick Mind SDK

A 10-minute guide to running your first examples.

## Prerequisites

- Python 3.8+
- Access to a Bifrost instance
- Service credentials (email/password)

## Step 1: Install SDK

```bash
cd AGD_Magick_Mind_SDK
pip install -e .
```

## Step 2: Set Environment Variables

**Option A: Using .env file** (Easier, persists across sessions)

1. Copy `test.env` to `.env`:
```bash
cp test.env .env
```

2. Edit `.env` with your credentials
3. Run examples using the helper script:
```bash
python run_example.py examples/chat_example.py
```

The helper script loads `.env` automatically (no extra dependencies needed).

**Alternative: Source manually (Bash/zsh only)**

```bash
set -a; source .env; set +a
python examples/chat_example.py
```

**Option B: Export manually** (Quick for testing)

```bash
# Bash/zsh
export BIFROST_BASE_URL="http://localhost:8888"
export BIFROST_EMAIL="service@example.com"
export BIFROST_PASSWORD="your-password"

# Fish
set -gx BIFROST_BASE_URL "http://localhost:8888"
set -gx BIFROST_EMAIL "service@example.com"
set -gx BIFROST_PASSWORD "your-password"

python examples/chat_example.py
```

## Step 3: Try Examples (In Order)

### 1. Authentication (30 seconds)
```bash
python examples/email_password_auth.py
```
**What it does:** Connects to Bifrost and authenticates.

### 2. Chat Message (1 minute)
```bash
python examples/chat_example.py
```
**What it does:** Sends a message to an AI mindspace.

### 3. Message History (1 minute)
```bash
python examples/history_example.py
```
**What it does:** Fetches past messages with pagination.

### 4. Realtime Messages (2 minutes)
```bash
python examples/realtime_chat.py
```
**What it does:** Listens for AI responses in real-time.

### 5. Complete Workflow (5 minutes)
```bash
python examples/complete_chat_workflow.py
```
**What it does:** Full loop - send via HTTP, receive via realtime.

## What's Next?

**Explore by Category:**
- **CRUD**: `mindspace_example.py`, `project_example.py`, `corpus_example.py`
- **Backend Patterns**: `caching_example.py`, `notification_pattern_example.py`
- **Production**: `backend_service.py`, `fan_out_relay.py`

**Read Documentation:**
- [Backend Architecture](docs/architecture/backend_architecture.md)
- [Event-Driven Patterns](docs/architecture/event_driven_patterns.md)
- [Realtime Guide](docs/realtime_guide.md)

## Troubleshooting

**"Connection refused"**
→ Start Bifrost: `docker-compose up bifrost`

**"Invalid credentials"**
→ Check `BIFROST_EMAIL` and `BIFROST_PASSWORD` in your environment

**"Module not found"**
→ Run `pip install -e .` from SDK root directory
