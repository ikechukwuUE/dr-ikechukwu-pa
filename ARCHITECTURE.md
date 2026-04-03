# ARCHITECTURE.md — Multi-Agent AI System

## MCP + BeeAI + Flask + React

---

## 1. System Overview

A domain-specialized multi-agent AI system built on four expert pipelines: **Medicine, Finance, Coding, and Fashion**. Each domain contains dedicated agents orchestrated through BeeAI Workflows, with MCP providing a standardized tool layer. Flask serves as the HTTP API gateway, and React provides the frontend.

### Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React + MUI | User interface with domain tabs |
| API Gateway | Flask | REST endpoints, request routing |
| Orchestration | BeeAI Framework | Workflows + RequirementAgents |
| Tool Layer | MCP (Model Context Protocol) | Domain-specific tools exposed as MCP servers |
| LLM Backend | OpenRouter (Free Models) | Configurable via `openrouter_config` |
| State | Pydantic V2 Models | Typed data passed between agents |

### Data Flow

```
React Frontend
     │ HTTP (JSON)
     ▼
Flask API (app.py)
     │ Async dispatch
     ▼
BeeAI Workflow
     │ State transitions
     ▼
RequirementAgents (per step)
     │ Tool calls via MCP
     ▼
MCP Server (domain tools)
     │ External APIs
     ▼
Result → back through the chain → JSON response → React
```

---

## 2. Project Structure

```
dr_ikechukwu_pa/
├── README.md
├── ARCHITECTURE.md                          ← This file
├── docker-compose.yml                       # Docker services for code execution
├── backend/
│   ├── app.py                               # Flask API — all routes
│   ├── Dockerfile                           # Backend container definition
│   ├── requirements.txt                     # Dependencies
│   ├── .env                                  # Configuration (API keys)
│   ├── domains/
│   │   ├── medicine/
│   │   │   ├── agents/agents.py             # 20+ agents (8 original + 12 specialists)
│   │   │   └── workflows/pipelines.py       # 4 workflow pipelines
│   │   ├── finance/
│   │   │   ├── agents/agents.py              # 6 agent definitions
│   │   │   └── workflows/pipelines.py       # 3 workflow pipelines
│   │   ├── coding/
│   │   │   ├── agents/agents.py              # 4 agent definitions
│   │   │   └── workflows/pipelines.py       # 4 workflow pipelines
│   │   └── fashion/
│   │       ├── agents/agents.py              # 4 agent definitions
│   │       └── workflows/pipelines.py       # 3 workflow pipelines
│   ├── mcp_servers/
│   │   └── server.py                        # MCP server with 8 domain tools
│   ├── mcp_clients/
│   │   └── client.py                        # MCP client utilities
│   └── shared/
│       ├── schemas.py                       # All Pydantic V2 models
│       ├── prompts.py                       # All agent prompts
│       ├── utils.py                         # Shared utilities
│       └── image_utils.py                   # Image processing utilities
├── frontend/
│   └── src/
│       ├── pages/                           # React pages
│       ├── services/api.ts                  # API client
│       └── components/                      # UI components
└── plans/                                   # Architecture diagrams and plans
```

---

## 3. Domain A — Medicine

### 3.1 Agent Stack (20+ agents: 8 core + 12 specialists + human role)

#### Core Agents (8)
| # | Agent | Role | Responsibility |
|---|-------|------|---------------|
| 1 | **Coordinator** | Orchestrator | Entry point — classifies request into correct pipeline |
| 2 | **Triage** | Classifier | Assesses urgency, routes to specialty |
| 3 | **Emergency Physician** | Acute care | Handles EMERGENCY cases |
| 4 | **Specialist** | Domain expert | Dynamic routing to 12 specialty agents |
| 5 | **Doctor_User** | 👨‍⚕️ HUMAN | Human-in-the-loop approval |
| 6 | **Researcher** | Literature review | Deep-dives into medical research |
| 7 | **Scientific Writer** | Formatter | Transforms output into medical documents |
| 8 | **Clinical Management Agent** | Care planner | Creates evidence-based management plans |

#### Specialist Agents (12)
Internal Medicine, General Surgery, Pediatrics, OB/GYN, Pharmacy, Pathology, Radiology, Anesthesiology, Family Medicine, Community Medicine, Psychiatry, Ophthalmology

### 3.2 Pipelines

