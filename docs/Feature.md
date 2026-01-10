### GlassBoxAgent Platform (v1.0)

**Objective:** Build a high-observability "Glass-Box" Agent Execution Environment.

**Core Philosophy:** Structure > Vibes. Every reasoning step and tool call must be captured, measured, and debuggable.

## 1. System Architecture & Tech Stack

- **Architecture Pattern:** Event-Driven Finite State Machine (FSM).
- **Constraint:** Zero Agent Frameworks (No LangChain/LangGraph). Pure Python logic.
- **Backend:** FastAPI (Async), SQLAlchemy 2.0.
- **Database:** PostgreSQL (Neon) with JSONB support for structured trace logs.
- **Frontend:** React (Vite) + Tailwind CSS + TanStack Query.
- **Infra:** Docker Compose (Service orchestration).

---

## 2. User Interface (UI) Specifications

### 2.1 Global Navigation (Sidebar)

A fixed-width left sidebar serves as the application controller.

- **Section 1: Chat**
    - Heading: AGENTS
    - Item: Calculator Agent (Active state indicates Chat Mode).
- **Section 2: Observability**
    - Heading: MONITORING
    - Item: Traces (Active state indicates Data/Debug Mode).

### 2.2 View A: The Chat Interface (User Mode)

- **Access:** Active when "Calculator Agent" is selected.
- **Layout:** Standard conversational UI.
- **Behavior:**
    - **Input:** Text area for user queries (e.g., "Calculate 50 * 55").
    - **Streaming:** The Assistant's response must stream token-by-token.
    - **Context:** The UI must maintain a session_id (UUID) in localStorage to allow multi-turn context (e.g., "Divide *that* by 10").
    - **State Indication:** While the agent is "Thinking" or "Calling Tools," show a subtle indeterminate loader. Do not show raw logs here (keep it clean).

### 2.3 View B: The Trace Table (Engineer Mode)

- **Access:** Active when "Traces" is selected.
- **Layout:** Full-width Data Table showing historical runs.
- **Columns:**
    1. **Status:** Icon (✅ Success / ❌ Error).
    2. **Trace ID:** UUID (Truncated, e.g., 8f2a...).
    3. **Input Preview:** First 50 chars of the user prompt.
    4. **Tokens:** Total tokens used (Input + Output).
    5. **Latency:** Total execution time (ms).
    6. **Cost:** Calculated USD cost (e.g., $0.0042).
    7. **Timestamp:** Relative time (e.g., "2 mins ago").
- **Interaction:** Clicking **any row** triggers the **Trace Inspection Modal**.

### 2.4 View C: The Trace Inspection Modal (Glass-Box View)

- **Component:** A modal overlay covering **90% of the screen width/height** with a backdrop blur.
- **Header:**
    - Title: Trace Details: {trace_id}
    - Metrics Badge: Total Latency: 450ms | Cost: $0.0002.
- **Left Panel (The Waterfall):**
    - A vertical timeline visualizing the Agent's execution loop.
    - **Nodes:**
        - 🧠 **Reasoning Node:** Displays the structured thought (JSON).
        - 🔧 **Tool Node:** Displays tool_name and arguments.
        - 📉 **Output Node:** Displays the raw tool result.
        - 🤖 **Response Node:** The final text sent to the user.
    - **Styling:** Each node must be expandable. Tool nodes should explicitly show latency (e.g., (12ms)).
- **Right Panel (Metadata):**
    - Session ID.
    - Model Config (e.g., "Gemini Pro").
    - System Prompt Snapshot (ReadOnly).

---

## 3. Functional Specifications (Backend)

### 3.1 The Agent Core (Finite State Machine)

The agent logic must be implemented as a while loop in pure Python:

1. **Observation:** Append user input to messages.
2. **Decision (ARQ):** Call LLM with a structured system prompt forcing JSON output.
    - *Schema:* {"thought": "...", "tool": "...", "args": {...}}.
3. **Log:** Persist the "Reasoning" step to the DB.
4. **Action:**
    - If tool == calculator: Execute Python math function.
    - If tool == final_answer: Break loop.
5. **Log:** Persist the "Tool Execution" step (Input/Output/Latency).
6. **Loop:** Feed tool output back into LLM context.

### 3.2 Structured Reasoning (ARQ)

To satisfy the CTO's requirement for "Attentive Reasoning Queries":

- The System Prompt must enforce a "Thought-First" approach.
- The Agent **must** generate a reasoning string *before* generating tool arguments.
- This reasoning is stored separately in the database (step_type='thought').

### 3.3 Calculator Tool

- **Constraint:** Must use Python's ast or operator module for safety (no eval()).
- **Operations:** Add, Subtract, Multiply, Divide.
- **Error Handling:** DivideByZero must return a clean error string to the Agent, not crash the server.

---

## 4. Data Model (PostgreSQL)

### Table: sessions

- id (UUID, PK)
- created_at (Timestamp)

### Table: traces (The Run)

- id (UUID, PK)
- session_id (FK -> sessions.id)
- user_input (Text)
- final_output (Text, Nullable)
- total_tokens (Integer)
- total_cost (Float, Decimal)
- latency_ms (Integer)
- status (Enum: running, completed, failed)
- created_at (Timestamp)

### Table: trace_steps (The Atomic Observations)

- id (UUID, PK)
- trace_id (FK -> traces.id)
- step_type (Enum: thought, tool_call, tool_result, llm_message)
- content (JSONB) - *Stores arguments, thoughts, or results.*
- latency_ms (Integer) - *Specific to this step.*
- created_at (Timestamp)

---

## 5. API Contract (FastAPI)

### Chat & Streaming

**POST** /api/v1/chat/stream

- **Input:** { "session_id": "uuid", "message": "string" }
- **Behavior:** Initiates the Agent Loop.
- **Response:** text/event-stream (SSE).
    - Streams tokens for the final answer to the UI.
    - *Internal:* Asynchronously writes steps to the DB as they happen.

### Observability

**GET** /api/v1/traces

- **Query Params:** limit, offset.
- **Response:** List of Trace objects (flattened for the table).

**GET** /api/v1/traces/{trace_id}

- **Response:** Full Trace object with a nested list of trace_steps.

---

## 6. Production Readiness Requirements

1. **Environment Configuration:**
    - GEMINI_API_KEY loaded via .env.
    - DATABASE_URL loaded via .env.
2. **Error Handling:**
    - Graceful handling of LLM Rate Limits (429).
    - Graceful handling of Tool Errors (e.g., Agent tries to calculate "Apple * Banana").
3. **Sanitization:**
    - Ensure tool outputs are truncated if they exceed 5KB (to prevent context window overflow).
4. **Security:**
    - CORS configured for the frontend domain only.
    - Input validation using Pydantic models.