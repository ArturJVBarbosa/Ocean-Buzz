import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sys
import os

# Add root folder to path so pages can see utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import apply_sunlight_theme

# 1. Page Config
st.set_page_config(page_title="Blue Carbon ROI", layout="wide")

# 2. Apply Theme
apply_sunlight_theme()

# --- 2. SIDEBAR: PROJECT & FINANCIAL INPUTS ---
st.sidebar.header("🌊 Project Controls")
budget = st.sidebar.number_input("Investment Budget ($)", min_value=10000, value=1000000, step=50000)
years = st.sidebar.slider("Project Horizon (Years)", 10, 50, 30)
region = st.sidebar.selectbox("Region", ["Caribbean (High Risk)", "SE Asia (Medium Risk)", "West Africa (Low Risk)"])

st.sidebar.subheader("💰 Financial Assumptions")
carbon_price = st.sidebar.slider("Carbon Credit Price ($/ton)", 20, 200, 65)
discount_rate = st.sidebar.slider("Discount Rate (%)", 1, 12, 7) / 100

# Risk mapping
risk_data = {
    "Caribbean (High Risk)": {"p": 0.12, "damage": (0.3, 0.7)},
    "SE Asia (Medium Risk)": {"p": 0.07, "damage": (0.1, 0.4)},
    "West Africa (Low Risk)": {"p": 0.03, "damage": (0.05, 0.2)}
}


# --- 3. THE ENGINE: STOCHASTIC GROWTH & ROI ---
def run_simulation(budget, years, p_storm, storm_bounds):
    cost_per_ha = 9200
    max_capacity = 24  # Tons CO2/ha/yr
    ha_restored = budget / cost_per_ha
    n_sims = 500

    all_paths = []
    for _ in range(n_sims):
        current_stock = 0
        path = []
        for t in range(1, years + 1):
            yearly_seq = max_capacity / (1 + np.exp(-0.5 * (t - 8)))
            current_stock += yearly_seq * ha_restored

            if np.random.random() < p_storm:
                damage = np.random.uniform(*storm_bounds)
                current_stock *= (1 - damage)
            path.append(current_stock)
        all_paths.append(path)
    return np.array(all_paths)


# Execute Math
p_storm = risk_data[region]["p"]
storm_bounds = risk_data[region]["damage"]
sim_results = run_simulation(budget, years, p_storm, storm_bounds)
mean_path = np.mean(sim_results, axis=0)

# Financial Metrics
total_co2 = mean_path[-1]
gross_rev = total_co2 * carbon_price
net_profit = gross_rev - budget
roi_perc = (net_profit / budget) * 100

# --- 4. THE UI LAYOUT ---
st.title("🌊 Blue Carbon ROI & Risk Simulator")
st.markdown(f"**Model Context:** High-integrity 2026 carbon credit benchmarks applied to {region}.")

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Total CO2 (Tons)", f"{int(total_co2):,}")
m2.metric("Gross Revenue", f"${int(gross_rev):,}")
m3.metric("Net Profit", f"${int(net_profit):,}")
m4.metric("Project ROI", f"{int(roi_perc)}%")

# Tabs for different views
tab1, tab2 = st.tabs(["📊 Carbon Sequestration", "📈 Cash Flow & Break-even"])

with tab1:
    fig_carbon = go.Figure()
    fig_carbon.add_trace(go.Scatter(x=list(range(1, years + 1)), y=mean_path,
                                    line=dict(color='#00796B', width=4), name="Mean Sequestration"))
    fig_carbon.update_layout(title="Projected Carbon Storage (Risk-Adjusted)", template="plotly_white")
    st.plotly_chart(fig_carbon, use_container_width=True)

with tab2:
    # NPV / Cash Flow Logic
    cash_flow = (mean_path * carbon_price) - budget
    fig_cash = go.Figure()
    fig_cash.add_trace(go.Scatter(x=list(range(1, years + 1)), y=cash_flow,
                                  line=dict(color='#005B96', width=4), name="Net Cash Flow"))
    fig_cash.add_trace(go.Scatter(x=[1, years], y=[0, 0], line=dict(color='red', dash='dash'), name="Break-even"))
    fig_cash.update_layout(title="Cumulative Investment Return (USD)", template="plotly_white")
    st.plotly_chart(fig_cash, use_container_width=True)

st.success(
    f"**Insight:** At ${carbon_price}/ton, this nature-based asset generates ${net_profit:,.0f} in net profit, accounting for localized storm risks.")