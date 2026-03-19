#!/usr/bin/env python3
"""
Finance MCP Server for dr_ikechukwu_pa
======================================
A custom MCP server providing financial analysis tools.

Tools:
- calculate_investment_returns: Calculate compound interest and investment returns
- analyze_budget: Analyze income vs expenses
- get_exchange_rate: Get currency exchange rates
- get_company_financials: Get company financial data (mock)

Usage:
    pip install fastmcp
    python finance_mcp_server.py

Environment:
    Configure API keys for production (Alpha Vantage, etc.)
"""

from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("Finance Tools")

# Sample exchange rates (in production, fetch from API)
EXCHANGE_RATES = {
    ("USD", "EUR"): 0.92,
    ("USD", "GBP"): 0.79,
    ("USD", "JPY"): 149.50,
    ("USD", "NGN"): 1500.00,
    ("EUR", "USD"): 1.09,
    ("GBP", "USD"): 1.27,
    ("JPY", "USD"): 0.0067,
    ("NGN", "USD"): 0.00067,
}


@mcp.tool()
def calculate_investment_returns(
    principal: float,
    annual_rate: float,
    years: float,
    compounding_frequency: int = 12
) -> str:
    """Calculate compound interest and investment returns over time.
    
    Args:
        principal: Initial investment amount
        annual_rate: Annual interest rate (percentage)
        years: Number of years
        compounding_frequency: Times per year interest compounds (default: 12 monthly)
        
    Returns:
        Detailed investment projection with breakdown
    """
    if principal <= 0 or annual_rate <= 0 or years <= 0:
        return "Error: All values must be positive"
    
    rate_decimal = annual_rate / 100
    
    # Compound interest formula: A = P(1 + r/n)^(nt)
    amount = principal * (1 + rate_decimal / compounding_frequency) ** (compounding_frequency * years)
    total_interest = amount - principal
    
    # Calculate year-by-year breakdown
    yearly_data = []
    for year in range(1, int(years) + 1):
        year_amount = principal * (1 + rate_decimal / compounding_frequency) ** (compounding_frequency * year)
        yearly_data.append({
            "year": year,
            "amount": year_amount,
            "gain": year_amount - principal
        })
    
    output = f"Investment Projection\n"
    output += "=" * 50 + "\n\n"
    output += f"Principal: ${principal:,.2f}\n"
    output += f"Annual Rate: {annual_rate}%\n"
    output += f"Compounding: {compounding_frequency}x per year\n"
    output += f"Duration: {years} years\n\n"
    output += f"Final Amount: ${amount:,.2f}\n"
    output += f"Total Interest Earned: ${total_interest:,.2f}\n"
    output += f"Total Return: {(total_interest/principal*100):.1f}%\n\n"
    
    if yearly_data:
        output += "Yearly Breakdown:\n"
        for data in yearly_data[-5:]:  # Show last 5 years
            output += f"  Year {data['year']}: ${data['amount']:,.2f} (+${data['gain']:,.2f})\n"
    
    return output


