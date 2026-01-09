---

### 📦 Phase 1: Backend Core & Agent Engine

### **Task 1.1: Database & Models Setup**

- **Tags:** `FastAPI` `NeonDB` `SQLAlchemy` `Pydantic`
- **Description:** Initialize the database connection and define the schema that supports the "Glass-Box" observability. This is the foundation. You need to handle the connection to NeonDB securely and ensure the ORM models map 1:1 with the provided SQL schema.
- **Tech Details:**
    - Use `sqlalchemy.ext.asyncio` to create an `AsyncSession`.
    - Define models in `backend/models.py`:
        - `Agent` (stores system prompt & config).
        - `Session` (links user_id to agent).
        - `Trace` (stores high-level run metrics: cost, latency, snapshots).
        - `TraceStep` (stores atomic steps: thoughts, tool calls).
    - Create a `backend/database.py` utility to handle `get_db` dependency injection for FastAPI routes.
- **Acceptance Criteria:**
    - `alembic` or `SQLModel.metadata.create_all()` runs without errors against NeonDB.
    - Tables `agents`, `sessions`, `traces`, `trace_steps` exist in the DB.

### **Task 1.2: The Calculator Tool (Secure Math)**

- **Tags:** `Python` `Logic`
- **Description:** Build the core tool the agent will use. Since this is an evaluation platform, the tool needs to be deterministic and safe. Do not use `eval()` as it introduces security risks.
- **Tech Details:**
    - Create `backend/tools/calculator.py`.
    - Implement a function `calculate(expression: str) -> str`.
    - Use Python's `ast` module or `operator` module to parse strings like `"50 * 10"` into operations.
    - **Error Handling:** If the math is invalid (e.g., divide by zero), return a string `"Error: Cannot divide by zero"` instead of raising an exception. This allows the Agent to see the error and try again (self-correction).
- **Acceptance Criteria:**
    - `calculate("2 + 2")` returns `"4"`.
    - `calculate("invalid")` returns a descriptive error string.

### **Task 1.3: Agent Context & State Machine**

- **Tags:** `FastAPI` `Gemini` `Prompt Engineering`
- **Description:** Implement the core "ReAct" (Reason + Act) loop. This function manages the conversation history and the decision-making process using Gemini.
- **Tech Details:**
    - Create `backend/agent_engine.py`.
    - **Step 1 (History):** Query the `traces` table for the last 5 runs associated with the current `session_id`. Concatenate `user_input` and `final_output` into a list of messages.
    - **Step 2 (The Loop):** Create a `while` loop (max 5 iterations).
        - Call Gemini with `tools` definitions (Function Calling) OR structured JSON prompting.
        - **Snapshotting:** On the first iteration, capture the `system_prompt` and `model_config` and save them to the `Trace` object in DB.
    - **Step 3 (Persistence):** Inside the loop, every time Gemini generates a "Thought" or "Tool Call", insert a row into `trace_steps`.
- **Acceptance Criteria:**
    - Agent remembers context (e.g., "Add 5 to that" works after a previous calculation).
    - Agent executes multi-step logic (e.g., "Multiply then Divide") in a single run.

### **Task 1.4: Async Streaming API**

