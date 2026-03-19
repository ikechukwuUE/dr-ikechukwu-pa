#!/usr/bin/env python3
"""
MCP Server Runner for dr_ikechukwu_pa
====================================
Script to run all custom MCP servers.

Usage:
    python run_mcp_servers.py              # Run all servers
    python run_mcp_servers.py clinical     # Run only clinical
    python run_mcp_servers.py finance     # Run only finance  
    python run_mcp_servers.py fashion     # Run only fashion
    python run_mcp_servers.py all         # Run all servers (default)
"""

import sys
import subprocess
import os
from concurrent.futures import ThreadPoolExecutor

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Server configurations
SERVERS = {
    "clinical": {
        "file": "backend/mcp_servers/clinical_mcp_server.py",
        "port": 8001,
        "description": "Clinical Decision Support Tools",
    },
    "finance": {
        "file": "backend/mcp_servers/finance_mcp_server.py", 
        "port": 8002,
        "description": "Financial Analysis Tools",
    },
    "fashion": {
        "file": "backend/mcp_servers/fashion_mcp_server.py",
        "port": 8004,
        "description": "Fashion Recommendation Tools",
    },
}


def run_server(name: str, config: dict) -> None:
    """Run a single MCP server."""
    print(f"\n{'='*60}")
    print(f"Starting {name} MCP Server on port {config['port']}")
    print(f"Description: {config['description']}")
    print(f"File: {config['file']}")
    print(f"{'='*60}\n")
    
    # Run with stdio transport (for local use)
    try:
        subprocess.run(
            ["python", "-m", "uvicorn", config["file"].replace("/", ".").replace(".py", ":mcp"), "--port", str(config["port"])],
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        )
    except Exception as e:
        print(f"Error running {name} server: {e}")


def run_standalone(name: str) -> None:
    """Run a server in standalone mode using its main block."""
    config = SERVERS[name]
    print(f"\nStarting {name} MCP Server...")
    print(f"File: {config['file']}")
    print("Note: These servers use FastMCP stdio transport")
    print("Run with: python backend/mcp_servers/{}_mcp_server.py".format(name))
    
    # Just print instructions since stdio servers need different handling
    print(f"\nTo run {name} server manually:")
    print(f"  cd backend/mcp_servers")
    print(f"  pip install fastmcp")
    print(f"  python {name}_mcp_server.py")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        # Default: show help
        print("MCP Server Runner for dr_ikechukwu_pa")
        print("=" * 50)
        print("\nAvailable servers:")
        for name, config in SERVERS.items():
            print(f"  - {name}: {config['description']} (port {config['port']})")
        print("\nUsage:")
        print("  python run_mcp_servers.py <server_name>")
        print("  python run_mcp_servers.py all")
        print("\nTo run individual servers manually:")
        for name, config in SERVERS.items():
            print(f"  python {config['file']}")
        return
    
    server_name = sys.argv[1].lower()
    
    if server_name == "all":
        print("Running all MCP servers...")
        for name in SERVERS:
            run_standalone(name)
    elif server_name in SERVERS:
        run_standalone(server_name)
    else:
        print(f"Unknown server: {server_name}")
        print(f"Available: {', '.join(SERVERS.keys())}")


if __name__ == "__main__":
    main()
