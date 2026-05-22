# ADK Project Template — Implementation Guide

This document describes every component in the template, what it does, when to activate it,
and the one-time setup steps required before it works.

---

## Quick Start (Windows)

```bat
REM 1. Run the setup script (creates venv + installs deps)
setup_venv.bat

REM 2. Edit your configuration
notepad .env

REM 3. Start the ADK dev UI
adk web
```

Open **http://localhost:8080** in your browser. The ADK web UI lets you chat with
the orchestrator, inspect event traces, and download artifacts.

For a quick CLI test without the UI:
```bat
python main.py "Hello, what can you help me with?"
```

---

## Agent Hierarchy

```
Orchestrator  (level 0 — root, only agent the Runner knows)
├── normal_agent          (level 1 — conversational Q&A)
│     ├── search_subagent      (level 2 — web retrieval, URL research)
│     └── summarizer_subagent  (level 2 — condensing, structuring text)
├── multitool_agent       (level 1 — tools + content generation)
│     ├── writer_subagent      (level 2 — reports, proposals, emails)
│     └── data_subagent        (level 2 — analysis, stats, PDF export)
├── sequential_agent      (level 1 — ordered multi-step pipeline)
└── parallel_agent        (level 1 — concurrent fan-out + aggregation)
```

Transfer mechanism: each agent's LLM can call `transfer_to_agent(agent_name='...')`
to hand off to any of its declared `sub_agents`. After the sub-agent finishes,
control returns to the calling agent.

Alternative — `AgentTool`: wrap any agent in `AgentTool` and put it in `tools=[]`.
The parent retains control and can inspect the result before responding.
See `tools/subagent_tool.py` for an example.

---

## Project Structure

```
.
├── main.py                   Entry point (CLI mode)
├── .env                      Your secrets and config (never commit!)
├── requirements.txt          Python dependencies
├── setup_venv.bat            Windows venv creation + activation script
├── Dockerfile                Container build
├── docker-compose.yml        Multi-service stack (app + PostgreSQL)
│
├── agents/
│   ├── orchestrator.py       Level-0 root — routes to level-1 agents
│   ├── normal_agent.py       Level-1 — Q&A + delegates to search/summarizer
│   ├── multitool_agent.py    Level-1 — tools + delegates to writer/data
│   ├── sequential_agent.py   Level-1 — ordered pipeline
│   └── parallel_agent.py     Level-1 — concurrent fan-out
│
├── subagents/
│   ├── search_subagent.py    Level-2 — web retrieval and URL research
│   ├── summarizer_subagent.py Level-2 — condensing and structuring text
│   ├── writer_subagent.py    Level-2 — document and report drafting
│   └── data_subagent.py      Level-2 — data analysis and PDF export
│
├── tools/
│   ├── common_tools.py       get_current_datetime, fetch_url (+ commented extras)
│   ├── pdf_generator.py      Generate PDF and save as artifact
│   └── subagent_tool.py      Wrap a specialist agent as an AgentTool
│
├── skills/
│   └── base_skills.py        Reusable instruction + tool bundles
│
├── callbacks/
│   ├── security_callbacks.py SQL injection / XSS / prompt-injection blocking
│   └── action_callbacks.py   Logging, timing, rate-limit hooks
│
├── plugins/
│   ├── security_plugin.py    Global guardrails applied to ALL agents
│   └── logging_plugin.py     Structured JSON logging + token tracking
│
├── database/
│   ├── connection.py         Async engine + session service factory
│   └── models.py             SQLAlchemy ORM models (User, ConversationLog)
│
├── storage/
│   └── artifact_service.py   InMemory (dev) or GCS (prod) artifact backend
│
├── rag/
│   └── rag_config.py         Vertex AI RAG tool builders (single + multi-corpus)
│
├── auth/
│   └── oauth.py              OAuth2 / APIKey scheme and credential helpers
│
└── artifacts/
    └── __init__.py           Package marker (helpers live in tools/pdf_generator.py)
```

---

## 1. Environment Configuration (`.env`)

**You must fill this in before running anything.**

