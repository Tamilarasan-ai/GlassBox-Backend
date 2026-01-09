---

# Conversational AI Agent Platform (Calculator)

## Objective

Build a **production-ready conversational AI agent platform** that supports:

- Multi-turn reasoning
- Tool calling
- Streaming execution
- Run inspection & replay
- Full observability UI (LangSmith-style)

The system must behave like a **debuggable agent execution platform**, not just a chatbot.

---

## Hard Constraints (Non-Negotiable)

1. You **must not** use any AI agent framework or orchestration library:
    - No LangChain
    - No LangGraph
    - No CrewAI
    - No AutoGen
    - No Semantic Kernel
    - No PydanticAI
    - No similar frameworks
2. You **must** implement:
    - Agent loop
    - Planning / reasoning
    - Tool routing
    - Memory / state handling
    **using plain Python only**
3. Tech stack is **fixed**:
    - Backend: Python, FastAPI, SQLAlchemy
    - Frontend: React
    - Database: PostgreSQL (Neon allowed)
    - Infra: Docker, docker-compose, Makefile
4. The UI **must follow** the provided reference image:
    - Debug / observability UI
    - Not a simple chat UI
    - Must show runs, steps, tool calls, outputs, metadata

---

## Core Behavior Requirement

Conversation example:

Turn 1:

> 1 + 1
Assistant → 2
> 

Turn 2:

> Multiply that by 3
Assistant → 6
> 

The system must:

- Maintain conversational context
- Resolve references like: *that, it, previous result*
- Decide when to call tools
- Execute tools
- Return results

---

## Functional Scope

You must build:

- A conversational agent execution system
- A calculator tool system
- A run execution engine
- A run inspection & replay system
- A streaming UI

---

## UI Requirements

The UI must:

- Be similar in **layout and purpose** to the provided reference image
- Show:
    - Past runs
    - Current run
    - Steps inside a run
    - Tool calls and tool outputs
    - Reasoning steps
    - Final output
    - Execution metadata (time, tokens, status, etc.)
- Support:
    - Replaying runs
    - Inspecting any step
    - Viewing structured tool call logs
    - Live streaming execution

---

## Data Persistence Requirements

You must persist:

- Conversations
- Turns
- Agent reasoning steps
- Tool calls
- Tool inputs & outputs
- Final answers
- Run metadata

Using PostgreSQL via SQLAlchemy.

---

## API Requirements

Backend must expose APIs for:

- Starting a run
- Streaming a run
- Fetching run history
- Fetching run details
- Replaying runs

---

## Deployment Requirements

Repository must include:

- Backend container
- Frontend container
- docker-compose setup
- Makefile
- README with setup instructions
- No secrets committed

One command must start the full system.

---

## Submission Requirements

- GitHub repository link
- README with:
    - How to run
    - How to test
- Short email summary describing:
    - What you built
    - How to run it

---

# Acceptance Criteria

A submission is considered **acceptable only if all conditions below are met**:

## 1. Architecture & Constraints

- [ ]  No agent framework is used anywhere
- [ ]  Agent logic, tool routing, and state handling are implemented manually
- [ ]  Only the allowed tech stack is used

## 2. Functional Correctness

- [ ]  Multi-turn context works correctly
- [ ]  References like “that” and “previous result” resolve correctly
- [ ]  Tool calls are used for calculations
- [ ]  Tool inputs and outputs are logged and visible
- [ ]  The system produces correct results for chained operations

## 3. UI & Observability

- [ ]  UI matches the **debug/inspection workflow** of the reference image
- [ ]  Past runs are visible and selectable
- [ ]  Each run shows:
    - [ ]  Steps
    - [ ]  Reasoning
    - [ ]  Tool calls
    - [ ]  Tool outputs
    - [ ]  Final answer
- [ ]  Streaming execution is visible in the UI
- [ ]  Runs can be replayed and inspected

## 4. Persistence

- [ ]  All runs and steps are stored in Postgres
- [ ]  Reloading the app does not lose history
- [ ]  Run data can be fetched and replayed

## 5. API Quality

- [ ]  Clean FastAPI endpoints
- [ ]  Streaming is implemented
- [ ]  Errors are handled gracefully

## 6. Engineering Quality

- [ ]  Code is clean and structured
- [ ]  Clear separation of concerns
- [ ]  Proper error handling
- [ ]  Reasonable logging
- [ ]  Project can be run using docker-compose

## 7. Delivery Quality

- [ ]  Repo builds and runs from README instructions
- [ ]  One command starts everything
- [ ]  No secrets in repo
- [ ]  README is clear and complete

---

## Evaluation Focus

You are being evaluated on:

- System design thinking
- Engineering maturity
- Ability to build agent systems from first principles
- Observability and debuggability mindset
- Production readiness

---