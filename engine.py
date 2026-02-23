import pandas as pd

def calculate_intrinsic_value_dcf(eps, growth_rate, discount_rate=0.09):
    total_pv = 0
    current_eps = eps
    for year in range(1, 11):
        current_eps *= (1 + growth_rate)
        pv = current_eps / ((1 + discount_rate) ** year)
        total_pv += pv
    terminal_value = (current_eps * 15) / ((1 + discount_rate) ** 10)
    return total_pv + terminal_value

def generate_recommendation(ticker_stats, macro):
    intrinsic = ticker_stats['intrinsic_value']
    price = ticker_stats['price']
    mos_pct = (intrinsic - price) / intrinsic if intrinsic > 0 else 0
    trend = ticker_stats.get('trend', "")
    div_yield = ticker_stats.get('div_yield', 0)

    # Base recommendation logic
    if mos_pct >= 0.30 and "Bullish" in trend:
        return "ELITE BUY", "Math & Momentum aligned.", "green", mos_pct
    elif mos_pct >= 0.30:
        return "VALUE PLAY", "Undervalued but trend is weak.", "blue", mos_pct
    elif div_yield > 0.04 and mos_pct > 0:
        return "INCOME BUY", "High yield with safety margin.", "orange", mos_pct
    elif mos_pct <= -0.15:
        return "AVOID", "Expensive; momentum fading.", "red", mos_pct
    else:
        return "NEUTRAL", "Fairly priced.", "gray", mos_pct

def calculate_alpha_score(ticker_stats, macro):
    """Generates a 0-100 score based on Value, Quality, and Macro risk."""
    score = 50 # Base score
    
    # 1. Valuation Component (up to +25 or -25)
    margin = (ticker_stats['intrinsic_value'] - ticker_stats['price']) / ticker_stats['price']
    score += min(max(margin * 100, -25), 25)
    
    # 2. Quality Component (ROE) (up to +15)
    if ticker_stats['roe'] > 0.20: score += 15
    elif ticker_stats['roe'] > 0.10: score += 5
    
    # 3. Macro Penalty (VIX)
    vix = macro.get('VIX', 20)
    if vix > 25: score -= 10
    if vix > 35: score -= 25
    
    return max(0, min(100, score))