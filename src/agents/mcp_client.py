import logging
from typing import Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

logger = logging.getLogger(__name__)

class MCPServerConfig(BaseSettings):
    """Configuration for MCP servers and required API keys."""
    github_token: Optional[str] = None
    allowed_fs_path: str = "./project_workspace" # Directory the AI is allowed to read/write
    
    model_config = ConfigDict(extra='ignore', env_file='.env')

class MCPClientManager:
    """Manages connections to multiple MCP servers."""
    
    def __init__(self):
        self.config = MCPServerConfig()
        
        # Initialize the MultiServerMCPClient with your tool servers
        github_config = {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
        }
        if self.config.github_token:
            github_config["env"] = {"GITHUB_TOKEN": self.config.github_token}

        self.client = MultiServerMCPClient({
            "pubmed_search": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "pubmed-search-mcp"],
            },
            "github": github_config,
            "filesystem": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", self.config.allowed_fs_path],
            },
            "financial_datasets": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@financial-datasets/mcp-server"],
            },
            "playwright": {
                "transport": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-playwright"],
            }
        })

    async def get_all_tools(self):
        """Fetch all tools dynamically from the configured MCP servers."""
        try:
            # This automatically connects to the servers, retrieves schemas, and converts them to LangChain tools
            tools = await self.client.get_tools()
            logger.info(f"Successfully loaded {len(tools)} MCP tools.")
            return tools
        except Exception as e:
            logger.error(f"Failed to load MCP tools: {e}")
            raise

# Singleton instance to be imported across your FastAPI routes
mcp_manager = MCPClientManager()