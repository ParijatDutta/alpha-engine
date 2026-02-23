import streamlit as st
import database
import pipeline
import engine
import pandas as pd

st.set_page_config(page_title="Alpha Engine", layout="wide")

# Force CSS to fix scrolling on Chromebooks
st.markdown("""
    <style>
    .main .block-container {
        overflow: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏛️ Alpha Engine: S&P 500 Pulse")

# Load Tickers
with st.spinner("Loading Database..."):
    df_metadata = database.initialize_sp500()

# Use tabs to organize data and keep the page 'short' (fixes scrolling)
tab1, tab2 = st.tabs(["🎯 Core Screener", "🔭 Live Intelligence"])

with tab1:
    st.subheader("S&P 500 Universe")
    st.dataframe(df_metadata, use_container_width=True, height=450)
    if st.button("Generate Recommendations"):
        with st.spinner("Fetching real-time fundamentals..."):
            # 1. Get fundamental data
            tickers = df_metadata['Symbol'].tolist()
            fundamentals = database.get_enriched_data(tickers)
            
            # 2. Get macro context
            macro = pipeline.fetch_macro_signals()
            
            # 3. Run the Engine
            final_report = []
            for _, row in fundamentals.iterrows():
                # Calculate intrinsic value using our Phase 4 engine
                intrinsic = engine.calculate_intrinsic_value(row['EPS'], row['BVPS'])
                
                ticker_stats = {
                    'price': row['Price'],
                    'intrinsic_value': intrinsic,
                    'roe': row['ROE']
                }
                
                rec, reason = engine.generate_recommendation(ticker_stats, macro)
                final_report.append({
                    "Ticker": row['Symbol'],
                    "Price": row['Price'],
                    "Intrinsic": round(intrinsic, 2),
                    "Action": rec,
                    "Logic": reason
                })
                
            st.subheader("🚀 Alpha Recommendations")
            st.dataframe(pd.DataFrame(final_report), use_container_width=True)

with tab2:
    st.subheader("🔭 Live Intelligence Scan")
    if st.button("Run Intel Scan"):
        with st.spinner("Bypassing security protocols..."):
            macro = pipeline.fetch_macro_signals()
            trades = pipeline.fetch_politician_trades()
            
            # Show Macro first
            c1, c2 = st.columns(2)
            c1.metric("VIX Index", f"{macro['VIX']:.2f}")
            c2.metric("10Y Treasury", f"{macro['10Y_Yield']:.2f}%")
            
            # Show Trades
            if not trades.empty:
                st.write("Recent Capitol Trades (S&P 500 Index):")
                # Show top 10 trades to save vertical space/memory
                st.dataframe(trades.head(10), use_container_width=True, height=400)
            else:
                st.error("Access Denied. Capitol Trades blocked the cloud IP. Try again in 5 mins.")