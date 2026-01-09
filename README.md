# Agent Backend

Production-ready FastAPI backend with an agent engine, structured logging, and async database support.

## Features

- **FastAPI**: High-performance async API
- **SQLAlchemy 2.0**: Async ORM with PostgreSQL support
- **Alembic**: Database migrations
- **Pydantic v2**: Data validation and settings management
- **Agent Engine**: Extensible loop for building AI agents
- **Testing**: Pytest with async support

## Project Structure

```
backend/
├── alembic/              # Database migrations
├── app/
│   ├── api/              # API endpoints (v1)
│   ├── core/             # Config, security, exceptions
│   ├── crud/             # Database operations
│   ├── db/               # Database connection & base models
│   ├── engine/           # Agent logic (loop, tools, prompts)
│   ├── models/           # SQLAlchemy ORM models
│   └── schemas/          # Pydantic schemas
├── tests/                # Test suite
└── ...
```

## Getting Started

### Prerequisites

- Python 3.11+
- Poetry
- PostgreSQL

### Installation

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and API keys
   ```

3. Run migrations:
   ```bash
   poetry run alembic upgrade head
   ```

4. Start the server:
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

## Development

- Run tests:
  ```bash
  poetry run pytest
  ```

- Create a new migration:
  ```bash
  poetry run alembic revision --autogenerate -m "description"
  ```
