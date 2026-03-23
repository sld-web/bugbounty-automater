"""Intel API endpoints for intelligence layer."""
from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from app.models.finding import Finding, Severity
from app.services.intel.github_monitor import GitHubMonitor, LeakDetector
from app.services.intel.cve_service import CVEService, TechStackDetector

router = APIRouter(prefix="/intel", tags=["intelligence"])


class IntelFinding(BaseModel):
    source: str
    finding_type: str
    title: str
    description: str
    severity: Severity
    target_id: str | None = None
    target_pattern: str | None = None
    cve_id: str | None = None
    cwe_id: str | None = None
    evidence: dict | None = None
    public_refs: list[str] | None = None


@router.get("/cards")
async def list_intel_cards():
    """List all intelligence cards from CVE and leak monitoring."""
    from app.services.intel.cve_service import CVEService
    from app.services.intel.github_monitor import GitHubMonitor
    
    cve_service = CVEService()
    try:
        cves = await cve_service.fetch_recent_cves(limit=50)
    except Exception as e:
        cves = []
    finally:
        await cve_service.close()
    
    github_monitor = GitHubMonitor()
    try:
        leaks = await github_monitor.search_leaks("*", limit=10)
    except Exception as e:
        leaks = []
    
    return {
        "total": len(cves) + len(leaks),
        "cves": cves[:50],
        "leaks": leaks[:10],
    }


@router.post("/findings")
async def submit_intel_finding(
    finding: IntelFinding,
    background_tasks: BackgroundTasks,
):
    """Submit a potential finding from intelligence sources."""
    background_tasks.add_task(process_intel_finding, finding)
    return {"status": "queued", "message": "Finding queued for processing"}


async def process_intel_finding(finding: IntelFinding):
    """Process an intelligence finding."""
    from app.database import get_db_context

    async with get_db_context() as db:
        finding_obj = Finding(
            title=finding.title,
            description=finding.description,
            severity=finding.severity,
            target_id=finding.target_id or "",
            vuln_type=finding.finding_type,
            cve_id=finding.cve_id,
            cwe_id=finding.cwe_id,
            evidence=finding.evidence or {},
            public_refs=finding.public_refs or [],
        )

        db.add(finding_obj)
        await db.commit()


@router.get("/sources")
async def list_intel_sources():
    """List configured intelligence sources."""
    return {
        "sources": [
            {
                "name": "NVD CVE Feed",
                "enabled": True,
                "type": "cve",
                "last_poll": None,
            },
            {
                "name": "GitHub Monitor",
                "enabled": True,
                "type": "github",
                "last_poll": None,
            },
            {
                "name": "AlienVault OTX",
                "enabled": True,
                "type": "otx",
                "last_poll": None,
            },
            {
                "name": "Shodan",
                "enabled": True,
                "type": "shodan",
                "last_poll": None,
            },
        ]
    }


class GitHubSearchRequest(BaseModel):
    query: str
    language: Optional[str] = None
    limit: int = 100


class GitHubOrgMonitorRequest(BaseModel):
    organization: str
    scan_secrets: bool = True
    scan_vulnerabilities: bool = True


class ScanContentRequest(BaseModel):
    content: str
    source: str = "manual_scan"


@router.post("/github/search")
async def github_code_search(request: GitHubSearchRequest):
    """Search GitHub code for patterns.
    
    Note: GitHub API search requires authentication for most queries.
    Use a GitHub token for better rate limits and access.
    """
    monitor = GitHubMonitor()
    try:
        results = await monitor.search_code(
            query=request.query,
            language=request.language,
            limit=request.limit,
        )
        return {
            "query": request.query,
            "results_count": len(results),
            "results": results[:20],
        }
    except PermissionError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e) or "GitHub API authentication required. Please provide a GitHub token."
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="GitHub API authentication required. Please provide a GitHub token."
            )
        elif e.response.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail="GitHub API rate limit exceeded or access denied."
            )
        raise
    finally:
        await monitor.close()


@router.post("/github/monitor-org")
async def github_monitor_org(request: GitHubOrgMonitorRequest):
    """Monitor an organization for security issues."""
    monitor = GitHubMonitor()
    try:
        findings = await monitor.monitor_organization(
            org=request.organization,
        )
        return {
            "organization": request.organization,
            "findings_count": len(findings),
            "findings": findings,
        }
    finally:
        await monitor.close()


