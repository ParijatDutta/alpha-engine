import pandas as pd

def calculate_intrinsic_value(eps, bvps, growth_rate=0.05):
    """
    Combines Graham Number and a simple DCF-lite model.
    """
    if eps <= 0: return 0
    # Graham Number
    graham = (22.5 * eps * bvps)**0.5 if bvps > 0 else 0
    # DCF-lite: Price = EPS * (8.5 + 2g)
    dcf_lite = eps * (8.5 + 2 * (growth_rate * 100))
    return (graham + dcf_lite) / 2

def generate_recommendation(ticker_data, macro_data):
    """
    Logic-driven recommendation engine.
    """
    price = ticker_data.get('price', 0)
    intrinsic = ticker_data.get('intrinsic_value', 0)
    vix = macro_data.get('VIX', 20)
    
    # 1. Valuation Gap
    margin_of_safety = (intrinsic - price) / intrinsic if intrinsic > 0 else 0
    
    # 2. Recommendation Logic
    if vix > 30:
        return "AVOID (High Market Volatility)", "Market risk is too high for new entries."
    
    if margin_of_safety > 0.20:
        if ticker_data.get('roe', 0) > 0.15:
            return "STRONG BUY", f"Undervalued by {margin_of_safety:.1%}. High quality ROE."
        return "BUY", f"Good margin of safety ({margin_of_safety:.1%})."
    
    if margin_of_safety < -0.10:
        return "SELL / OVERVALUED", "Price significantly exceeds intrinsic value."
    
    return "HOLD", "Trading near fair value."

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