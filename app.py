import streamlit as st
import database
import pipeline
import engine

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
        with st.spinner("Analyzing S&P 500 fundamentals..."):
            # For now, we apply this to the first 10 for speed; 
            # later we will batch this to the database.
            results = []
            macro = pipeline.fetch_macro_signals()
            
            for index, row in df_metadata.head(10).iterrows():
                # Mocking fundamental data fetch for the demo
                # In Phase 5, we'll pull this from a cached fundamental file
                mock_ticker = {
                    'price': 150.0, 
                    'intrinsic_value': 185.0, 
                    'roe': 0.18
                }
                rec, reason = engine.generate_recommendation(mock_ticker, macro)
                results.append({"Ticker": row['Symbol'], "Action": rec, "Reason": reason})
                
            st.table(pd.DataFrame(results))

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