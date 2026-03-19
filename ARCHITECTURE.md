# Dr. Ikechukwu PA - Multi-Agent AI System Architecture

## Executive Summary
`dr_ikechukwu_pa` is a state-of-the-art multi-agent and multimodal application that unifies four distinct domains (Clinical, Finance, Fashion, and AI-Dev) under a single FastAPI gateway. The system enforces strict Pydantic V2 output schemas, utilizes OpenRouter for entirely free multimodal inference, and relies on a React/Vite frontend with Material UI featuring a modern dark theme with glass morphism effects.

## 1. Core Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend API** | FastAPI (async) | REST API gateway with rate limiting, CORS, structured logging |
| **Frontend** | React + Vite + TypeScript | SPA with MUI components, React Router, toast notifications |
| **Frontend Theme** | MUI Dark Theme + Glass Morphism | Modern dark UI with backdrop blur effects |
| **CDS Orchestration** | CrewAI (Hierarchical) | 15-agent medical team with specialist coordination |
| **Finance Orchestration** | CrewAI (Hierarchical) | Reflection pattern with human-in-the-loop approval |
| **AI-Dev Orchestration** | LangGraph | Cyclic state machine: Write → Execute → Evaluate → Fix |
| **Fashion Pipeline** | Direct LangChain | Low-latency single-pass generation |
| **LLM Provider** | OpenRouter | Free-tier multimodal inference |
| **Conversation Memory** | Qdrant + sentence-transformers | Vector embeddings for context |
| **MCP Servers** | FastMCP | Standalone tool servers for Clinical, Finance, Fashion |

---

## 2. OpenRouter LLM Factory Configuration

Domain-specific model routing configured in [`backend/app/core/config.py`](backend/app/core/config.py:34):

| Domain | OpenRouter Model | Modality | Purpose |
|--------|------------------|----------|---------|
| **Clinical (CDS)** | `qwen/qwen3-vl-30b-a3b-thinking` | Text + Vision | Multimodal patient analysis (thoracic scans, skin lesions) |
| **Finance** | `openai/gpt-oss-120b:free` | Text | High-reasoning reflection workflows |
| **AI-Dev** | `stepfun/step-3.5-flash:free` | Text | Fast, high-context code generation |
| **Fashion** | `google/gemma-3-27b-it:free` | Text + Vision | Image analysis + trend generation |

*Note: All images must be converted to base64 via [`backend/app/utils/image_processor.py`](backend/app/utils/image_processor.py) before OpenRouter API calls.*

---

## 3. Directory Structure

```
dr_ikechukwu_pa/
├── frontend/                          # React/Vite SPA
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Dashboard.tsx          # Landing page with domain cards (dark theme)
│   │   │   ├── Clinical.tsx           # Clinical decision support + Medical Research UI
│   │   │   ├── Finance.tsx           # Financial analysis UI (dark theme)
│   │   │   ├── Fashion.tsx           # Fashion analysis UI
│   │   │   └── AIDev.tsx             # Code generation UI (dark theme)
│   │   ├── services/api.ts           # API client with medical research method
│   │   ├── App.tsx                   # Router + MUI dark theme + sidebar
│   │   ├── main.tsx                  # Entry point
│   │   └── index.css                 # Global dark theme styles
│   └── package.json
│
└── backend/
    ├── app/
    │   ├── main.py                    # FastAPI entry + middleware + routers
    │   ├── api/
    │   │   ├── routes_cds.py          # CDS endpoints (analyze + query)
    │   │   ├── routes_finance.py      # Finance endpoints
    │   │   ├── routes_aidev.py        # AI-Dev endpoints
    │   │   └── routes_fashion.py      # Fashion endpoints
    │   ├── core/
    │   │   ├── config.py              # OpenRouter factory + App settings
    │   │   ├── schemas.py             # Pydantic V2 schemas (all domains)
    │   │   ├── memory.py              # Qdrant client + embeddings
    │   │   └── conversation.py        # Conversation management
    │   ├── orchestrators/
    │   │   ├── crews/
    │   │   │   ├── cds_crew.py       # 15-agent Clinical crew
    │   │   │   └── finance_crew.py    # Finance crew with reflection
    │   │   └── graphs/
    │   │       └── aidev_graph.py    # LangGraph code generation
    │   ├── tools/
    │   │   ├── mcp_client.py          # MCP tool wrappers
    │   │   └── mcp_servers.py         # MCP server utilities
    │   └── utils/
    │       ├── image_processor.py      # Base64 image encoding
    │       └── security.py             # Auth utilities
    │
    ├── mcp_servers/
    │   ├── clinical_mcp_server.py     # Clinical tools (drug interactions, guidelines)
    │   ├── finance_mcp_server.py      # Finance tools (portfolio analysis)
    │   └── fashion_mcp_server.py      # Fashion tools (trend analysis)
    │
    ├── requirements.txt
    └── run_mcp_servers.py             # MCP server launcher
```