| Variable | Required | Description |
| --- | --- | --- |
| `GOOGLE_API_KEY` | Dev only | Google AI Studio key (Option A — free tier) |
| `GOOGLE_GENAI_USE_VERTEXAI` | Yes | `0` = AI Studio, `1` = Vertex AI |
| `GOOGLE_CLOUD_PROJECT` | Vertex only | Your GCP project ID |
| `GOOGLE_CLOUD_LOCATION` | Vertex only | **Use `europe-west1`** — fewer quota/model issues |
| `DEFAULT_MODEL` | Yes | `gemini-2.0-flash` (fast) or `gemini-2.5-pro` (smart) |
| `DATABASE_URL` | Sessions | SQLite default; swap for Postgres in production |
| `SESSION_BACKEND` | Yes | `memory` or `database` |
| `ARTIFACT_BACKEND` | Yes | `memory` or `gcs` |
| `GCS_BUCKET_NAME` | GCS only | Your storage bucket name |
| `VERTEX_RAG_CORPUS_1` | RAG only | Full RAG corpus resource name |

> **TIP — European servers**: Set `GOOGLE_CLOUD_LOCATION=europe-west1` (Belgium)
> or `europe-west4` (Netherlands). These regions have better model availability
> and fewer quota errors than `us-central1` for European users.

---

## 2. Agents

### Orchestrator (`agents/orchestrator.py`)

The **root agent** — the only agent the Runner knows about directly.
It receives every user message and decides what to do:
- Answer directly for simple queries.
- Transfer control to a sub-agent for specialised tasks.

**To add a new specialised agent:**
1. Build it in `agents/your_new_agent.py`.
2. Import it in `orchestrator.py`.
3. Add it to `sub_agents=[...]`.

### Normal Agent (`agents/normal_agent.py`)

General-purpose `LlmAgent`. Good default for conversational queries.
Add tools to its `tools=[]` list as you build them.

### Sequential Agent (`agents/sequential_agent.py`)

`SequentialAgent` runs 3 steps in order:
```
Step 1 (research_step)  →  state["research_output"]
Step 2 (analysis_step)  →  state["analysis_output"]
Step 3 (report_step)    →  state["report_output"]
```
Each step reads the previous step's `output_key` from session state.

**To customise:** rename the steps and instructions for your use-case
(e.g. `extract → transform → load`, or `draft → review → publish`).

### Parallel Agent (`agents/parallel_agent.py`)

`ParallelAgent` runs 3 branches concurrently, then an aggregator merges results:
```
branch_a_agent ─┐
branch_b_agent ─┤ → aggregator_agent → final response
branch_c_agent ─┘
```
Each branch writes to a distinct state key (`branch_a`, `branch_b`, `branch_c`).

**To customise:** replace the 3 branches with independent tasks that can run
simultaneously (e.g. fetch data from 3 APIs, generate 3 alternative drafts).

### Multi-tool Agent (`agents/multitool_agent.py`)

`LlmAgent` with access to multiple tools. The LLM chooses which tools to use.
Uncomment `google_search` or `build_rag_tool()` in this file once configured.

---

## 3. Subagents (`subagents/`)

Subagents are **level-2 LlmAgents** declared in the `sub_agents=[]` list of a
level-1 agent. They are invisible to the orchestrator — only their immediate
parent can delegate to them.

### How transfer works

When the parent's LLM decides a subtask fits a subagent, it emits:
```
transfer_to_agent(agent_name="search_subagent")
```
ADK intercepts this, runs the named subagent with the current conversation
context, and returns control to the parent once the subagent produces a final
response.

### Available subagents

| File | Parent agent | Speciality |
| --- | --- | --- |
| `search_subagent.py` | `normal_agent` | Fetch + cite web content from URLs |
| `summarizer_subagent.py` | `normal_agent` | Bullets, key-points, action items, tables |
| `writer_subagent.py` | `multitool_agent` | Reports, proposals, emails, READMEs |
| `data_subagent.py` | `multitool_agent` | Stats, comparisons, trends + PDF export |

### Adding a new subagent

1. Create `subagents/my_subagent.py` with a `build_my_subagent()` factory.
2. Add it to the parent agent's `sub_agents=[]` list.
3. Update the parent's `instruction` to tell the LLM when to delegate there.
4. Export it from `subagents/__init__.py`.

```python
# subagents/my_subagent.py
def build_my_subagent() -> LlmAgent:
    return LlmAgent(
        name="my_subagent",          # must match the transfer_to_agent() name
        description="One sentence — the LLM reads this to decide when to delegate.",
        instruction="Detailed instructions for this subagent only.",
        tools=[...],
    )

# agents/normal_agent.py  (or whichever parent)
from subagents.my_subagent import build_my_subagent

def build_normal_agent() -> LlmAgent:
    return LlmAgent(
        ...
        sub_agents=[
            build_search_subagent(),
            build_summarizer_subagent(),
            build_my_subagent(),   # ← add here
        ],
    )
```

### sub_agents vs AgentTool — choosing the right pattern

