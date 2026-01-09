# GlassBox Agent Backend

> **Pure Python ReAct Agent with Full Observability**

A production-ready FastAPI backend implementing a transparent, observable AI agent system using Google's Gemini API. Built for debugging, tracing, and understanding every step of agent execution.

---

## 🏗️ Architecture Overview

### System Architecture
```mermaid
graph TB
    subgraph "Client Layer"
        FE[Frontend/Client]
    end
    
    subgraph "API Gateway"
        CORS[CORS Middleware]
        AUTH[Authentication]
        RATE[Rate Limiter]
    end
    
    subgraph "API Endpoints"
        STREAM[/chat/stream<br/>SSE Streaming]
        TRACES[/traces<br/>List & Detail]
        REPLAY[/traces/:id/replay<br/>Replay]
        SESSION[/sessions<br/>Management]
    end
    
    subgraph "Agent Engine"
        direction TB
        ARQ[ARQ Pattern:<br/>1. Thought<br/>2. Action<br/>3. Observation]
        METRICS[Metrics Tracker:<br/>Tokens, Cost, Latency]
        SNAPSHOT[System Snapshots]
    end
    
    subgraph "Tool Execution"
        CALC[Calculator Tool]
        TOOLS[Extensible Tools]
    end
    
    subgraph "LLM Provider"
        GEMINI[Google Gemini API<br/>gemini-2.5-flash]
    end
    
    subgraph "Persistence Layer"
        DB[(PostgreSQL<br/>AsyncPG)]
        ENCRYPT[Encryption at Rest<br/>AES-256]
    end
    
    subgraph "Observability"
        TRACE_DB[Trace Storage]
        STEP_DB[Step-by-Step Logs]
        METRICS_DB[Per-Step Metrics]
    end
    
    FE -->|HTTP/SSE| CORS
    CORS --> AUTH
    AUTH --> RATE
    RATE --> STREAM
    RATE --> TRACES
    RATE --> REPLAY
    RATE --> SESSION
    
    STREAM --> ARQ
    REPLAY --> ARQ
    
    ARQ -->|Tool Call| CALC
    ARQ -->|Tool Call| TOOLS
    ARQ -->|LLM Request| GEMINI
    ARQ --> METRICS
    ARQ --> SNAPSHOT
    
    GEMINI -->|Response| ARQ
    CALC -->|Result| ARQ
    TOOLS -->|Result| ARQ
    
    ARQ -->|Write| TRACE_DB
    METRICS -->|Write| METRICS_DB
    ARQ -->|Write| STEP_DB
    
    TRACE_DB --> DB
    STEP_DB --> DB
    METRICS_DB --> DB
    
    DB --> ENCRYPT
    
    TRACES -->|Read| DB
    SESSION -->|Read/Write| DB
    
    style ARQ fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff
    style METRICS fill:#2196F3,stroke:#333,stroke-width:2px,color:#fff
    style GEMINI fill:#FF9800,stroke:#333,stroke-width:2px,color:#fff
    style DB fill:#9C27B0,stroke:#333,stroke-width:2px,color:#fff
```
---

### Database Schema

```mermaid
erDiagram
    agents ||--o{ sessions : "uses"
    sessions ||--o{ traces : "has"
    traces ||--o{ trace_steps : "contains"
    
    agents {
        uuid id PK "default: gen_random_uuid()"
        varchar name UK
        varchar slug UK "For URL routing (e.g., /agent/calculator)"
        text description
        text system_prompt "Current active prompt"
        jsonb model_config "Default model settings"
        boolean is_active
        timestamptz created_at
        timestamptz updated_at
    }
    
    sessions {
        uuid id PK
        varchar user_id "Client-side UUID or Auth ID"
        uuid agent_id FK
        jsonb context_data "Custom session metadata"
        timestamptz created_at
        timestamptz last_active_at
        boolean is_active
    }
    
    traces {
        uuid id PK
        uuid session_id FK
        uuid agent_id FK "Denormalized for analytics speed"
        varchar run_name "Optional user-friendly name"
        text user_input "The prompt that started this run"
        text final_output "The final agent response"
        
        %% Metrics
        integer total_tokens
        numeric total_cost "USD, precision 10,6"
        integer latency_ms
        boolean is_successful
        text error_message
        
        %% Observability Snapshots (Glass Box)
        text system_prompt_snapshot "Copy of agent prompt at runtime"
        jsonb model_config_snapshot "Copy of temp/top_p at runtime"
        text[] tags
        varchar environment "dev/staging/prod"
        
        timestamptz created_at
        timestamptz completed_at
    }
    
    trace_steps {
        uuid id PK
        uuid trace_id FK
        integer sequence_order "1, 2, 3... Essential for linear visualization"
        
        varchar step_type "thought | tool_call | tool_result | llm_response"
        varchar step_name "e.g., 'Calculator Tool' or 'Reasoning'"
        
        %% The Glass Box Split
        jsonb input_payload "Arguments or Context"
        jsonb output_payload "Result or Thought"
        
        integer latency_ms
        integer tokens
        numeric cost_usd
        
        boolean is_error
        text error_message
        
        timestamptz started_at
        timestamptz completed_at
    }
```