---

## 4. Implemented Features

### 4.1 Clinical Decision Support (CDS)
- **15 specialist agents**: Coordinator, Pediatrics, OBGYN, Internal Medicine, Surgery, Psychiatry, Pathology, Pharmacology, Radiology, Family Medicine, Community Medicine, Ophthalmology, Anesthesia, Emergency
- **Additional agents**: Medical Researcher, Treatment Advisor
- **Task-based tools**: Drug interactions, clinical guidelines lookup, medical literature search
- **Multimodal**: Supports medical images alongside patient data
- **Medical Research Query**: Evidence-backed responses for doctors with sources and evidence levels

### 4.2 Finance
- **4-agent crew**: Financial Analyzer, Investment Advisor, Risk Assessor, Financial Strategy Director
- **Reflection pattern**: 3 iteration feedback loop between analysts and risk assessor
- **Human-in-the-loop**: Users approve/modify preliminary recommendations
- **Tools**: Investment returns calculator, budget analyzer, exchange rates, company financials

### 4.3 AI-Dev
- **LangGraph workflow**: Write Code → Execute → Evaluate → Fix (cyclic, max 5 iterations)
- **TypedDict state**: Full type safety for state management
- **MemorySaver**: Checkpoint persistence for long-running tasks
- **Code generation + debugging** modes

### 4.4 Fashion
- **Direct LangChain pipeline**: Single-pass generation (no orchestration overhead)
- **Vision support**: Image upload + analysis
- **Trend generation**: Style recommendations based on uploaded images

---

## 5. Frontend Design System

