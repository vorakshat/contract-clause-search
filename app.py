"""Web demo for the clause search system.

    streamlit run app.py
"""
from __future__ import annotations

import html
from pathlib import Path

import streamlit as st

from clausesearch.chunking import doc_title
from clausesearch.config import load_config
from clausesearch.data import load_queries
from clausesearch.pipeline import Pipeline

st.set_page_config(page_title="Contract clause search", layout="wide")


@st.cache_resource(show_spinner="Loading contracts and building the index...")
def get_pipeline(config_path: str) -> Pipeline:
    return Pipeline.from_config(load_config(config_path))


@st.cache_data
def example_questions(config_path: str) -> list[str]:
    try:
        queries = load_queries(load_config(config_path), split="train")
    except FileNotFoundError:
        return []
    return [q.text for q in queries]


configs = sorted(str(p) for p in Path("configs").glob("*.yaml") if p.name != "objective.yaml")
default = "configs/final.yaml" if "configs/final.yaml" in configs else "configs/baseline.yaml"

with st.sidebar:
    st.header("Settings")
    config_path = st.selectbox("Pipeline configuration", configs, index=configs.index(default))
    top_k = st.slider("Passages to show", 1, 10, 5)
    context_chars = st.slider("Context around each passage (characters)", 0, 1000, 300, step=100)
    try:
        pipeline = get_pipeline(config_path)
    except FileNotFoundError as err:
        st.error(f"{err}")
        st.stop()
    with st.expander(f"Indexed contracts ({len(pipeline.corpus)})"):
        for doc_id in pipeline.corpus:
            st.caption(doc_title(doc_id))

st.title("Contract clause search")
st.write("Ask a question about one of the indexed contracts. You get the best-matching passages, each with "
         "its file and character positions, or a 'no answer' message when nothing clears the confidence threshold.")

examples = example_questions(config_path)
picked = st.selectbox("Example questions from the train split (optional)", [""] + examples)
question = st.text_area("Question", value=picked, height=90,
                        placeholder="Consider the <agreement> between <party A> and <party B>; <question>")

if st.button("Search", type="primary") and question.strip():
    result = pipeline.search(question.strip(), top_k=top_k)
    if result.routed:
        doc, coverage = result.routed[0]
        st.caption(f"Routed to: {doc_title(doc)} (coverage {coverage:.2f})")
    if result.abstained:
        st.warning(f"No answer. {result.message}")
    else:
        for rank, p in enumerate(result.passages, 1):
            text = pipeline.corpus[p.doc_id]
            before = text[max(0, p.start - context_chars):p.start]
            after = text[p.end:p.end + context_chars]
            st.markdown(f"**{rank}. {html.escape(doc_title(p.doc_id))}** · characters {p.start}–{p.end} · "
                        f"score {p.score:.3f}")
            st.markdown(
                "<div style='white-space: pre-wrap; font-size: 0.9rem; border: 1px solid #ddd; "
                "border-radius: 6px; padding: 0.75rem; margin-bottom: 1rem;'>"
                f"<span style='opacity: 0.55'>{html.escape(before)}</span>"
                f"<mark>{html.escape(p.text)}</mark>"
                f"<span style='opacity: 0.55'>{html.escape(after)}</span></div>",
                unsafe_allow_html=True)
            st.caption(f"File: {p.doc_id}")
    with st.expander("Details"):
        st.json({"reason": result.reason, "gate_score": result.gate_score, "timings_ms": result.timings_ms,
                 "retrieval_text": result.processed.lexical if result.processed else None})
