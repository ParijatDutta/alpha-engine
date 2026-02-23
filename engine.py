import pandas as pd

def calculate_intrinsic_value_dcf(eps, growth_rate, discount_rate=0.09):
    """
    Buffett-style DCF: Sum of 10-year projected earnings discounted to PV.
    """
    total_pv = 0
    current_eps = eps
    for year in range(1, 11):
        # Project future EPS
        current_eps *= (1 + growth_rate)
        # Discount to Present Value
        pv = current_eps / ((1 + discount_rate) ** year)
        total_pv += pv
    
    # Terminal Value (Year 10 price assuming 15x multiple)
    terminal_value = (current_eps * 15) / ((1 + discount_rate) ** 10)
    return total_pv + terminal_value

def generate_recommendation(ticker_stats, macro):
    intrinsic = ticker_stats['intrinsic_value']
    price = ticker_stats['price']
    
    # Margin of Safety (MOS) Calculation
    mos_price = intrinsic * 0.70  # 30% discount
    overvalued_price = intrinsic * 1.15 # 15% premium
    
    if price <= mos_price:
        return "STRONG BUY", f"Buy if price is below ${mos_price:.2f}. (30% Margin of Safety)"
    elif price <= intrinsic:
        return "BUY / FAIR VALUE", f"Intrinsic value is ${intrinsic:.2f}."
    elif price >= overvalued_price:
        return "SELL / TAKE PROFIT", f"Significantly overvalued. Exit above ${overvalued_price:.2f}."
    else:
        return "HOLD", "Trading within fair value range."

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