@mcp.tool()
def analyze_budget(
    income: float,
    expenses: Dict[str, float]
) -> str:
    """Analyze income vs expenses and calculate savings rate.
    
    Args:
        income: Monthly or annual income
        expenses: Dictionary of expense categories and amounts
        
    Returns:
        Budget analysis with recommendations
    """
    if income <= 0:
        return "Error: Income must be positive"
    
    total_expenses = sum(expenses.values())
    savings = income - total_expenses
    savings_rate = (savings / income * 100) if income > 0 else 0
    
    # Determine financial health
    if savings_rate >= 20:
        health = "EXCELLENT"
        recommendation = "Great job! Consider investing surplus"
    elif savings_rate >= 10:
        health = "GOOD"
        recommendation = "Healthy savings rate, aim for 20%"
    elif savings_rate >= 0:
        health = "FAIR"
        recommendation = "Try to increase savings rate to 10%"
    else:
        health = "NEEDS ATTENTION"
        recommendation = "Expenses exceed income - review budget immediately"
    
    # Expense categories analysis
    expense_ratio = {}
    for category, amount in expenses.items():
        expense_ratio[category] = (amount / income * 100) if income > 0 else 0
    
    output = f"Budget Analysis\n"
    output += "=" * 50 + "\n\n"
    output += f"Total Income: ${income:,.2f}\n"
    output += f"Total Expenses: ${total_expenses:,.2f}\n"
    output += f"Savings: ${savings:,.2f}\n"
    output += f"Savings Rate: {savings_rate:.1f}%\n\n"
    output += f"Financial Health: {health}\n"
    output += f"Recommendation: {recommendation}\n\n"
    
    output += "Expense Breakdown:\n"
    for category, ratio in sorted(expense_ratio.items(), key=lambda x: x[1], reverse=True):
        output += f"  {category}: ${expenses[category]:,.2f} ({ratio:.1f}%)\n"
    
    # Identify high expenses
    high_expenses = [c for c, r in expense_ratio.items() if r > 30]
    if high_expenses:
        output += "\n⚠️ High expense categories (>30% of income):\n"
        for cat in high_expenses:
            output += f"  - {cat}\n"
    
    return output


@mcp.tool()
def get_exchange_rate(from_currency: str, to_currency: str) -> str:
    """Get currency exchange rate between two currencies.
    
    Args:
        from_currency: Source currency code (e.g., USD)
        to_currency: Target currency code (e.g., EUR)
        
    Returns:
        Exchange rate with conversion example
    """
    from_curr = from_currency.upper().strip()
    to_curr = to_currency.upper().strip()
    
    # Direct rate
    rate = EXCHANGE_RATES.get((from_curr, to_curr))
    
    # Try inverse if not found
    if rate is None:
        inverse_rate = EXCHANGE_RATES.get((to_curr, from_curr))
        if inverse_rate:
            rate = 1 / inverse_rate
    
    # Try via USD as intermediate
    if rate is None:
        from_usd = EXCHANGE_RATES.get((from_curr, "USD"))
        if from_usd is None:
            usd_from = EXCHANGE_RATES.get(("USD", from_curr))
            from_usd = 1/usd_from if usd_from else None
        to_usd = EXCHANGE_RATES.get((to_curr, "USD"))
        if to_usd is None:
            usd_to = EXCHANGE_RATES.get(("USD", to_curr))
            to_usd = 1/usd_to if usd_to else None
        if from_usd and to_usd:
            rate = to_usd / from_usd
    
    if rate is None:
        return f"Exchange rate not available for {from_curr} to {to_curr}"
    
    # Example conversion
    example_amount = 100
    converted = example_amount * rate
    
    output = f"Currency Exchange Rate\n"
    output += "=" * 50 + "\n\n"
    output += f"From: {from_curr}\n"
    output += f"To: {to_curr}\n"
    output += f"Rate: 1 {from_curr} = {rate:.4f} {to_curr}\n\n"
    output += f"Example: {example_amount} {from_curr} = {converted:.2f} {to_curr}\n\n"
    output += "Note: Rates are approximate. Verify with live market rates."
    
    return output


