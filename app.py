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

#st.subheader("📊 Live Intelligence Pulse")
#if st.button("Refresh Intelligence"):
#    trades = pipeline.fetch_politician_trades()
#    if not trades.empty:
#        st.write("Recent Congressional Activity:")
#        st.dataframe(trades, use_container_width=True)
#    
#    macro = pipeline.fetch_macro_signals()
#    st.write(f"Market Volatility (VIX): {macro['VIX']:.2f}")

# Wrap intelligence in a container to prevent layout jumping
with st.container():
    st.divider()
    st.subheader("📊 Live Intelligence Pulse")
    
    if st.button("Refresh Intelligence"):
        with st.spinner("Scanning Capitol Hill & Macro signals..."):
            trades = pipeline.fetch_politician_trades()
            macro = pipeline.fetch_macro_signals()
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.metric("Market Volatility (VIX)", f"{macro['VIX']:.2f}")
                st.metric("10Y Treasury Yield", f"{macro['10Y_Yield']:.2f}%")
            
            with col2:
                if not trades.empty:
                    st.write("Recent Congressional Trades:")
                    st.dataframe(trades[['politician', 'asset', 'txType', 'value']], use_container_width=True)

# Add empty space at the bottom to force scrollability
st.markdown("<br><br><br>", unsafe_allow_html=True)