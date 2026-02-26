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
                # 1. Clean Growth: If growth is 15.0, make it 0.15
                raw_growth = row.get('GrowthRate', 0.05)
                growth = raw_growth / 100 if raw_growth > 1 else raw_growth
                
                # 2. Clean ROE & Yield: If 6000, make it 6.0 (still high, but possible)
                roe = row.get('ROE', 0)
                roe = roe / 100 if roe > 2 else roe # Cap at 200% for sanity
                
                dy = row.get('DivYield', 0)
                dy = dy / 100 if dy > 0.5 else dy # Cap at 50% for sanity

                ticker_data = {
                    "Ticker": row['Symbol'],
                    "Price": float(row.get('Price', 0)),
                    "intrinsic_value": engine.calculate_intrinsic_value_dcf(row.get('EPS', 0), growth),
                    "roe": roe,
                    "DivYield": dy,
                    "DivSafe": row.get('DivSafe', 'Stable'),
                    "Sector": row.get('Sector', 'General')
                }
                
                # Run Engine
                res = engine.generate_recommendation(ticker_data, st.session_state.macro)
                score = engine.calculate_alpha_score(ticker_data, st.session_state.macro, row['Symbol'])
                
                ticker_data.update({
                    "Action": res[0], "Logic": res[1], "Color": res[2], 
                    "MOS": res[3], "buy_at": res[4], "sell_at": res[5],
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
                with st.container(border=True):
                    st.markdown(f"### :{row['Color']}[{row['Ticker']} - {row['Action']}]")
                    
                    # Show the Targets
                    st.write(f"🎯 **Buy at:** :green[${row['buy_at']:.2f}] | **Sell at:** :red[${row['sell_at']:.2f}]")
                    
                    st.metric(
                        label="Price vs Fair Value", 
                        value=f"${row['Price']:.2f}", 
                        delta=f"FV: ${row['intrinsic_value']:.2f} ({row['MOS']:.1%})",
                        delta_color="normal"
                    )
                    
                    st.info(f"**Strategy:** {row['Logic']}")
                    
                    # Use Fixed ROE logic here
                    c1, c2 = st.columns(2)
                    c1.caption(f"Yield: {row['DivYield']:.2%}")
                    # FIXED SYNTAX ERROR BELOW
                    c2.caption(f"ROE: {row['roe']:.1%}") 
                    
                    st.progress(row['AlphaScore'] / 100)
    else:
        st.info("Analysis required. Please go to **Core Screener** and click 'Generate Recommendations'.")