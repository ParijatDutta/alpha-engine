import pandas as pd
import os

def calculate_politician_bonus(ticker, trades_file="daily_trades.csv"):
    """Scans the daily trades file for politician activity."""
    if not os.path.exists(trades_file):
        return 0
    try:
        df = pd.read_csv(trades_file)
        # Handle potential column name variations from different scrapers
        col = 'asset' if 'asset' in df.columns else 'symbol'
        ticker_trades = df[df[col].str.contains(ticker, na=False, case=False)]
        
        if ticker_trades.empty:
            return 0
            
        bonus = 0
        for _, trade in ticker_trades.iterrows():
            tx_type = str(trade.get('txType', '')).lower()
            if 'buy' in tx_type or 'purchase' in tx_type:
                bonus += 10 
            elif 'sell' in tx_type:
                bonus -= 5  
        return max(-15, min(20, bonus))
    except:
        return 0

def calculate_intrinsic_value_dcf(eps, growth_rate, shares_outstanding):
    """5-Year Exit Multiplier DCF."""
    if eps <= 0: return 0
    
    discount_rate = 0.10
    terminal_multiple = 20
    years = 5
    
    # Project future earnings and discount back
    future_eps = eps * ((1 + growth_rate) ** years)
    terminal_value = future_eps * terminal_multiple
    intrinsic_value = terminal_value / ((1 + discount_rate) ** years)
    
    return round(intrinsic_value, 2)

def generate_recommendation(ticker_data, macro):
    """
    Determines Action and specific Buy/Sell price targets.
    Factors in Politician activity to adjust thresholds.
    """
    price = float(ticker_data.get('Price', 0))
    iv = float(ticker_data.get('intrinsic_value', 0))
    ticker = ticker_data.get('Ticker', 'Unknown')
    
    # Calculate Politician Influence
    pol_bonus = calculate_politician_bonus(ticker)
    
    # Thresholds (Standard is 15% Margin of Safety)
    # If politicians are buying, we reduce the required MOS by 5-10%
    buy_threshold = 0.85 + (pol_bonus / 200) 
    sell_threshold = 1.15 + (pol_bonus / 200)
    
    buy_at = round(iv * buy_threshold, 2)
    sell_at = round(iv * sell_threshold, 2)
    mos_pct = (iv - price) / iv if iv > 0 else 0

    # Logic Engine with Politician Awareness
    if price <= buy_at:
        action = "STRONG BUY"
        color = "green"
        pol_msg = " + Hill Support" if pol_bonus > 0 else ""
        logic = f"Undervalued. Entry below ${buy_at}{pol_msg}."
    elif price > sell_at:
        action = "SELL"
        color = "red"
        logic = f"Overvalued. Target exit above ${sell_at}."
    elif pol_bonus >= 10 and price < iv:
        action = "CONGRESSIONAL BUY"
        color = "green"
        logic = f"Politician accumulation detected below ${iv}."
    else:
        action = "HOLD"
        color = "orange"
        logic = f"Fairly Valued. Buy < ${buy_at} | Sell > ${sell_at}."

    return action, logic, color, mos_pct, buy_at, sell_at

def calculate_alpha_score(ticker_stats, macro, ticker_symbol):
    """Final 0-100 Intelligence Score."""
    score = 50 
    price = ticker_stats.get('Price', 0)
    intrinsic = ticker_stats.get('intrinsic_value', 0)
    roe = ticker_stats.get('roe', 0)

    # 1. Valuation Component
    if intrinsic > 0 and price > 0:
        margin = (intrinsic - price) / price
        score += min(max(margin * 100, -25), 25)
    
    # 2. Quality & Macro
    if roe > 0.15: score += 15
    if macro.get('VIX', 20) > 25: score -= 10
    
    # 3. Politician Bonus (Direct Impact)
    score += calculate_politician_bonus(ticker_symbol)
    
    return int(max(0, min(100, score)))