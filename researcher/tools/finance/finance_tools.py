from typing import Optional

# This code defines a LangChain tool for analyzing financial data and computing various financial ratios.
from typing import Dict, Any, Optional
from langchain_core.tools import tool
@tool
def analyze_financials(
    revenue: float,
    gross_profit: float,
    operating_income: float,
    net_income: float,
    ebitda: float,
    current_assets: float,
    current_liabilities: float,
    inventory: float,
    total_debt: float,
    shareholders_equity: float,
    interest_expense: float
) -> Dict[str, Optional[float]]:
    """
    Compute profitability, liquidity, and solvency ratios from financial data.

    Args:
        revenue (float): Total revenue
        gross_profit (float): Gross profit
        operating_income (float): Operating income
        net_income (float): Net income
        ebitda (float): Earnings before interest, taxes, depreciation, and amortization
        current_assets (float): Current assets
        current_liabilities (float): Current liabilities
        inventory (float): Inventory value
        total_debt (float): Total debt
        shareholders_equity (float): Shareholders' equity
        interest_expense (float): Interest expense

    Returns:
        Dict[str, Optional[float]]: Dictionary with computed ratios.
    """
    def safe_divide_and_round(numerator: float, denominator: float, multiplier: float = 1) -> Optional[float]:
        """Helper function to safely divide and round to 2 decimal places."""
        if denominator == 0:
            return None
        return round((numerator / denominator) * multiplier, 2)
    
    return {
        "Gross Margin (%)": safe_divide_and_round(gross_profit, revenue, 100),
        "Operating Margin (%)": safe_divide_and_round(operating_income, revenue, 100),
        "Net Margin (%)": safe_divide_and_round(net_income, revenue, 100),
        "EBITDA Margin (%)": safe_divide_and_round(ebitda, revenue, 100),
        "Current Ratio": safe_divide_and_round(current_assets, current_liabilities),
        "Quick Ratio": safe_divide_and_round(current_assets - inventory, current_liabilities),
        "Debt-to-Equity Ratio": safe_divide_and_round(total_debt, shareholders_equity),
        "Interest Coverage Ratio": safe_divide_and_round(operating_income, interest_expense),
    }



# Sample test call
if __name__ == "__main__":
    # Sample financial data for a hypothetical company
    sample_data = {
        "revenue": 1000000.0,
        "gross_profit": 400000.0,
        "operating_income": 250000.0,
        "net_income": 180000.0,
        "ebitda": 300000.0,
        "current_assets": 500000.0,
        "current_liabilities": 200000.0,
        "inventory": 100000.0,
        "total_debt": 300000.0,
        "shareholders_equity": 800000.0,
        "interest_expense": 25000.0
    }
    
    # Test the LangChain tool
    result = analyze_financials.invoke(sample_data)
    
    print(result)