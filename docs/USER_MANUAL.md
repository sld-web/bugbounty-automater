# Bug Bounty Automator - User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Managing Programs](#managing-programs)
4. [Target Management](#target-management)
5. [Credential Management](#credential-management)
6. [Testing Workflow](#testing-workflow)
7. [Approval System](#approval-system)
8. [Reporting](#reporting)
9. [API Reference](#api-reference)

---

## Introduction

The Bug Bounty Automator is a semi-automated security testing platform that helps researchers efficiently test bug bounty programs while maintaining safety and compliance.

### Key Features

- **Modular Architecture**: Pluggable security tools (Amass, Nmap, Nuclei, etc.)
- **Program Ingestion**: AI-assisted conversion of program policies to structured configs
- **Human-in-the-Loop**: Approval workflow for risky actions
- **Intelligence Layer**: CVE feeds, GitHub monitoring, leak detection
- **Progress Tracking**: Interactive flowchart dashboard
- **Risk Scoring**: Automated risk assessment before actions

---

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+ (for frontend)
- API keys for external services (optional)

### Installation

1. Clone the repository
2. Copy environment file: `cp .env.example .env`
3. Edit `.env` with your API keys
4. Build and start:

```bash
docker-compose up -d
```

Or for development:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

cd frontend
npm install
npm run dev
```

### Accessing the Platform

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Frontend**: http://localhost:5173

---

## Managing Programs

### Creating a Program

Programs define the scope and rules for bug bounty testing.

```bash
curl -X POST http://localhost:8000/api/programs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example Program",
    "url": "https://example.com",
    "scope": {
      "domains": ["*.example.com"],
      "excluded": ["*.staging.example.com"]
    }
  }'
```

### Program Configuration

| Field | Description |
|-------|-------------|
| `name` | Program name |
| `url` | Program URL |
| `scope.domains` | In-scope domains |
| `scope.excluded` | Out-of-scope domains |
| `auth_level` | Authentication requirement (L0-L4) |
| `credential_policy` | Credential handling rules |

### Authentication Levels

| Level | Name | Description |
|-------|------|-------------|
| L0 | No Auth | Public testing only |
| L1 | Optional | Can test with or without credentials |
| L2 | Required | Valid credentials required |
| L3 | Program-Provided | Must use program-provided account |
| L4 | Domain-Validated | Email must match program domain |

---

## Target Management

### Adding a Target

```bash
curl -X POST http://localhost:8000/api/targets \
  -H "Content-Type: application/json" \
  -d '{
    "program_id": "program-uuid",
    "name": "api.example.com",
    "target_type": "domain"
  }'
```

### Target Types

- `domain` - Domain names
- `ip` - IP addresses
- `url` - Specific URLs
- `api` - API endpoints

---

## Credential Management

### Adding Credentials

```bash
curl -X POST http://localhost:8000/api/credentials \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Key for Example",
    "credential_type": "api_key",
    "api_key": "your-api-key",
    "program_id": "program-uuid"
  }'
```

### Credential Types

| Type | Fields |
|------|--------|
| `user_pass` | username, password |
| `api_key` | api_key |
| `session_token` | token |
| `certificate` | cert_file, key_file |
| `totp` | secret |

### Credential Expiry

Set expiration dates to ensure credentials are rotated:

```bash
curl -X POST http://localhost:8000/api/credentials \
  -d '{"expires_at": "2024-12-31T23:59:59", ...}'
```

---

## Testing Workflow

### Starting a Test

```bash
curl -X POST http://localhost:8000/api/targets/{target_id}/start
```

### Pipeline Phases

1. **Reconnaissance** - Subdomain enumeration, port scanning
2. **Discovery** - Endpoint discovery, tech stack detection
3. **Attack** - Vulnerability testing based on findings
4. **Verification** - Manual verification of findings

### Flow Cards

Flow cards represent testing workflow items:
- **Recon Card** - Reconnaissance tasks
- **Discovery Card** - Endpoint enumeration
- **Attack Card** - Vulnerability tests
- **Manual Card** - Manual testing tasks

### Plugin Execution

Plugins run in isolated Docker containers:

| Plugin | Permission | Description |
|--------|-------------|-------------|
| Amass | SAFE | Subdomain enumeration |
| Subfinder | SAFE | Passive subdomain discovery |
| Nmap | SAFE | Port scanning |
| httpx | LIMITED | HTTP probing |
| Nuclei | LIMITED | Vulnerability scanning |

---

## Approval System

### Approval Levels

Risk scores determine approval requirements:

| Risk Score | Action |
|------------|--------|
| 0-25 | Auto-approve |
| 26-50 | Optional approval |
| 51-75 | Approval required |
| 76-100 | Block with justification |

### Managing Approvals

```bash
# Approve
curl -X POST http://localhost:8000/api/approvals/{id}/approve

# Deny
curl -X POST http://localhost:8000/api/approvals/{id}/deny

# Timeout
curl -X POST http://localhost:8000/api/approvals/{id}/timeout
```

---

## Reporting

### Generating Reports

```bash
curl -X POST http://localhost:8000/api/reports/generate \
  -H "Content-Type: application/json" \
  -d '{
    "program_name": "Example",
    "target": "api.example.com",
    "findings": [...],
    "format": "html"
  }'
```

### Submitting to Platforms

```bash
# HackerOne
curl -X POST http://localhost:8000/api/reports/submit/hackerone \
  -H "Content-Type: application/json" \
  -d '{
    "program_name": "example",
    "target": "api.example.com",
    "findings": [...],
    "hackerone_api_key": "your-key"
  }'

# Bugcrowd
curl -X POST http://localhost:8000/api/reports/submit/bugcrowd \
  -H "Content-Type: application/json" \
  -d '{
    "program_name": "example",
    "target": "api.example.com",
    "findings": [...],
    "bugcrowd_api_key": "your-key"
  }'
```

---

## API Reference

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/programs` | GET, POST | List/Create programs |
| `/api/targets` | GET, POST | List/Create targets |
| `/api/credentials` | GET, POST | List/Create credentials |
| `/api/flows` | GET | Get flow cards |
| `/api/approvals` | GET | List approvals |
| `/api/plugins` | GET | List plugins |
| `/api/reports/generate` | POST | Generate report |
| `/api/intel/cve` | GET | CVE data |
| `/api/coverage/{id}` | GET | Coverage metrics |

### Authentication

Most endpoints require no authentication in development mode.
For production, set `SECRET_KEY` in environment.

---

## Troubleshooting

### Docker Not Running

```bash
# Check Docker status
docker ps

# Start Docker
sudo systemctl start docker
```

### Plugin Fails to Run

1. Check Docker socket permissions
2. Verify plugin image exists: `docker images | grep bugbounty`
3. Check plugin logs: `/api/plugins/{name}/logs`

### Database Issues

```bash
# Reset database
cd backend
rm test.db
python -c "from app.database import engine, Base; import asyncio; asyncio.run(engine.begin())"
```

---

## Support

- **GitHub Issues**: https://github.com/anomalyco/bugbounty-automater/issues
- **Documentation**: This manual

---

*Last updated: 2026-03-20*
