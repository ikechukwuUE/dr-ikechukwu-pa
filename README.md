# Vogue Space - Dr. Ikechukwu's Personal Assistant

A domain-specialized multi-agent AI system built on four expert pipelines: **Medicine, Finance, Coding, and Fashion**. Each domain contains dedicated agents orchestrated through BeeAI Framework, with MCP (Model Context Protocol) providing a standardized tool layer.

## 🎯 System Overview

Vogue Space is designed to serve as Dr. Ikechukwu's personal AI assistant, combining medical expertise with financial planning, coding assistance, and fashion advisory capabilities.

### Architecture

```
React Frontend
      │ HTTP (JSON)
      ▼
Flask API Gateway (backend/app.py)
      │ Async dispatch
      ▼
Domain Pipelines (Medicine | Finance | Coding | Fashion)
      │ State transitions
      ▼
BeeAI RequirementAgents (8+ agents per domain)
      │ Tool calls via MCP
      ▼
MCP Server (domain tools + built-in tools)
      │ External APIs + Code Execution
      ▼
beeai-code-interpreter (optional - for real code execution)
      ▼
Result → JSON Response → React
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenRouter API Key
- Docker & Docker Compose (recommended for full functionality)

### Option 1: Docker Deployment (Recommended)

```bash
# Clone and navigate to project
cd dr_ikechukwu_pa

# Start all services
docker-compose up -d

# Services will be available at:
# - Frontend: http://localhost:5173
# - Backend API: http://localhost:5000
# - MCP Server: http://localhost:8001/mcp
# - Code Interpreter: http://localhost:50081
```

### Option 2: Manual Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
python app.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## 📁 Project Structure

```
dr_ikechukwu_pa/
├── docker-compose.yml               # Docker services
├── ARCHITECTURE.md                  # Detailed architecture
├── README.md                        # This file
├── backend/
│   ├── app.py                       # Flask API Gateway
│   ├── Dockerfile                   # Backend container
│   ├── requirements.txt             # Python dependencies
│   ├── .env                         # Configuration
│   ├── domains/
│   │   ├── medicine/
│   │   │   ├── agents/agents.py    # 20+ medical agents
│   │   │   └── workflows/pipelines.py
│   │   ├── finance/
│   │   │   ├── agents/agents.py     # 6 financial agents
│   │   │   └── workflows/pipelines.py
│   │   ├── coding/
│   │   │   ├── agents/agents.py     # 4 coding agents
│   │   │   └── workflows/pipelines.py
│   │   └── fashion/
│   │       ├── agents/agents.py      # 4 fashion agents
│   │       └── workflows/pipelines.py
│   ├── mcp_servers/
│   │   └── server.py                 # MCP server (8 domain tools)
│   ├── mcp_clients/
│   │   └── client.py                 # MCP client utilities
│   └── shared/
│       ├── schemas.py                # Pydantic V2 models
│       ├── prompts.py                # Agent prompts
│       ├── utils.py                  # Shared utilities
│       └── image_utils.py            # Image processing
└── frontend/
    └── src/
        ├── pages/                    # React pages
        ├── services/api.ts            # API client
        └── components/                # UI components
```

## 🔌 API Endpoints

### Medicine Domain

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/medicine/qa` | Medical question answering |
| POST | `/api/medicine/research` | Medical research queries |
| POST | `/api/medicine/clinical` | Clinical Decision Support (CDS) |
| POST | `/api/medicine/clinical/approve` | Human-in-the-loop approval |
| GET | `/api/medicine/news` | Latest medical news |

### Finance Domain

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/finance/qa` | Financial question answering |
| POST | `/api/finance/investment` | Investment planning |
| GET | `/api/finance/news` | Latest financial news |

### Coding Domain

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/coding/generate` | Code generation with review |
| POST | `/api/coding/review` | Standalone code review |
| POST | `/api/coding/debug` | Standalone code debugging |
| GET | `/api/coding/news` | Latest AI/coding news |

### Fashion Domain

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/fashion/analyze` | Outfit analysis |
| GET | `/api/fashion/trends` | Current fashion trends |
| POST | `/api/fashion/recommend` | Personalized recommendations |

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | System health status |

## 🤖 Agent Architecture

### Medicine (20+ Agents)
- **Coordinator** - Entry point, classifies request
- **Triage** - Urgency assessment
- **Emergency Physician** - Critical care
- **Specialist** - Dynamic routing to 12 specialties
- **Doctor_User** - Human-in-the-loop approval
- **Researcher** - Literature review
- **Scientific Writer** - Document formatting
- **Clinical Management Agent** - Care plans

**12 Specialist Agents**: Internal Medicine, Surgery, Pediatrics, OB/GYN, Pharmacy, Pathology, Radiology, Anesthesiology, Family Medicine, Community Medicine, Psychiatry, Ophthalmology

### Finance (6 Agents)
- **Financial Coach** - Personalized guidance
- **Writer** - Document formatting
- **Aggressive Persona** - High-growth strategy
- **Conservative Persona** - Capital preservation
- **Risk Assessor** - Portfolio risk (loop ≤3)
- **News Anchor** - Market news

### Coding (4 Agents)
- **Code Generator** - Production code
- **Code Reviewer** - Security/style review
- **Code Debugger** - Systematic fixes
- **News Anchor** - AI/ML news

### Fashion (4 Agents)
- **Outfit Descriptor** - Image analysis
- **Outfit Analyzer** - Evaluation
- **Style Trend Analyzer** - Trend tracking
- **Style Planner** - Personal styling

## 🔧 Configuration

```env
# OpenRouter (required)
OPENROUTER_API_KEY=your_key_here

# MCP Server (for domain tools)
MCP_SERVER_URL=http://127.0.0.1:8001/mcp

# Code Interpreter (optional - for real code execution)
CODE_INTERPRETER_URL=http://127.0.0.1:50081

# Domain Models (free tier)
MEDICINE_MODEL=openai:nvidia/nemotron-nano-12b-v2-vl:free
FINANCE_MODEL=openai:stepfun/step-3.5-flash:free
AIDEV_MODEL=openai:stepfun/step-3.5-flash:free
FASHION_MODEL=openai:nvidia/nemotron-nano-12b-v2-vl:free
```

## 🛠️ Technologies

### Backend
- **Flask** - REST API Gateway
- **BeeAI Framework** - RequirementAgents + Workflows
- **MCP** - Model Context Protocol
- **Pydantic V2** - Data validation
- **OpenRouter** - Free LLM routing
- **GlobalTrajectoryMiddleware** - Agent monitoring

### Frontend
- **React 18** + Vite
- **MUI** - Component library
- **React Markdown** - Formatting
- **Zustand** - State management
- **Axios** - HTTP client

### Docker Services
- **beeai-code-interpreter** - Real Python code execution
- **mcp-server** - Domain tools via MCP

## ✨ Key Features

- **20+ Medical Specialists** - Dynamic routing based on triage
- **Parallel Investment Personas** - Aggressive & Conservative simultaneously
- **Code Execution** - Real Python via beeai-code-interpreter
- **MCP Tools** - Unified tool layer across domains
- **Agent Monitoring** - GlobalTrajectoryMiddleware for debugging
- **Structured Output** - Pydantic schemas with expected_output
- **Parallel Tool Calls** - Enabled for all agents
- **Human-in-the-Loop** - Doctor approval gate for clinical decisions

## 📜 License

Proprietary software for Dr. Ikechukwu's personal use.

---

**Vogue Space** - Your Personal AI Assistant, Built with Precision.