| | `sub_agents=[]` | `AgentTool` in `tools=[]` |
| --- | --- | --- |
| Parent retains control after? | Yes (returns after subagent) | Yes |
| LLM decides when to use it? | Yes (transfer_to_agent) | Yes (tool call) |
| Parent can inspect result? | Limited | Full — tool returns a dict |
| Best for | Full delegation of a task | Calling agent, using result in further processing |

For most 3-level hierarchies `sub_agents` is the simpler choice.
Use `AgentTool` when the parent needs to act on the subagent's output
(e.g. validate content before saving as PDF).

---

## 4. Tools

### Writing a New Tool

```python
from google.adk.tools import ToolContext

async def my_tool(param_one: str, count: int, tool_context: ToolContext) -> dict:
    """Short description — this is sent to the LLM as the tool description.

    Args:
        param_one: What this parameter does.
        count: How many items to return.

    Returns:
        dict with keys: status, data
    """
    # ... implementation ...
    return {"status": "success", "data": [...]}
```

Rules:
- Always async.
- Type-annotate all parameters (str, int, float, bool, list, dict only).
- Return `{"status": "success", ...}` or `{"status": "error", "message": "..."}`.
- Access session state via `tool_context.state`.
- Save artifacts via `tool_context.save_artifact(filename, part)`.

### PDF Generator (`tools/pdf_generator.py`)

Generates a PDF from title + body text and saves it as an ADK artifact.

```python
# Agent instruction example:
"Use generate_pdf to save the report. Filename: 'my_report.pdf'."
```

The artifact appears in the ADK web UI's artifacts panel for download.
Requires `reportlab` (already in `requirements.txt`).

### Sub-agent Tool (`tools/subagent_tool.py`)

Wraps a specialist `LlmAgent` as an `AgentTool`. The parent agent calls it like
a regular tool, passing a task string, and gets back the specialist's response.

Difference from `sub_agents=[]`:
- `sub_agents` — LLM can transfer full control (the child takes over).
- `AgentTool` — parent retains control; child answers and returns.

### Common Tools (`tools/common_tools.py`)

| Tool | Description |
|---|---|
| `get_current_datetime` | Returns current UTC date/time |
| `fetch_url` | HTTP GET a public URL, returns first 4000 chars |

Commented-out extras: `send_email`, `get_weather`, `run_python_snippet`.
Uncomment and add required env vars to activate.

---

## 4. Skills (`skills/base_skills.py`)

Skills are reusable `(instruction_fragment, tools_list)` bundles.
Inject them into any agent at build time:

```python
from skills.base_skills import SKILLS

agent = LlmAgent(
    instruction=SKILLS["summarisation"]["instruction"] + MY_INSTRUCTION,
    tools=[*SKILLS["summarisation"]["tools"], my_own_tool],
)
```

Available skills:

| Skill key | What it adds |
|---|---|
| `summarisation` | Bullet-point summary instructions |
| `document_generation` | Structured document + PDF export |
| `web_research` | URL retrieval + citation instructions |
| `temporal_awareness` | Date/time grounding |

Add new skills by appending to the `SKILLS` dict.

---

## 5. Callbacks

Callbacks are **agent-level hooks** for a specific agent instance.
For **global** hooks across all agents, use Plugins (Section 6).

### Security Callbacks (`callbacks/security_callbacks.py`)

`before_model_security_cb` — runs before every LLM call on the agent it is
attached to. Blocks:
- **SQL injection**: `UNION SELECT`, `DROP TABLE`, `INSERT INTO`, etc.
- **XSS**: `<script>`, `javascript:`, event handlers.
- **Prompt injection**: phrases like "ignore previous instructions".

Returns a blocking `LlmResponse` if a threat is found; `None` otherwise.

Attach to an agent:
```python
agent = LlmAgent(
    before_model_callback=before_model_security_cb,
    ...
)
```

### Action Callbacks (`callbacks/action_callbacks.py`)

| Callback | Hook | What it does |
| --- | --- | --- |
| `before_agent_cb` | `before_agent_callback` | Log start, record timestamp |
| `after_agent_cb` | `after_agent_callback` | Log end, print elapsed time |
| `before_tool_log_cb` | `before_tool_callback` | Log tool name + args |
| `after_tool_log_cb` | `after_tool_callback` | Log tool result status |

Commented-out extras: response cache, per-session rate limiter.

---

## 6. Plugins (`plugins/`)

Plugins attach to the **Runner** and apply to **all agents** globally.

```python
# main.py / your app entrypoint
runner = Runner(
    agent=build_orchestrator(),
    plugins=[SecurityPlugin(), LoggingPlugin()],
    ...
)
```

