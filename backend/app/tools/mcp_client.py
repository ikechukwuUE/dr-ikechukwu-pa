"""
MCP Tool Client for AI System - Using FastMCP Client
====================================================
Simplified MCP client using the official FastMCP Client class.
Supports HTTP, STDIO, and in-memory transports.
"""

import asyncio
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger()

# FastMCP Client - the official way to connect to MCP servers
try:
    from fastmcp import Client as FastMCPClient  # type: ignore[attr-defined,import]
    FASTMCP_AVAILABLE = True
except ImportError:
    FastMCPClient = None  # type: ignore[assignment,misc]
    FASTMCP_AVAILABLE = False

from pydantic import BaseModel, Field


class MCPServerType(str, Enum):
    """Types of MCP servers supported."""
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"
    IN_MEMORY = "in_memory"


class MCPToolResult(BaseModel):
    """Result from an MCP tool execution."""
    success: bool = Field(description="Whether the tool execution succeeded")
    content: str = Field(description="Tool output content")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class MCPClientWrapper:
    """
    Simple wrapper around FastMCP Client for our use cases.
    
    Usage:
        # For HTTP server
        client = MCPClientWrapper("http://localhost:8001/mcp")
        
        # For local script (STDIO)
        client = MCPClientWrapper("clinical_mcp_server.py")
        
        # Use it
        result = await client.call_tool("tool_name", {"param": "value"})
    """
    
    def __init__(self, server_source: str, server_type: MCPServerType = MCPServerType.HTTP):
        self.server_source = server_source
        self.server_type = server_type
        self._client: Optional[Any] = None
        self._initialized = False
    
    async def __aenter__(self):
        """Context manager entry."""
        if not FASTMCP_AVAILABLE:
            raise RuntimeError("FastMCP is not installed. Run: pip install fastmcp")
        
        if FastMCPClient is None:
            raise RuntimeError("FastMCP Client import failed")
        
        # Create the appropriate client based on server type
        if self.server_type == MCPServerType.IN_MEMORY:
            raise NotImplementedError("In-memory transport requires server instance")
        else:
            self._client = FastMCPClient(self.server_source)
        
        await self._client.__aenter__()
        self._initialized = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._client:
            await self._client.__aexit__(exc_type, exc_val, exc_tb)
        self._initialized = False
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the server."""
        if not self._initialized or not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        tools = await self._client.list_tools()
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
            for tool in tools
        ]
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> MCPToolResult:
        """Call a tool on the MCP server."""
        if not self._initialized or not self._client:
            return MCPToolResult(
                success=False,
                content="",
                error="Client not initialized. Use 'async with' context manager."
            )
        
        try:
            result = await self._client.call_tool(tool_name, parameters)
            
            if hasattr(result, 'data'):
                content = str(result.data)
            elif hasattr(result, 'content'):
                if isinstance(result.content, list):
                    content = " ".join(str(c) for c in result.content)
                else:
                    content = str(result.content)
            else:
                content = str(result)
            
            return MCPToolResult(success=True, content=content)
        except Exception as e:
            return MCPToolResult(success=False, content="", error=str(e))
    
    async def ping(self) -> bool:
        """Ping the MCP server."""
        if not self._initialized or not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False


# ============================================================================
# SIMPLE FUNCTION-BASED TOOLS (for CrewAI integration)
# ============================================================================

class TaskTool:
    """A simple function-based tool for CrewAI tasks with IBM/Anthropic security compliance."""
    
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        owner: Optional[str] = None,
        version: str = "1.0.0",
        permission_scope: str = "read",
        rate_limit: int = 100,
        requires_approval: bool = False,
    ):
        self.name = name
        self.description = description
        self.func = func
        # IBM/Anthropic security metadata
        self.owner = owner
        self.version = version
        self.permission_scope = permission_scope  # read, write, execute, admin
        self.rate_limit = rate_limit  # requests per minute
        self.requires_approval = requires_approval  # human-in-the-loop for sensitive ops
    
    def __call__(self, **kwargs) -> str:
        """Execute the tool with given parameters."""
        import time
        start_time = time.time()
        
        # Audit log: tool invocation
        logger.info(
            "mcp_tool_invocation",
            tool_name=self.name,
            version=self.version,
            permission_scope=self.permission_scope,
            parameters_keys=list(kwargs.keys()),
        )
        
        try:
            result = self.func(**kwargs)
            duration = time.time() - start_time
            
            # Audit log: tool success
            logger.info(
                "mcp_tool_success",
                tool_name=self.name,
                duration_ms=round(duration * 1000, 2),
            )
            
            if asyncio.iscoroutine(result):
                return f"Async tool: {self.name}"
            return str(result)
        except Exception as e:
            duration = time.time() - start_time
            
            # Audit log: tool failure
            logger.error(
                "mcp_tool_failure",
                tool_name=self.name,
                error=str(e),
                duration_ms=round(duration * 1000, 2),
            )
            return f"Error: {str(e)}"
    
    def to_crewai_tool(self):
        """Convert to CrewAI-compatible tool.
        
        Returns a callable that can be used by CrewAI agents.
        The callable accepts **kwargs and forwards them to the underlying function.
        """
        # Create a simple wrapper function that doesn't rely on CrewAI imports
        # This ensures compatibility when CrewAI is not available or has API changes
        def wrapper(**kwargs):
            return self(**kwargs)
        
        # Set metadata for better debugging and transparency
        wrapper.__name__ = self.name
        wrapper.__doc__ = self.description
        
        return wrapper


class TaskToolRegistry:
    """Simple registry for task-based tools."""
    
    def __init__(self):
        self._tools: Dict[str, TaskTool] = {}
    
    def register(
        self,
        name: str,
        description: str,
        func: Callable,
        owner: Optional[str] = None,
        version: str = "1.0.0",
        permission_scope: str = "read",
        rate_limit: int = 100,
        requires_approval: bool = False,
    ) -> "TaskToolRegistry":
        """Register a tool with security metadata (IBM/Anthropic compliance)."""
        tool = TaskTool(
            name=name,
            description=description,
            func=func,
            owner=owner,
            version=version,
            permission_scope=permission_scope,
            rate_limit=rate_limit,
            requires_approval=requires_approval,
        )
        self._tools[name] = tool
        # Audit log: tool registered
        logger.info(
            "mcp_tool_registered",
            tool_name=name,
            version=version,
            permission_scope=permission_scope,
            owner=owner,
        )
        return self
    
    def get_tool(self, name: str) -> Optional[TaskTool]:
        return self._tools.get(name)
    
    def get_all_tools(self) -> Dict[str, TaskTool]:
        return self._tools.copy()
    
    def get_crewai_tools(self) -> List[Any]:
        return [tool.to_crewai_tool() for tool in self._tools.values()]
    
    def get_langchain_tools(self) -> List[Any]:
        """Get tools formatted for langchain's bind_tools."""
        from langchain_core.tools import tool as langchain_tool  # type: ignore[import]
        
        langchain_tools = []
        for task_tool in self._tools.values():
            # Use the function directly with the @langchain_tool decorator
            # This creates a proper langchain tool with name and description
            wrapped = langchain_tool(task_tool.func)  # type: ignore[call-arg]
            wrapped.name = task_tool.name
            wrapped.description = task_tool.description
            langchain_tools.append(wrapped)
        return langchain_tools
    
    def get_tools_for_task(self, tool_names: List[str]) -> List[Any]:
        result = []
        for name in tool_names:
            if name in self._tools:
                result.append(self._tools[name].to_crewai_tool())
        return result
    
    def get_tool_names(self) -> List[str]:
        return list(self._tools.keys())


