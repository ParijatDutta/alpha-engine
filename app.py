import streamlit as st
import pandas as pd
import database
import pipeline
import engine

# --- 1. INITIALIZE SESSION STATE ---
if 'final_report' not in st.session_state:
    st.session_state.final_report = []
if 'macro' not in st.session_state:
    st.session_state.macro = {"VIX": 20.0, "10Y_Yield": 4.0}

st.title("🏛️ Alpha Engine")

df_metadata = database.initialize_sp500()
tab1, tab2, tab3 = st.tabs(["🎯 Core Screener", "🔭 Live Intelligence", "🏛️ Intelligence Hub"])

with tab1:
    st.subheader("S&P 500 Universe")
    st.dataframe(df_metadata, use_container_width=True, height=300)
    
    if st.button("Generate Recommendations"):
        with st.spinner("Analyzing..."):
            tickers = df_metadata['Symbol'].head(20).tolist()
            fundamentals = database.get_enriched_data(tickers)
            st.session_state.macro = pipeline.fetch_macro_signals()
            
            # Save to session_state so Tab 3 can see it
            st.session_state.final_report = [] 
            for _, row in fundamentals.iterrows():
                intrinsic = engine.calculate_intrinsic_value(row['EPS'], row['BVPS'])
                ticker_stats = {'price': row['Price'], 'intrinsic_value': intrinsic, 'roe': row['ROE']}
                rec, reason = engine.generate_recommendation(ticker_stats, st.session_state.macro)
                
                st.session_state.final_report.append({
                    "Ticker": row['Symbol'], "Price": row['Price'], 
                    "Intrinsic": round(intrinsic, 2), "Action": rec, "Logic": reason
                })
        st.success("Analysis Complete! Head to Intelligence Hub.")

with tab3:
    st.header("Top Alpha Signals")
    if st.session_state.final_report:
        df_alpha = pd.DataFrame(st.session_state.final_report)
        # (Rest of your scoring logic here...)
        st.dataframe(df_alpha)
    else:
        st.info("Run 'Generate Recommendations' in the first tab to see data here.")