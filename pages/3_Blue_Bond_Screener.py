import streamlit as st
import pdfplumber
import re
from collections import Counter
import sys
import os

# Add root folder to path so pages can see utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import apply_sunlight_theme

# 1. Page Config
st.set_page_config(page_title="Blue Bond Screener", layout="wide")

# 2. Apply Theme
apply_sunlight_theme()


# --- THE UPGRADED NLP ENGINE ---
def extract_text(pdf_file):
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def analyze_bond(text):
    clean_text = re.sub(r'[^a-zA-Z\s]', '', text.lower())
    words = clean_text.split()
    word_counts = Counter(words)

    # 1. SPLIT AND UPGRADE THE DICTIONARIES
    core_blue = [
        "aquaculture", "marine", "ocean", "offshore",
        "water", "ballast", "biodiversity", "mangroves", "coastal"
    ]

    general_green = [
        "sdg", "baseline", "metrics", "tons", "emissions",
        "audited", "taxonomy", "kpi", "energy", "wind", "solar"
    ]

    vague_terms = [
        "ecofriendly", "synergies", "mindset", "initiatives",
        "vision", "awareness", "journey", "aspirations",
        "momentum", "exploration", "greener"
    ]

    # 2. CALCULATE RAW HITS
    blue_raw = sum(word_counts[term] for term in core_blue)
    green_raw = sum(word_counts[term] for term in general_green)
    vague_raw = sum(word_counts[term] for term in vague_terms)

    # 3. APPLY THE MATHEMATICAL WEIGHTS
    blue_weight = 3
    green_weight = 1
    vague_weight = 2  # Penalize fluff more heavily

    weighted_blue = blue_raw * blue_weight
    weighted_green = green_raw * green_weight
    weighted_vague = vague_raw * vague_weight

    total_weight = weighted_blue + weighted_green + weighted_vague

    # Calculate the final score based on the weighted ratio
    score = (weighted_blue / total_weight) * 100 if total_weight > 0 else 0

    return score, blue_raw, green_raw, vague_raw, len(words)


st.title("🌊 Blue Bond Authenticity Screener v2.0")
st.markdown("Advanced NLP model with weighted scoring for ocean-specific metrics.")

# 1. NEW: Add a text box for the user to type the company name
company_name = st.text_input("Enter Company Name (Optional):", placeholder="e.g., H&M Group")

uploaded_file = st.file_uploader("Upload PDF Document", type="pdf")

if uploaded_file is not None:
    with st.spinner('Running weighted NLP analysis...'):
        raw_text = extract_text(uploaded_file)
        score, blue, green, vague, total_words = analyze_bond(raw_text)

        st.divider()

        # 2. NEW: Dynamic Report Title
        # If you typed a name, it uses that. If not, it defaults to the file name!
        if company_name:
            st.header(f"📊 Analysis Report: {company_name}")
        else:
            st.header(f"📊 Analysis Report: {uploaded_file.name}")

        st.subheader("Metrics Breakdown")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Words", f"{total_words:,}")
        col2.metric("Core Blue (x3)", blue)
        col3.metric("Gen Green (x1)", green)
        col4.metric("Vague Flags (x2)", vague)

        st.divider()

        st.subheader(f"Weighted Authenticity Score: {score:.1f}%")
        st.progress(int(score) / 100)

        # --- V3.0 VERDICT LOGIC WITH SAFETY NET ---
        if score >= 75:
            st.success("VERDICT: Authentic Blue Bond (Ocean-Centric & Measurable)")
        elif score >= 40:
            st.warning("VERDICT: Authentic Green Bond (Moderate Blue Focus)")
        else:
            # THE SAFETY NET: Catching Algorithmic Bias
            # If they scored poorly on "Blue", but have massive "Green" hits
            # and very few "Vague" hits, they are NOT greenwashers.
            if green > 30 and green > (vague * 3):
                st.info("VERDICT: Authentic Green Bond (Data-Driven, but Zero Ocean Focus)")
            else:
                st.error("VERDICT: High Risk of Greenwashing (Heavily Vague)")