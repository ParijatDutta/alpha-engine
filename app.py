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
    st.dataframe(df_metadata, use_container_width=True, height=300)
    
    if st.button("Generate Recommendations"):
        with st.spinner("Calculating Dynamic Sector Heatmap..."):
            # Get fresh 2026 sector data
            dynamic_ratings = pipeline.get_dynamic_sector_ratings()

        with st.spinner("Analyzing Fundamentals..."):
            # Fetch for top 20 to stay within memory/time limits
            tickers = df_metadata['Symbol'].head(50).tolist()
            fundamentals = database.get_enriched_data(tickers)
            st.session_state.final_report = [] 

            # --- Inside Tab 1 Generate Recommendations Loop ---
            for _, row in fundamentals.iterrows():
                # 1. Fetch Sector explicitly (if row.get fails, use metadata fallback)
                raw_sector = row.get('Sector')
                if not raw_sector or raw_sector == "N/A":
                    # Fallback to the metadata we loaded at the start
                    meta_match = df_metadata[df_metadata['Symbol'] == row['Symbol']]['GICS Sector'].values
                    current_sector = meta_match[0] if len(meta_match) > 0 else "Uncategorized"
                else:
                    current_sector = raw_sector

                # 2. Build the exact dictionary required by Tab 3
                ticker_data = {
                    "Ticker": row['Symbol'],
                    "Price": float(row.get('Price', 0)),
                    "intrinsic_value": round(engine.calculate_intrinsic_value_dcf(
                        row['EPS'], 
                        row.get('GrowthRate', 0.05),
                        row.get('Shares_Outstanding', 1)
                    ), 2),
                    "roe": row.get('ROE', 0), # Match lowercase engine requirements
                    "Sector": current_sector, # Critical for Treemap 'path'
                    "Action": "HOLD",        # Default placeholders
                    "Logic": "N/A",
                    "Color": "gray",
                    "MOS": 0.0,
                    "AlphaScore": 0
                }
                
                # 3. Apply the brain logic
                rec, logic, color, mos = engine.generate_recommendation(ticker_data, st.session_state.macro)
                score = engine.calculate_alpha_score(ticker_data, st.session_state.macro, dynamic_ratings)
                
                # 4. Update with results
                ticker_data.update({
                    "Action": rec, 
                    "Logic": logic, 
                    "Color": color, 
                    "MOS": mos, 
                    "AlphaScore": score
                })
                
                st.session_state.final_report.append(ticker_data)
        st.success("Analysis Complete! Check Tab 3.")

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
        
        # --- 1. SECTOR HEATMAP (Restored) ---
        st.subheader("🗺️ Sector Value Heatmap")
        try:
            fig = px.treemap(
                df_alpha, 
                path=[px.Constant("Market"), 'Sector', 'Ticker'], 
                values='Price',
                color='AlphaScore',
                color_continuous_scale='RdYlGn', 
                color_continuous_midpoint=50,
                hover_data=['Action', 'MOS']
            )
            st.plotly_chart(fig, use_container_width=True)
        except:
            st.warning("Heatmap updating...")

        # --- 2. SECTOR INSIGHTS (The New Feature) ---
        sector_stats = df_alpha.groupby('Sector').agg({'AlphaScore': 'mean', 'Ticker': 'count'}).rename(columns={'Ticker': 'Count', 'AlphaScore': 'Avg Alpha'})
        st.dataframe(sector_stats.style.background_gradient(cmap='RdYlGn', subset=['Avg Alpha']).format("{:.1f}"), use_container_width=True)

        # --- 3. THE ALPHA GRID (Restored Styling) ---
        st.divider()
        grid_cols = st.columns(3) 
        for idx, row in df_alpha.reset_index().iterrows():
            with grid_cols[idx % 3]:
                # Dynamic Styling Logic
                action = row['Action']
                # Restore the high-visibility color logic
                card_color = "green" if "BUY" in action else "red" if "SELL" in action else "orange"
                
                with st.container(border=True):
                    # Card Header with Color-coded Action
                    st.markdown(f"### :{card_color}[{row['Ticker']} - {action}]")
                    st.markdown(f"**Alpha Score: {int(row['AlphaScore'])}/100**")
                    
                    # Logic & Strategy
                    st.caption(f"**Strategy:** {row['Logic']}")
                    
                    # DIVIDEND & QUALITY ANALYSIS (Restored)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.caption(f"Yield: {row.get('DivYield', 0):.2%}")
                        st.caption(f"Safety: {row.get('DivSafe', 'N/A')}")
                    with col2:
                        st.caption(f"ROE: {row.get('roe', 0):.1%}")
                        # Politician Tag
                        pol_bonus = engine.calculate_politician_bonus(row['Ticker'])
                        if pol_bonus > 0: st.markdown("🏛️ :green[**Congress Buy**]")

                    # VALUATION METRIC (Restored Price vs Intrinsic)
                    price_gap = row['intrinsic_value'] - row['Price']
                    st.metric(
                        label="Price vs Intrinsic", 
                        value=f"${row['Price']:.2f}", 
                        delta=f"{price_gap:+.2f} ({row['MOS']:.1%})",
                        delta_color="normal"
                    )
                    
                    # Conviction Bar
                    st.progress(row['AlphaScore'] / 100, text="Engine Conviction")
    else:
        st.info("Run Analysis in Tab 1 to see recommendations.")