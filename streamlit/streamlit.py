import json
import os
import requests
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Configure page metadata and layout before rendering UI elements.
st.set_page_config(page_title="Evaluator", layout="wide")
st.title("🧪 Evaluation Dashboard")
st.caption("Upload JSON → Send to API → View & Download Results")

# API endpoint can be overridden from UI for local/remote testing.
api_url = st.text_input(
    "Evaluate endpoint",
    value=os.environ.get("API_URL")
)

# Accept a JSON dataset file from user.
uploaded_file = st.file_uploader("Upload JSON file", type=["json"])

# Stop rendering dependent sections until a file is provided.
if not uploaded_file:
    st.stop()

# Parse uploaded JSON payload.
try:
    dataset = json.loads(uploaded_file.read().decode("utf-8"))
except Exception as e:
    st.error(f"Invalid JSON: {e}")
    st.stop()

st.success(f"Loaded {len(dataset)} items")

# Trigger evaluation only when the user clicks.
if st.button("▶️ Evaluate", type="primary"):
    # Transform dataset rows into API request format expected by backend.
    payload = {
        "turns": [
            [
                {"role": "user", "content": item["user"]},
                {"role": "assistant", "content": item["agent"]},
            ]
            for item in dataset
        ]
    }

    # Send one batch request for the whole uploaded dataset.
    try:
        response = requests.post(api_url, json=payload, timeout=60)
        response.raise_for_status()
        results = response.json()  # list of EvaluateResponse
    except Exception as e:
        st.error(f"API error: {e}")
        st.stop()

    # Normalize API response into tabular rows for display/export.
    rows = []
    try:
        for i, res in enumerate(results["results"]):
            rows.append({
                "index": i,
                "user_message":res["user_message"],
                "agent": res["agent"],
                "empathy_score": res["empathy_score"],
                "groundedness": res["groundedness"],
                "medical_safety": res["medical_safety"],
                "violations": ", ".join(res["violations"]),
                "kb_ids_used": ", ".join(res["kb_ids_used"]),
            })
    except (TypeError, KeyError) as e:
        st.error(f"Unexpected API response format: {e}")
        st.stop()

    df = pd.DataFrame(rows)

    # Highlight hallucination rows in red to aid triage.
    def highlight(row):
        if row["groundedness"] == "HALLUCINATION":
            return ["background-color: #ff0000"] * len(row)
        return [""] * len(row)

    st.subheader("📊 Results")
    st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True)

    # Offer exports in both machine-friendly and analyst-friendly formats.
    st.subheader("⬇️ Download")
    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "Download JSON",
            data=json.dumps(results, indent=2),
            file_name="results.json",
            mime="application/json",
        )

    with col2:
        st.download_button(
            "Download CSV",
            data=df.to_csv(index=False),
            file_name="results.csv",
            mime="text/csv",
        )