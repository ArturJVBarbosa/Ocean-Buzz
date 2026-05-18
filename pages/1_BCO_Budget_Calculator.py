import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

# Add root folder to path so pages can see utils.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import apply_sunlight_theme

# Page Configuration
st.set_page_config(page_title="BCO Budget Calculator", layout="wide")

# Apply Theme
apply_sunlight_theme()

# Metrics: capex_per_ton (€), opex_per_ton_yr (€), ramp_up_years (Mother Nature's clock)
assets = [
    {"name": "Ocean Alkalinity", "capex": 200, "opex": 30, "ramp_up": 0},
    {"name": "Kelp Farming", "capex": 10, "opex": 15, "ramp_up": 1},
    {"name": "Salt Marshes", "capex": 25, "opex": 2, "ramp_up": 3},
    {"name": "Seagrass Meadows", "capex": 40, "opex": 10, "ramp_up": 4},
    {"name": "Mangrove Forests", "capex": 85, "opex": 12, "ramp_up": 7}
]

# UI: Sidebar Inputs
st.sidebar.title("🎯 Carbon Offset Target")
st.sidebar.markdown("Define your ultimate carbon goal and deadline.")

target_co2 = st.sidebar.number_input("Total CO2 to Offset (tons)", min_value=1000, max_value=1000000, value=50000,
                                     step=5000)
timeline_years = st.sidebar.slider("Time Window to Hit Goal (Years)", min_value=1, max_value=30, value=10)

st.sidebar.divider()
st.sidebar.markdown(
    "*This engine automatically calculates the required 'overbuild' capacity needed to survive biological ramp-up times.*")

# Math
results = []

for asset in assets:
    ramp = asset["ramp_up"]

    # Step A: Calculate the "Efficiency Multiplier" over the timeline
    # How many effective years of 100% capacity does this asset yield in this timeframe?
    sum_efficiency = 0
    for year in range(1, timeline_years + 1):
        if ramp > 0 and year <= ramp:
            sum_efficiency += (year / ramp)  # Growing phase
        else:
            sum_efficiency += 1.0  # Mature phase

    # Step B: Calculate Required Annual Capacity to guarantee the Target CO2
    # If the timeline is too short for a slow asset, sum_efficiency could be very low, forcing a massive capacity.
    if sum_efficiency > 0:
        required_capacity = target_co2 / sum_efficiency
    else:
        required_capacity = 0

        # Step C: Calculate the Financial Cost based on that Required Capacity
    total_capex = required_capacity * asset["capex"]
    total_opex = (required_capacity * asset["opex"]) * timeline_years
    total_investment = total_capex + total_opex

    results.append({
        "Asset Class": asset["name"],
        "Ramp-up (Years)": ramp,
        "Required Capacity Built (tons/yr)": required_capacity,
        "Total CAPEX (€)": total_capex,
        "Total Lifetime OPEX (€)": total_opex,
        "Total Investment Needed (€)": total_investment
    })

# Convert to DataFrame and sort by Total Investment (Cheapest to Most Expensive)
df = pd.DataFrame(results).sort_values(by="Total Investment Needed (€)", ascending=True).reset_index(drop=True)

# UI: Main Dashboard
st.title("💰 Blue Carbon Offset Budget Calculator")
st.markdown(f"**Goal:** Offset **{target_co2:,.0f} tons** of CO2 exactly by **Year {timeline_years}**.")

# Plotly Bar Chart for Visual Comparison
fig = px.bar(
    df,
    x="Asset Class",
    y=["Total CAPEX (€)", "Total Lifetime OPEX (€)"],
    title="Total Required Investment by Asset Class",
    labels={"value": "Total Cost (€)", "variable": "Cost Type"},
    color_discrete_sequence=["#1f77b4", "#ff7f0e"]
)
fig.update_layout(barmode='stack', yaxis_tickprefix='€')
st.plotly_chart(fig, use_container_width=True)

# Data Table Output
st.subheader("Financial Breakdown")

# Formatting the dataframe for a clean display
df_display = df.copy()
for col in ["Required Capacity Built (tons/yr)", "Total CAPEX (€)", "Total Lifetime OPEX (€)",
            "Total Investment Needed (€)"]:
    df_display[col] = df_display[col].apply(lambda x: f"{x:,.0f}")

st.dataframe(df_display, use_container_width=True, hide_index=True)

st.divider()
st.info(
    "💡 **Why do slow-growing assets cost so much on short timelines?** To hit a short-term carbon target using a slow-growing ecosystem (like Mangroves), you are mathematically forced to build a massively oversized project so the fractional early-year growth is enough to cover your footprint.")