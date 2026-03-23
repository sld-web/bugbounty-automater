"""Program API endpoints."""
import json
from typing import Annotated
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.program import Program
from app.models.target import Target
from app.schemas.program import (
    ProgramCreate,
    ProgramUpdate,
    ProgramResponse,
    ProgramConfigResponse,
    ScopeConfig,
)

router = APIRouter(prefix="/programs", tags=["programs"])


@router.get("", response_model=list[ProgramResponse])
async def list_programs(
    db: Annotated[AsyncSession, Depends(get_db)],
    skip: int = 0,
    limit: int = 100,
    platform: str | None = None,
    needs_review: bool | None = None,
):
    """List all programs."""
    query = select(Program).options(selectinload(Program.targets))

    if platform:
        query = query.where(Program.platform == platform)
    if needs_review is not None:
        query = query.where(Program.needs_review == needs_review)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    programs = result.scalars().all()

    response = []
    for program in programs:
        target_count = len(program.targets)
        finding_count = 0  # Skip for now to avoid lazy loading issues

        response.append(
            ProgramResponse(
                id=program.id,
                name=program.name,
                platform=program.platform,
                url=program.url,
                scope=ScopeConfig(
                    domains=program.scope_domains,
                    excluded=program.scope_excluded,
                    mobile_apps=program.scope_mobile_apps,
                    repositories=program.scope_repositories,
                ),
                priority_areas=program.priority_areas,
                out_of_scope=program.out_of_scope,
                severity_mapping=program.severity_mapping,
                reward_tiers=program.reward_tiers,
                campaigns=[],
                special_requirements=program.special_requirements,
                confidence_score=program.confidence_score,
                needs_review=program.needs_review,
                reviewed_at=program.reviewed_at,
                review_notes=program.review_notes,
                created_at=program.created_at,
                updated_at=program.updated_at,
                target_count=target_count,
                finding_count=finding_count,
            )
        )

    return response


