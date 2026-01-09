"""glass_box_schema

Revision ID: 9699e24ec699
Revises: 
Create Date: 2026-01-08 20:03:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9699e24ec699'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ====================================================================
    # Quraite Agent Platform - PostgreSQL Schema (Production-Ready Final)
    # ====================================================================

    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    # ====================================================================
    # TABLE: agents
    # ====================================================================
    op.execute("""
        CREATE TABLE agents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL,
            slug VARCHAR(100) NOT NULL,
            description TEXT,
            system_prompt TEXT NOT NULL,
            model_config JSONB NOT NULL DEFAULT '{}'::jsonb,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

            CONSTRAINT uq_agents_name UNIQUE (name),
            CONSTRAINT uq_agents_slug UNIQUE (slug)
        );
    """)
    op.execute("CREATE INDEX idx_agents_slug ON agents(slug);")

    # ====================================================================
    # TABLE: sessions
    # ====================================================================
    op.execute("""
        CREATE TABLE sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id VARCHAR(255) NOT NULL,
            agent_id UUID NOT NULL,
            context_data JSONB NOT NULL DEFAULT '{}'::jsonb,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_active_at TIMESTAMPTZ NOT NULL DEFAULT now(),

            CONSTRAINT fk_sessions_agent
                FOREIGN KEY (agent_id)
                REFERENCES agents(id)
                ON DELETE RESTRICT
        );
    """)
    op.execute("CREATE INDEX idx_sessions_user_id ON sessions(user_id);")
    op.execute("CREATE INDEX idx_sessions_last_active ON sessions(last_active_at DESC);")

    # ====================================================================
    # TABLE: traces
    # ====================================================================
    op.execute("""
        CREATE TABLE traces (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID NOT NULL,
            agent_id UUID NOT NULL,

            -- Inputs/Outputs
            user_input TEXT NOT NULL,
            final_output TEXT,
            run_name VARCHAR(255),

            -- Metrics
            total_tokens INTEGER DEFAULT 0,
            total_cost NUMERIC(10, 6) DEFAULT 0.000000,
            latency_ms INTEGER DEFAULT 0,

            -- Status & Error Handling
            is_successful BOOLEAN DEFAULT true,
            error_message TEXT,

            -- Glass Box Observability Snapshots
            system_prompt_snapshot TEXT,
            model_config_snapshot JSONB,
            tags TEXT[] DEFAULT ARRAY[]::TEXT[],
            environment VARCHAR(50) DEFAULT 'production',

            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,

            CONSTRAINT fk_traces_session
                FOREIGN KEY (session_id)
                REFERENCES sessions(id)
                ON DELETE CASCADE,

            CONSTRAINT fk_traces_agent
                FOREIGN KEY (agent_id)
                REFERENCES agents(id)
                ON DELETE RESTRICT
        );
    """)
    op.execute("CREATE INDEX idx_traces_session_id ON traces(session_id);")
    op.execute("CREATE INDEX idx_traces_agent_id ON traces(agent_id);")
    op.execute("CREATE INDEX idx_traces_created_at ON traces(created_at DESC);")
    op.execute("CREATE INDEX idx_traces_env ON traces(environment);")

    # ====================================================================
    # TABLE: trace_steps
    # ====================================================================
    op.execute("""
        CREATE TABLE trace_steps (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            trace_id UUID NOT NULL,

            -- Ordering
            sequence_order INTEGER NOT NULL,

            -- Classification
            step_type VARCHAR(50) NOT NULL,
            step_name VARCHAR(100),

            -- Glass Box Content
            input_payload JSONB,
            output_payload JSONB,

            -- Metrics
            latency_ms INTEGER DEFAULT 0,
            tokens INTEGER DEFAULT 0,
            cost_usd NUMERIC(10, 6) DEFAULT 0.000000,

            -- Error tracking
            is_error BOOLEAN DEFAULT false,
            error_message TEXT,

            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,

            CONSTRAINT fk_steps_trace
                FOREIGN KEY (trace_id)
                REFERENCES traces(id)
                ON DELETE CASCADE
        );
    """)
    op.execute("CREATE INDEX idx_steps_trace_id ON trace_steps(trace_id);")
    op.execute("CREATE INDEX idx_steps_order ON trace_steps(trace_id, sequence_order);")
    op.execute("CREATE INDEX idx_steps_type ON trace_steps(step_type);")

    # ====================================================================
    # SEED DATA
    # ====================================================================
    op.execute("""
        INSERT INTO agents (name, slug, description, system_prompt, model_config) VALUES (
            'Calculator Agent',
            'calculator',
            'A helpful assistant that can perform basic arithmetic. It explicitly reasons before acting.',
            'You are a helpful assistant with access to a Calculator tool. You MUST output your response in strict JSON format. Your JSON object must contain: "thought" (reasoning), "action" (tool name or "final_answer"), and "args" (tool arguments).',
            '{"model": "gpt-4-turbo", "temperature": 0.0}'::jsonb
        );
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS trace_steps;")
    op.execute("DROP TABLE IF EXISTS traces;")
    op.execute("DROP TABLE IF EXISTS sessions;")
    op.execute("DROP TABLE IF EXISTS agents;")
    # We might not want to drop the extension if other things use it, but for this schema it's fine
    # op.execute('DROP EXTENSION IF EXISTS "pgcrypto";')