Plugin hooks fire **before** the equivalent agent callbacks.

### Security Plugin (`plugins/security_plugin.py`)

- `before_model_callback` — blocks dangerous patterns application-wide.
- `after_model_callback` — redacts `password=`, `api_key=` in model output.
- `before_tool_callback` — audit-logs every tool call.
- `on_tool_error_callback` — alerts on unauthorized/forbidden errors.

### Logging Plugin (`plugins/logging_plugin.py`)

- Emits JSON-structured log lines per run start/end and per model call.
- Tracks input/output token counts for cost monitoring.
- Compatible with Cloud Logging (uncomment GCP section to forward automatically).

---

## 7. Database (`database/`)

### Session Backends

| `SESSION_BACKEND` | Service | Notes |
| --- | --- | --- |
| `memory` | `InMemorySessionService` | Default. Fast, no setup, lost on restart. |
| `database` | `DatabaseSessionService` | Persistent. Requires `DATABASE_URL`. |

### SQLite (local, zero-config)

```ini
# .env
DATABASE_URL=sqlite+aiosqlite:///./adk_project.db
SESSION_BACKEND=database
```

### PostgreSQL (production)

```ini
# .env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/adk_db
SESSION_BACKEND=database
```

Create the database first: `createdb adk_db`

### Application Models (`database/models.py`)

Contains `User` and `ConversationLog` ORM models.
Add your own domain models here (commented examples: `Document`, `AgentRunMetric`).

Tables are auto-created on first run via `create_tables()` called in `main.py`.

---

## 8. Storage / Artifacts (`storage/`)

Artifacts are versioned binary files (PDFs, images, CSVs) produced by tools.

| `ARTIFACT_BACKEND` | Service | Notes |
| --- | --- | --- |
| `memory` | `InMemoryArtifactService` | Default. No setup, lost on restart. |
| `gcs` | `GcsArtifactService` | Persisted in Google Cloud Storage. |

### GCS Setup (one-time)

```bash
# 1. Create a bucket — use europe-west1 for best model availability
gcloud storage buckets create gs://YOUR_BUCKET_NAME \
  --project=YOUR_PROJECT \
  --location=europe-west1 \
  --uniform-bucket-level-access

# 2. Grant your service account object access
gcloud storage buckets add-iam-policy-binding gs://YOUR_BUCKET_NAME \
  --member="serviceAccount:YOUR_SA@YOUR_PROJECT.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

```ini
# .env
ARTIFACT_BACKEND=gcs
GCS_BUCKET_NAME=YOUR_BUCKET_NAME
```

---

## 9. RAG — Retrieval-Augmented Generation (`rag/`)

RAG lets agents search your private documents before answering.

### Full Setup (one-time per project)

```bash
# 1. Enable Vertex AI
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT

# 2. Create a RAG corpus (european location recommended)
gcloud ai rag-corpora create \
  --display-name="my-knowledge-base" \
  --project=YOUR_PROJECT \
  --location=europe-west1

# Note the output:
#   name: projects/YOUR_PROJECT/locations/europe-west1/ragCorpora/CORPUS_ID

# 3. Upload documents (PDF, TXT, HTML, DOCX, Google Drive)
#    Option A — from GCS bucket:
gcloud ai rag-files import \
  --rag-corpus=CORPUS_ID \
  --project=YOUR_PROJECT \
  --location=europe-west1 \
  --gcs-uris=gs://YOUR_BUCKET/docs/

#    Option B — from Google Drive folder:
gcloud ai rag-files import \
  --rag-corpus=CORPUS_ID \
  --project=YOUR_PROJECT \
  --location=europe-west1 \
  --google-drive-resource-ids=DRIVE_FOLDER_ID
```

```ini
# .env
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT
GOOGLE_CLOUD_LOCATION=europe-west1
VERTEX_RAG_CORPUS_1=projects/YOUR_PROJECT/locations/europe-west1/ragCorpora/CORPUS_ID
```

### Activating RAG in an Agent

Uncomment in `agents/multitool_agent.py`:
```python
from rag.rag_config import build_rag_tool

tools=[
    ...
    build_rag_tool(),   # ← add this
]
```

### Multiple Corpora

Set `VERTEX_RAG_CORPUS_2`, `VERTEX_RAG_CORPUS_3`… and use:
```python
from rag.rag_config import build_multi_rag_toolset

