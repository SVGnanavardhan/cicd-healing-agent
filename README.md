# ⚡ CI/CD Healing Agent — RIFT 2026

An **Autonomous DevOps Agent** that clones, analyzes, fixes, commits, and verifies GitHub repositories without human intervention. Built for the RIFT 2026 Hackathon.

---

## 🔗 Links

| | URL |
|---|---|
| **Live Dashboard** | `https://your-app.vercel.app` |
| **API** | `https://your-app.railway.app` |
| **LinkedIn Demo Video** | `https://linkedin.com/posts/your-post` |
| **GitHub Repository** | `https://github.com/your-username/cicd-healing-agent` |

---

## 🏗 Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                  React Dashboard                     │
│   Input → Run Summary → Score → Fixes → CI/CD       │
└─────────────────────┬───────────────────────────────┘
                      │ POST /api/run
┌─────────────────────▼───────────────────────────────┐
│              FastAPI REST Backend                    │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│           Multi-Agent Pipeline (Orchestrator)        │
│                                                     │
│  ClonerAgent → AnalyzerAgent → FixerAgent           │
│                     ↑              ↓                │
│              CommitterAgent ← MonitorAgent          │
│               (loop max 5x until PASSED)            │
└─────────────────────────────────────────────────────┘
                      │
              ┌───────▼───────┐
              │  results.json │
              └───────────────┘
```

---

## 🚀 Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/your-username/cicd-healing-agent
cd cicd-healing-agent
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend:  http://localhost:8000
- API docs: http://localhost:8000/docs

### Manual

```bash
# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
uvicorn api.server:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

---

## ⚙️ Environment Setup

### Backend (`backend/.env`)

```env
MAX_ITERATIONS=5          # configurable retry limit (default: 5)
GIT_USER_NAME=CI/CD AI Agent
GIT_USER_EMAIL=ai-agent@cicd.bot
PORT=8000
RESULTS_DIR=/tmp/cicd_results
# GITHUB_TOKEN=ghp_...   # for private repos
```

### Frontend (`frontend/.env`)

```env
VITE_API_URL=http://localhost:8000
```

---

## 📖 Usage

1. Open the dashboard at `http://localhost:3000`
2. Enter a **GitHub Repository URL**
3. Enter your **Team Name** (e.g. `RIFT ORGANISERS`)
4. Enter your **Team Leader Name** (e.g. `Saiyam Kumar`)
5. Click **▶ RUN AGENT**

The agent runs autonomously for ~17 seconds (simulation) or real time on live repos, displaying live progress across all 5 dashboard panels.

---

## 🌿 Branch Naming

Format: `TEAM_NAME_LEADER_NAME_AI_Fix`

| Team Name | Leader Name | Branch |
|---|---|---|
| RIFT ORGANISERS | Saiyam Kumar | `RIFT_ORGANISERS_SAIYAM_KUMAR_AI_Fix` |
| Code Warriors | John Doe | `CODE_WARRIORS_JOHN_DOE_AI_Fix` |

Rules: all uppercase, spaces → underscores, end with `_AI_Fix`.

---

## 📋 Test Case Output Format

Judges evaluate output line-by-line. Exact format:

```
LINTING error in src/utils.py line 15 → Fix: remove the import statement
SYNTAX error in src/validator.py line 8 → Fix: add the colon at the correct position
```

---

## 🐛 Supported Bug Types

| Type | Detection | Fix |
|---|---|---|
| `LINTING` | Unused imports | Remove the import line |
| `SYNTAX` | Missing colons | Append `:` |
| `LOGIC` | Bare `except:` | Replace with `except Exception:` |
| `TYPE_ERROR` | `== None` | Replace with `is None` |
| `IMPORT` | Wildcard `import *` | Comment out |
| `INDENTATION` | Tab characters | Replace `\t` with 4 spaces |

---

## 🤖 Agent Architecture

### 5-Agent Pipeline

| Agent | Responsibility |
|---|---|
| **ClonerAgent** | `git clone` + create `TEAM_LEADER_AI_Fix` branch |
| **AnalyzerAgent** | Regex scan all `.py/.js/.ts` files → detect all 6 bug types |
| **FixerAgent** | Apply deterministic patch per bug type |
| **CommitterAgent** | `git add -A` → `[AI-AGENT] commit` → `git push` to new branch |
| **MonitorAgent** | Run `flake8` + `pytest` → return PASSED or FAILED, loop back |

### Iteration Loop

```
AnalyzerAgent → FixerAgent → CommitterAgent → MonitorAgent
      ↑                                            |
      └──────── if FAILED and iter < max ──────────┘
```

Maximum 5 iterations (configurable via `MAX_ITERATIONS` env var).

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Context API + `useReducer` |
| Backend | Python 3.11, FastAPI, Uvicorn |
| Agent | Custom multi-agent pipeline (5 agents) |
| Analysis | `flake8`, `pytest`, regex pattern matching |
| Sandbox | Docker, `tmpfs`, `mem_limit`, `security_opt` |
| Deploy | Vercel (frontend), Railway (backend) |

---

## 🚢 Production Deployment

### Frontend → Vercel

```bash
cd frontend
npm run build
# Deploy dist/ to Vercel
# Set environment variable: VITE_API_URL=https://your-backend.railway.app
```

### Backend → Railway

```bash
# Connect GitHub repo to Railway
# Set environment variables:
#   MAX_ITERATIONS=5
#   GIT_USER_NAME=CI/CD AI Agent
#   GIT_USER_EMAIL=ai-agent@cicd.bot
```

---

## 📊 Scoring

| Component | Points |
|---|---|
| Base score | 100 |
| Speed bonus (< 5 min) | +10 |
| Efficiency penalty (per commit over 20) | −2 |
| **Maximum possible** | **110** |

---

## ⚠️ Known Limitations

- Private repos require `GITHUB_TOKEN` in `.env`
- Large repos (>500 files) may hit the 120s clone timeout
- Only `.py`, `.js`, `.ts`, `.jsx`, `.tsx` files are analyzed
- Push requires write access to the target repository

---

## 👥 Team Members

| Name | Role |
|---|---|
| [Your Name] | Architecture, Agent Pipeline |
| [Member 2] | React Dashboard |
| [Member 3] | DevOps, Docker |

---

*RIFT 2026 Hackathon Submission*