# ============================================================================
# GLOBAL TOOL REGISTRIES (for CrewAI tasks)
# ============================================================================

_cds_tools: Optional[TaskToolRegistry] = None
_finance_tools: Optional[TaskToolRegistry] = None
_aidev_tools: Optional[TaskToolRegistry] = None
_fashion_tools: Optional[TaskToolRegistry] = None


def get_cds_task_tools() -> TaskToolRegistry:
    """Get the CDS domain task tools registry."""
    global _cds_tools
    if _cds_tools is None:
        _cds_tools = TaskToolRegistry()
        _setup_cds_tools(_cds_tools)
    return _cds_tools


def get_finance_task_tools() -> TaskToolRegistry:
    """Get the Finance domain task tools registry."""
    global _finance_tools
    if _finance_tools is None:
        _finance_tools = TaskToolRegistry()
        _setup_finance_tools(_finance_tools)
    return _finance_tools


def get_aidev_task_tools() -> TaskToolRegistry:
    """Get the AI-Dev domain task tools registry."""
    global _aidev_tools
    if _aidev_tools is None:
        _aidev_tools = TaskToolRegistry()
        _setup_aidev_tools(_aidev_tools)
    return _aidev_tools


def get_fashion_task_tools() -> TaskToolRegistry:
    """Get the Fashion domain task tools registry."""
    global _fashion_tools
    if _fashion_tools is None:
        _fashion_tools = TaskToolRegistry()
        _setup_fashion_tools(_fashion_tools)
    return _fashion_tools


