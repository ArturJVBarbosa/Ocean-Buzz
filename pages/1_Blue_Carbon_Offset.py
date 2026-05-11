import streamlit as st
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

# --- 2. PROJECT DATABASE (Upgraded with Market Prices) ---
projects = [
    {
        "name": "Mangroves",
        "ramp_up_years": 7, # Takes 7 years to reach 100% capacity
        "capex_per_ton": 15,
        "opex_per_ton_yr": 3,
        "market_price_per_ton": 45,  # What the credit sells for
        "region": "Tropical / Global South",
        "goal": "Biodiversity & Wildlife",
        "horizon": "Mid-term 5-20y",
        "permanence_score": 7,
        "co_benefit_score": 9,
        "desc": "The 'Sediment Vault'. Highly efficient at storing carbon in tropical root systems."
    },
    {
        "name": "Seagrass Meadows",
        "ramp_up_years": 4,
        "capex_per_ton": 40,
        "opex_per_ton_yr": 10,
        "market_price_per_ton": 65,  # Premium price due to high demand
        "region": "Europe / Mediterranean",
        "goal": "Biodiversity & Wildlife",
        "horizon": "Mid-term 5-20y",
        "permanence_score": 8,
        "co_benefit_score": 9,
        "desc": "The 'Lungs of the Sea'. Premium Mediterranean restoration that boosts local fish stocks."
    },
    {
        "name": "Kelp Farming",
        "ramp_up_years": 1,
        "capex_per_ton": 10,
        "opex_per_ton_yr": 15,
        "market_price_per_ton": 35,
        "region": "Global Anywhere",
        "goal": "Commercial Revenue / Biomass",
        "horizon": "Short-term <5y",
        "permanence_score": 5,
        "co_benefit_score": 7,
        "desc": "The 'Dual-Stream Crop'. Fast-growing biomass that offers commercial revenue."
    },
    {
        "name": "Salt Marshes",
        "ramp_up_years": 3,
        "capex_per_ton": 25,
        "opex_per_ton_yr": 2,
        "market_price_per_ton": 40,
        "region": "Europe / Mediterranean",
        "goal": "Coastal Flood Protection",
        "horizon": "Mid-term 5-20y",
        "permanence_score": 8,
        "co_benefit_score": 8,
        "desc": "The 'Coastal Shield'. Natural infrastructure that absorbs storm surges."
    },
    {
        "name": "Ocean Alkalinity",
        "ramp_up_years": 0, #It's a machine, it works instantly
        "capex_per_ton": 200,
        "opex_per_ton_yr": 30,
        "market_price_per_ton": 350,  # High tech, high price
        "region": "Global Anywhere",
        "goal": "Pure Carbon Permanence",
        "horizon": "Legacy >20y",
        "permanence_score": 10,
        "co_benefit_score": 4,
        "desc": "The 'Tech Frontier'. Industrial mineral distribution that guarantees geological permanence."
    }
]

# --- 3. UI: SIDEBAR INPUTS ---
st.sidebar.title("🌊 Strategy Parameters")
st.sidebar.markdown("Define your corporate mandate.")

st.sidebar.subheader("1. Emissions & Scale")
corporate_footprint = st.sidebar.number_input("Annual Corporate Footprint (tons to retire)", min_value=100, max_value=100000, value=2000, step=500)
project_capacity = st.sidebar.number_input("Annual Project Capacity (tons to generate)", min_value=100, max_value=200000, value=5000, step=500)

if project_capacity < corporate_footprint:
    st.sidebar.warning("⚠️ Capacity is smaller than footprint. You won't reach Net Zero.")

max_budget = st.sidebar.number_input("Max Budget (€)", min_value=10000, max_value=10000000, value=1500000, step=10000)
funding_years = st.sidebar.slider("Years of Operation to Fund", min_value=1, max_value=20, value=10)

st.sidebar.divider()
st.sidebar.subheader("2. Strategic Mandate")