- **Tags:** `FastAPI` `SSE` `AsyncIO`
- **Description:** Create the endpoint that the frontend connects to. This needs to stream data in real-time so the user feels the "chat" experience, while simultaneously logging data to NeonDB in the background.
- **Tech Details:**
    - Define `POST /api/v1/chat/stream`.
    - Use `sbt.StreamingResponse` (FastAPI).
    - Implement an async generator `event_generator()`:
        - Yield JSON chunks for UI: `{"type": "token", "content": "..."}`.
        - Await DB writes: `await db.commit()` (Crucial: use `await` so the stream doesn't freeze while saving to NeonDB).
- **Acceptance Criteria:**
    - Endpoint returns `text/event-stream`.
    - UI receives the `trace_id` in the very first event (needed for linking).

---

### 📦 Phase 2: Frontend Setup & Sync

### **Task 2.1: Layout & Session State**

- **Tags:** `React` `TailwindCSS` `Zustand/Context`
- **Description:** Set up the application shell. Establish the user's identity so they can refresh the page and not lose their history.
- **Tech Details:**
    - **Router:** Setup `react-router-dom` with routes `/chat` and `/traces`.
    - **Sidebar:** Create a collapsible sidebar using Tailwind (`w-64`, `fixed`, `border-r`).
    - **Session Management:**
        - On `App.tsx` mount: Check `localStorage` for `quraite_user_id`. If missing, generate `crypto.randomUUID()` and save it.
        - Create a Context or Zustand store to hold `currentSessionId`.
- **Acceptance Criteria:**
    - Refreshing the page keeps the same User ID.
    - Sidebar navigation switches views without full page reload.

### **Task 2.2: Chat UI with History**

- **Tags:** `React` `Fetch API` `TailwindCSS`
- **Description:** The user-facing interface. Needs to handle optimistic updates (showing user message immediately) and rendering the streamed response.
- **Tech Details:**
    - **History Loader:** `useEffect` call to `GET /api/v1/sessions/{id}/history` to populate previous chat bubbles.
    - **Stream Reader:** Use `fetch()` with a `ReadableStream` reader to parse the SSE events from Task 1.4.
    - **Visuals:** Standard chat bubbles (User = Blue/Right, Agent = Gray/Left).
- **Acceptance Criteria:**
    - Message list auto-scrolls to bottom on new token.
    - "Thinking..." indicator appears while waiting for first token.

---

### 📦 Phase 3: Observability & Replay

### **Task 3.1: The Live Trace Table**

- **Tags:** `React` `TanStack Query` `TailwindCSS`
- **Description:** The "Engineer Mode" view. This table displays the list of all executions.
- **Tech Details:**
    - **Data Fetching:** Use `useQuery` to fetch `GET /api/v1/traces`.
    - **Columns:** Status (Icon), Trace ID (monospace font), Input Summary, Tokens, Cost (formatted as currency), Latency (formatted as `ms` or `s`).
    - **Auto-Refetch:** Configure React Query to `invalidateQueries(['traces'])` whenever a chat message finishes streaming in the Chat UI. This makes the table update "magically" when the user switches tabs.
- **Acceptance Criteria:**
    - Table displays data from NeonDB.
    - Clicking a row sets a `selectedTraceId` state.

### **Task 3.2: The Inspection Modal (Glass Box)**

- **Tags:** `React` `Headless UI` `JSON View`
- **Description:** The most critical UI component. It visualizes the Agent's internal thought process.
- **Tech Details:**
    - **Modal:** Create a full-screen overlay (`fixed inset-0 bg-black/50 backdrop-blur`).
    - **Waterfall Visualization:** Map through the `trace_steps` fetched from the API.
        - If `type === 'thought'`, render a Blue box.
        - If `type === 'tool_call'`, render an Orange box.
    - **Data Display:** Use a `<pre className="font-mono text-xs">` tag to render the JSON payloads (`input_payload`, `output_payload`) cleanly.
    - **Snapshot Panel:** On the right side, display the `system_prompt_snapshot` used during that specific run.
- **Acceptance Criteria:**
    - Modal opens when table row is clicked.
    - Shows "Thought" -> "Tool" -> "Result" sequence clearly.

### **Task 3.3: True Replay System**

- **Tags:** `FastAPI` `React` `Gemini`
- **Description:** Allow engineers to re-run a past input to check if the logic is deterministic or to debug a failure.
- **Tech Details:**
    - **Backend:** Create `POST /api/v1/traces/{id}/replay`.
        - Logic: Fetch the *old* trace, extract the `user_input` and `agent_id`, and immediately invoke `agent_engine.run_agent()` with these parameters. Return the *new* `trace_id`.
    - **Frontend:** Add a "Replay 🔄" button in the Modal header.
    - **Action:** On success, close the current modal and immediately open the modal for the *new* trace ID.
- **Acceptance Criteria:**
    - Replaying a trace creates a NEW row in the Trace Table.
    - The new trace contains the exact same input as the original.

---

### 📦 Phase 4: Delivery Polish

### **Task 4.1: Docker & Config**

- **Tags:** `Docker` `Docker Compose` `Bash`
- **Description:** Containerize the application so it can be run with a single command.
- **Tech Details:**
    - `Dockerfile.backend`: Python 3.11 slim image. Install dependencies. `CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]`.
    - `Dockerfile.frontend`: Node 18 image. Build React app. Serve via simple static server (or Nginx).
    - `docker-compose.yml`: Define services `backend`, `frontend`. Pass `DATABASE_URL` and `GEMINI_API_KEY` as environment variables.
    - **Seeding:** Create a `scripts/seed.py` that checks if the "Calculator Agent" exists in NeonDB. If not, insert it. Run this on container startup.
- **Acceptance Criteria:**
    - `docker-compose up --build` starts the whole stack.
    - The "Calculator Agent" is pre-populated in the DB on first run.

### **Task 4.2: End-to-End Verification**

- **Tags:** `QA` `Manual Testing`
- **Description:** Final sanity check before submission.
- **Tech Details:**
    - **Scenario:**
        1. Open App -> Chat.
        2. Type "What is 100 * 5?". Wait for "500".
        3. Type "Divide that by 2". Wait for "250".
        4. Go to "Traces".
        5. Open the second trace ("Divide that by 2").
        6. Verify the `system_prompt_snapshot` is present.
        7. Verify the input payload to the tool was `500` (proving context worked).
- **Acceptance Criteria:**
    - All steps in the scenario pass.
    - No console errors in browser.