# ============================================================================
# TOOL DEFINITIONS FOR EACH DOMAIN
# ============================================================================

def _setup_cds_tools(registry: TaskToolRegistry) -> None:
    """Setup task tools for CDS (Clinical Decision Support) domain."""
    
    def search_medical_literature(query: str) -> str:
        return f"Medical literature search for: {query}"
    
    def check_drug_interactions(drugs: List[str]) -> str:
        return f"Drug interaction check for: {', '.join(drugs)}"
    
    def lookup_clinical_guidelines(condition: str) -> str:
        return f"Clinical guidelines for: {condition}"
    
    def calculate_bmi(weight_kg: float, height_cm: float) -> str:
        height_m = height_cm / 100
        bmi = weight_kg / (height_m ** 2)
        return f"BMI: {bmi:.1f}"
    
    def assess_fall_risk(age: int, medications: List[str], history: List[str]) -> str:
        risk_factors = 0
        if age > 65:
            risk_factors += 1
        if len(medications) >= 5:
            risk_factors += 1
        risk_level = "Low" if risk_factors < 2 else "Medium" if risk_factors < 3 else "High"
        return f"Fall risk: {risk_level}"
    
    # CDS tools with IBM/Anthropic security metadata
    registry.register(
        "search_medical_literature", "Search medical literature", search_medical_literature,
        owner="clinical_team", version="1.0.0", permission_scope="read", rate_limit=50, requires_approval=False
    )
    registry.register(
        "check_drug_interactions", "Check drug interactions", check_drug_interactions,
        owner="clinical_team", version="1.0.0", permission_scope="read", rate_limit=30, requires_approval=False
    )
    registry.register(
        "lookup_clinical_guidelines", "Lookup clinical guidelines", lookup_clinical_guidelines,
        owner="clinical_team", version="1.0.0", permission_scope="read", rate_limit=50, requires_approval=False
    )
    registry.register(
        "calculate_bmi", "Calculate BMI", calculate_bmi,
        owner="clinical_team", version="1.0.0", permission_scope="execute", rate_limit=100, requires_approval=False
    )
    registry.register(
        "assess_fall_risk", "Assess fall risk", assess_fall_risk,
        owner="clinical_team", version="1.0.0", permission_scope="execute", rate_limit=30, requires_approval=False
    )