tools=[*build_multi_rag_toolset(), ...]
```

---

## 10. OAuth Authentication (`auth/`)

### Setup (one-time)

1. Go to **GCP Console → APIs & Services → Credentials**.
2. Click **Create Credentials → OAuth client ID**.
3. Application type: **Web application**.
4. Add authorised redirect URI: `http://localhost:8080/oauth2callback` (dev).
5. Copy Client ID and Client Secret.

```ini
# .env
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
OAUTH_REDIRECT_URI=http://localhost:8080/oauth2callback
```

### Using OAuth with an OpenAPI Toolset

```python
from auth.oauth import build_authenticated_toolset

# Load your OpenAPI spec
with open("openapi_spec.json") as f:
    spec = json.load(f)

toolset = build_authenticated_toolset(
    openapi_spec=spec,
    authorization_url="https://accounts.google.com/o/oauth2/v2/auth",
    token_url="https://oauth2.googleapis.com/token",
    scopes={"https://www.googleapis.com/auth/drive.readonly": "Read Drive files"},
)

agent = LlmAgent(name="drive_agent", tools=[toolset], ...)
```

---

## 11. Docker

### Build and run locally

```bash
docker compose up --build
```

- ADK web UI: http://localhost:8080
- PostgreSQL: localhost:5432

### Environment variables in Docker

Docker Compose reads `.env` automatically via `env_file: .env`.
Override individual variables in the `environment:` section of `docker-compose.yml`.

### Disable PostgreSQL (use SQLite instead)

Comment out the `db:` service and `depends_on:` in `docker-compose.yml`,
and set `SESSION_BACKEND=memory` in `.env`.

---

## 12. Adding Google Search (Grounding)

```bash
# 1. Enable Custom Search API
#    https://console.cloud.google.com/apis/library/customsearch.googleapis.com

# 2. Create a Programmable Search Engine
#    https://programmablesearchengine.google.com/
#    → Copy the Search Engine ID

# 3. Create an API key for the Custom Search API in GCP Console
```

```ini
# .env
GOOGLE_SEARCH_API_KEY=your-api-key
GOOGLE_SEARCH_ENGINE_ID=your-engine-id
```

Uncomment in `agents/normal_agent.py` and `agents/multitool_agent.py`:
```python
from google.adk.tools import google_search
tools=[..., google_search]
```

---

## 13. Using Alternative Models

### Claude (Anthropic) via LiteLLM

```bash
pip install litellm
```

```ini
# .env
ANTHROPIC_API_KEY=your-key
```

```python
from google.adk.models.lite_llm import LiteLlm

agent = LlmAgent(
    model=LiteLlm(model="anthropic/claude-sonnet-4-6"),
    ...
)
```

### OpenAI

```ini
# .env
OPENAI_API_KEY=your-key
```

```python
agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"),
    ...
)
```

---

## 14. Checklist for a New Project

Use this checklist when starting from this template:

- [ ] Run `setup_venv.bat` to create venv and install dependencies.
- [ ] Fill in `.env` — at minimum `GOOGLE_API_KEY` (dev) or Vertex AI vars (prod).
- [ ] Set `GOOGLE_CLOUD_LOCATION=europe-west1` if using Vertex AI.
- [ ] Rename agents in `agents/` to match your domain.
- [ ] Replace the placeholder instructions in each agent.
- [ ] Add your domain tools in `tools/`.
- [ ] Decide: `SESSION_BACKEND=memory` (dev) or `database` (prod).
- [ ] Decide: `ARTIFACT_BACKEND=memory` (dev) or `gcs` (prod).
- [ ] Uncomment `google_search` in agent files if you need web search.
- [ ] Set up Vertex AI RAG corpus if you have private documents.
- [ ] Set up OAuth if you need to call authenticated APIs.
- [ ] Run `adk web` and test through the browser UI.
- [ ] Add security callbacks to sensitive agents.
- [ ] Register `SecurityPlugin` + `LoggingPlugin` in `main.py`'s `Runner`.

---

## 15. Useful ADK CLI Commands

```bash
adk web                    # Start dev UI at http://localhost:8080
adk run agents.orchestrator  # Run agent in terminal (interactive)
adk eval                   # Run evaluation suite
adk deploy cloud_run       # Deploy to Google Cloud Run
```

---

## 16. Reference Links

- ADK documentation: https://adk.dev
- ADK Python source: https://github.com/google/adk-python
- ADK samples: https://github.com/google/adk-samples
- Vertex AI RAG: https://cloud.google.com/vertex-ai/generative-ai/docs/rag-overview
- Google Cloud Console: https://console.cloud.google.com
- Programmable Search Engine: https://programmablesearchengine.google.com
