"""RAG chat: retrieve relevant guidelines, then answer grounded in them.

The answer is generated ONLY from retrieved knowledge-base entries and must cite
them. When nothing relevant is retrieved, the model is instructed to say so and
defer to a professional rather than hallucinate — the core reliability property.
"""

from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from chatbot.retriever import KBRetriever
from chatbot.guardrail import review

CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4.1-mini")
GUARDRAIL_ENABLED = os.getenv("GUARDRAIL_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}

SAFE_FALLBACK = (
    "I can't give a reliable, source-backed answer to that. Please check with a "
    "pharmacist or physician for guidance."
)

SYSTEM_PROMPT = """You are a careful preventive-health assistant supporting pharmacy staff.

Rules:
- Answer ONLY using the numbered guidelines below. Do not use outside knowledge.
- If the guidelines do not contain the answer, say clearly that you don't have a
  referenced source for it and suggest consulting the appropriate health
  professional. Never invent facts or figures.
- State the eligible population or scope EXACTLY as the guideline defines it. Do not
  reshape it to match the user's wording. For example, if the user asks about "adults"
  but the guideline covers "people aged 6 months and older", say the guideline applies
  to everyone aged 6 months and older (which includes adults) — never write a
  contradiction such as "adults aged 6 months and older".
- Cite the guideline id and source organisation you relied on, inline, e.g. [PH001 - CDC].
- Be concise, factual and neutral. Never diagnose, never give personalised medical
  or medication advice, never rule out a serious condition, never discourage
  professional or emergency care.

Guidelines:
{context}
"""


def _client() -> OpenAI:
    return OpenAI(base_url=os.getenv("OPENAI_BASE_URL") or None, api_key=os.getenv("OPENAI_API_KEY"))


def _format_context(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return "(no relevant guidelines were found for this question)"
    return "\n".join(
        f"[{e.get('id')}] {e.get('topic')}: {e.get('guideline')} "
        f"(Population: {e.get('population')}; Source: {e.get('source_org')}, "
        f"{e.get('source_url')}, {e.get('source_date')})"
        for e in entries
    )


def answer_question(
    retriever: KBRetriever,
    question: str,
    history: list[dict[str, str]] | None = None,
    k: int = 3,
) -> dict[str, Any]:
    """Return {answer, sources, safety} for a question, grounded in the retrieved KB.

    The answer is generated from the retrieved guidelines, then (if enabled) passed
    through the safety guardrail. If the guardrail flags a hallucination or a
    medical-safety failure, the answer is replaced with a safe fallback.
    """
    hits = retriever.search(question, k=k)
    context = _format_context(hits)

    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT.format(context=context)}]
    for turn in history or []:
        if turn.get("role") in ("user", "assistant") and turn.get("content"):
            messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": question})

    completion = _client().chat.completions.create(model=CHAT_MODEL, messages=messages, temperature=0)
    answer = (completion.choices[0].message.content or "").strip()

    safety: dict[str, Any] = {"checked": False, "blocked": False}
    if GUARDRAIL_ENABLED:
        try:
            verdict = review(context, question, answer)
            blocked = verdict.groundedness == "HALLUCINATION" or verdict.medical_safety == "FAIL"
            safety = {
                "checked": True,
                "blocked": blocked,
                "groundedness": verdict.groundedness,
                "medical_safety": verdict.medical_safety,
                "violations": verdict.violations,
            }
            if blocked:
                answer = SAFE_FALLBACK
        except Exception:
            # Never fail the request because the guardrail errored.
            safety = {"checked": False, "blocked": False}

    sources = [] if safety.get("blocked") else [
        {
            "id": e.get("id"),
            "topic": e.get("topic"),
            "source_org": e.get("source_org"),
            "source_url": e.get("source_url"),
            "score": e.get("score"),
        }
        for e in hits
    ]
    return {"answer": answer, "sources": sources, "safety": safety}