pref_region = st.sidebar.selectbox("Preferred Region", ("Global Anywhere", "Europe / Mediterranean", "Tropical / Global South"))
pref_goal = st.sidebar.selectbox("Primary Goal", ("Pure Carbon Permanence", "Biodiversity & Wildlife", "Coastal Flood Protection", "Commercial Revenue / Biomass"))

# --- 4. SCORING ENGINE ---
results = []

# Pre-calculate the surplus
total_generated = project_capacity * funding_years
total_retired = corporate_footprint * funding_years
total_surplus = total_generated - total_retired

# --- 4. SCORING ENGINE ---
results = []

for p in projects:
    score = 0

    # NEW YEAR-BY-YEAR MATURATION MATH
    total_generated = 0
    total_surplus = 0
    total_retired = 0

    for year in range(1, funding_years + 1):
        # Calculate this year's efficiency based on the ramp-up curve
        if p["ramp_up_years"] > 0 and year <= p["ramp_up_years"]:
            efficiency = year / p["ramp_up_years"]  # Linear growth
        else:
            efficiency = 1.0  # 100% mature

        year_generation = project_capacity * efficiency
        total_generated += year_generation

        # Corporate Footprint is immediate. Do they have enough credits this year?
        if year_generation >= corporate_footprint:
            year_retired = corporate_footprint
            year_surplus = year_generation - corporate_footprint
        else:
            year_retired = year_generation  # They fall short of Net Zero this year!
            year_surplus = 0

        total_retired += year_retired
        total_surplus += year_surplus

    # Costs are still based on the total scale of the project built
    total_capex = p["capex_per_ton"] * project_capacity
    total_opex = (p["opex_per_ton_yr"] * project_capacity) * funding_years
    total_cost = total_capex + total_opex

    # Blended Cost per Ton (Based on total generated)
    blended_cost_per_ton = total_cost / total_generated if total_generated > 0 else 0

    # Revenue ONLY comes from the surplus credits sold to the market over the lifetime
    total_market_value = p["market_price_per_ton"] * total_surplus if total_surplus > 0 else 0

    projected_profit = total_market_value - total_cost
    roi_percentage = (projected_profit / total_cost) * 100 if total_cost > 0 else 0

    # NEW: Shortfall Penalty
    # If they failed to generate enough to cover their footprint over the lifetime
    if total_retired < (corporate_footprint * funding_years):
        score -= 30  # Heavy penalty for failing Net Zero

    # 1. Budget Constraint (Hard filter)
    if total_cost > max_budget:
        cost_efficiency = 0
        score -= 50
    else:
        cost_efficiency = min(10, (max_budget / total_cost) * 2)
        score += 20

    # 2. Region Match
    region_match = 10 if (p["region"] == pref_region or p[
        "region"] == "Global Anywhere" or pref_region == "Global Anywhere") else 2
    if p["region"] == pref_region:
        score += 25

    # 3. Goal Match
    goal_match = 10 if p["goal"] == pref_goal else 3
    if p["goal"] == pref_goal:
        score += 30

    # 4. Horizon Match
    if funding_years < 5:
       implied_horizon = "Short-term <5y"
    elif funding_years <= 20:  # Since our slider maxes at 20 right now
       implied_horizon = "Mid-term 5-20y"
    else:
       implied_horizon = "Legacy >20y"

    if p["horizon"] == implied_horizon:
       score += 15

    # 5. Financial Viability Boost (Bonus points for positive ROI)
    if roi_percentage > 0:
        score += 10

    results.append({
        "Project": p["name"],
        "Total Score": score,
        "Total Cost (€)": total_cost,
        "Capex (€)": total_capex,
        "Opex (€)": total_opex,
        "Blended Cost/Ton (€)": blended_cost_per_ton,
        "Market Value (€)": total_market_value,
        "Projected Profit (€)": projected_profit,
        "ROI (%)": roi_percentage,
        "Description": p["desc"],
        "Cost Efficiency": cost_efficiency if cost_efficiency <= 10 else 10,
        "Permanence": p["permanence_score"],
        "Co-Benefits": p["co_benefit_score"],
        "Strategic Alignment": (region_match + goal_match) / 2
    })

