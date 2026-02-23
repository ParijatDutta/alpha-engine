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
    intrinsic = ticker_stats.get('intrinsic_value') or ticker_stats.get('Intrinsic', 0)
    price = ticker_stats.get('price') or ticker_stats.get('Price', 0)
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

def calculate_alpha_score(ticker_stats, macro, dynamic_ratings):
    # Core Math: Margin of Safety (MOS)
    mos = (ticker_stats['intrinsic_value'] - ticker_stats['price']) / ticker_stats['intrinsic_value']
    base_score = mos * 100
    
    # Sector Influence: Dynamic look-up
    sector = ticker_stats.get('Sector', "General")
    multiplier = dynamic_ratings.get(sector, 1.0)
    
    # Quality Filter: Bonus for high ROE
    roe_bonus = 5 if ticker_stats.get('roe', 0) > 0.20 else 0
    
    final_score = (base_score * multiplier) + roe_bonus
    return round(min(max(final_score, 0), 100), 2)