---

## ✨ Features

### ✅ Implemented (Production Ready)

- **🔄 Streaming Chat** - Server-Sent Events (SSE) for real-time responses
- **🧠 ARQ Pattern** - Transparent reasoning (Thought → Action → Result → Thought)
- **📊 Full Observability** - Every step logged with timing and metrics
- **💾 Trace Management** - List, inspect, and replay any execution
- **📈 Metrics Tracking** - Per-step latency, total tokens, cost calculation
- **🔒 Encryption** - User inputs/outputs encrypted at rest (AES-256)
- **🎯 Guest Authentication** - UUID-based auth with device fingerprinting
- **⚡ Rate Limiting** - 60 RPM / 1000 RPH per guest user
- **🔄 Auto Model Sync** - .env model config auto-syncs to database
- **📸 System Snapshots** - Captures system prompt & model config per trace

### 🔄 Active Development

- Documentation updates (this file!)
- Automated testing suite
- Frontend observability dashboard

---

## 🗄️ Database Schema

### Core Tables

**`traces`** - Top-level execution records
- Encrypted user input/output
- Total metrics (tokens, cost, latency)
- System snapshots for replay

**`trace_steps`** - Individual steps
- ARQ flow: thought → tool_call → tool_result → thought
- Per-step latency and timestamps
- Complete audit trail

**`sessions`** - Conversation context
- Multi-turn memory (last 5 traces)
- Guest user association

**`guest_users`** - Anonymous users
- Device fingerprinting
- Rate limit tracking
- GDPR retention (90 days)

---

## 🚀 Quick Start

### Prerequisites
```bash
# Required
- Python 3.11+
- PostgreSQL 14+
- Poetry

# API Keys
- Gemini API key (get from https://ai.google.dev/)
```

### Installation

```bash
# 1. Clone and navigate
cd backend

# 2. Install dependencies
poetry install

# 3. Configure environment
cp .env.example .env
# Edit .env with your API keys and database URL

# 4. Run migrations
poetry run alembic upgrade head

# 5. Start server
poetry run uvicorn app.main:app --reload
```

Server runs at: `http://localhost:8000`  
Swagger docs at: `http://localhost:8000/docs`

---

## 📡 API Endpoints

### Chat
```bash
POST /api/v1/chat/stream
# Streaming chat with SSE events
Headers: Authorization: Bearer <client_uuid>, X-API-Key: <api_key>
Body: {"message": "Calculate 10 + 5"}
```

### Traces
```bash
GET /api/v1/traces?limit=10&offset=0
# List all traces with pagination

GET /api/v1/traces/{trace_id}
# Get trace with nested steps

POST /api/v1/traces/{trace_id}/replay
# Replay trace with same input
```

### Sessions
```bash
GET /api/v1/sessions/{session_id}/traces
# Get all traces for a session
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname

# API Keys
GEMINI_API_KEY=your_gemini_api_key
API_KEY=your_backend_api_key
ENCRYPTION_KEY=your_32_byte_encryption_key

# LLM Config (auto-synced to DB on startup)
LLM_MODEL=gemini-2.5-flash
LLM_PROVIDER=gemini

# Agent Config
AGENT_MAX_ITERATIONS=10
AGENT_TIMEOUT=300

# Rate Limiting
RATE_LIMIT_RPM=60
RATE_LIMIT_RPH=1000
```

### Model Configuration
Model config in `.env` automatically syncs to database on application startup:
```python
# Changes to LLM_MODEL are auto-applied
LLM_MODEL=gemini-2.5-flash  # → DB updates on next startup
```

---

## 📊 Observability

