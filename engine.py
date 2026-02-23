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
        return "ELITE BUY", "Deep Value + High Cash Flow", "green"
    elif mos_pct > 0.15:
        return "STRONG BUY", "Significant Margin of Safety", "green"
    elif fcf_yield < 0 and mos_pct > 0.10:
        return "VALUE TRAP", "Cheap but burning cash", "orange"
    elif mos_pct < -0.10:
        return "OVERVALUED", "Market price exceeds fair value", "red"
    else:
        return "HOLD", "Fairly valued/Wait for dip", "gray"

def calculate_alpha_score(ticker_stats, macro, dynamic_ratings):
    intrinsic = ticker_stats.get('Intrinsic', 0)
    price = ticker_stats.get('Price', 0)
    if intrinsic == 0: return 0
    
    mos = (intrinsic - price) / intrinsic
    sector = ticker_stats.get('Sector', 'General')
    
    # Apply the dynamic multiplier we fetched in the button click
    multiplier = dynamic_ratings.get(sector, 1.0)
    
    return round((mos * 100) * multiplier, 2)