import pandas as pd

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

def calculate_alpha_score(ticker_stats, macro, dynamic_ratings):
    intrinsic = ticker_stats.get('Intrinsic', 0)
    price = ticker_stats.get('Price', 0)
    if intrinsic == 0: return 0
    
    mos = (intrinsic - price) / intrinsic
    sector = ticker_stats.get('Sector', 'General')
    
    # Apply the dynamic multiplier we fetched in the button click
    multiplier = dynamic_ratings.get(sector, 1.0)
    
    return round((mos * 100) * multiplier, 2)