import streamlit as st
import database

st.title("🏛️ Alpha Engine: S&P 500 Pulse")

# Initialize and load the static data
with st.spinner("Initializing S&P 500 Database..."):
    try:
        df_metadata = database.initialize_sp500()
        st.success(f"Database Ready: {len(df_metadata)} companies loaded.")
        
        # Display the static list for verification
        st.dataframe(df_metadata, use_container_width=True)
    except Exception as e:
        st.error(f"Database Error: {e}")

import pipeline

st.subheader("📊 Live Intelligence Pulse")
if st.button("Refresh Intelligence"):
    trades = pipeline.fetch_politician_trades()
    if not trades.empty:
        st.write("Recent Congressional Activity:")
        st.dataframe(trades, use_container_width=True)
    
    macro = pipeline.fetch_macro_signals()
    st.write(f"Market Volatility (VIX): {macro['VIX']:.2f}")