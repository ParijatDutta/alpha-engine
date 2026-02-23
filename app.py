import streamlit as st
import database
import pipeline

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

with tab2:
    st.subheader("Market & Legislative Intelligence")
    if st.button("Run Intel Scan"):
        with st.spinner("Fetching..."):
            macro = pipeline.fetch_macro_signals()
            trades = pipeline.fetch_politician_trades()
            
            c1, c2 = st.columns(2)
            c1.metric("VIX (Fear Index)", f"{macro['VIX']:.2f}")
            c2.metric("10Y Treasury", f"{macro['10Y_Yield']:.2f}%")
            
            if not trades.empty:
                st.write("Recent Congressional Activity:")
                # Using the new column names defined in pipeline.py
                display_cols = ['politician_name', 'asset', 'txType', 'value']
                st.dataframe(trades[display_cols], height=400, use_container_width=True)
            else:
                st.warning("No recent trades found or source is temporarily blocked.")