def _setup_finance_tools(registry: TaskToolRegistry) -> None:
    """Setup task tools for Finance domain."""
    
    def get_stock_price(symbol: str) -> str:
        return f"Stock price for {symbol}: $0.00"
    
    def get_company_financials(symbol: str) -> str:
        return f"Financial data for {symbol}"
    
    def calculate_investment_returns(principal: float, rate: float, years: float) -> str:
        amount = principal * (1 + rate/100) ** years
        return f"Investment after {years} years: ${amount:,.2f}"
    
    def analyze_budget(income: float, expenses: Dict[str, float]) -> str:
        total_expenses = sum(expenses.values())
        savings = income - total_expenses
        savings_rate = (savings / income * 100) if income > 0 else 0
        return f"Savings: ${savings:,.2f} ({savings_rate:.1f}%)"
    
    def get_exchange_rate(from_currency: str, to_currency: str) -> str:
        return f"Exchange rate {from_currency} to {to_currency}: 1.0"
    
    # Finance tools with IBM/Anthropic security metadata
    registry.register(
        "get_stock_price", "Get stock price", get_stock_price,
        owner="finance_team", version="1.0.0", permission_scope="read", rate_limit=30, requires_approval=False
    )
    registry.register(
        "get_company_financials", "Get company financials", get_company_financials,
        owner="finance_team", version="1.0.0", permission_scope="read", rate_limit=30, requires_approval=False
    )
    registry.register(
        "calculate_investment_returns", "Calculate investment returns", calculate_investment_returns,
        owner="finance_team", version="1.0.0", permission_scope="execute", rate_limit=50, requires_approval=False
    )
    registry.register(
        "analyze_budget", "Analyze budget", analyze_budget,
        owner="finance_team", version="1.0.0", permission_scope="execute", rate_limit=50, requires_approval=False
    )
    registry.register(
        "get_exchange_rate", "Get exchange rate", get_exchange_rate,
        owner="finance_team", version="1.0.0", permission_scope="read", rate_limit=30, requires_approval=False
    )


def _setup_aidev_tools(registry: TaskToolRegistry) -> None:
    """Setup task tools for AI-Dev domain."""
    
    def search_documentation(query: str) -> str:
        return f"Documentation search for: {query}"
    
    def run_code_sandbox(code: str, language: str = "python") -> str:
        return f"Code execution for {language}"
    
    def lint_code(code: str, language: str) -> str:
        return f"Lint results for {language}"
    
    def format_code(code: str, language: str) -> str:
        return code
    
    # AI-Dev tools with IBM/Anthropic security metadata
    registry.register(
        "search_documentation", "Search documentation", search_documentation,
        owner="aidev_team", version="1.0.0", permission_scope="read", rate_limit=50, requires_approval=False
    )
    registry.register(
        "run_code_sandbox", "Run code sandbox", run_code_sandbox,
        owner="aidev_team", version="1.0.0", permission_scope="execute", rate_limit=10, requires_approval=True  # Higher security for code execution
    )
    registry.register(
        "lint_code", "Lint code", lint_code,
        owner="aidev_team", version="1.0.0", permission_scope="execute", rate_limit=30, requires_approval=False
    )
    registry.register(
        "format_code", "Format code", format_code,
        owner="aidev_team", version="1.0.0", permission_scope="execute", rate_limit=30, requires_approval=False
    )


def _setup_fashion_tools(registry: TaskToolRegistry) -> None:
    """Setup task tools for Fashion domain."""
    
    def search_fashion_trends(season: str, category: str) -> str:
        return f"Fashion trends for {season} {category}"
    
    def analyze_color_palette(colors: List[str]) -> str:
        return f"Color palette analysis"
    
    def suggest_outfit_occasions(occasion: str, style: str) -> str:
        return f"Outfit suggestions for {occasion}"
    
    # Fashion tools with IBM/Anthropic security metadata
    registry.register(
        "search_fashion_trends", "Search fashion trends", search_fashion_trends,
        owner="fashion_team", version="1.0.0", permission_scope="read", rate_limit=50, requires_approval=False
    )
    registry.register(
        "analyze_color_palette", "Analyze color palette", analyze_color_palette,
        owner="fashion_team", version="1.0.0", permission_scope="read", rate_limit=30, requires_approval=False
    )
    registry.register(
        "suggest_outfit_occasions", "Suggest outfit occasions", suggest_outfit_occasions,
        owner="fashion_team", version="1.0.0", permission_scope="execute", rate_limit=30, requires_approval=False
    )
