import streamlit as st
from utils import apply_sunlight_theme  # Import your custom function

# 1. Page Config (Must be first)
st.set_page_config(page_title="Ocean Buzz | Data Lab", page_icon="🌊", layout="centered")

# 2. Apply Theme
apply_sunlight_theme()

# --- 3. LANDING PAGE CONTENT ---
st.title("🌊 Welcome to Ocean Buzz")
st.subheader("Deep-Diving into Data to Protect the Pale Blue Dot.")

st.write("---")

st.markdown("""
I am a Data Scientist and Scuba Diver from a country planted by the sea—a place with <span class="highlight">18 times more water than land</span>. 

My perspective is shaped by the deep, but my tools are built on data. At **Ocean Buzz**, I take the vast, often murky currents of global information and transform them into real signal. We don't just look at the surface; we deep-dive into the numbers to find what’s actually driving the Blue Economy and our planet's future.

### 🤿 The Data Lab
This space houses the interactive simulators and auditing tools featured in the Ocean Buzz newsletter. 

**👈 Use the sidebar to navigate between our current tools:**
*   **Blue Carbon Offset:** Input your corporate footprint, budget, and investment horizon to algorithmically match your mandate with the optimal coastal asset class..
*   **Blue Bond NLP Screener:** Upload corporate sustainability reports to automatically detect greenwashing and verify ocean-centric impact.
*   *(More tools deploying soon...)*
""", unsafe_allow_html=True)

st.write("---")
st.info("Subscribe to the [Ocean Buzz Substack](#) to get the weekly data audits and methodology breakdowns behind these tools.")