### Trace Structure
```json
{
  "id": "uuid",
  "user_input": "Calculate 10 + 5",
  "final_output": "15",
  "total_tokens": 129,
  "total_cost": "0.000015",
  "latency_ms": 2881,
  "system_prompt_snapshot": "You are a helpful assistant...",
  "model_config_snapshot": {
    "model": "gemini-2.5-flash",
    "temperature": 0.1
  },
  "steps": [
    {
      "sequence_order": 1,
      "step_type": "thought",
      "output_payload": {
        "thought": "I need to use calculator",
        "reasoning": "Math operation required"
      },
      "latency_ms": 2,
      "completed_at": "2026-01-09T..."
    },
    {
      "sequence_order": 2,
      "step_type": "tool_call",
      "step_name": "calculator",
      "input_payload": {"expression": "10 + 5"},
      "latency_ms": 15,
      "completed_at": "2026-01-09T..."
    },
    {
      "sequence_order": 3,
      "step_type": "tool_result",
      "output_payload": {"result": "15"},
      "latency_ms": 3,
      "completed_at": "2026-01-09T..."
    },
    {
      "sequence_order": 4,
      "step_type": "thought",
      "output_payload": {"thought": "The answer is 15"},
      "latency_ms": 8,
      "completed_at": "2026-01-09T..."
    }
  ]
}
```

### Metrics Tracked

**Trace Level:**
- Total tokens (input + output)
- Total cost (Gemini 2.5 Flash pricing: $0.075/1M in, $0.30/1M out)
- End-to-end latency
- Success/failure status

**Step Level:**
- Individual step latency
- Completion timestamps
- Error tracking

---

## 🛠️ Development

### Project Structure
```
backend/
├── app/
│   ├── api/v1/          # API endpoints
│   │   ├── chat.py      # (Deprecated) Sync chat
│   │   ├── stream.py    # SSE streaming endpoint
│   │   ├── traces.py    # Trace management
│   │   └── analytics.py # Analytics endpoints
│   ├── core/            # Core utilities
│   │   ├── config.py    # Settings management
│   │   ├── startup.py   # Auto model sync
│   │   ├── auth.py      # Guest authentication
│   │   └── security.py  # Encryption/hashing
│   ├── crud/            # Database operations
│   │   ├── crud_trace.py
│   │   ├── crud_session.py
│   │   └── crud_guest_user.py
│   ├── engine/          # Agent logic
│   │   ├── agent_engine.py   # Sync agent
│   │   ├── stream_engine.py  # Streaming agent
│   │   └── tools/            # Tool implementations
│   ├── models/          # SQLAlchemy models
│   └── schemas/         # Pydantic schemas
├── alembic/            # Database migrations
├── docs/               # Technical documentation
├── examples/           # Example clients
└── tests/              # Test suite
```

### Running Tests
```bash
poetry run pytest
poetry run pytest --cov=app tests/
```

### Database Migrations
```bash
# Create migration
poetry run alembic revision --autogenerate -m "description"

# Apply migrations
poetry run alembic upgrade head

# Rollback
poetry run alembic downgrade -1
```

---

## 🔐 Security

- **Encryption at Rest** - User inputs/outputs encrypted (AES-256-GCM)
- **Device Fingerprinting** - SHA-256 hashed device IDs
- **Rate Limiting** - Per-user request throttling
- **API Key Auth** - Required for all endpoints
- **Guest UUID Auth** - Stateless UUID-based sessions
- **GDPR Compliance** - 90-day data retention, consent tracking

---

## 📈 Performance

**Typical Response Times:**
- Simple queries: 2-5 seconds
- Tool-using queries: 5-15 seconds
- Complex multi-tool: 15-30 seconds

**Bottlenecks:**
- Gemini API latency (main factor)
- Database writes (minimal overhead with async)

**Optimizations:**
- Async database operations (AsyncPG)
- Connection pooling
- Efficient step logging
- Encryption only on PII fields

---

## 📚 Additional Documentation

- [`docs/DbSchema.md`](docs/DbSchema.md) - Complete database schema
- [`docs/Feature.md`](docs/Feature.md) - Detailed feature specs
- [`docs/Project.md`](docs/Project.md) - Project requirements
- [Task Artifact](../../.gemini/antigravity/brain/.../task.md) - Implementation checklist

---

## 🐛 Known Limitations

1. **Gemini API Quota** - Free tier: 15 RPM / 1500 RPD
2. **Per-Step Tokens** - Gemini doesn't provide per-step token counts (only totals)
3. **Tool Repertoire** - Currently only calculator (extensible design)

---

## 🚧 Roadmap

### Near Term
- [ ] Documentation updates (DbSchema, Feature, Security)
- [ ] Automated test suite
- [ ] Additional tools (web search, code execution)

### Future
- [ ] Frontend observability dashboard
- [ ] Multi-agent orchestration
- [ ] Cost optimization tools
- [ ] Advanced analytics

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/Tamilarasan-ai/GlassBox-Backend/issues)
- **Docs:** See `docs/` directory
- **API Docs:** `http://localhost:8000/docs` (when running)

---

**Built with transparency and observability in mind** 🔍
