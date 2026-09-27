"""
app.py

Sunbeams AI Multi-Level Worksheet Generator -- Streamlit app.

Flow:
  1. Teacher picks Grade band (PA/PB/PC)
  2. Teacher picks Term (populated dynamically from what's in the dataset)
  3. Teacher picks Subject (populated dynamically from what's in the dataset)
  4. Teacher types a Topic
  5. Teacher picks a Difficulty level (1-4, matching the syllabus scaffold pattern)
  6. Click "Generate Worksheet" -> calls AI, grounded on extracted syllabus text
  7. Worksheet + answer key shown on screen, downloadable as PDF

Run locally / in Colab:
    streamlit run app.py

Set your free Groq API key (https://console.groq.com/keys) as an
environment variable before running:
    export GROQ_API_KEY=gsk_...
(In Colab, use userdata.get() -- see colab_setup notes in the README.)
"""

import os
import streamlit as st

from utils.pdf_indexer import get_index
from utils.pdf_extractor import extract_summary
from utils.ai_generator import generate_worksheet
from utils.pdf_exporter import export_worksheet_pdf

DATASET_ROOT = os.environ.get("DATASET_ROOT", "dataset-sunbeams")

st.set_page_config(page_title="Sunbeams Worksheet Generator", page_icon="📝", layout="centered")

st.title("📝 Sunbeams AI Worksheet Generator")
st.caption("Instant, leveled, bilingual (Urdu/English) practice worksheets for multi-grade classrooms.")

# ---------------------------------------------------------------------
# Load dataset index (cached so we don't re-scan the folder every run)
# ---------------------------------------------------------------------
@st.cache_data(show_spinner="Reading syllabus dataset...")
def load_index():
    return get_index(DATASET_ROOT)

try:
    index = load_index()
except FileNotFoundError:
    st.error(
        f"Could not find dataset folder at '{DATASET_ROOT}'. "
        "Set the DATASET_ROOT environment variable to point at your "
        "dataset-sunbeams folder, or place it next to app.py."
    )
    st.stop()

if not index:
    st.warning("Dataset folder was found but no grade folders (PA/PB/PC) were detected.")
    st.stop()

# ---------------------------------------------------------------------
# Sidebar: selection controls, populated dynamically from the index
# ---------------------------------------------------------------------
st.sidebar.header("Worksheet Settings")

grade = st.sidebar.selectbox("Grade band", sorted(index.keys()))

terms_available = sorted(index.get(grade, {}).keys())
if not terms_available:
    st.sidebar.error(f"No terms found for grade {grade}.")
    st.stop()
term = st.sidebar.selectbox("Term", terms_available)

subjects_available = sorted(index.get(grade, {}).get(term, {}).keys())
if not subjects_available:
    st.sidebar.error(f"No subjects found for {grade} / {term}.")
    st.stop()
subject = st.sidebar.selectbox("Subject", subjects_available)

topic = st.sidebar.text_input("Topic", placeholder="e.g. کھانا, Addition up to 20, Parts of a plant")

difficulty = st.sidebar.slider(
    "Difficulty level",
    min_value=1,
    max_value=4,
    value=2,
    help=(
        "1 = smallest building block (e.g. single letter/sound), "
        "4 = full, real-world complexity (matches the syllabus scaffold pattern)."
    ),
)

generate_clicked = st.sidebar.button("🚀 Generate Worksheet", type="primary", use_container_width=True)

# ---------------------------------------------------------------------
# Main panel
# ---------------------------------------------------------------------
if "worksheet" not in st.session_state:
    st.session_state.worksheet = None

if generate_clicked:
    if not topic.strip():
        st.warning("Please enter a topic before generating.")
    else:
        pdf_path = index[grade][term][subject]
        with st.spinner("Reading syllabus PDF for context..."):
            syllabus_context = extract_summary(pdf_path)

        with st.spinner("Generating worksheet with AI..."):
            try:
                worksheet = generate_worksheet(
                    grade=grade,
                    term=term,
                    subject=subject,
                    topic=topic,
                    difficulty=difficulty,
                    syllabus_context=syllabus_context,
                )
                st.session_state.worksheet = worksheet
            except Exception as e:
                st.error(f"Worksheet generation failed: {e}")
                st.session_state.worksheet = None

worksheet = st.session_state.worksheet

if worksheet:
    st.subheader(worksheet.get("worksheet_title", "Worksheet"))

    if worksheet.get("instructions_english"):
        st.markdown(f"**Instructions:** {worksheet['instructions_english']}")
    if worksheet.get("instructions_urdu"):
        st.markdown(
            f'<div dir="rtl" style="font-size:1.1em;">{worksheet["instructions_urdu"]}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### Questions")
    for i, q in enumerate(worksheet.get("questions", []), start=1):
        is_urdu = any("\u0600" <= ch <= "\u06FF" for ch in q)
        if is_urdu:
            st.markdown(f'<div dir="rtl">{i}. {q}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f"{i}. {q}")

    with st.expander("🔑 Answer Key (teacher only)"):
        for i, a in enumerate(worksheet.get("answer_key", []), start=1):
            st.markdown(f"{i}. {a}")

    st.markdown("---")
    if st.button("📄 Export as PDF"):
        with st.spinner("Building PDF..."):
            out_path = export_worksheet_pdf(worksheet, output_path="generated_worksheet.pdf")
        with open(out_path, "rb") as f:
            st.download_button(
                "⬇️ Download Worksheet PDF",
                data=f.read(),
                file_name="worksheet.pdf",
                mime="application/pdf",
            )
else:
    st.info("Fill in the settings on the left and click **Generate Worksheet** to begin.")
