import pandas as pd
import os

def calculate_politician_bonus(ticker, trades_file="daily_trades.csv"):
    if not os.path.exists(trades_file): return 0
    try:
        df = pd.read_csv(trades_file)
        col = 'asset' if 'asset' in df.columns else 'symbol'
        ticker_trades = df[df[col].str.contains(ticker, na=False, case=False)]
        if ticker_trades.empty: return 0
        
        bonus = 0
        for _, trade in ticker_trades.iterrows():
            tx_type = str(trade.get('txType', '')).lower()
            if 'buy' in tx_type or 'purchase' in tx_type: bonus += 10 
            elif 'sell' in tx_type: bonus -= 5  
        return max(-15, min(20, bonus))
    except: return 0

def calculate_intrinsic_value_dcf(eps, growth_rate, shares_outstanding=1):
    """
    Standardized Graham Formula. 
    Expects growth_rate as decimal (0.05 for 5%).
    """
    if eps <= 0: return 0
    
    # GUARDRAIL: Cap growth at 20% to prevent infinite valuations
    g = min(growth_rate, 0.20) 
    
    # Graham Formula: V = (EPS * (8.5 + 2g_as_whole_number) * 4.4) / 4.5
    # g * 100 converts 0.05 to 5
    yield_aaa = 4.5
    intrinsic_value = (eps * (8.5 + (2 * (g * 100))) * 4.4) / yield_aaa
    
    return round(intrinsic_value, 2)

def generate_recommendation(ticker_data, macro):
    """
    Determines action using normalized MOS (decimal).
    Returns: action, logic, color, mos, buy_at, sell_at
    """
    price = float(ticker_data.get('Price', 0))
    iv = float(ticker_data.get('intrinsic_value', 0))
    ticker = ticker_data.get('Ticker', 'Unknown')
    
    if price <= 0 or iv <= 0:
        return "N/A", "Insufficient Data", "gray", 0, 0, 0

    pol_bonus = calculate_politician_bonus(ticker)
    
    # 15% Standard Margin of Safety, adjusted by politician bonus
    # A +20 bonus lowers the required discount to 5%
    buy_threshold = 0.85 + (pol_bonus / 200) 
    buy_at = round(iv * buy_threshold, 2)
    sell_at = round(iv * 1.15, 2)
    
    mos = (iv - price) / iv

    if price <= buy_at:
        return "STRONG BUY", f"Target Entry: ${buy_at}", "green", mos, buy_at, sell_at
    elif price > sell_at:
        return "SELL", f"Target Exit: ${sell_at}", "red", mos, buy_at, sell_at
    else:
        return "HOLD", f"Wait for ${buy_at}", "orange", mos, buy_at, sell_at

def calculate_alpha_score(ticker_stats, macro, ticker_symbol):
    score = 50 
    price = float(ticker_stats.get('Price', 0))
    intrinsic = float(ticker_stats.get('intrinsic_value', 0))
    # Ensure ROE is treated as decimal (0.15 instead of 15.0)
    roe = float(ticker_stats.get('roe', 0))
    if roe > 1: roe = roe / 100 # Emergency fix for 6000% errors

    if intrinsic > 0 and price > 0:
        mos = (intrinsic - price) / intrinsic
        score += min(max(mos * 100, -25), 25)
    
    if roe > 0.15: score += 15
    if macro.get('VIX', 20) > 25: score -= 10
    score += calculate_politician_bonus(ticker_symbol)
    
    return int(max(0, min(100, score)))