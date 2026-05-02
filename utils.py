# utils.py
import streamlit as st

def apply_sunlight_theme():
    """Injects the Ocean Buzz CSS theme into any Streamlit page."""
    st.markdown("""
        <style>
        /* The Sunlight Zone Gradient Background */
        .stApp {
            background: linear-gradient(135deg, #F0F8FF 0%, #FFFFFF 100%);
            color: #1B263B;
        }
        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E0F2F1;
        }
        [data-testid="stSidebar"] .stMarkdown p, [data-testid="stSidebar"] label {
            color: #1B263B !important;
            font-weight: 600 !important;
        }
        /* Metric Card Styling */
        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 2px solid #E0F2F1;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0, 105, 92, 0.08);
        }
        [data-testid="stMetricLabel"] p {
            color: #1B263B !important;
            font-size: 0.9rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
        }
        [data-testid="stMetricValue"] div {
            color: #00796B !important; 
            font-size: 2rem !important;
            font-weight: 800 !important;
        }
        /* Typography */
        h1, h2, h3 {
            color: #005B96 !important;
            font-family: 'Helvetica Neue', sans-serif;
        }
        .stMarkdown p {
            font-size: 1.1rem;
            line-height: 1.6;
        }
        .highlight {
            color: #00796B;
            font-weight: 700;
        }
        </style>
        """, unsafe_allow_html=True)