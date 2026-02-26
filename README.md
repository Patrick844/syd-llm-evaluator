# SYD LLM Evaluator

A lightweight evaluation pipeline for preventive-health assistant responses.

This project includes:
- A **FastAPI backend** that evaluates assistant outputs with an LLM
- A **Streamlit dashboard** to upload conversations, trigger evaluation, and download results
- A **knowledge base** used as grounding context for evaluation
- Docker support to run both services together

## Project Status

This repository is currently a **POC (Proof of Concept)** focused on validating evaluation logic and end-to-end workflow.

---

## What This App Does

Given pairs of:
- `user` message
- `agent` response

the evaluator returns structured scores and flags:
- `empathy_score` (`0`, `1`, `2`)
- `groundedness` (`PASS` or `HALLUCINATION`)
- `medical_safety` (`PASS` or `FAIL`)
- `violations` (policy labels)
- `kb_ids_used` (knowledge base IDs used for grounding)

---

## Project Structure

```text
syds/
├── app.py                         # FastAPI app and endpoints
├── utils.py                       # Config + dataset/KB loading helpers
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Single image used by both services
├── docker-compose.yml             # Runs FastAPI + Streamlit together
├── ai_services/
│   └── ai_service.py              # LLM evaluation orchestration
├── config/
│   ├── config.yaml                # Prompt + model config
│   └── llm_config.py              # OpenAI client wrapper
├── schemas/
│   ├── fast_api_templates.py      # Request/response API schemas
│   └── response_templates.py      # Structured LLM output schema
├── data/
│   ├── conversations.json         # Example conversation dataset
│   └── knowledge_base.json        # Grounding KB entries
└── streamlit/
    └── streamlit.py               # Dashboard UI
```

---

## How It Works (Flow)

1. `streamlit/streamlit.py` loads a JSON dataset from the UI.
2. Streamlit sends payloads to `POST /evaluate`.
3. `app.py` calls `run_llm(...)` for each item.
4. `ai_services/ai_service.py`:
   - reads `llm_evaluator` config from `config/config.yaml`
   - injects KB content into the system prompt
   - sends the request through `LLM_OPENAI`
5. `config/llm_config.py` uses OpenAI structured output (`responses.parse`) with the `Evaluation` schema.
6. FastAPI returns aggregated results; Streamlit renders and allows JSON/CSV download.

---

## Prerequisites

- Python `3.11+` recommended
- An OpenAI-compatible API key in environment:
  - `OPENAI_API_KEY`
- Use a `.env.example` file as a template for required environment variables, then copy it to `.env` for local or Docker runs.

Optional:
- `KB_PATH` (path to knowledge base JSON file)
- `API_URL` (used by Streamlit to find the backend)

---

## Run Locally (without Docker)

### 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Set environment variables

```bash
export OPENAI_API_KEY="your_key_here"
export KB_PATH="/absolute/path/to/syd/data/knowledge_base.json"
```

If `KB_PATH` is not set correctly, `/health` may show `kb_items: 0` and `/evaluate` will return a 500.

### 3) Start FastAPI

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

### 4) Start Streamlit (new terminal)

```bash
export API_URL="http://127.0.0.1:8000/evaluate"
streamlit run streamlit/streamlit.py
```

Open: `http://localhost:8501`

---

## Run with Docker Compose

### 1) Set required env var

Create a `.env` file in project root (recommended):

```env
OPENAI_API_KEY=your_key_here
KB_PATH=/app/data/knowledge_base.json
API_URL=http://fastapi:8000/evaluate
```

### 2) Build and run

```bash
docker compose up --build
```

### 3) Access services

- FastAPI health: `http://localhost:8000/health`
- Streamlit UI: `http://localhost:8501`

Stop:

```bash
docker compose down
```

---

## API Reference

### `GET /health`

Returns service status and number of KB items loaded.

Example response:

```json
{
  "status": "ok",
  "kb_items": 42
}
```

### `POST /evaluate`

Evaluates a batch and returns `results`.

Current backend code reads `req.turns` and appends one evaluated row per turn.

Expected response envelope:

```json
{
  "results": [
    {
      "empathy_score": 2,
      "groundedness": "PASS",
      "medical_safety": "PASS",
      "violations": [],
      "kb_ids_used": ["PH001"],
      "user_message": "...",
      "agent": "..."
    }
  ]
}
```

---

## Dataset Format for Streamlit Upload

Upload a JSON array where each item has:

```json
[
  {
    "user": "How long should I sleep to stay healthy?",
    "agent": "Adults aged 18-60 should aim for 7 or more hours of sleep each night."
  }
]
```

You can use `data/conversations.json` as a sample file.

---

## Data Files and Required Structure

The `data/` folder currently contains:
- `data/conversations.json` (input examples for Streamlit upload)
- `data/knowledge_base.json` (grounding source used in evaluation prompt)

### `data/conversations.json`

This should be a JSON array of objects with this shape:

```json
[
  {
    "user": "string",
    "agent": "string"
  }
]
```

Rules:
- Must be valid JSON (not JSONL)
- Top-level must be a list
- Each item should include both `user` and `agent`
- Values should be plain strings

### `data/knowledge_base.json`

This should be a JSON array where each object represents one guideline entry.

Recommended structure per item:

```json
{
  "id": "PH001",
  "topic": "Annual Influenza Vaccination",
  "guideline": "People aged 6 months and older should receive an annual influenza vaccine.",
  "population": "Age 6 months+",
  "source_org": "CDC",
  "source_url": "https://example.org",
  "source_date": "2025",
  "notes": "Optional supporting notes"
}
```


### Data quality tips

- Keep language consistent across KB entries
- Prefer atomic entries (one guideline per object)
- Version your KB when making major updates
- Validate JSON format before upload/use

---

## Configuration

### `config/config.yaml`

Contains `llm_evaluator`:
- `model_name`
- `response_type` (currently `structured_output`)
- `system_prompt` template (includes `{kb}` placeholder)

### `config/llm_config.py`

Wraps OpenAI client creation and invocation logic.

Environment variables used:
- `OPENAI_API_KEY` (required)
- Base URL is currently read from an empty env key and defaults to `None` unless code is adjusted.


## Useful Commands

Run backend:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

Run dashboard:

```bash
streamlit run streamlit/streamlit.py
```

Docker (build + run):

```bash
docker compose up --build
```

---

## POC and Improvement Roadmap

This project is a **POC (Proof of Concept)** and is intentionally simple for fast iteration.

To improve **accuracy**, **efficiency**, and **production readiness**, the next steps are:
- Implement a **RAG** pipeline (retrieval + context selection) to ground evaluations more reliably.
- Add a **database** to store evaluation requests/results for logging, analytics, and auditability.
- Deploy to **cloud infrastructure** for scalable API/UI hosting.
- Use **cloud storage** for datasets, knowledge-base versions, and exported results.
- Add **monitoring and logging** (metrics, structured logs, tracing, alerts) for observability and operations.
