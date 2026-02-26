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

            # --- Inside Tab 1 Generate Recommendations Loop ---
            for _, row in fundamentals.iterrows():
                # 1. Fetch Sector explicitly (if row.get fails, use metadata fallback)
                raw_sector = row.get('Sector')
                if not raw_sector or raw_sector == "N/A":
                    # Fallback to the metadata we loaded at the start
                    meta_match = df_metadata[df_metadata['Symbol'] == row['Symbol']]['GICS Sector'].values
                    current_sector = meta_match[0] if len(meta_match) > 0 else "Uncategorized"
                else:
                    current_sector = raw_sector

                # 2. Build the exact dictionary required by Tab 3
                ticker_data = {
                    "Ticker": row['Symbol'],
                    "Price": float(row.get('Price', 0)),
                    "intrinsic_value": round(engine.calculate_intrinsic_value_dcf(
                        row['EPS'], 
                        row.get('GrowthRate', 0.05),
                        row.get('Shares_Outstanding', 1)
                    ), 2),
                    "roe": row.get('ROE', 0), # Match lowercase engine requirements
                    "Sector": current_sector, # Critical for Treemap 'path'
                    "Action": "HOLD",        # Default placeholders
                    "Logic": "N/A",
                    "Color": "gray",
                    "MOS": 0.0,
                    "AlphaScore": 0
                }
                
                # 3. Apply the brain logic
                rec, logic, color, mos = engine.generate_recommendation(ticker_data, st.session_state.macro)
                score = engine.calculate_alpha_score(ticker_data, st.session_state.macro, dynamic_ratings)
                
                # 4. Update with results
                ticker_data.update({
                    "Action": rec, 
                    "Logic": logic, 
                    "Color": color, 
                    "MOS": mos, 
                    "AlphaScore": score
                })
                
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
    if st.session_state.final_report:
        df_alpha = pd.DataFrame(st.session_state.final_report)
        
        # CLEANUP: Ensure numeric types and drop rows with missing hierarchical data
        df_alpha['Price'] = pd.to_numeric(df_alpha['Price'], errors='coerce')
        df_alpha['AlphaScore'] = pd.to_numeric(df_alpha['AlphaScore'], errors='coerce')
        
        # Fill any missing sectors to prevent the 'ValueError' in px.treemap
        df_alpha['Sector'] = df_alpha['Sector'].fillna("Uncategorized")
        
        # Drop rows where critical plotting data is missing
        df_alpha = df_alpha.dropna(subset=['Ticker', 'Sector', 'Price', 'AlphaScore'])

        st.subheader("🗺️ Sector Value Heatmap")
        
        try:
            fig = px.treemap(
                df_alpha, 
                path=[px.Constant("Market"), 'Sector', 'Ticker'], 
                values='Price',
                color='AlphaScore',
                color_continuous_scale='RdYlGn', 
                color_continuous_midpoint=50,
                hover_data=['Action', 'MOS', 'AlphaScore']
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Treemap pending: Data structure sync required. (Error: {e})")

        # --- SECTOR INSIGHT SUMMARY ---
        st.divider()
        st.subheader("📊 Sector Intelligence")
        
        # Calculate average scores per sector
        sector_stats = df_alpha.groupby('Sector').agg({
            'AlphaScore': 'mean',
            'Ticker': 'count'
        }).rename(columns={'Ticker': 'Stock Count', 'AlphaScore': 'Avg Alpha'}).sort_values('Avg Alpha', ascending=False)

        col_a, col_b = st.columns([1, 2])
        
        with col_a:
            st.write("**Top Sectors by Alpha**")
            sector_stats['Avg Alpha'] = pd.to_numeric(sector_stats['Avg Alpha'], errors='coerce')
    
            # Apply the styling
            styled_stats = sector_stats.style.background_gradient(
                cmap='RdYlGn', 
                subset=['Avg Alpha'],
                vmin=0, 
                vmax=100
            ).format({"Avg Alpha": "{:.1f}"})
            
            st.dataframe(styled_stats, use_container_width=True)

        with col_b:
            best_sector = sector_stats.index[0]
            avg_val = sector_stats['Avg Alpha'].iloc[0]
            st.info(f"💡 **Opportunity Found:** The **{best_sector}** sector is showing the highest relative strength with an average Alpha Score of **{avg_val:.1f}**. Consider deeper fundamental analysis here.")

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
                    col1.caption(f"ROE: {row['roe']:.1%}")
                    
                    # Display a Politician Icon if a bonus was applied
                    # We check if a bonus exists by recalculating (or you can store it in final_report)
                    pol_bonus = engine.calculate_politician_bonus(row['Ticker'])
                    if pol_bonus > 0:
                        col2.markdown("🏛️ **Politician Buy**")
                    elif pol_bonus < 0:
                        col2.markdown("📉 **Politician Sell**")

                    price_gap = row['intrinsic_value'] - row['Price']
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