# Sort by highest score
df_results = pd.DataFrame(results).sort_values(by="Total Score", ascending=False).reset_index(drop=True)
winner = df_results.iloc[0]
top_3 = df_results.head(3)

# --- 5. UI: MAIN DASHBOARD ---
st.title("🎯 Investment Recommendation Engine")

if winner["Total Score"] < 0:
    st.error(
        "⚠️ **No viable projects found within your budget.** Your Target CO2 combined with operating years exceeds your Max Budget.")
else:
    # Top Result Display
    st.success(f"### Best Match: **{winner['Project']}**")
    st.markdown(f"*{winner['Description']}*")

    # NEW: Credit Allocation Row
    st.markdown("#### ⚖️ Lifetime Credit Allocation")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total Generated (Factoring Growth)", f"{total_generated:,.0f} tons")

    # Check if they had a shortfall due to slow growth
    target_retirement = corporate_footprint * funding_years
    if total_retired < target_retirement:
        shortfall = target_retirement - total_retired
        col_b.metric("Retired (Net Zero Goal)", f"{total_retired:,.0f} tons", delta=f"Shortfall: {shortfall:,.0f} tons",
                     delta_color="inverse")
    else:
        col_b.metric("Retired (Net Zero Goal)", f"{total_retired:,.0f} tons", delta="Target Met", delta_color="normal")

    col_c.metric("Surplus (For Sale)", f"{total_surplus:,.0f} tons", delta="Available to trade", delta_color="off")
    st.divider()

    # Financial Row 1: Cost
    st.markdown("#### 💰 Cost Breakdown")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cost (Lifetime)", f"€{winner['Total Cost (€)']:,.0f}")
    col2.metric("Capex (Initial)", f"€{winner['Capex (€)']:,.0f}")
    col3.metric("Opex (Lifetime)", f"€{winner['Opex (€)']:,.0f}")
    col4.metric("Blended Cost/Ton", f"€{winner['Blended Cost/Ton (€)']:,.0f}")

    # Financial Row 2: Return on Investment
    st.markdown("#### 📈 Carbon Market Return")
    col5, col6, col7 = st.columns(3)
    col5.metric("Market Value of Credits", f"€{winner['Market Value (€)']:,.0f}")

    # Color-code the profit to highlight green/red
    profit_color = "normal" if winner['Projected Profit (€)'] > 0 else "inverse"
    col6.metric("Projected Profit/Loss", f"€{winner['Projected Profit (€)']:,.0f}",
                delta=f"€{winner['Projected Profit (€)']:,.0f}", delta_color=profit_color)
    col7.metric("Estimated ROI", f"{winner['ROI (%)']:.1f}%")

    st.divider()

    # Radar Chart comparing Top 3
    st.subheader("Top 3 Asset Comparison")

    categories = ['Cost Efficiency', 'Permanence', 'Co-Benefits', 'Strategic Alignment']

    fig = go.Figure()

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']

    for i, row in top_3.iterrows():
        fig.add_trace(go.Scatterpolar(
            r=[row['Cost Efficiency'], row['Permanence'], row['Co-Benefits'], row['Strategic Alignment']],
            theta=categories,
            fill='toself',
            name=row['Project'],
            line=dict(color=colors[i % len(colors)])
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10]
            )),
        showlegend=True,
        margin=dict(t=40, b=40, l=40, r=40)
    )

    st.plotly_chart(fig, use_container_width=True)

    # Breakdown Table
    st.subheader("Financial Breakdown Data")
    st.dataframe(
        top_3[["Project", "Total Cost (€)", "Market Value (€)", "Projected Profit (€)", "ROI (%)", "Total Score"]],
        hide_index=True)