@router.get("/github/repos/{org}")
async def github_list_org_repos(org: str):
    """List repositories in an organization."""
    monitor = GitHubMonitor()
    try:
        repos = await monitor.search_repositories(
            query=f"org:{org}",
            limit=100,
        )
        return {
            "organization": org,
            "repositories_count": len(repos),
            "repositories": [
                {
                    "name": r.get("full_name"),
                    "stars": r.get("stargazers_count", 0),
                    "language": r.get("language"),
                    "url": r.get("html_url"),
                    "description": r.get("description"),
                }
                for r in repos
            ],
        }
    finally:
        await monitor.close()


@router.post("/github/scan-file")
async def github_scan_file(request: ScanContentRequest):
    """Scan content for secrets."""
    detector = LeakDetector()
    findings = detector.scan_content(
        content=request.content,
        source=request.source,
    )
    return {
        "findings_count": len(findings),
        "findings": findings,
    }


@router.post("/leak/scan")
async def scan_for_leaks(request: ScanContentRequest):
    """Scan content for leaked credentials."""
    detector = LeakDetector()
    findings = detector.scan_content(
        content=request.content,
        source=request.source,
    )
    return {
        "source": request.source,
        "findings_count": len(findings),
        "findings": findings,
    }


@router.get("/github/rate-limit")
async def github_rate_limit():
    """Check GitHub API rate limit status."""
    monitor = GitHubMonitor()
    try:
        response = await monitor.client.get("/rate_limit")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        await monitor.close()


class CVEProductRequest(BaseModel):
    product: str
    vendor: Optional[str] = None
    days_back: int = 30
    limit: int = 50


class CVECorrelateRequest(BaseModel):
    target_id: str
    target_url: str
    technologies: list[str] = []
    versions: dict[str, str] = {}


@router.get("/cve/recent")
async def get_recent_cves(days: int = Query(7, ge=1, le=90), limit: int = Query(50, ge=1, le=200)):
    """Get recent high-severity CVEs from NVD."""
    cve_service = CVEService()
    try:
        cves = await cve_service.fetch_recent_cves(days=days, limit=limit)
        return {
            "count": len(cves),
            "cves": cves,
        }
    finally:
        await cve_service.close()


@router.post("/cve/product")
async def get_cves_for_product(request: CVEProductRequest):
    """Get CVEs for a specific product."""
    cve_service = CVEService()
    try:
        cves = await cve_service.fetch_cves_for_product(
            product=request.product,
            vendor=request.vendor,
            days_back=request.days_back,
            limit=request.limit,
        )
        return {
            "product": request.product,
            "vendor": request.vendor,
            "count": len(cves),
            "cves": cves,
        }
    finally:
        await cve_service.close()


@router.post("/cve/correlate")
async def correlate_cves_to_target(request: CVECorrelateRequest):
    """Correlate CVEs to a target based on detected technologies."""
    cve_service = CVEService()
    try:
        target = {
            "id": request.target_id,
            "url": request.target_url,
            "technologies": request.technologies,
            "versions": request.versions,
        }

        all_cves = []
        for tech in request.technologies:
            cves = await cve_service.fetch_cves_for_product(
                product=tech,
                days_back=365,
                limit=20,
            )
            all_cves.extend(cves)

        matched_cves = cve_service.correlate_cves_to_target(target, all_cves)

        return {
            "target_id": request.target_id,
            "total_cves_found": len(all_cves),
            "matched_cves": len(matched_cves),
            "correlations": matched_cves,
        }
    finally:
        await cve_service.close()


@router.post("/tech/detect")
async def detect_technologies(request: ScanContentRequest):
    """Detect technologies from content."""
    cve_service = CVEService()
    detector = TechStackDetector()

    tech_stack = detector.detect_from_response(request.content, {})
    technologies = cve_service.detect_technologies(request.content)
    versions = cve_service.extract_versions(request.content)

    combined_tech = list(set(tech_stack.get("technologies", []) + technologies))

    return {
        "source": request.source,
        "technologies": combined_tech,
        "versions": versions,
        "tech_stack": tech_stack,
    }


