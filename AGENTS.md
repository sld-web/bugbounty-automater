# Bug Bounty Automator - Agent Instructions

This document provides guidance for AI agents working on this codebase.

## Architecture Overview

The Bug Bounty Automator is a semi-automated security testing platform with these core components:

1. **Backend (FastAPI)**: REST API, orchestration engine, plugin execution
2. **Frontend (Electron + React)**: Desktop app with interactive flowchart UI
3. **Plugins**: Docker-isolated security tools

## Key Design Patterns

### 1. Plugin Architecture
- Each plugin is a Docker container with a `plugin.json` manifest
- Plugins declare: name, version, permission_level, inputs, outputs, timeout
- Permission levels: `SAFE` (recon only), `LIMITED` (controlled), `DANGEROUS` (exploitation)

### 2. State Machine (Orchestrator)
- Targets follow: `PENDING → RUNNING → PAUSED → COMPLETED/FAILED`
- Each target has a DAG of phases
- Human approval required at configurable checkpoints

### 3. Approval Workflow
- Risk score determines if action needs approval
- Low risk → auto-run
- Medium risk → optional approval
- High risk → mandatory approval

### 4. Program Configuration Schema
```json
{
  "program_name": "string",
  "scope": {
    "domains": ["*.example.com"],
    "excluded": ["*.staging.example.com"]
  },
  "campaigns": [],
  "priority_areas": [],
  "out_of_scope_vulnerabilities": [],
  "severity_mapping": {},
  "reward_tiers": {}
}
```

## Adding a New Plugin

1. Create directory: `plugins/<plugin_name>/`
2. Add `plugin.json` with metadata
3. Create `Dockerfile` based on template
4. Create `run.py` entrypoint
5. Register in plugin registry

## Database Models

- `Program`: Bug bounty program configuration
- `Target`: Individual target (domain, IP, etc.)
- `Finding`: Discovered vulnerability
- `FlowCard`: Testing workflow card
- `ApprovalRequest`: Pending human decision
- `PluginRun`: Plugin execution record

## API Conventions

- All endpoints return JSON
- Use Pydantic schemas for validation
- Include pagination for list endpoints
- Return appropriate HTTP status codes

## Security Considerations

- Never log API keys or secrets
- Validate all user inputs
- Sanitize plugin outputs before storage
- Always check scope before executing plugins
