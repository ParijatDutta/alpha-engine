import streamlit as st
import pandas as pd
import os
import database
import pipeline
import engine

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
        with st.spinner("Analyzing Fundamentals..."):
            # Fetch for top 20 to stay within memory/time limits
            tickers = df_metadata['Symbol'].head(20).tolist()
            fundamentals = database.get_enriched_data(tickers)
            st.session_state.macro = pipeline.fetch_macro_signals()
            
            # Clear and rebuild report in session state
            st.session_state.final_report = [] 
            for _, row in fundamentals.iterrows():
                intrinsic = engine.calculate_intrinsic_value_dcf(row['EPS'], row['GrowthRate'])
                ticker_stats = {'price': row['Price'], 'intrinsic_value': intrinsic, 'roe': row['ROE']}
                rec, reason = engine.generate_recommendation(ticker_stats, st.session_state.macro)
                
                st.session_state.final_report.append({
                    "Ticker": row['Symbol'], "Price": row['Price'], 
                    "Intrinsic": round(intrinsic, 2), "Action": rec, "Logic": reason,
                    "ROE": row['ROE']
                })
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
    st.header("🏛️ Intelligence Hub: Conviction Grid")
    
    if st.session_state.final_report:
        df_alpha = pd.DataFrame(st.session_state.final_report)
        
        # Scoring & Sorting
        df_alpha['Alpha Score'] = df_alpha.apply(
            lambda x: engine.calculate_alpha_score(
                {'price': x['Price'], 'intrinsic_value': x['Intrinsic'], 'roe': x['ROE']}, 
                st.session_state.macro
            ), axis=1
        )
        df_alpha = df_alpha.sort_values(by='Alpha Score', ascending=False)

        # GRID DISPLAY: 3 cards per row
        cols = st.columns(3) 
        for idx, row in df_alpha.iterrows():
            # Match the recommendation to a color
            rec, logic, color, mos = engine.generate_recommendation(
                {'intrinsic_value': row['Intrinsic'], 'price': row['Price']}, 
                st.session_state.macro
            )
            
            # Place card in rotating columns
            with cols[idx % 3]:
                with st.container(border=True):
                    st.markdown(f"### :{color}[{row['Ticker']}]")
                    st.metric("Price", f"${row['Price']}")
                    st.metric("Intrinsic", f"${row['Intrinsic']}", 
                              delta=f"{mos:.1%}", delta_color="normal")
                    
                    st.markdown(f"**{rec}**")
                    st.caption(f"MOS: {mos:.1%}")
                    
    else:
        st.info("Run analysis in Tab 1 to populate the Hub.")