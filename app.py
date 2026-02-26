import streamlit as st
import pandas as pd
import os
import database
import pipeline
import engine
import plotly.express as px

# --- 1. SESSION STATE INITIALIZATION ---
# This keeps data alive when you switch between tabs
if 'final_report' not in st.session_state:
    st.session_state.final_report = []
if 'macro' not in st.session_state:
    st.session_state.macro = {"VIX": 20.0, "10Y_Yield": 4.0}

st.set_page_config(page_title="Alpha Engine", layout="wide")
st.title("🏛️ Alpha Engine")

# Load base metadata
df_metadata = database.initialize_sp500()

# --- 2. TABS DEFINITION ---
tab1, tab2, tab3 = st.tabs(["🎯 Core Screener", "🔭 Live Intelligence", "🏛️ Intelligence Hub"])

# --- TAB 1: SCREENER & DATA FETCH ---
with tab1:
    st.subheader("S&P 500 Universe")
    st.dataframe(df_metadata, use_container_width=True, height=250)
    
    if st.button("Generate Recommendations", type="primary"):
        with st.spinner("Crunching 2026 Macro & Sector Data..."):
            dynamic_ratings = pipeline.get_dynamic_sector_ratings()
            st.session_state.macro = pipeline.fetch_macro_signals()

        with st.spinner("Analyzing Fundamentals & Intrinsic Values..."):
            # Fetch for top 50
            tickers = df_metadata['Symbol'].head(50).tolist()
            fundamentals = database.get_enriched_data(tickers)
            st.session_state.final_report = [] 

            for _, row in fundamentals.iterrows():
                # --- STEP 1: Extract All Data (Fixed Mapping) ---
                price = float(row.get('Price', 0))
                eps = float(row.get('EPS', 0))
                growth = float(row.get('GrowthRate', 0.05))
                
                # Calculate Intrinsic Value
                iv = engine.calculate_intrinsic_value_dcf(eps, growth, row.get('Shares_Outstanding', 1))
                mos = (iv - price) / price if price > 0 else 0

                # --- STEP 2: Build the Comprehensive Dictionary ---
                ticker_data = {
                    "Ticker": row['Symbol'],
                    "Price": price,
                    "intrinsic_value": round(iv, 2),
                    "roe": row.get('ROE', 0),
                    "DivYield": row.get('DivYield', 0),
                    "DivSafe": row.get('DivSafe', 'Stable'),
                    "Sector": row.get('Sector', "General"),
                    "MOS": mos,
                    "Growth": growth
                }
                
                # --- STEP 3: Run the Engine Brain ---
                # Pass the ticker_data dictionary to get the labels
                #rec, logic, color, _ = engine.generate_recommendation(ticker_data, st.session_state.macro)
                action, logic, color, mos, buy_at, sell_at = engine.generate_recommendation(ticker_data, st.session_state.macro)
                
                # Pass ticker_data, macro, and symbol for the final score
                score = engine.calculate_alpha_score(ticker_data, st.session_state.macro, row['Symbol'])
                
                # --- STEP 4: Store results ---
                ticker_data.update({
                    "Action": action, 
                    "Logic": logic, 
                    "Color": color, 
                    "AlphaScore": score
                })
                st.session_state.final_report.append(ticker_data)
        st.success("Analysis Complete! Head to the Intelligence Hub.")

# --- TAB 2: POLITICIAN TRADES (AUTOMATED) ---
with tab2:
    st.subheader("Congressional Intelligence")
    # Check if the automated CSV from GitHub Actions exists
    if os.path.exists("daily_trades.csv"):
        trades_df = pd.read_csv("daily_trades.csv")
        st.write("✅ Daily Auto-Scan Results (2:00 AM Sync):")
        st.dataframe(trades_df, use_container_width=True)
    else:
        st.warning("Daily sync file not found. Running manual fallback...")
        if st.button("Manual Trade Fetch"):
            manual_trades = pipeline.fetch_politician_trades()
            if not manual_trades.empty:
                st.dataframe(manual_trades, use_container_width=True)
            else:
                st.error("Manual fetch blocked. Use the automated GitHub Action.")

# --- TAB 3: INTELLIGENCE HUB (THE BRAIN) ---
with tab3:
    st.header("🏛️ Intelligence Hub: Alpha Grid")
    
    if st.session_state.final_report:
        df_alpha = pd.DataFrame(st.session_state.final_report)
        
        # --- 1. SECTOR HEATMAP ---
        st.subheader("🗺️ Sector Value Heatmap")
        try:
            fig = px.treemap(
                df_alpha, 
                path=[px.Constant("Market"), 'Sector', 'Ticker'], 
                values='Price',
                color='AlphaScore',
                color_continuous_scale='RdYlGn', 
                color_continuous_midpoint=50,
                hover_data=['Action', 'MOS', 'intrinsic_value']
            )
            fig.update_layout(margin=dict(t=0, l=0, r=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.info("Visualizing market structure...")

        # --- 2. SECTOR LEADERBOARD ---
        st.write("### 📊 Sector Strength")
        sector_stats = df_alpha.groupby('Sector').agg({'AlphaScore': 'mean', 'Ticker': 'count'}).rename(columns={'Ticker': 'Stocks', 'AlphaScore': 'Avg Alpha'}).sort_values('Avg Alpha', ascending=False)
        st.dataframe(sector_stats.style.background_gradient(cmap='RdYlGn', subset=['Avg Alpha']).format("{:.1f}"), use_container_width=True)

        # --- 3. THE ALPHA GRID ---
        st.divider()
        search = st.text_input("🔍 Filter by Ticker", "").upper()
        if search:
            df_alpha = df_alpha[df_alpha['Ticker'].str.contains(search)]

        grid_cols = st.columns(3) 
        for idx, row in df_alpha.reset_index().iterrows():
            with grid_cols[idx % 3]:
                # CAPTURE ALL 6 OUTPUTS FROM ENGINE
                action, logic, color, mos, buy_at, sell_at = engine.generate_recommendation(row, st.session_state.macro)
                
                with st.container(border=True):
                    st.markdown(f"### :{color}[{row['Ticker']} - {action}]")
                    
                    # THE "WHEN PRICE IS XXX" DISPLAY
                    st.write(f"🎯 **Target Entry:** :green[**${buy_at}**]")
                    st.write(f"🎯 **Target Exit:** :red[**${sell_at}**]")
                    
                    st.metric(
                        label="Current vs Fair Value", 
                        value=f"${row['Price']:.2f}", 
                        delta=f"Fair Value: ${row['intrinsic_value']:.2f}",
                        delta_color="normal"
                    )
                    
                    st.info(f"**Engine Logic:** {logic}")
                    
                    # Metric Row
                    c1, c2 = st.columns(2)
                    c1.caption(f"Yield: {row.get('DivYield', 0):.2%}")
                    c2.caption(f"ROE: {row.get('roe', 0):.1%}") # Syntax fixed here too
                    
                    st.progress(row['AlphaScore'] / 100)
    else:
        st.info("Analysis required. Please go to **Core Screener** and click 'Generate Recommendations'.")