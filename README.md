# Bug Bounty Automator

A modular, semi-automated bug hunting platform that adapts to any bug bounty program.

## Features

- **Modular Architecture**: Pluggable security tools (Amass, Nmap, Nuclei, etc.)
- **Program Ingestion**: AI-assisted conversion of program policies to structured configs
- **Human-in-the-Loop**: Approval workflow for risky actions
- **Intelligence Layer**: CVE feeds, GitHub monitoring, leak detection
- **Progress Tracking**: Interactive flowchart dashboard
- **Risk Scoring**: Automated risk assessment before actions

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Program       │     │   Scope Guard   │     │   Orchestrator  │
│   Ingestion     │────▶│     Engine      │────▶│   (Risk Engine) │
│ (Hybrid Parser) │     │ (Filter assets) │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                          │
                                                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Plugin Isolation Layer                        │
│  (Docker containers with permission levels: SAFE, LIMITED, DANGEROUS)│
└─────────────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- API keys (see `.env.example`)

### Installation

1. Clone the repository
2. Copy environment file: `cp .env.example .env`
3. Edit `.env` with your API keys
4. Build and start:

```bash
# Start all services
docker-compose up -d

# Or for development with hot-reload
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d
```

5. Access the app at `http://localhost:5173`

### Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py  # Load sample programs
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Project Structure

```
bugbounty-automater/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # REST endpoints
│   │   ├── core/     # Business logic
│   │   ├── models/   # Database models
│   │   ├── services/ # External integrations
│   │   └── ingestion/# Program parsing
│   └── plugins/      # Plugin definitions
├── frontend/         # Electron + React app
│   └── src/
│       ├── components/  # React components
│       └── pages/      # App pages
├── plugins/          # Security tool plugins
│   ├── amass/
│   ├── nmap/
│   ├── nuclei/
│   ├── subfinder/
│   └── httpx/
└── docker/           # Docker configuration
```

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Plugins

| Plugin | Permission | Description |
|--------|-------------|-------------|
| Amass | SAFE | Subdomain enumeration |
| Subfinder | SAFE | Passive subdomain discovery |
| Nmap | SAFE | Port scanning |
| httpx | LIMITED | HTTP probing |
| Nuclei | LIMITED | Vulnerability scanning |

## License

MIT
