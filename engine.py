import pandas as pd
import os

def calculate_politician_bonus(ticker, trades_file="daily_trades.csv"):
    """Scans the daily trades file for politician activity on a specific ticker."""
    if not os.path.exists(trades_file):
        return 0
    
    try:
        df = pd.read_csv(trades_file)
        # Filter trades for this specific ticker
        # Note: Capitol Trades columns are usually 'asset' or 'symbol'
        ticker_trades = df[df['asset'].str.contains(ticker, na=False, case=False)]
        
        if ticker_trades.empty:
            return 0
            
        bonus = 0
        for _, trade in ticker_trades.iterrows():
            tx_type = str(trade.get('txType', '')).lower()
            if 'buy' in tx_type or 'purchase' in tx_type:
                bonus += 10 # Bonus for "Smart Money" following
            elif 'sell' in tx_type:
                bonus -= 5  # Penalty for exits
        
        return max(-15, min(20, bonus)) # Cap the bonus at +20 or -15
    except:
        return 0

def calculate_intrinsic_value_dcf(eps, growth_rate, shares_outstanding):
    if eps <= 0 or shares_outstanding <= 0:
        return 0
    
    # 1. Project Earnings for 5 years
    # 2. Terminal Value: Assume we sell the company at year 5 for 20x earnings
    # 3. Discount everything back at 10% (standard hurdle rate)
    
    discount_rate = 0.10
    terminal_multiple = 20
    years = 5
    
    # Calculate Year 5 Earnings
    future_eps = eps * ((1 + growth_rate) ** years)
    
    # Calculate Terminal Value per share
    terminal_value = future_eps * terminal_multiple
    
    # Discount Terminal Value back to today
    intrinsic_value = terminal_value / ((1 + discount_rate) ** years)
    
    return round(intrinsic_value, 2)

def generate_recommendation(ticker_stats, macro):
    # Use .get to check both naming conventions to be safe
    intrinsic = ticker_stats.get('Intrinsic', 0)
    price = ticker_stats.get('Price', 0)
    fcf_yield = ticker_stats.get('FCF_Yield', 0)
    div_safe = ticker_stats.get('DivSafe', "")

    mos_pct = (intrinsic - price) / intrinsic if intrinsic > 0 else 0

    # 2026 Logic: ELITE status requires MOS > 30% and Bullish Trend
    trend = ticker_stats.get('Trend', "")
    
    # 2026 'Quality' Logic
    if mos_pct > 0.25 and fcf_yield > 0.08:
        return "ELITE BUY", "Deep Value + High Cash Flow", "green", mos_pct
    elif mos_pct > 0.15:
        return "STRONG BUY", "Significant Margin of Safety", "green", mos_pct
    elif fcf_yield < 0 and mos_pct > 0.10:
        return "VALUE TRAP", "Cheap but burning cash", "orange", mos_pct
    elif mos_pct < -0.10:
        return "OVERVALUED", "Market price exceeds fair value", "red", mos_pct
    else:
        return "HOLD", "Fairly valued/Wait for dip", "gray", mos_pct

def calculate_alpha_score(ticker_stats, macro, ticker_symbol):
    """Generates a 0-100 score including valuation, macro, and politician bonus."""
    score = 50 # Base
    
    # 1. Valuation Gap (Up to +/- 25)
    margin = (ticker_stats['intrinsic_value'] - ticker_stats['price']) / ticker_stats['price']
    score += min(max(margin * 100, -25), 25)
    
    # 2. Quality (ROE) (Up to +15)
    if ticker_stats.get('roe', 0) > 0.15: score += 15
    
    # 3. Macro Penalty (VIX)
    vix = macro.get('VIX', 20)
    if vix > 25: score -= 10
    
    # 4. POLITICIAN BONUS (NEW)
    pol_bonus = calculate_politician_bonus(ticker_symbol)
    score += pol_bonus
    
    return max(0, min(100, score))