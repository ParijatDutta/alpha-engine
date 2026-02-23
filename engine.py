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