#### Pipeline 1: Clinical Decision Support (CDS)
```
Patient Info → Coordinator → Triage → [Emergency if EMERGENCY] → Specialist
    → Doctor_User (human gate) → Clinical Management → Management Plan
```

#### Pipeline 2: Medical Q&A
```
User Query → Coordinator → Triage → Specialist → Scientific Writer → Answer
```

#### Pipeline 3: Research
```
Research Question → Coordinator → Researcher → Specialist → Writer → Manuscript
```

#### Pipeline 4: News
```
Page Load → News Anchor → Medical News Report
```

---

## 4. Domain B — Finance

### 4.1 Agent Stack (6 agents)

| # | Agent | Role |
|---|-------|------|
| 1 | **Financial Coach** | Advisor |
| 2 | **Writer** | Formatter |
| 3 | **Aggressive Persona** | Risk-on strategist |
| 4 | **Conservative Persona** | Risk-off strategist |
| 5 | **Risk Assessor** | Evaluator (loop ≤3) |
| 6 | **News Anchor** | Reporter |

### 4.2 Pipelines

#### Pipeline 1: Finance Q&A
```
Query → Financial Coach → Writer → Response
```

#### Pipeline 2: Investment Planning
```
Investor Info → [Aggressive ∥ Conservative] → Risk Assessor (loop) → Writer → Plan
```

#### Pipeline 3: News
```
Trigger → News Anchor → Report
```

---

## 5. Domain C — Coding

### 5.1 Agent Stack (4 agents)

| # | Agent | Role |
|---|-------|------|
| 1 | **Code Generator** | Developer |
| 2 | **Code Reviewer** | Senior reviewer |
| 3 | **Code Debugger** | Debugger |
| 4 | **News Anchor** | Reporter |

### 5.2 Pipelines

#### Pipeline 1: Generate → Review → Debug (loop)
```
Description → Generator → Reviewer → [approved? → END : Debugger → Reviewer]
```

#### Pipeline 2-4: Review, Debug, News

---

## 6. Domain D — Fashion

### 6.1 Agent Stack (4 agents)

| # | Agent | Role |
|---|-------|------|
| 1 | **Outfit Descriptor** | Analyst (image analysis) |
| 2 | **Outfit Analyzer** | Consultant |
| 3 | **Style Trend Analyzer** | Trendspotter |
| 4 | **Style Planner** | Personal stylist |

### 6.2 Pipelines

#### Pipeline 1: Outfit Analysis
```
Image → Outfit Descriptor → Outfit Analyzer → Analysis
```

#### Pipeline 2: Trend Analysis
```
Query → Trend Analyzer → Report
```

#### Pipeline 3: Outfit Recommendation
```
Budget + Occasion + Time + Location → Trend Analyzer → Planner → Recommendation
```

---

## 7. MCP Tool Server

The MCP server exposes domain-specific tools via Model Context Protocol.

### Registered Tools

| Tool | Domain | Description |
|------|--------|-------------|
| `medical_database_search` | Medicine | Clinical guidelines & drug info |
| `lab_value_interpreter` | Medicine | Lab value interpretation |
| `stock_price_lookup` | Finance | Stock price & performance |
| `risk_calculator` | Finance | Portfolio risk metrics |
| `code_executor` | Coding | Sandboxed code execution |
| `documentation_search` | Coding | Programming docs |
| `fashion_trend_api` | Fashion | Fashion trends |
| `price_comparison` | Fashion | Price comparison |

### BeeAI Built-in Tools
The MCP server also exposes:
- `DuckDuckGoSearchTool` - Web search
- `OpenMeteoTool` - Weather data
- `PythonTool` - Real Python code execution (requires beeai-code-interpreter)

### Configuration

```python
# MCP Server runs on port 8001
config = MCPServerConfig(
    transport="streamable-http",
    settings=MCPSettings(port=8001),
)
```

---

## 8. Shared Components

### Image Processing (`shared/image_utils.py`)
- `encode_image_to_base64()` - Convert images to base64
- `create_openrouter_multimodal_message()` - Create multimodal messages for vision models

### MCP Client (`mcp_clients/client.py`)
- `get_mcp_tools()` - Fetch tools from any MCP server
- `create_mcp_agent()` - Create RequirementAgent with MCP tools

### Agent Monitoring
All agents use `GlobalTrajectoryMiddleware` for trajectory monitoring and debugging.

---

## 9. Environment Configuration

```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxx
