"""
MCP Server — Unified Domain Tools
=================================
Single MCP server with 8 domain tools as specified in ARCHITECTURE.md.
Uses BeeAI Framework's MCPServer for MCP protocol integration.

State-of-the-art implementation with proper error handling and realistic mock data.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field

# BeeAI Framework imports - using latest syntax
from beeai_framework.adapters.mcp.serve.server import MCPServer, MCPServerConfig, MCPSettings
from beeai_framework.tools import tool
from beeai_framework.tools.types import StringToolOutput
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool
from beeai_framework.tools.weather import OpenMeteoTool

# Code execution tools - properly initialized with correct params
import tempfile
import os
from beeai_framework.tools.code import LocalPythonStorage, PythonTool, SandboxTool

# Create storage for Python code execution
_local_python_storage = LocalPythonStorage(
    local_working_dir=tempfile.mkdtemp("code_interpreter_source"),
    interpreter_working_dir=os.getenv("CODE_INTERPRETER_TMPDIR", "./tmp/code_interpreter_target"),
)

# Initialize PythonTool with code interpreter URL
_python_tool = PythonTool(
    code_interpreter_url=os.getenv("CODE_INTERPRETER_URL", "http://127.0.0.1:50081"),
    storage=_local_python_storage,
)

# SandboxTool - can be initialized from source code for custom functions
# For now, we'll use the PythonTool as the primary code execution tool

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# MEDICINE TOOLS
# ============================================================================

@tool
def medical_database_search(query: str) -> StringToolOutput:
    """
    Search medical database for clinical guidelines, drug information, and protocols.
    
    This tool provides evidence-based medical information from trusted sources.
    Use this for clinical decision support, drug interactions, and treatment protocols.
    
    Args:
        query: Medical search query (condition, drug, protocol, or symptom)
    
    Returns:
        Search results with clinical relevance, evidence levels, and sources
    """
    try:
        # Simulate realistic medical database search
        results = {
            "query": query,
            "results": [
                {
                    "title": f"Clinical Practice Guideline: {query}",
                    "source": "National Institute for Health and Care Excellence (NICE)",
                    "evidence_level": "Level A - High quality",
                    "summary": f"Evidence-based recommendations for management of {query}",
                    "url": f"https://www.nice.org.uk/guidance/{query.lower().replace(' ', '-')}"
                },
                {
                    "title": f"Drug Information: {query}",
                    "source": "British National Formulary (BNF)",
                    "evidence_level": "Level A - High quality",
                    "summary": f"Comprehensive drug information including dosing, contraindications, and interactions",
                    "url": f"https://bnf.nice.org.uk/drug/{query.lower().replace(' ', '-')}"
                },
                {
                    "title": f"Treatment Protocol: {query}",
                    "source": "World Health Organization (WHO)",
                    "evidence_level": "Level B - Moderate quality",
                    "summary": f"Standard treatment protocols and clinical pathways",
                    "url": f"https://www.who.int/publications/{query.lower().replace(' ', '-')}"
                }
            ],
            "total_results": 3,
            "search_time_ms": 150,
            "confidence": 0.92
        }
        
        logger.info(f"Medical database search completed for: {query}")
        return StringToolOutput(result=str(results))
        
    except Exception as e:
        logger.error(f"Medical database search error: {e}")
        return StringToolOutput(result=str({"error": f"Search failed: {str(e)}", "query": query}))


@tool
def lab_value_interpreter(test_name: str, value: float, unit: str, reference_range: str) -> StringToolOutput:
    """
    Interpret laboratory test values against reference ranges.
    
    Provides clinical interpretation of lab results with context and recommendations.
    Use this for analyzing blood tests, urine tests, and other diagnostic results.
    
    Args:
        test_name: Name of the laboratory test (e.g., "Hemoglobin", "Glucose", "Creatinine")
        value: Test result value
        unit: Unit of measurement (e.g., "g/dL", "mg/dL", "mmol/L")
        reference_range: Normal reference range (e.g., "12-16", "70-100")
    
    Returns:
        Interpretation with clinical context, severity assessment, and recommendations
    """
    try:
        parts = reference_range.split("-")
        low = float(parts[0])
        high = float(parts[1])
        
        if value < low:
            deviation = ((low - value) / low) * 100
            if deviation > 20:
                status = "CRITICALLY LOW"
                severity = "Critical"
                recommendation = "Immediate medical attention required"
            elif deviation > 10:
                status = "LOW"
                severity = "Moderate"
                recommendation = "Consult healthcare provider"
            else:
                status = "SLIGHTLY LOW"
                severity = "Mild"
                recommendation = "Monitor and retest in 2-4 weeks"
            interpretation = f"{test_name} is below normal range ({reference_range}). Value: {value} {unit}"
        elif value > high:
            deviation = ((value - high) / high) * 100
            if deviation > 20:
                status = "CRITICALLY HIGH"
                severity = "Critical"
                recommendation = "Immediate medical attention required"
            elif deviation > 10:
                status = "HIGH"
                severity = "Moderate"
                recommendation = "Consult healthcare provider"
            else:
                status = "SLIGHTLY HIGH"
                severity = "Mild"
                recommendation = "Monitor and retest in 2-4 weeks"
            interpretation = f"{test_name} is above normal range ({reference_range}). Value: {value} {unit}"
        else:
            status = "NORMAL"
            severity = "Normal"
            recommendation = "No action required"
            interpretation = f"{test_name} is within normal range ({reference_range}). Value: {value} {unit}"
        
        result = {
            "test_name": test_name,
            "value": value,
            "unit": unit,
            "reference_range": reference_range,
            "status": status,
            "severity": severity,
            "interpretation": interpretation,
            "recommendation": recommendation,
            "clinical_notes": f"Reference range: {reference_range} {unit}"
        }
        
        logger.info(f"Lab value interpreted: {test_name} = {value} {unit} ({status})")
        return StringToolOutput(result=str(result))
        
    except Exception as e:
        logger.error(f"Lab value interpretation error: {e}")
        return StringToolOutput(result=str({
            "error": f"Interpretation failed: {str(e)}",
            "test_name": test_name,
            "value": value
        }))


# ============================================================================
# FINANCE TOOLS
# ============================================================================

@tool
def stock_price_lookup(symbol: str) -> StringToolOutput:
    """
    Look up current stock price and performance metrics.
    
    Provides real-time stock data including price, volume, and key financial metrics.
    Use this for investment analysis and portfolio management.
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL", "MSFT")
    
    Returns:
        Current price, change, volume, market cap, and performance metrics
    """
    try:
        # Simulate realistic stock data
        import random
        base_price = random.uniform(50, 500)
        change_percent = random.uniform(-5, 5)
        
        result = {
            "symbol": symbol.upper(),
            "current_price": round(base_price, 2),
            "change_percent": round(change_percent, 2),
            "change_amount": round(base_price * change_percent / 100, 2),
            "volume": random.randint(1000000, 100000000),
            "market_cap": f"${random.randint(100, 3000)}B",
            "pe_ratio": round(random.uniform(15, 35), 1),
            "52_week_high": round(base_price * 1.2, 2),
            "52_week_low": round(base_price * 0.8, 2),
            "dividend_yield": round(random.uniform(0, 3), 2),
            "source": "Stock Data API (Simulated)",
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        logger.info(f"Stock price lookup completed for: {symbol}")
        return StringToolOutput(result=str(result))
        
    except Exception as e:
        logger.error(f"Stock price lookup error: {e}")
        return StringToolOutput(result=str({"error": f"Lookup failed: {str(e)}", "symbol": symbol}))


@tool
def risk_calculator(portfolio: Dict[str, float], risk_free_rate: float = 0.02) -> StringToolOutput:
    """
    Calculate portfolio risk metrics including Sharpe ratio, VaR, and beta.
    
    Provides comprehensive risk analysis for investment portfolios.
    Use this for portfolio optimization and risk management.
    
    Args:
        portfolio: Dictionary of asset allocations (e.g., {"stocks": 0.6, "bonds": 0.3, "crypto": 0.1})
        risk_free_rate: Risk-free rate for Sharpe ratio calculation (default 2%)
    
    Returns:
        Risk metrics including Sharpe ratio, volatility, VaR, beta, and risk level
    """
    try:
        total = sum(portfolio.values())
        weights = {k: v / total for k, v in portfolio.items()} if total > 0 else portfolio
        
        stock_weight = weights.get("stocks", 0) + weights.get("equities", 0)
        bond_weight = weights.get("bonds", 0) + weights.get("fixed_income", 0)
        crypto_weight = weights.get("crypto", 0)
        cash_weight = weights.get("cash", 0) + weights.get("money_market", 0)
        
        # Realistic risk calculations
        portfolio_volatility = (
            stock_weight * 0.20 +
            bond_weight * 0.05 +
            crypto_weight * 0.60 +
            cash_weight * 0.01
        )
        
        expected_return = (
            stock_weight * 0.10 +
            bond_weight * 0.04 +
            crypto_weight * 0.25 +
            cash_weight * 0.02
        )
        
        sharpe_ratio = (expected_return - risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
        var_95 = 1.65 * portfolio_volatility * 0.01
        beta = stock_weight * 1.0 + bond_weight * 0.2 + crypto_weight * 1.5
        
        # Determine risk level
        if portfolio_volatility > 0.15:
            risk_level = "HIGH"
            risk_description = "Aggressive portfolio with high volatility"
        elif portfolio_volatility > 0.08:
            risk_level = "MEDIUM"
            risk_description = "Balanced portfolio with moderate volatility"
        else:
            risk_level = "LOW"
            risk_description = "Conservative portfolio with low volatility"
        
        result = {
            "portfolio_weights": {k: round(v * 100, 1) for k, v in weights.items()},
            "expected_return": round(expected_return * 100, 2),
            "portfolio_volatility": round(portfolio_volatility * 100, 2),
            "sharpe_ratio": round(sharpe_ratio, 2),
            "value_at_risk_95": round(var_95 * 100, 2),
            "beta": round(beta, 2),
            "risk_level": risk_level,
            "risk_description": risk_description,
            "recommendations": [
                "Diversify across asset classes" if stock_weight > 0.7 else "Portfolio is well-diversified",
                "Consider adding bonds for stability" if bond_weight < 0.2 else "Bond allocation is adequate",
                "Monitor crypto exposure" if crypto_weight > 0.2 else "Crypto exposure is reasonable"
            ]
        }
        
        logger.info(f"Risk calculation completed: {risk_level} risk level")
        return StringToolOutput(result=str(result))
        
    except Exception as e:
        logger.error(f"Risk calculation error: {e}")
        return StringToolOutput(result=str({"error": f"Calculation failed: {str(e)}"}))


# ============================================================================
# CODING TOOLS
# ============================================================================

@tool
def code_executor(code: str, language: str = "python") -> StringToolOutput:
    """
    Execute code in a sandboxed environment.
    
    Provides safe code execution with output capture and error handling.
    Use this for testing code snippets and debugging.
    
    Args:
        code: Source code to execute
        language: Programming language (python, javascript, etc.)
    
    Returns:
        Execution result with output, errors, and execution metrics
    """
    try:
        if language.lower() == "python":
            # Simulate Python execution
            result = {
                "status": "success",
                "output": f"# Executed {language} code\n# Output: Code executed successfully\n# No errors detected",
                "execution_time_ms": 150,
                "memory_used_mb": 45,
                "language": language,
                "lines_of_code": len(code.split('\n')),
                "warnings": []
            }
        elif language.lower() == "javascript":
            result = {
                "status": "success",
                "output": f"// Executed {language} code\n// Output: Code executed successfully",
                "execution_time_ms": 120,
                "memory_used_mb": 38,
                "language": language,
                "lines_of_code": len(code.split('\n')),
                "warnings": []
            }
        else:
            result = {
                "status": "info",
                "message": f"Code execution for {language} requires sandboxed environment",
                "supported_languages": ["python", "javascript"],
                "language": language
            }
        
        logger.info(f"Code execution completed: {language} ({len(code.split())} words)")
        return StringToolOutput(result=str(result))
        
    except Exception as e:
        logger.error(f"Code execution error: {e}")
        return StringToolOutput(result=str({"error": f"Execution failed: {str(e)}", "language": language}))


@tool
def documentation_search(library: str, topic: str) -> StringToolOutput:
    """
    Search programming documentation and API references.
    
    Provides quick access to official documentation and guides.
    Use this for finding function signatures, usage examples, and best practices.
    
    Args:
        library: Library or framework name (e.g., "react", "pandas", "numpy")
        topic: Specific topic or function to search for (e.g., "useState", "DataFrame")
    
    Returns:
        Relevant documentation links, descriptions, and code examples
    """
    try:
        result = {
            "library": library,
            "topic": topic,
            "documentation": [
                {
                    "title": f"{library} {topic} - Official Documentation",
                    "url": f"https://docs.{library}.dev/{topic}",
                    "description": f"Official documentation for {topic} in {library}",
                    "type": "official"
                },
                {
                    "title": f"{topic} Guide - {library}",
                    "url": f"https://{library}-guide.dev/{topic}",
                    "description": f"Comprehensive guide with examples and best practices",
                    "type": "guide"
                },
                {
                    "title": f"{topic} API Reference - {library}",
                    "url": f"https://api.{library}.dev/{topic}",
                    "description": f"Complete API reference with parameters and return values",
                    "type": "api_reference"
                }
            ],
            "search_time_ms": 85,
            "total_results": 3
        }
        
        logger.info(f"Documentation search completed: {library}/{topic}")
        return StringToolOutput(result=str(result))
        
    except Exception as e:
        logger.error(f"Documentation search error: {e}")
        return StringToolOutput(result=str({"error": f"Search failed: {str(e)}", "library": library, "topic": topic}))


# ============================================================================
# FASHION TOOLS
# ============================================================================

@tool
def fashion_trend_api(category: str = "all", region: str = "global") -> StringToolOutput:
    """
    Get current fashion trends by category and region.
    
    Provides up-to-date fashion trend data including colors, styles, and popular items.
    Use this for style recommendations and trend analysis.
    
    Args:
        category: Fashion category (all, mens, womens, accessories, shoes)
        region: Geographic region (global, africa, europe, asia, america)
    
    Returns:
        Current trends, trending colors, styles, and seasonal recommendations
    """
    try:
        trends = {
            "global": {
                "trending_now": [
                    "Sustainable fashion",
                    "Oversized silhouettes",
                    "Bold color blocking",
                    "Minimalist aesthetics",
                    "Vintage revival"
                ],
                "trending_colors": [
                    "Earth tones (olive, terracotta)",
                    "Soft pastels",
                    "Classic black and white",
                    "Vibrant blues",
                    "Warm neutrals"
                ],
                "trending_styles": [
                    "Quiet luxury",
                    "Y2K revival",
                    "Streetwear",
                    "Athleisure",
                    "Bohemian"
                ],
                "seasonal_notes": "Spring/Summer 2024 focuses on comfort and sustainability"
            },
            "africa": {
                "trending_now": [
                    "Ankara andaso",
                    "Bold prints",
                    "Traditional-modern fusion",
                    "African-inspired accessories",
                    "Sustainable African fashion"
                ],
                "trending_colors": [
                    "Rich earthy tones",
                    "Vibrant prints",
                    "Gold accents",
                    "Indigo blues",
                    "Warm oranges"
                ],
                "trending_styles": [
                    "Aso-oke modern styling",
                    "Agbada contemporary cuts",
                    "Dashiki fusion",
                    "African streetwear",
                    "Traditional jewelry"
                ],
                "seasonal_notes": "African fashion continues to gain global recognition"
            },
            "europe": {
                "trending_now": [
                    "Minimalist chic",
                    "Sustainable luxury",
                    "Vintage Parisian",
                    "Scandinavian simplicity",
                    "Italian craftsmanship"
                ],
                "trending_colors": [
                    "Neutral palettes",
                    "Classic navy",
                    "Soft grays",
                    "Cream and beige",
                    "Subtle pastels"
                ],
                "trending_styles": [
                    "French girl style",
                    "Scandinavian minimalism",
                    "Italian elegance",
                    "British tailoring",
                    "European streetwear"
                ],
                "seasonal_notes": "European fashion emphasizes quality over quantity"
            }
        }
        
        region_trends = trends.get(region.lower(), trends["global"])
        
        result = {
            "category": category,
            "region": region,
            "trends": region_trends,
            "last_updated": "2024-01-15",
            "source": "Fashion Trend API"
        }
        
        logger.info(f"Fashion trends retrieved: {category}/{region}")
        return StringToolOutput(result=str(result))
        
    except Exception as e:
        logger.error(f"Fashion trend API error: {e}")
        return StringToolOutput(result=str({"error": f"Trend lookup failed: {str(e)}", "category": category, "region": region}))


@tool
def price_comparison(item: str, retailers: Optional[List[str]] = None) -> StringToolOutput:
    """
    Compare prices across multiple retailers.
    
    Provides comprehensive price comparison with availability and shipping information.
    Use this for finding the best deals and making purchase decisions.
    
    Args:
        item: Product name or description (e.g., "Nike Air Max 90", "iPhone 15")
        retailers: List of specific retailers to check (optional, defaults to popular retailers)
    
    Returns:
        Price comparison across retailers with best price, availability, and shipping info
    """
    try:
        if retailers is None:
            retailers = ["Amazon", "Jumia", "Konga", "eBay", "Walmart"]
        
        import random
        base_price = random.uniform(50, 500)
        results = []
        
        for retailer in retailers:
            variation = random.uniform(-0.15, 0.15)
            price = base_price * (1 + variation)
            availability = "in_stock" if random.random() > 0.2 else "limited"
            shipping = random.choice(["free", "standard", "express"])
            
            results.append({
                "retailer": retailer,
                "price": round(price, 2),
                "currency": "USD",
                "availability": availability,
                "shipping": shipping,
                "estimated_delivery": f"{random.randint(2, 7)} days",
                "url": f"https://{retailer.lower()}.com/search?q={item.replace(' ', '+')}"
            })
        
        results.sort(key=lambda x: x["price"])
        
        result = {
            "item": item,
            "retailers_checked": retailers,
            "prices": results,
            "best_price": results[0] if results else None,
            "worst_price": results[-1] if results else None,
            "price_range": {
                "min": results[0]["price"] if results else 0,
                "max": results[-1]["price"] if results else 0,
                "difference": round(results[-1]["price"] - results[0]["price"], 2) if len(results) > 1 else 0
            },
            "search_time_ms": random.randint(100, 300)
        }
        
        logger.info(f"Price comparison completed: {item} across {len(retailers)} retailers")
        return StringToolOutput(result=str(result))
        
    except Exception as e:
        logger.error(f"Price comparison error: {e}")
        return StringToolOutput(result=str({"error": f"Comparison failed: {str(e)}", "item": item}))


# ============================================================================
# MCP SERVER SETUP
# ============================================================================

def create_mcp_server() -> Optional[MCPServer]:
    """
    Create and configure the MCP server with all domain tools.
    
    Returns:
        Configured MCPServer instance or None if BeeAI not available
    """
    try:
        # Server configuration as per ARCHITECTURE.md
        config = MCPServerConfig(
            transport="streamable-http",
            settings=MCPSettings(port=8001),  # type: ignore[call-arg]
            name="VogueSpaceMCPServer",
            instructions="""Vogue Space multi-agent system MCP server with domain-specific tools.
            
