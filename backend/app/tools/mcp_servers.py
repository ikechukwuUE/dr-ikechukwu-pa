"""
MCP Server Configurations for dr_ikechukwu_pa
=============================================
This file defines MCP server configurations for the AI system.
External servers can be connected via URL, and custom servers can be added.

External MCP Servers (ready to use with API keys):
- Alpha Vantage: Stock market data
- Alpaca: Trading + market data  
- E2B: Code execution sandbox
- FindMine: Fashion styling

Custom MCP Servers (need to be built):
- Clinical: Drug interactions, guidelines, literature
- Finance: Portfolio analysis, budget tools
- AI-Dev: Custom code tools
- Fashion: Trend analysis, color palette
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class MCPServerCategory(str, Enum):
    """Categories of MCP servers."""
    EXTERNAL = "external"  # Ready-to-use external services
    CUSTOM = "custom"      # Custom-built for this project
    HYBRID = "hybrid"     # External + custom combination


@dataclass
class MCPAppConfig:
    """Configuration for an MCP server for a specific app domain."""
    name: str
    category: MCPServerCategory
    server_type: str  # "stdio", "http", "sse"
    url: Optional[str] = None
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    headers: Optional[Dict[str, str]] = None
    description: str = ""
    tools: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.tools is None:
            self.tools = []


# ============================================================================
# EXTERNAL MCP SERVERS (Ready to use with API keys)
# ============================================================================

def get_external_finance_servers() -> List[MCPAppConfig]:
    """Get external finance MCP server configurations."""
    return [
        MCPAppConfig(
            name="alpha_vantage",
            category=MCPServerCategory.EXTERNAL,
            server_type="http",
            url="https://mcp.alphavantage.co",
            description="Real-time and historical stock market data",
            tools=["get_stock_quote", "get_historical_data", "get_forex", "get_crypto"]
        ),
    ]


def get_external_aidev_servers() -> List[MCPAppConfig]:
    """Get external AI-Dev MCP server configurations.

    Using custom AI-Dev tools instead (code linting, formatting, documentation search).
    """
    return []  # No external servers - using custom tools instead


# ============================================================================
# CUSTOM MCP SERVERS (Built for this project)
# ============================================================================

def get_custom_clinical_servers() -> List[MCPAppConfig]:
    """Get custom clinical MCP server configurations.
    
    These would connect to:
    - Drug interaction APIs (when integrated)
    - Medical literature search
    - Clinical guidelines lookup
    """
    return [
        MCPAppConfig(
            name="clinical_tools",
            category=MCPServerCategory.CUSTOM,
            server_type="http",
            url="http://localhost:8001/mcp",
            description="Custom clinical decision support tools",
            tools=[
                "search_medical_literature",
                "check_drug_interactions", 
                "lookup_clinical_guidelines",
                "calculate_bmi",
                "assess_fall_risk"
            ]
        ),
    ]


def get_custom_finance_servers() -> List[MCPAppConfig]:
    """Get custom finance MCP server configurations.
    
    These would connect to:
    - Budget analysis tools
    - Investment calculators
    - Portfolio optimizers
    """
    return [
        MCPAppConfig(
            name="finance_tools",
            category=MCPServerCategory.CUSTOM,
            server_type="http",
            url="http://localhost:8002/mcp",
            description="Custom financial analysis tools",
            tools=[
                "calculate_investment_returns",
                "analyze_budget",
                "get_exchange_rate",
                "get_company_financials"
            ]
        ),
    ]


def get_custom_aidev_servers() -> List[MCPAppConfig]:
    """Get custom AI-Dev MCP server configurations.
    
    These would connect to:
    - Code linting tools
    - Documentation search
    - Code formatting
    """
    return [
        MCPAppConfig(
            name="aidev_tools",
            category=MCPServerCategory.CUSTOM,
            server_type="http",
            url="http://localhost:8003/mcp",
            description="Custom AI development tools",
            tools=[
                "search_documentation",
                "lint_code",
                "format_code"
            ]
        ),
    ]


def get_custom_fashion_servers() -> List[MCPAppConfig]:
    """Get custom fashion MCP server configurations.
    
    These would connect to:
    - Fashion trend analysis
    - Color palette tools
    - Outfit suggestions
    """
    return [
        MCPAppConfig(
            name="fashion_tools",
            category=MCPServerCategory.CUSTOM,
            server_type="http",
            url="http://localhost:8004/mcp",
            description="Custom fashion recommendation tools",
            tools=[
                "search_fashion_trends",
                "analyze_color_palette",
                "suggest_outfit_occasions"
            ]
        ),
    ]


# ============================================================================
# UNIFIED CONFIGURATION GETTERS
# ============================================================================

def get_mcp_config_for_domain(domain: str) -> List[MCPAppConfig]:
    """Get MCP configuration for a specific domain.
    
    Args:
        domain: One of 'cds', 'finance', 'aidev', 'fashion'
        
    Returns:
        List of MCP server configurations for that domain
    """
    configs = {
        "cds": get_custom_clinical_servers() + get_external_aidev_servers(),
        "finance": get_custom_finance_servers() + get_external_finance_servers(),
        "aidev": get_custom_aidev_servers() + get_external_aidev_servers(),
        "fashion": get_custom_fashion_servers(),
    }
    return configs.get(domain.lower(), [])


def get_all_mcp_configs() -> Dict[str, List[MCPAppConfig]]:
    """Get all MCP configurations for the project."""
    return {
        "cds": get_mcp_config_for_domain("cds"),
        "finance": get_mcp_config_for_domain("finance"),
        "aidev": get_mcp_config_for_domain("aidev"),
        "fashion": get_mcp_config_for_domain("fashion"),
    }


# ============================================================================
# MCP SERVER REGISTRY (for display purposes)
# ============================================================================

MCP_SERVER_REGISTRY = """
# MCP Server Registry for dr_ikechukwu_pa

## Domain: Clinical Decision Support (CDS)
- **clinical_tools** (Custom): Drug interactions, guidelines, BMI, fall risk
- **e2b_code_execution** (External): Secure code execution

## Domain: Finance
- **finance_tools** (Custom): Budget analysis, investment returns, exchange rates
- **alpha_vantage** (External): Stock quotes, historical data

## Domain: AI-Dev
- **aidev_tools** (Custom): Documentation search, linting, formatting
- **e2b_code_execution** (External): Code sandbox execution

## Domain: Fashion
- **fashion_tools** (Custom): Trends, color analysis, outfit suggestions

---

## Setup Instructions:

### For External Servers:
1. Get API keys from providers (Alpha Vantage, E2B, etc.)
2. Add environment variables to .env
3. Configure server URL in MCP settings

### For Custom Servers:
1. Build the custom MCP server (see /mcp-servers/ directory)
2. Run the server locally or deploy
3. Update URLs in this configuration

### Environment Variables Required:
```
# External APIs
ALPHA_VANTAGE_API_KEY=your_key

# Custom Servers (when deployed)
CLINICAL_MCP_URL=http://localhost:8001/mcp
FINANCE_MCP_URL=http://localhost:8002/mcp
AIDEV_MCP_URL=http://localhost:8003/mcp
FASHION_MCP_URL=http://localhost:8004/mcp
```
"""
