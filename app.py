import streamlit as st
import database

st.title("🏛️ Alpha Engine: S&P 500 Pulse")

# Initialize and load the static data
with st.spinner("Initializing S&P 500 Database..."):
    try:
        df_metadata = database.initialize_sp500()
        st.success(f"Database Ready: {len(df_metadata)} companies loaded.")
        
        # Display the static list for verification
        st.dataframe(df_metadata, use_container_width=True, height=400)
    except Exception as e:
        st.error(f"Database Error: {e}")

import pipeline

# Wrap intelligence in a container to prevent layout jumping
st.divider()
st.subheader("📊 Live Intelligence Pulse")

if st.button("Refresh Intelligence"):
    with st.spinner("Bypassing rate limits..."):
        # Fetch data
        macro = pipeline.fetch_macro_signals()
        trades = pipeline.fetch_politician_trades()
        
        # Display Metrics
        m1, m2 = st.columns(2)
        m1.metric("Market Volatility (VIX)", f"{macro['VIX']:.2f}")
        m2.metric("10Y Treasury Yield", f"{macro['10Y_Yield']:.2f}%")
        
        if not trades.empty:
            st.write("Recent Trades:")
            st.dataframe(trades[['politician', 'asset', 'txType', 'value']], height=300)

# 3. Add a footer to ensure the page has 'breathing room'
st.write("---")
st.caption("Alpha Engine v1.0 | Data cached to avoid compute burn.")