# Bug Bounty Automator - Project Context

## Overview
This is a modular, semi-automated bug hunting platform designed to adapt to any bug bounty program. The system orchestrates security testing tools while maintaining human oversight for critical decisions.

## Key Components

### Backend (FastAPI)
- **Location**: `backend/app/`
- **Key Files**:
  - `main.py`: FastAPI application entry point
  - `orchestrator.py`: DAG-based testing workflow engine
  - `approval_manager.py`: Human-in-the-loop approval queue
  - `risk_engine.py`: Risk scoring calculator
  - `plugin_runner.py`: Docker container execution for security tools

### Frontend (Electron + React)
- **Location**: `frontend/`
- **Stack**: React 18, TypeScript, TailwindCSS, React Flow
- **Desktop Features**: Auto-updater, system tray, native notifications

### Plugins
- **Location**: `plugins/`
- **Current Plugins**: Amass, Nmap, Nuclei, Subfinder, httpx
- **Execution**: Docker containers with permission levels

## Environment Variables
Copy `.env.example` to `.env` and configure:
- Database (PostgreSQL)
- Redis for task queue
- API keys for external services
- Notification settings (Slack, Email)

## Database
- PostgreSQL with SQLAlchemy ORM
- Alembic for migrations
- Seed data includes: Eternal, X, PayPal programs

## Getting Started
```bash
docker-compose up -d
# Access at http://localhost:5173
```

## Important Rules
1. Never commit secrets or API keys
2. Always validate scope before running plugins
3. Require human approval for DANGEROUS permission level actions
4. Log all approval decisions for audit trail
