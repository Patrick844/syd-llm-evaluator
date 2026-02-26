import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas.fast_api_templates import *
from dotenv import load_dotenv
from utils import get_kb
from ai_services.ai_service import run_llm
import os

# Load environment variables from .env at startup.
load_dotenv()

# Path to the knowledge base JSON file, configured via environment variable.
KB_PATH = os.environ.get("KB_PATH")



app = FastAPI()

# Allow cross-origin requests from frontend clients.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load KB once at process startup so requests don't re-read disk.
try:
    KNOWLEDGE_BASE = get_kb(KB_PATH)
except Exception as e:
    KNOWLEDGE_BASE = []
    print(f"[WARN] KB not loaded: {e}")


@app.get("/health")
def health():
    # Simple readiness endpoint for monitoring and quick smoke checks.
    return {"status": "ok", "kb_items": len(KNOWLEDGE_BASE)}


@app.post("/evaluate")
def evaluate(req: EvaluateRequest):
    # Fail fast if startup KB load failed.
    if not KNOWLEDGE_BASE:
        raise HTTPException(status_code=500, detail="Knowledge base is not loaded.")

    final_result = []

    # Evaluate each submitted turn and normalize output for the frontend table.
    for idx, turn in enumerate(req.turns):
        try:
            response = dict(run_llm(KNOWLEDGE_BASE, str(turn)))
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"LLM evaluation failed for turn index {idx}: {e}",
            ) from e

        try:
            # Echo selected source fields for easy comparison in the dashboard output.
            response["user_message"] = turn[0]["content"]
            response["agent"] = turn[1]["content"]
        except (TypeError, IndexError, KeyError) as e:
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Invalid turn format at index {idx}. "
                    "Expected a list with user and assistant message objects."
                ),
            ) from e

        final_result.append(response)

    # Return list under a stable envelope key for UI compatibility.
    return {"results": final_result}

