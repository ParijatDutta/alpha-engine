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
            for _, row in fundamentals.iterrows():
                # Use .get() to avoid KeyErrors if one fetch fails
                ticker_data = {
                    "Ticker": row['Symbol'],
                    "Price": row['Price'],
                    "intrinsic_value": round(engine.calculate_intrinsic_value_dcf(row['EPS'], row.get('GrowthRate', 0.05),row.get('Shares_Outstanding', 1)), 2),
                    "ROE": row.get('ROE', 0),
                    "DivYield": row.get('DivYield', 0),
                    "Trend": row.get('Trend', "N/A"), 
                    "Sector": row.get('Sector', "General"),
                    "FCF_Yield": row.get('FCF_Yield', 0),    
                    "DivSafe": row.get('DivSafe', 'N/A')
                }
                
                # Get recommendation using the new multi-factor brain
                rec, logic, color, mos = engine.generate_recommendation(ticker_data, st.session_state.macro)
                score = engine.calculate_alpha_score(ticker_data, st.session_state.macro, dynamic_ratings)
                
                # Store everything
                ticker_data.update({"Action": rec, "Logic": logic, "Color": color, "MOS": mos, "AlphaScore": score})
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
        # Convert the session report to a DataFrame
        df_alpha = pd.DataFrame(st.session_state.final_report)

        # --- 1. INTEGRATE ALPHA SCORE LOGIC ---
        # Apply the new scoring logic from engine.py using valuation, macro, and ticker symbol
        df_alpha['AlphaScore'] = df_alpha.apply(
            lambda x: engine.calculate_alpha_score(
                {'price': x['Price'], 'intrinsic_value': x['intrinsic_value'], 'roe': x['ROE']}, 
                st.session_state.macro,
                x['Ticker']
            ), axis=1
        )

        # Add a column for Margin of Safety (MOS) percentage for the Treemap
        df_alpha['MOS'] = (df_alpha['intrinsic_value'] - df_alpha['Price']) / df_alpha['Price']
        df_alpha = df_alpha.dropna(subset=['Sector', 'Price', 'AlphaScore'])

        st.subheader("🗺️ Sector Value Heatmap")
        st.caption("Size = Price Weight | Color = Alpha Score (Green = High Opportunity)")
        
        # Build the treemap using AlphaScore as the color metric
        fig = px.treemap(
            df_alpha, 
            path=[px.Constant("Market"), 'Sector', 'Ticker'], 
            values='Price',
            color='AlphaScore',
            color_continuous_scale='RdYlGn', 
            color_continuous_midpoint=50, # 50 is the neutral base in our engine
            hover_data={
                'Action': True,
                'Intrinsic': ':$.2f',
                'AlphaScore': ':.0f',
                'MOS': ':.1%'
            }
        )
        
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

        # --- 2. SEARCH & FILTER ---
        st.divider()
        search_query = st.text_input("🔍 Search Ticker or Sector", "")
        sort_by = st.selectbox("Sort by:", ["Alpha Score", "Margin of Safety", "Ticker"])

        # Sorting Logic
        if sort_by == "Alpha Score":
            df_alpha = df_alpha.sort_values(by='AlphaScore', ascending=False)
        elif sort_by == "Margin of Safety":
            df_alpha = df_alpha.sort_values(by='MOS', ascending=False)
        else:
            df_alpha = df_alpha.sort_values(by='Ticker')

        # Filter the dataframe
        if search_query:
            df_alpha = df_alpha[
                df_alpha['Ticker'].str.contains(search_query.upper()) | 
                df_alpha['Sector'].str.contains(search_query.title())
            ]
            
        # --- 3. ALPHA GRID CARDS ---
        grid_cols = st.columns(3) 
        for idx, row in df_alpha.reset_index().iterrows():
            with grid_cols[idx % 3]:
                # Determine recommendation text and color
                # (Note: we use the Action/Logic already stored or recalculate if needed)
                with st.container(border=True):
                    # Card Header - Color code based on Action
                    header_color = "green" if "BUY" in row['Action'] else "red" if "SELL" in row['Action'] else "gray"
                    st.markdown(f"### :{header_color}[{row['Ticker']}]")
                    st.markdown(f"**Score: {int(row['AlphaScore'])}/100**")
                    
                    st.caption(f"**Strategy:** {row['Logic']}")
                    
                    # Core Metrics
                    col1, col2 = st.columns(2)
                    col1.caption(f"ROE: {row['ROE']:.1%}")
                    
                    # Display a Politician Icon if a bonus was applied
                    # We check if a bonus exists by recalculating (or you can store it in final_report)
                    pol_bonus = engine.calculate_politician_bonus(row['Ticker'])
                    if pol_bonus > 0:
                        col2.markdown("🏛️ **Politician Buy**")
                    elif pol_bonus < 0:
                        col2.markdown("📉 **Politician Sell**")

                    price_gap = row['Intrinsic'] - row['Price']
                    st.metric(
                        label="Price vs Intrinsic", 
                        value=f"${row['Price']:.2f}", 
                        delta=round(price_gap, 2),
                        delta_color="normal"
                    )
                    
                    # Progress bar based on Alpha Score
                    st.progress(row['AlphaScore'] / 100)
    else:
        st.info("Run Analysis in Tab 1 to populate the Intelligence Hub.")