@router.get("/cve/risk-score")
async def calculate_risk_score(
    cvss_score: float = Query(..., ge=0, le=10),
    cvss_vector: str = Query(""),
    data_sensitivity: str = Query("medium"),
    asset_tier: int = Query(2, ge=1, le=3),
):
    """Calculate adjusted risk score."""
    cve_service = CVEService()
    score = cve_service.calculate_risk_score(
        cvss_score=cvss_score,
        cvss_vector=cvss_vector,
        data_sensitivity=data_sensitivity,
        asset_tier=asset_tier,
    )
    return {
        "cvss_score": cvss_score,
        "cvss_vector": cvss_vector,
        "adjusted_risk_score": score,
        "data_sensitivity": data_sensitivity,
        "asset_tier": asset_tier,
    }


@router.get("/cve/{cve_id}")
async def get_cve_details(cve_id: str):
    """Get detailed information about a specific CVE."""
    if not cve_id.startswith("CVE-"):
        raise HTTPException(status_code=400, detail="Invalid CVE ID format")

    cve_service = CVEService()
    try:
        cves = await cve_service.fetch_cves_for_product(
            product=cve_id,
            days_back=3650,
            limit=1,
        )
        for cve in cves:
            if cve.get("cve_id") == cve_id:
                cve["cwes"] = cve_service.get_cwe_from_description(cve.get("description", ""))
                return cve

        raise HTTPException(status_code=404, detail=f"CVE {cve_id} not found")
    finally:
        await cve_service.close()


class EndpointRequest(BaseModel):
    path: str
    method: str = "GET"
    parameters: Optional[dict] = None


class AutoExpandRequest(BaseModel):
    target_id: str
    endpoints: list[EndpointRequest]


@router.post("/auto-expand")
async def auto_expand_flow_cards(request: AutoExpandRequest):
    """Auto-generate flow cards from discovered endpoints."""
    from app.services.intel.flow_generator import FlowCardGenerator

    generator = FlowCardGenerator()

    endpoints = [
        {"path": e.path, "method": e.method, "parameters": e.parameters}
        for e in request.endpoints
    ]

    flow_cards = generator.generate_flow_cards(
        endpoints=endpoints,
        target_id=request.target_id,
    )

    return {
        "target_id": request.target_id,
        "endpoints_scanned": len(endpoints),
        "flow_cards_generated": len(flow_cards),
        "flow_cards": flow_cards,
    }


class AIHypothesisRequest(BaseModel):
    target_id: str
    endpoints: list[EndpointRequest]
    use_ai: bool = True


class AIHypothesisResponse(BaseModel):
    target_id: str
    hypotheses_generated: int
    flow_cards_generated: int
    ai_used: bool
    hypotheses: list[dict]


@router.post("/ai-hypotheses", response_model=AIHypothesisResponse)
async def generate_ai_hypotheses(request: AIHypothesisRequest):
    """Generate test hypotheses using AI for discovered endpoints."""
    from app.services.openai_service import openai_service
    from app.services.intel.flow_generator import FlowCardGenerator
    
    if request.use_ai and not openai_service.is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available",
        )
    
    all_hypotheses = []
    
    if request.use_ai and openai_service.is_available:
        for endpoint in request.endpoints:
            target_info = {
                "target_id": request.target_id,
                "endpoint": endpoint.path,
                "method": endpoint.method,
            }
            
            patterns = [{"type": "endpoint", "path": endpoint.path, "method": endpoint.method}]
            
            hypotheses = await openai_service.generate_test_hypothesis(
                target_info=target_info,
                patterns=patterns,
            )
            
            for h in hypotheses:
                h["endpoint"] = endpoint.path
                h["method"] = endpoint.method
            
            all_hypotheses.extend(hypotheses)
    
    flow_generator = FlowCardGenerator()
    
    endpoints = [
        {"path": e.path, "method": e.method, "parameters": e.parameters}
        for e in request.endpoints
    ]
    
    flow_cards = flow_generator.generate_flow_cards(
        endpoints=endpoints,
        target_id=request.target_id,
    )
    
    return AIHypothesisResponse(
        target_id=request.target_id,
        hypotheses_generated=len(all_hypotheses),
        flow_cards_generated=len(flow_cards),
        ai_used=request.use_ai and openai_service.is_available,
        hypotheses=all_hypotheses,
    )