@router.get("/{program_id}", response_model=ProgramResponse)
async def get_program(
    program_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific program."""
    result = await db.execute(
        select(Program).where(Program.id == program_id)
    )
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )

    return ProgramResponse(
        id=program.id,
        name=program.name,
        platform=program.platform,
        url=program.url,
        scope=ScopeConfig(
            domains=program.scope_domains or [],
            excluded=program.scope_excluded or [],
            mobile_apps=program.scope_mobile_apps or [],
            repositories=program.scope_repositories or [],
        ),
        scope_domains=program.scope_domains or [],
        scope_excluded=program.scope_excluded or [],
        priority_areas=program.priority_areas or [],
        target_configs=program.target_configs or [],
        workflow_data=program.workflow_data,
        out_of_scope=program.out_of_scope or [],
        severity_mapping=program.severity_mapping or {},
        reward_tiers=program.reward_tiers or {},
        campaigns=[],
        special_requirements=program.special_requirements or {},
        confidence_score=program.confidence_score or 0,
        needs_review=program.needs_review,
        reviewed_at=program.reviewed_at,
        review_notes=program.review_notes,
        created_at=program.created_at,
        updated_at=program.updated_at,
        target_count=0,
        finding_count=0,
    )


@router.post("", response_model=ProgramResponse, status_code=status.HTTP_201_CREATED)
async def create_program(
    program_data: ProgramCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new program."""
    existing = await db.execute(
        select(Program).where(Program.name == program_data.name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Program with this name already exists",
        )

    program = Program(
        name=program_data.name,
        platform=program_data.platform,
        url=program_data.url,
        raw_policy=program_data.raw_policy,
        scope_domains=program_data.scope.domains,
        scope_excluded=program_data.scope.excluded,
        scope_mobile_apps=program_data.scope.mobile_apps,
        scope_repositories=program_data.scope.repositories,
        priority_areas=program_data.priority_areas,
        out_of_scope=program_data.out_of_scope,
        severity_mapping=program_data.severity_mapping,
        reward_tiers=program_data.reward_tiers,
        campaigns=[c.model_dump() for c in program_data.campaigns],
        special_requirements=program_data.special_requirements,
        target_configs=program_data.target_configs or [],
    )

    db.add(program)
    await db.commit()
    await db.refresh(program)

    return ProgramResponse(
        id=program.id,
        name=program.name,
        platform=program.platform,
        url=program.url,
        scope=program_data.scope,
        scope_domains=program.scope_domains,
        scope_excluded=program.scope_excluded,
        priority_areas=program.priority_areas,
        target_configs=program.target_configs,
        out_of_scope=program.out_of_scope,
        severity_mapping=program.severity_mapping,
        reward_tiers=program.reward_tiers,
        campaigns=program_data.campaigns,
        special_requirements=program.special_requirements,
        confidence_score=0,
        needs_review=True,
        reviewed_at=None,
        review_notes=None,
        created_at=program.created_at,
        updated_at=program.updated_at,
        target_count=0,
        finding_count=0,
    )


@router.put("/{program_id}", response_model=ProgramResponse)
async def update_program(
    program_id: str,
    program_data: ProgramUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a program."""
    result = await db.execute(
        select(Program).where(Program.id == program_id)
    )
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )

    update_data = program_data.model_dump(exclude_unset=True)

    if "scope" in update_data:
        scope = update_data.pop("scope")
        if scope:
            program.scope_domains = scope.get("domains", program.scope_domains)
            program.scope_excluded = scope.get("excluded", program.scope_excluded)
            program.scope_mobile_apps = scope.get("mobile_apps", program.scope_mobile_apps)
            program.scope_repositories = scope.get("repositories", program.scope_repositories)

    if "reviewed" in update_data:
        program.needs_review = not update_data["reviewed"]
        program.reviewed_at = program.created_at

    for key, value in update_data.items():
        if hasattr(program, key) and key not in ("scope", "reviewed"):
            setattr(program, key, value)

    await db.commit()
    await db.refresh(program)

    return ProgramResponse(
        id=program.id,
        name=program.name,
        platform=program.platform,
        url=program.url,
        scope=ScopeConfig(
            domains=program.scope_domains,
            excluded=program.scope_excluded,
            mobile_apps=program.scope_mobile_apps,
            repositories=program.scope_repositories,
        ),
        priority_areas=program.priority_areas,
        out_of_scope=program.out_of_scope,
        severity_mapping=program.severity_mapping,
        reward_tiers=program.reward_tiers,
        campaigns=[],
        special_requirements=program.special_requirements,
        confidence_score=program.confidence_score,
        needs_review=program.needs_review,
        reviewed_at=program.reviewed_at,
        review_notes=program.review_notes,
        created_at=program.created_at,
        updated_at=program.updated_at,
        target_count=len(program.targets),
        finding_count=sum(len(t.findings) for t in program.targets),
    )


@router.delete("/{program_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_program(
    program_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Delete a program."""
    result = await db.execute(
        select(Program).where(Program.id == program_id)
    )
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )

    await db.delete(program)
    await db.commit()


@router.get("/{program_id}/config", response_model=ProgramConfigResponse)
async def get_program_config(
    program_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get program configuration for orchestration."""
    result = await db.execute(
        select(Program).where(Program.id == program_id)
    )
    program = result.scalar_one_or_none()

    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )

    return ProgramConfigResponse(
        program_id=program.id,
        program_name=program.name,
        scope=ScopeConfig(
            domains=program.scope_domains,
            excluded=program.scope_excluded,
            mobile_apps=program.scope_mobile_apps,
            repositories=program.scope_repositories,
        ),
        priority_areas=program.priority_areas,
        out_of_scope=program.out_of_scope,
        severity_mapping=program.severity_mapping,
        reward_tiers=program.reward_tiers,
        campaigns=[],
        special_requirements=program.special_requirements,
        confidence_score=program.confidence_score,
    )


@router.post("/{program_id}/attachments")
async def upload_attachment(
    program_id: str,
    file: Annotated[UploadFile, File(description="File to upload")],
    db: Annotated[AsyncSession, Depends(get_db)],
    pfx_password: Annotated[str | None, Form()] = None,
):
    """Upload an attachment for a program."""
    from pydantic import BaseModel
    
    result = await db.execute(
        select(Program).where(Program.id == program_id)
    )
    program = result.scalar_one_or_none()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )
    
    content = await file.read()
    
    from app.services.file_processor import process_file
    processed = process_file(file.filename or 'unknown', content, pfx_password or "")
    
    class AttachmentResponse(BaseModel):
        filename: str
        type: str
        size: int
        credentials_found: list[dict]
        certificate_info: dict | None
        text_content: str | None
        extracted_data: dict
        warnings: list[str]
        ai_used: bool
        ai_extraction: dict | None
    
    return AttachmentResponse(
        filename=processed['filename'],
        type=processed['type'],
        size=processed['size'],
        credentials_found=processed['credentials_found'],
        certificate_info=processed['certificate_info'],
        text_content=processed.get('text_content', '')[:1000] if processed.get('text_content') else None,
        extracted_data=processed.get('extracted_data', {}),
        warnings=processed['warnings'],
        ai_used=processed.get('ai_used', False),
        ai_extraction=processed.get('ai_extraction'),
    )


@router.post("/{program_id}/credentials")
async def add_program_credential(
    program_id: str,
    request: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Add a credential extracted from attachment to the vault."""
    from app.models.credential import Credential, CredentialType
    
    result = await db.execute(
        select(Program).where(Program.id == program_id)
    )
    program = result.scalar_one_or_none()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )
    
    cred_type_str = request.get('type', 'user_pass')
    try:
        cred_type = CredentialType(cred_type_str)
    except ValueError:
        cred_type = CredentialType.USER_PASS
    
    extra_data = request.get('metadata', {})
    extra_data['source'] = request.get('source', 'attachment')
    
    credential = Credential(
        program_id=program_id,
        name=request.get('name', 'Extracted Credential'),
        credential_type=cred_type,
        username=request.get('username'),
        password=request.get('password'),
        extra_data=extra_data,
        is_active=True,
    )
    
    db.add(credential)
    await db.commit()
    await db.refresh(credential)
    
    return {
        "id": credential.id,
        "name": credential.name,
        "type": credential.credential_type.value,
        "status": "stored"
    }


@router.get("/{program_id}/attachments")
async def list_attachments(
    program_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List attachments for a program."""
    result = await db.execute(
        select(Program).where(Program.id == program_id)
    )
    program = result.scalar_one_or_none()
    
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Program not found",
        )
    
    return {
        "program_id": program_id,
        "attachments": [],
        "message": "Attachment tracking not yet implemented"
    }


class ToolSuggestion(BaseModel):
    name: str
    available: bool
    reason: str


class TargetAnalysis(BaseModel):
    name: str
    type: str
    description: str | None
    suggested_tools: list[ToolSuggestion]
    scope_domains: list[str] = []
    scope_ips: list[str] = []
    excluded: list[str] = []
    reward_tiers: dict = {}


class ProgramAnalysisResponse(BaseModel):
    introduction: str
    rules: list[str]
    targets: list[TargetAnalysis]
    rewards_summary: dict = {}
    out_of_scope: list[str] = []
    testing_notes: str | None = None
    severity_mapping: dict = {}


@router.post("/analyze")
async def analyze_program(
    policy_text: str = Form(...),
    files: list[UploadFile] = File(default=[]),
):
    """Analyze program policy with AI to extract structured information."""
    from pydantic import BaseModel
    from app.services.openai_service import openai_service
    from app.core.plugin_runner import PluginRunner
    
    combined_text = policy_text
    
    for file in files:
        if file.filename:
            content = await file.read()
            ext = file.filename.lower().split('.')[-1] if '.' in file.filename else ''
            
            if ext == 'pdf':
                from app.services.file_processor import extract_text_from_pdf
                text = extract_text_from_pdf(content)
                if text:
                    combined_text += f"\n\n[File: {file.filename}]\n{text}"
            else:
                try:
                    text = content.decode('utf-8', errors='ignore')
                    combined_text += f"\n\n[File: {file.filename}]\n{text}"
                except Exception:
                    pass
    
    runner = PluginRunner()
    available_plugins = runner.list_available_plugins()
    available_tool_names = set(p.get('name', '').lower() for p in available_plugins)
    
    common_tools = [
        "nmap", "amass", "subfinder", "httpx", "nuclei", "sqlmap", 
        "ffuf", "dirsearch", "wpscan", "nikto", "whatweb", "gobuster", 
        "curl", "wget", "burpsuite", "zap", "metasploit", "hydra",
        "smbclient", "ldapsearch", "snmpwalk", "dig", "nslookup",
        "masscan", "rustscan", "naabu", "shuffledns", "puredns",
        "gau", "waybackurls", "katana", "xnlinkfinder", "linkfinder"
    ]
    
    all_tools = sorted(set(available_tool_names | set(common_tools)))
    available_tools_str = ", ".join(available_tool_names) if available_tool_names else "none installed"
    
    system_prompt = """You are a bug bounty program analyst. Analyze the provided program policy and extract structured information.

IMPORTANT: You MUST mark the "available" field for each tool based on whether it is in the list of AVAILABLE TOOLS below.

Available tools (installed in system): [""" + available_tools_str + """]
All supported tools: [""" + ", ".join(all_tools) + """]
For each suggested tool:
- If the tool name matches (case-insensitive) an item in AVAILABLE TOOLS, set "available": true
- If not in available tools, set "available": false

Return ONLY valid JSON with this exact structure:

{
    "introduction": "Brief program overview (2-3 sentences)",
    "rules": ["rule 1", "rule 2", ...],
    "targets": [
        {
            "name": "Target name",
            "type": "webapp|api|mobile|network|hardware|cloud|other",
            "description": "Target description",
            "scope_domains": ["domain1.com", "*.domain2.com"],
            "scope_ips": ["1.2.3.4"],
            "excluded": ["excluded.domain.com"],
            "suggested_tools": [
                {"name": "tool_name", "available": true, "reason": "why this tool is useful"},
                {"name": "external_tool", "available": false, "reason": "why manual testing needed"}
            ]
        }
    ],
    "rewards_summary": {
        "critical": {"min": 0, "max": 0},
        "high": {"min": 0, "max": 0},
        "medium": {"min": 0, "max": 0},
        "low": {"min": 0, "max": 0}
    },
    "out_of_scope": ["item 1", "item 2"],
    "testing_notes": "Any special testing instructions",
    "severity_mapping": {
        "critical": ["criteria"],
        "high": ["criteria"],
        "medium": ["criteria"],
        "low": ["criteria"]
    }
}

Be thorough - extract ALL domains, IPs, and special instructions from attachments."""

    if not openai_service.is_available:
        return {
            "error": "OpenAI service not available",
            "combined_text_length": len(combined_text)
        }
    
    try:
        response = await openai_service.client.chat.completions.create(
            model=openai_service.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": combined_text[:100000]}
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        if content:
            result = json.loads(content)
            return result
        else:
            return {"error": "No response from AI"}
            
    except Exception as e:
        return {"error": str(e)}
