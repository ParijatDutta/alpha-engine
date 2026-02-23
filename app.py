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