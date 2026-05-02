import streamlit as st
import numpy as np
import plotly.graph_objects as go
import sys
import os

# Add root folder to path so pages can see utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import apply_sunlight_theme

# 1. Page Config
st.set_page_config(page_title="Blue Carbon Offset", layout="wide")

# 2. Apply Theme
apply_sunlight_theme()



# --- 2. SIDEBAR: CORPORATE INPUTS ---
st.sidebar.header("🎯 Corporate Targets")
target_co2 = st.sidebar.number_input("Target CO2 Offset (Tons)", min_value=1000, value=50000, step=5000)
years = st.sidebar.slider("Timeline to Target (Years)", 10, 50, 30)
region = st.sidebar.selectbox("Project Region",
                              ["Caribbean (High Risk)", "SE Asia (Medium Risk)", "West Africa (Low Risk)"])

st.sidebar.subheader("💰 Financial Assumptions")
carbon_price = st.sidebar.slider("Estimated Credit Price ($/ton)", 20, 200, 65)

# Risk mapping
risk_data = {
    "Caribbean (High Risk)": {"p": 0.12, "damage": (0.3, 0.7)},
    "SE Asia (Medium Risk)": {"p": 0.07, "damage": (0.1, 0.4)},
    "West Africa (Low Risk)": {"p": 0.03, "damage": (0.05, 0.2)}
}


# --- 3. THE REVERSE ENGINE ---
def calculate_required_budget(target_tons, years, p_storm, storm_bounds):
    cost_per_ha = 9200
    max_capacity = 24  # Tons CO2/ha/yr
    n_sims = 500

    # First, simulate the yield of exactly ONE hectare to find the expected baseline
    per_ha_paths = []
    for _ in range(n_sims):
        current_stock = 0
        path = []
        for t in range(1, years + 1):
            yearly_seq = max_capacity / (1 + np.exp(-0.5 * (t - 8)))
            current_stock += yearly_seq

            if np.random.random() < p_storm:
                damage = np.random.uniform(*storm_bounds)
                current_stock *= (1 - damage)
            path.append(current_stock)
        per_ha_paths.append(path)

    # Find average expected yield for 1 hectare over the timeline
    mean_per_ha_path = np.mean(per_ha_paths, axis=0)
    expected_yield_per_ha = mean_per_ha_path[-1]

    # Reverse math: How many hectares do we need?
    required_ha = target_tons / expected_yield_per_ha
    required_budget = required_ha * cost_per_ha

    # Scale the path up to the required hectares for plotting
    final_path = mean_per_ha_path * required_ha

    return required_budget, required_ha, final_path


# Execute Math
p_storm = risk_data[region]["p"]
storm_bounds = risk_data[region]["damage"]
req_budget, req_ha, mean_path = calculate_required_budget(target_co2, years, p_storm, storm_bounds)

# Financial Metrics
gross_rev = mean_path[-1] * carbon_price
net_profit = gross_rev - req_budget

# --- 4. THE UI LAYOUT ---
st.title("🎯 Corporate Offset Calculator")
st.markdown(
    f"**Model Context:** Reverse-calculating the investment required to securely offset **{target_co2:,} tons** of CO2 in {region}.")

# Metrics Row
m1, m2, m3, m4 = st.columns(4)
m1.metric("Required Investment", f"${int(req_budget):,}")
m2.metric("Land Required (Hectares)", f"{int(req_ha):,}")
m3.metric("Asset Value (At Maturity)", f"${int(gross_rev):,}")
m4.metric("Net Financial ROI", f"${int(net_profit):,}")

# Tabs for different views
tab1, tab2 = st.tabs(["📊 Path to Target", "📈 Corporate Cash Flow"])

with tab1:
    fig_carbon = go.Figure()
    fig_carbon.add_trace(go.Scatter(x=list(range(1, years + 1)), y=mean_path,
                                    line=dict(color='#00796B', width=4), name="Projected Sequestration"))
    fig_carbon.add_trace(go.Scatter(x=[1, years], y=[target_co2, target_co2],
                                    line=dict(color='red', dash='dash'), name="Corporate Target"))
    fig_carbon.update_layout(title="Risk-Adjusted Path to Net Zero", template="plotly_white")
    st.plotly_chart(fig_carbon, use_container_width=True)

with tab2:
    # Cash flow: Starts at negative budget, climbs as asset value grows
    cash_flow = (mean_path * carbon_price) - req_budget
    fig_cash = go.Figure()
    fig_cash.add_trace(go.Scatter(x=list(range(1, years + 1)), y=cash_flow,
                                  line=dict(color='#005B96', width=4), name="Net Asset Value"))
    fig_cash.add_trace(go.Scatter(x=[1, years], y=[0, 0], line=dict(color='gray', dash='dash'), name="Break-even"))
    fig_cash.update_layout(title="Investment Recovery Timeline", template="plotly_white")
    st.plotly_chart(fig_cash, use_container_width=True)

st.success(
    f"**The Bottom Line:** To guarantee an offset of {target_co2:,} tons within {years} years, factoring in localized storm risk, you need to restore {int(req_ha):,} hectares at a cost of **${req_budget:,.0f}**.")