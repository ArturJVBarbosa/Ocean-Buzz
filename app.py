import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os
import textwrap
import streamlit as st
from live_quotes import fetch_live_portfolio_status, display_live_asset_cards

st.set_page_config(layout="wide", page_title="Ocean Fund Dashboard", page_icon="⚓")

DB_PATH = "data/ocean_fund.db"

# Frontend Presentation Dictionary: Maps raw broker ISINs to clean UI tickers
TICKER_MAP = {
    'US0378331005': 'AAPL',
    'US5949181045': 'MSFT',
    'IE00B0M62S72': 'IDVY.AS'
}

st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        color: #0077b6 !important;
        font-family: 'Courier New', Courier, monospace;
        font-weight: bold;
    }
    h1, h2, h3 { color: #03045e !important; }
    </style>
""", unsafe_allow_html=True)

st.title("🌊 Ocean Fund Dashboard")
#st.markdown("*Pure decoupled visualizer. Reading immutable SQLite analytics cube.*")
st.markdown("---")

@st.cache_data(ttl=60)
def load_dashboard_data():
    if not os.path.exists(DB_PATH): return None, None, None
    conn = sqlite3.connect(DB_PATH)

    fleet_curve = pd.read_sql_query("""
        SELECT date, SUM(market_value_eur) as fleet_val 
        FROM daily_ledger GROUP BY date ORDER BY date ASC
    """, conn)

    deposit_history = pd.read_sql_query("""
        SELECT date, net_change FROM cash_movements 
        WHERE type IN ('DEPOSIT', 'WITHDRAWAL') ORDER BY date ASC
    """, conn)

    # Registro de Fluxo de Caixa de Dividendos
    div_registry = pd.read_sql_query("""
        SELECT date, isin, net_change as dividend_eur, description
        FROM cash_movements 
        WHERE type = 'DIVIDEND' ORDER BY date ASC
    """, conn)

    tax_registry = pd.read_sql_query("""
        SELECT date, abs(net_change) as tax_eur
        FROM cash_movements 
        WHERE type = 'TAX' AND (
            LOWER(description) LIKE '%div%' OR 
            LOWER(description) LIKE '%retent%' OR 
            LOWER(description) LIKE '%fonte%' OR 
            LOWER(description) LIKE '%withhold%'
        ) ORDER BY date ASC
    """, conn)

    # --- SQL JOIN: Dynamically pulls the official Company Name from your trade history ---
    latest_manifest = pd.read_sql_query("""
        SELECT 
            dl.date,
            dl.isin,
            COALESCE(t.product_name, dl.isin) AS company_name,
            dl.shares_owned,
            dl.avg_cost_basis,
            dl.close_price,
            dl.market_value_eur,
            dl.cumulative_dividends
        FROM daily_ledger dl
        LEFT JOIN (
            SELECT isin, MIN(product_name) AS product_name 
            FROM transactions 
            WHERE product_name IS NOT NULL AND product_name != ''
            GROUP BY isin
        ) t ON dl.isin = t.isin
        WHERE dl.date = (SELECT MAX(date) FROM daily_ledger)
    """, conn)

    conn.close()
    return fleet_curve, deposit_history, latest_manifest, div_registry, tax_registry


fleet_curve, deposit_history, latest_manifest, div_registry, tax_registry = load_dashboard_data()

if fleet_curve is None or fleet_curve.empty:
    st.warning("⚓ Storage vault unreachable or empty! Please execute `python update_db.py` in your terminal.")
else:
    # 1. MAPEAMENTO DE TICKERS (Nascem logo no topo para estarem disponíveis em todo o script)
    latest_manifest['ticker'] = latest_manifest['isin'].map(TICKER_MAP).fillna(latest_manifest['isin'])
    div_registry['ticker'] = div_registry['isin'].map(TICKER_MAP).fillna(div_registry['isin'])

    # 2. CÁLCULO DE CAPITAL ANCHOR & FLEET VALUE
    deposit_history['date'] = pd.to_datetime(deposit_history['date'])
    daily_deposits = deposit_history.groupby('date')['net_change'].sum().reset_index()
    daily_deposits['cum_injected'] = daily_deposits['net_change'].cumsum()

    fleet_curve['date'] = pd.to_datetime(fleet_curve['date'])
    daily_timeline = pd.date_range(start=fleet_curve['date'].min(), end=fleet_curve['date'].max(), freq='D')

    dep_curve = daily_deposits.set_index('date').reindex(daily_timeline, method='ffill')['cum_injected'].fillna(0)
    perf_df = fleet_curve.set_index('date').reindex(daily_timeline, method='ffill').reset_index()
    perf_df.rename(columns={'index': 'Date', 'fleet_val': 'Active Fleet Value'}, inplace=True)
    perf_df['Anchored Capital (Deposited)'] = dep_curve.values

    # 3. VARIÁVEIS GLOBAIS DE WEALTH (Onde a total_divs_lifetime nasce em segurança!)
    perf_df['Date'] = pd.to_datetime(perf_df['Date'])
    master_series = perf_df.set_index('Date').sort_index()

    current_dt = master_series.index.max()
    current_val = float(master_series.iloc[-1]['Active Fleet Value'])
    total_injected = float(master_series.iloc[-1]['Anchored Capital (Deposited)'])
    total_divs_lifetime = float(div_registry['dividend_eur'].sum()) if not div_registry.empty else 0.0

    # --- MATEMÁTICA DA LINHA 2 (TTM & CONCENTRAÇÃO) ---
    # --- MATEMÁTICA DA LINHA 2 (TTM & CONCENTRAÇÃO BLINDADA) ---

    c_qty  = next((c for c in ['shares_owned', 'shares', 'Shares', 'quantity', 'Quantity', 'units'] if c in latest_manifest.columns), None)
    c_val  = next((c for c in ['market_value_eur', 'market_value', 'Market Value', 'value_eur', 'total_value'] if c in latest_manifest.columns), None)
    c_name = next((c for c in ['product', 'Product', 'produto', 'Produto', 'name', 'Name', 'asset_name', 'company', 'description'] if c in latest_manifest.columns), None)

    if c_qty and not latest_manifest.empty:
        active_fleet = latest_manifest.copy()

        # Peneira 1: Matar fantasmas de posições vendidas (Valor de Mercado >= 1.00€)
        if c_val:
            active_fleet = active_fleet[active_fleet[c_val] >= 1.0]
        else:
            active_fleet = active_fleet[active_fleet[c_qty] >= 0.01] # Fallback se não achar a coluna de valor

        # Peneira 2: Matar varredura automática de liquidez da DEGIRO
        if c_name:
            cash_words = 'CASH|FUNDSHARE|FLATEX|LIQUIDEZ|MONEY MARKET'
            active_fleet = active_fleet[~active_fleet[c_name].astype(str).str.contains(cash_words, case=False, na=False)]

        active_assets_count = len(active_fleet)
    else:
        active_assets_count = 0

    # ... O resto do código (one_year_ago, monthly_run_rate, etc.) continua exatamente igual para baixo ...

    # Filtro TTM (Trailing Twelve Months - estritamente os últimos 365 dias)
    one_year_ago = pd.to_datetime(current_dt) - pd.DateOffset(years=1)
    if not div_registry.empty:
        ttm_mask = pd.to_datetime(div_registry['date']) >= one_year_ago
        ttm_divs = float(div_registry[ttm_mask]['dividend_eur'].sum())
    else:
        ttm_divs = 0.0

    monthly_run_rate = ttm_divs / 12.0
    ttm_yield_pct = (ttm_divs / current_val * 100) if current_val > 0 else 0.0

    if not latest_manifest.empty and 'market_value_eur' in latest_manifest.columns:
        max_pos_val = float(latest_manifest['market_value_eur'].max())
        top_weight_pct = (max_pos_val / current_val * 100) if current_val > 0 else 0.0
    else:
        top_weight_pct = 0.0


    # 4. MOTOR DE PERFORMANCE POR HORIZONTE TEMPORAL
    def get_horizon_pnl(target_dt):
        sub = master_series.loc[:target_dt]
        if sub.empty: return 0.0, 0.0
        start_val = float(sub.iloc[-1]['Active Fleet Value'])
        start_dep = float(sub.iloc[-1]['Anchored Capital (Deposited)'])
        window_deposits = total_injected - start_dep
        pure_pnl = (current_val - start_val) - window_deposits
        cost_base = start_val + window_deposits
        pct = (pure_pnl / cost_base) * 100 if cost_base > 0 else 0.0
        return pure_pnl, pct

    horizons = {
        "1D (Day)": current_dt - pd.DateOffset(days=1),
        "1W (Week)": current_dt - pd.DateOffset(weeks=1),
        "1M (Month)": current_dt - pd.DateOffset(months=1),
        "YTD": pd.to_datetime(f"{current_dt.year}-01-01"),
        "1Y (Year)": current_dt - pd.DateOffset(years=1),
        "3Y": current_dt - pd.DateOffset(years=3),
        "All-Time": master_series.index.min()
    }
    h_metrics = {label: get_horizon_pnl(dt) for label, dt in horizons.items()}


    # 5. SIDEBAR NAVIGATION CONTROLLER
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        page = st.sidebar.radio(
            "Select View:",
            ["🏠 Home Overview", "📈 Multi-Year Evolution", "🚢 Active Fleet Manifest", "🐳 Dividend Command Deck"]
        )

    # ==========================================
    # --- VIEW 1: HOME OVERVIEW ----------------
    # ==========================================
    if page == "🏠 Home Overview":
        st.markdown("### ⚓ Ocean Fund Overview")

        # 1. Vai buscar a informação fresca
        df_live = fetch_live_portfolio_status()
        # 2. Em vez da tabela, chama os novos cartões instantaneamente!
        display_live_asset_cards(df_live)
        st.markdown("---")

        # --- LINHA 1: BALANÇO PATRIMONIAL ---
        r1_c1, r1_c2, r1_c3, r1_c4 = st.columns(4)
        r1_c1.metric("⚓ Hard Capital (Injected)", f"€{total_injected:,.2f}")
        r1_c2.metric("🚢 Fleet Valuation", f"€{current_val:,.2f}")

        at_pnl, at_pct = h_metrics["All-Time"]
        r1_c3.metric("🌊 Net Tide (All-Time PnL)", f"€{at_pnl:,.2f}", f"{at_pct:+.2f}%")
        r1_c4.metric("🐳 Lifetime Dividends", f"€{total_divs_lifetime:,.2f}")

        st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

        st.markdown("---")

        # --- TIER 2: REVOLUT GLASS RIBBON ---
        st.markdown("### ⏱️ Trailing Time-Horizon Performance")
        tape_keys = ["1D (Day)", "1W (Week)", "1M (Month)", "YTD", "1Y (Year)", "3Y"]

        ribbon_html = '<div style="display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 25px;">'
        for key in tape_keys:
            _, pnl_rate = h_metrics[key]
            is_pos = pnl_rate >= 0

            bg = "rgba(16, 185, 129, 0.12)" if is_pos else "rgba(239, 68, 68, 0.12)"
            border = "rgba(16, 185, 129, 0.45)" if is_pos else "rgba(239, 68, 68, 0.45)"
            text_col = "#10b981" if is_pos else "#ef4444"

            card_block = f"""
                    <div style="flex: 1; min-width: 105px; background: {bg}; border: 1px solid {border}; border-radius: 10px; padding: 12px 8px; text-align: center; backdrop-filter: blur(4px);">
                    <div style="font-size: 11px; color: #778da9; font-weight: 600; letter-spacing: 0.5px; margin-bottom: 6px;">{key}</div>
                    <div style="font-size: 18px; font-weight: 700; color: {text_col}; font-family: 'Courier New', monospace;">{pnl_rate:+.2f}%</div>
                    </div>
                    """
            ribbon_html += textwrap.dedent(card_block)

        ribbon_html += '</div>'
        st.markdown(ribbon_html, unsafe_allow_html=True)

    # ==========================================
    # --- VIEW 2: EVOLUTION CURVE --------------
    # ==========================================
    elif page == "📈 Multi-Year Evolution":
        st.subheader("Compass: Capital Accumulation vs. Fleet Valuation")
        fig_net = px.area(perf_df, x='Date', y=['Anchored Capital (Deposited)', 'Active Fleet Value'],
                          color_discrete_sequence=['#00b4d8', '#03045e'])
        fig_net.update_layout(hovermode="x unified", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_net, use_container_width=True)

    # ==========================================
    # --- VIEW 3: FLEET MANIFEST ---------------
    # ==========================================
    elif page == "🚢 Active Fleet Manifest":
        latest_date_str = latest_manifest['date'].iloc[0]
        st.subheader(f"Holdings Snapshot as of {latest_date_str}")

        display_df = latest_manifest[
            ['company_name', 'ticker', 'shares_owned', 'avg_cost_basis', 'close_price', 'market_value_eur',
             'cumulative_dividends']].copy()
        display_df.columns = ['Asset Name', 'Ticker', 'Shares', 'Avg Basis', 'Close Price', 'Market Value',
                              'Cum. Dividends']

        st.dataframe(
            display_df.style.format({
                'Shares': '{:,.2f}', 'Avg Basis': '€{:,.2f}',
                'Close Price': '€{:,.2f}', 'Market Value': '€{:,.2f}',
                'Cum. Dividends': '€{:,.2f}'
            }),
            use_container_width=True, hide_index=True
        )
        st.title("🌊 Ocean Fund - Real Time Dashboard")

        df_live = fetch_live_portfolio_status()

        if not df_live.empty:
            total_portfolio_value = df_live['Market Value (€)'].sum()
            st.metric(label="Valor Total da Carteira (Live)", value=f"{total_portfolio_value:,.2f} €")

            st.subheader("Cotações e Desempenho Atual")
            st.dataframe(
                df_live.style.format({
                    'Shares': '{:,.4f}',
                    'Avg Cost (€)': '{:,.2f} €',
                    'Live Price (€)': '{:,.2f} €',
                    'Market Value (€)': '{:,.2f} €',
                    'Day Change (%)': '{:+.2f}%',
                    'Total Profit (%)': '{:+.2f}%'
                })
            )
        else:
            st.info("Nenhum ativo ativo encontrado na carteira.")

    # ==========================================
    # --- VIEW 4: DIVIDEND COMMAND DECK --------
    # ==========================================
    elif page == "🐳 Dividend Command Deck":
        st.subheader("Passive Cash Flow Analytics")

        if div_registry.empty:
            st.info("No dividend logs captured in storage vault yet.")
        else:
            div_registry['date'] = pd.to_datetime(div_registry['date'])
            div_registry['Year'] = div_registry['date'].dt.strftime('%Y')
            div_registry['Month_Year'] = div_registry['date'].dt.strftime('%Y-%m')

            one_year_ago = pd.to_datetime('today') - pd.DateOffset(years=1)
            t12_divs = div_registry[div_registry['date'] >= one_year_ago]['dividend_eur'].sum()

            cur_yield = (t12_divs / current_val) * 100 if current_val > 0 else 0
            yoc = (t12_divs / total_injected) * 100 if total_injected > 0 else 0
            avg_monthly_t12 = t12_divs / 12

            d_col1, d_col2, d_col3, d_col4 = st.columns(4)
            d_col1.metric("⏱️ Trailing 12M Income", f"€{t12_divs:,.2f}")
            d_col2.metric("📅 Monthly Average (T12M)", f"€{avg_monthly_t12:,.2f}")
            d_col3.metric("🎯 Current Yield", f"{cur_yield:.2f}%")
            d_col4.metric("🛡️ Yield on Cost (YoC)", f"{yoc:.2f}%")

            st.markdown("---")

            yearly_divs = div_registry.groupby('Year')['dividend_eur'].sum().reset_index()
            monthly_divs = div_registry.groupby('Month_Year')['dividend_eur'].sum().reset_index()

            st.markdown("#### Annual Income Allocation")
            y_gross = div_registry.groupby('Year')['dividend_eur'].sum().reset_index()
            y_gross.rename(columns={'dividend_eur': 'Gross'}, inplace=True)

            if not tax_registry.empty:
                tax_registry['Year'] = pd.to_datetime(tax_registry['date']).dt.strftime('%Y')
                y_tax = tax_registry.groupby('Year')['tax_eur'].sum().reset_index()
                y_tax.rename(columns={'tax_eur': 'Tax'}, inplace=True)
            else:
                y_tax = pd.DataFrame({'Year': y_gross['Year'], 'Tax': 0.0})

            annual_financials = pd.merge(y_gross, y_tax, on='Year', how='left').fillna(0.0)
            annual_financials['Net'] = annual_financials['Gross'] - annual_financials['Tax']

            fig_year = px.bar(
                annual_financials, x='Year', y=['Net', 'Tax'],
                barmode='stack', text_auto='.2s',
                labels={'value': 'Euros (€)', 'variable': 'Pocket'},
                color_discrete_map={'Net': '#03045e', 'Tax': '#e63946'}
            )
            fig_year.update_traces(textfont_size=11, textposition="inside")
            fig_year.update_layout(
                height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title="")
            )
            st.plotly_chart(fig_year, use_container_width=True)

            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("#### Overall Monthly Income")
            monthly_divs = div_registry.groupby('Month_Year')['dividend_eur'].sum().reset_index()

            sorted_peaks = monthly_divs['dividend_eur'].sort_values(ascending=False).values
            second_place = sorted_peaks[1] if len(sorted_peaks) > 1 else sorted_peaks[0]
            smart_ceiling = max(second_place * 1.15, 10.0)

            fig_month = px.bar(
                monthly_divs, x='Month_Year', y='dividend_eur', text_auto='.2s',
                labels={'Month_Year': 'Month', 'dividend_eur': 'Euros (€)'},
                color_discrete_sequence=['#00b4d8']
            )

            fig_month.update_traces(textfont_size=11, textangle=0, textposition="auto", cliponaxis=False)
            fig_month.update_layout(
                height=380, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', hovermode="x unified",
                yaxis=dict(range=[0, smart_ceiling])
            )
            st.plotly_chart(fig_month, use_container_width=True)

            st.markdown("#### 🏆 Top Income Generators (Lifetime)")
            asset_divs = div_registry.groupby('ticker')['dividend_eur'].sum().reset_index()
            asset_divs['Share of Total'] = (asset_divs['dividend_eur'] / total_divs_lifetime) * 100
            asset_divs = asset_divs.sort_values(by='dividend_eur', ascending=False)

            st.dataframe(asset_divs.style.format({
                'dividend_eur': '€{:,.2f}',
                'Share of Total': '{:.1f}%'
            }), use_container_width=True, hide_index=True)