@mcp.tool()
def get_company_financials(symbol: str) -> str:
    """Get company financial data and metrics.
    
    Args:
        symbol: Stock ticker symbol (e.g., AAPL)
        
    Returns:
        Company financial summary with key metrics
    """
    # In production, connect to financial data API (Alpha Vantage, FMP, etc.)
    # This is mock data for demonstration
    
    symbol_upper = symbol.upper().strip()
    
    # Mock financial data
    financials = {
        "AAPL": {
            "name": "Apple Inc.",
            "price": 178.50,
            "pe_ratio": 28.5,
            "market_cap": "2.8T",
            "dividend_yield": 0.52,
            "eps": 6.26,
            "beta": 1.28
        },
        "GOOGL": {
            "name": "Alphabet Inc.",
            "price": 141.25,
            "pe_ratio": 24.2,
            "market_cap": "1.8T",
            "dividend_yield": 0.0,
            "eps": 5.84,
            "beta": 1.05
        },
        "MSFT": {
            "name": "Microsoft Corporation",
            "price": 378.90,
            "pe_ratio": 35.1,
            "market_cap": "2.8T",
            "dividend_yield": 0.75,
            "eps": 10.80,
            "beta": 0.91
        }
    }
    
    data = financials.get(symbol_upper)
    
    if not data:
        return f"Financial data for {symbol_upper} not available.\n\nNote: Connect to Alpha Vantage or FMP API for live data."
    
    output = f"Company Financials: {data['name']} ({symbol_upper})\n"
    output += "=" * 50 + "\n\n"
    output += f"Current Price: ${data['price']}\n"
    output += f"P/E Ratio: {data['pe_ratio']}\n"
    output += f"Market Cap: ${data['market_cap']}\n"
    output += f"Dividend Yield: {data['dividend_yield']}%\n"
    output += f"EPS: ${data['eps']}\n"
    output += f"Beta: {data['beta']}\n\n"
    output += "Note: Connect to financial API for real-time data"
    
    return output


@mcp.tool()
def analyze_investment_portfolio(
    holdings: List[Dict[str, Any]]
) -> str:
    """Analyze an investment portfolio for diversification and risk.
    
    Args:
        holdings: List of holdings with symbol, value, and asset_class
        
    Returns:
        Portfolio analysis with recommendations
    """
    if not holdings:
        return "Error: No holdings provided"
    
    # Calculate total value
    total_value = sum(h.get("value", 0) for h in holdings)
    
    if total_value <= 0:
        return "Error: Portfolio value must be positive"
    
    # Group by asset class
    by_class = {}
    for h in holdings:
        asset_class = h.get("asset_class", "Other")
        if asset_class not in by_class:
            by_class[asset_class] = []
        by_class[asset_class].append(h)
    
    # Calculate allocation percentages
    allocation = {}
    for asset_class, assets in by_class.items():
        class_value = sum(a.get("value", 0) for a in assets)
        allocation[asset_class] = (class_value / total_value * 100)
    
    risk_level = "BALANCED"  # Default
    risk_score = 0  # Initialize risk score
    recommendations = []
    
    # Risk assessment
    if allocation.get("Stocks", 0) > 80:
        risk_score += 2
        recommendations.append("Consider reducing stock allocation for better diversification")
    
    if allocation.get("Bonds", 0) < 20:
        risk_score += 1
        recommendations.append("Consider adding bonds for stability")
    
    if len(by_class) < 3:
        risk_score += 2
        recommendations.append("Portfolio lacks diversification across asset classes")
    
    if risk_score == 0:
        risk_level = "BALANCED"
        recommendations.append("Good diversification across asset classes")
    
    output = f"Portfolio Analysis\n"
    output += "=" * 50 + "\n\n"
    output += f"Total Value: ${total_value:,.2f}\n\n"
    
    output += "Asset Allocation:\n"
    for asset_class, pct in sorted(allocation.items(), key=lambda x: x[1], reverse=True):
        class_value = sum(h.get("value", 0) for h in by_class[asset_class])
        output += f"  {asset_class}: {pct:.1f}% (${class_value:,.2f})\n"
    
    output += f"\nRisk Level: {risk_level}\n\n"
    
    if recommendations:
        output += "Recommendations:\n"
        for rec in recommendations:
            output += f"  • {rec}\n"
    
    return output


if __name__ == "__main__":
    print("Starting Finance MCP Server...")
    print("Tools available: calculate_investment_returns, analyze_budget,")
    print("                 get_exchange_rate, get_company_financials,")
    print("                 analyze_investment_portfolio")
    mcp.run(transport="stdio")