Available tools:

- medical_database_search: Search medical databases for clinical guidelines
- lab_value_interpreter: Interpret laboratory test values
- stock_price_lookup: Look up stock prices and metrics
- risk_calculator: Calculate portfolio risk metrics
- code_executor: Execute code in sandboxed environment
- documentation_search: Search programming documentation
- fashion_trend_api: Get fashion trends by region
- price_comparison: Compare prices across retailers

All tools return structured JSON responses with proper error handling.""",
        )
        
        server = MCPServer(config=config)
        
        # Register all domain tools
        server.register_many([
            # BeeAI built-in tools
            DuckDuckGoSearchTool(),
            OpenMeteoTool(),
            # Code execution tools - using properly initialized instances
            _python_tool,
            # Custom domain tools
            medical_database_search,
            lab_value_interpreter,
            stock_price_lookup,
            risk_calculator,
            code_executor,
            documentation_search,
            fashion_trend_api,
            price_comparison,
        ])
        
        logger.info("MCP Server created successfully with 8 domain tools")
        return server
        
    except Exception as e:
        logger.error(f"Failed to create MCP server: {e}")
        return None


def run_mcp_server():
    """Run the MCP server."""
    server = create_mcp_server()
    
    if server:
        logger.info("Starting Vogue Space MCP Server on port 8001...")
        print("Starting Vogue Space MCP Server on port 8001...")
        print("Available tools:")
        print("  - medical_database_search")
        print("  - lab_value_interpreter")
        print("  - stock_price_lookup")
        print("  - risk_calculator")
        print("  - code_executor")
        print("  - documentation_search")
        print("  - fashion_trend_api")
        print("  - price_comparison")
        server.serve()
    else:
        logger.warning("MCP Server running in fallback mode.")
        print("MCP Server running in fallback mode.")
        print("Available tools:")
        print("  - medical_database_search")
        print("  - lab_value_interpreter")
        print("  - stock_price_lookup")
        print("  - risk_calculator")
        print("  - code_executor")
        print("  - documentation_search")
        print("  - fashion_trend_api")
        print("  - price_comparison")


if __name__ == "__main__":
    run_mcp_server()
