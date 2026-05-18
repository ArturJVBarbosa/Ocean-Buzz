import streamlit as st
from utils import apply_sunlight_theme  # Import Ocean Buzz theme

# URLs definition
SUBSTACK_URL = "https://oceanbuzz.substack.com"
GITHUB_URL = "https://github.com/ArturJVBarbosa/Ocean-Buzz"
INSTAGRAM_URL = "https://instagram.com/oceanbuzz_"

# Page Config
st.set_page_config(page_title="Ocean Buzz | Data Lab", page_icon="🌊", layout="centered")

# Apply Theme
apply_sunlight_theme()

# Landing Page
st.title("🌊 Welcome to Ocean Buzz")
st.subheader("Deep-Diving into Data to Protect the Pale Blue Dot.")

st.write("---")

st.markdown("""
At **Ocean Buzz**, I take the vast, often murky currents of global information and transform them into real signal. Don't just look at the surface; deep-dive into the numbers to find what’s actually driving the Blue Economy and our planet's future.

### 🤿 The Data Lab
This space houses the interactive simulators and auditing tools featured in the Ocean Buzz newsletter. 

**👈 Use the sidebar to navigate between our current tools:**
*   **Blue Carbon Offset (BCO) Budget Calculator:** Input your corporate Carbon Offset Target and time window to have an estimation of needed budget to meet your needs.
*   **Blue Bond NLP Screener:** Upload corporate sustainability reports to automatically detect greenwashing and verify ocean-centric impact.
*   *(More tools deploying soon...)*
""", unsafe_allow_html=True)

st.markdown("---")

# Wrap the entire ecosystem section in a bordered container
with st.container(border=True):
    st.subheader("🌐 Explore the Ecosystem")
    st.write("Choose your depth level for how you want to consume this data:")

    st.write("")  # Adds a tiny bit of breathing room before the buttons

    # Use a consistent column ratio
    col_ratio = [3.5, 1]

    # --- Row 1: Substack ---
    row1_col1, row1_col2 = st.columns(col_ratio)
    with row1_col1:
        st.markdown("⚓ **Deep Dives:** For the comprehensive data audits and methodology breakdowns.")
    with row1_col2:
        st.link_button("📢 Substack", SUBSTACK_URL, type="primary", use_container_width=True)

    # --- Row 2: GitHub ---
    row2_col1, row2_col2 = st.columns(col_ratio)
    with row2_col1:
        st.markdown("💻 **The Code:** For the open-source repository, Python scripts, and raw pipelines.")
    with row2_col2:
        st.link_button("⚙️ GitHub", GITHUB_URL, use_container_width=True)

    # --- Row 3: Instagram ---
    row3_col1, row3_col2 = st.columns(col_ratio)
    with row3_col1:
        st.markdown("📸 **The Visuals:** For the TLDR people and basic concepts.")
    with row3_col2:
        st.link_button("📱 Instagram", INSTAGRAM_URL, use_container_width=True)