### 5.1 Dark Theme Features
- **Glass morphism**: Semi-transparent cards with backdrop blur
- **Gradient accents**: Teal (#14B8A6) to purple (#A78BFA) color scheme
- **Custom scrollbar**: Gradient-styled with dark track
- **Animated elements**: Fade-in, slide-in, glow effects
- **Responsive sidebar**: 280px drawer with navigation items
- **Evidence level badges**: Color-coded badges for clinical evidence (guidelines, RCT, cohort, etc.)

### 5.2 Component Styling
- **Cards**: `rgba(15, 23, 42, 0.6)` background with `blur(20px)` backdrop filter
- **Borders**: `1px solid rgba(148, 163, 184, 0.1)`
- **Gradients**: Radial gradients for background atmosphere effects
- **Hover states**: Gradient backgrounds with increased opacity

---

## 6. Security & Observability

| Feature | Implementation |
|---------|---------------|
| **Rate Limiting** | slowapi (10 req/60s default) |
| **Auth** | JWT (HS256) with python-jose |
| **Structured Logging** | structlog (JSON output) |
| **Request Tracing** | X-Request-ID middleware |
| **Error Handling** | Global exception handler |
| **Health Checks** | `/health` endpoint with memory service status |

---

## 7. API Endpoints

| Domain | Prefix | Key Endpoints |
|--------|--------|----------------|
| **CDS** | `/api/cds` | `POST /analyze` - Patient analysis with 15 agents |
| **CDS** | `/api/cds` | `POST /query` - Medical research query (evidence-backed) |
| **Finance** | `/api/finance` | `POST /analyze` - Financial analysis with reflection |
| **Finance** | `/api/finance/approve` | `POST /` - Human approval processing |
| **AI-Dev** | `/api/aidev` | `POST /generate` - Code generation |
| **AI-Dev** | `/api/aidev/debug` | `POST /` - Code debugging |
| **Fashion** | `/api/fashion` | `POST /analyze` - Fashion analysis |

---

## 8. Data Schemas

All outputs constrained via Pydantic V2 in [`backend/app/core/schemas.py`](backend/app/core/schemas.py):

- `CDSResponse`, `PatientInfo`, `SpecialistConsultationResponse`
- `MedicalResearchRequest`, `MedicalResearchResponse` - Evidence-backed queries
- `FinanceResponse`, `FinancialQuery`, `InvestmentPortfolio`
- `CodeGenerationResponse`, `CodeDebugResponse`
- `FashionResponse`, `FashionQuery`

---

## 9. Development Status

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | ✅ Complete | FastAPI with all 4 domain routes |
| CDS Crew | ✅ Complete | 15 agents with hierarchical process |
| Finance Crew | ✅ Complete | Reflection pattern + human approval |
| AI-Dev Graph | ✅ Complete | LangGraph with 5-iteration limit |
| Fashion Pipeline | ✅ Complete | Direct LangChain invocation |
| MCP Servers | ✅ Complete | Clinical, Finance, Fashion tools |
| Frontend | ✅ Complete | Dashboard + 4 domain pages + dark theme |
| Medical Research Query | ✅ Complete | Evidence-backed CDS query endpoint |
| Pydantic Schemas | ✅ Complete | All domains fully typed |
| Memory/Embeddings | ✅ Complete | Qdrant + sentence-transformers |
| Security | ✅ Complete | JWT, rate limiting, structured logging |
| Tests | 🔲 Pending | Test directory exists, not populated |

---

## 10. Environment Variables

Required in `.env`:
```
OPENROUTER_API_KEY=<your-key>
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_URL=redis://localhost:6379
SECRET_KEY=<production-secret>
```

---

*Last Updated: 2026-03-17*
*This document is iteratively updated as the system evolves.*

---

## 11. How to Run the Application

### Prerequisites
- Python 3.10+
- Node.js 18+
- OpenRouter API key (set in `.env`)

### Step 1: Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2: Install Frontend Dependencies
```bash
cd frontend
npm install
```

### Step 3: Configure Environment Variables
Create a `.env` file in the `backend/` directory:
```env
OPENROUTER_API_KEY=your_openrouter_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
REDIS_URL=redis://localhost:6379
SECRET_KEY=your_secret_key_here
```

### Step 4: Start Required Services

**Option A: Using Docker (recommended)**
```bash
# Start Qdrant (vector database)
docker run -p 6333:6333 qdrant/qdrant

# Start Redis (caching)
docker run -p 6379:6379 redis:alpine
```

**Option B: Windows without Docker**

For Qdrant:
1. Download Qdrant from https://github.com/qdrant/qdrant/releases
2. Extract and run: `qdrant.exe` (starts on port 6333)

For Redis:
1. Download Redis from https://github.com/tporadowski/redis/releases
2. Run: `redis-server.exe`

**Option C: Skip external services (development only)**
The application will work without Qdrant/Redis but conversation memory won't persist. Set these in `.env`:
```env
QDRANT_HOST=localhost
QDRANT_PORT=6333
# Comment out or use dummy values if services unavailable
```

### Step 5: Run the Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```
The API will be available at `http://localhost:8000`

### Step 6: Run the Frontend
```bash
cd frontend
npm run dev
```
The frontend will be available at `http://localhost:5173`

### Optional: Run MCP Servers
```bash
# Run individual MCP servers
cd backend
python -m uvicorn mcp_servers.clinical_mcp_server:mcp --port 8001
python -m uvicorn mcp_servers.finance_mcp_server:mcp --port 8002
python -m uvicorn mcp_servers.fashion_mcp_server:mcp --port 8004
```
