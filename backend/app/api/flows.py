"""Flow card API endpoints."""
from typing import Annotated
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.flow_card import FlowCard, CardStatus, CardType
from app.models.program import Program
from app.schemas.flow import (
    FlowCardCreate,
    FlowCardUpdate,
    FlowCardResponse,
    FlowDAGResponse,
    CoverageResponse,
)
from app.core.coverage_tracker import CoverageTracker
from app.core.plugin_runner import PluginRunner
from app.services.intel.ai_workflow_generator import workflow_generator

router = APIRouter(prefix="/flows", tags=["flows"])


class WorkflowGenerateRequest(BaseModel):
    program_analysis: dict
    target_id: str | None = None
    program_id: str | None = None


class WorkflowStepExecuteRequest(BaseModel):
    step_id: str
    workflow_data: dict
    target: str
    params: dict | None = None


@router.post("/generate")
async def generate_workflow(request: WorkflowGenerateRequest):
    """Generate a detailed workflow for a program based on AI analysis."""
    runner = PluginRunner()
    available_plugins = runner.list_available_plugins()
    available_tool_names = [p.get('name', '').lower() for p in available_plugins]
    
    workflow = workflow_generator.generate_workflow(
        program_analysis=request.program_analysis,
        available_tools=available_tool_names,
    )
    
    if request.program_id and db:
        result = await db.execute(select(Program).where(Program.id == request.program_id))
        program = result.scalar_one_or_none()
        if program:
            program.workflow_data = workflow
            await db.commit()
    
    return {
        "workflow": workflow,
        "available_tools": available_tool_names,
        "summary": {
            "total_targets": len(workflow.get("phases", [])),
            "total_steps": workflow.get("total_steps", 0),
            "auto_steps": workflow.get("auto_steps", 0),
            "manual_steps": workflow.get("manual_steps", 0),
            "approval_points": len(workflow.get("approval_points", [])),
        }
    }


@router.post("/program/{program_id}/generate")
async def generate_workflow_for_program(
    program_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Generate workflow for a program using its existing configuration."""
    from app.models.target import Target
    
    result = await db.execute(select(Program).where(Program.id == program_id))
    program = result.scalar_one_or_none()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    targets_result = await db.execute(select(Target).where(Target.program_id == program_id))
    targets = targets_result.scalars().all()
    
    runner = PluginRunner()
    available_plugins = runner.list_available_plugins()
    available_tool_names = [p.get('name', '').lower() for p in available_plugins]
    
    target_configs = []
    for target in targets:
        target_configs.append({
            "name": target.name,
            "type": target.target_type.value.lower() if target.target_type else "webapp",
            "scope_domains": [target.name],
            "scope_ips": target.subdomains or [],
        })
    
    if not target_configs and program.target_configs:
        target_configs = program.target_configs
    
    program_analysis = {
        "targets": target_configs,
        "rules": program.special_requirements.get("rules", []) if program.special_requirements else [],
        "out_of_scope": program.out_of_scope or [],
        "testing_notes": program.special_requirements.get("testing_notes", "") if program.special_requirements else "",
        "priority_areas": program.priority_areas or [],
    }
    
    workflow = workflow_generator.generate_workflow(
        program_analysis=program_analysis,
        available_tools=available_tool_names,
    )
    
    program.workflow_data = workflow
    await db.commit()
    
    return {
        "workflow": workflow,
        "program_id": program_id,
        "summary": {
            "total_targets": len(workflow.get("phases", [])),
            "total_steps": workflow.get("total_steps", 0),
            "auto_steps": workflow.get("auto_steps", 0),
            "manual_steps": workflow.get("manual_steps", 0),
            "approval_points": len(workflow.get("approval_points", [])),
        }
    }


@router.get("/program/{program_id}/workflow")
async def get_program_workflow(
    program_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get saved workflow for a program."""
    result = await db.execute(select(Program).where(Program.id == program_id))
    program = result.scalar_one_or_none()
    
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
    
    return {
        "workflow": program.workflow_data,
        "program_id": program_id,
    }


@router.post("/execute-step")
async def execute_workflow_step(
    request: WorkflowStepExecuteRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Execute a single workflow step with result persistence."""
    runner = PluginRunner()
    
    step_data = None
    for target in request.workflow_data.get("phases", []):
        for phase in target.get("phases", []):
            for step in phase.get("steps", []):
                if step.get("id") == request.step_id:
                    step_data = step
                    break
            if step_data:
                break
        if step_data:
            break
    
    if not step_data:
        raise HTTPException(status_code=404, detail="Step not found")
    
    tool_name = step_data.get("tool")
    
    if not tool_name:
        return {
            "status": "manual_required",
            "step_id": request.step_id,
            "message": "This step requires manual execution",
            "instructions": step_data.get("name"),
        }
    
    if not step_data.get("tool_available"):
        return {
            "status": "tool_not_available",
            "step_id": request.step_id,
            "tool": tool_name,
            "message": f"Tool '{tool_name}' is not installed",
        }
    
    try:
        result = await runner.run_plugin(
            plugin_name=tool_name,
            target=request.target,
            params=request.params or {},
        )
        
        stdout = result.stdout if hasattr(result, 'stdout') else ""
        results = result.results if hasattr(result, 'results') else {}
        status = result.status.value if hasattr(result, 'status') else "unknown"
        exit_code = getattr(result, 'exit_code', 0)
        
        if db:
            from app.models.plugin_run import PluginRun, PluginStatus, PermissionLevel
            plugin_run = PluginRun(
                plugin_name=tool_name,
                target_id=request.target,
                permission_level=PermissionLevel.LIMITED,
                params=request.params or {},
                container_image=f"bugbounty-{tool_name}:latest",
                status=PluginStatus(status),
                stdout=stdout,
                stderr=result.stderr if hasattr(result, 'stderr') else "",
                exit_code=exit_code,
                results=results,
            )
            plugin_run.mark_completed(exit_code=exit_code, results=results)
            db.add(plugin_run)
            await db.commit()
            await db.refresh(plugin_run)
            run_id = plugin_run.id
        else:
            run_id = None
        
        combined_output = {
            "plugin": tool_name,
            "target": request.target,
            "status": status,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": result.stderr if hasattr(result, 'stderr') else "",
            "results": results,
        }
        
        return {
            "status": "completed",
            "step_id": request.step_id,
            "tool": tool_name,
            "run_id": run_id,
            "result": {
                "id": run_id,
                "status": status,
                "output": combined_output,
                "stdout": stdout,
                "stderr": result.stderr if hasattr(result, 'stderr') else "",
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "step_id": request.step_id,
            "tool": tool_name,
            "error": str(e),
        }


@router.post("/approval-request")
async def request_approval(
    step_id: str,
    workflow_data: dict,
    target: str,
    reason: str | None = None,
):
    """Request human approval for a step."""
    return {
        "request_id": f"approval_{step_id}_{target}",
        "step_id": step_id,
        "target": target,
        "reason": reason or "Human approval required for this step",
        "status": "pending",
        "message": "Approval request submitted. Awaiting human review.",
    }


@router.get("/target/{target_id}", response_model=list[FlowCardResponse])
async def list_flow_cards(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    card_type: CardType | None = None,
):
    """List flow cards for a target."""
    query = select(FlowCard).where(FlowCard.target_id == target_id)

    if card_type:
        query = query.where(FlowCard.card_type == card_type)

    query = query.order_by(FlowCard.position_y, FlowCard.position_x)
    result = await db.execute(query)
    cards = result.scalars().all()

    return [
        FlowCardResponse(
            id=c.id,
            name=c.name,
            card_type=c.card_type,
            status=c.status,
            target_id=c.target_id,
            parent_id=c.parent_id,
            description=c.description,
            card_metadata=c.card_metadata,
            position_x=c.position_x,
            position_y=c.position_y,
            results=c.results,
            logs=c.logs,
            error=c.error,
            started_at=c.started_at,
            completed_at=c.completed_at,
            duration_seconds=c.duration_seconds,
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
        for c in cards
    ]


@router.post("", response_model=FlowCardResponse, status_code=status.HTTP_201_CREATED)
async def create_flow_card(
    card_data: FlowCardCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Create a new flow card."""
    card = FlowCard(
        name=card_data.name,
        card_type=card_data.card_type,
        target_id=card_data.target_id,
        parent_id=card_data.parent_id,
        description=card_data.description,
        card_metadata=card_data.card_metadata,
        position_x=card_data.position_x,
        position_y=card_data.position_y,
    )

    db.add(card)
    await db.commit()
    await db.refresh(card)

    return FlowCardResponse(
        id=card.id,
        name=card.name,
        card_type=card.card_type,
        status=card.status,
        target_id=card.target_id,
        parent_id=card.parent_id,
        description=card.description,
        card_metadata=card.card_metadata,
        position_x=card.position_x,
        position_y=card.position_y,
        results=card.results,
        logs=card.logs,
        error=card.error,
        started_at=card.started_at,
        completed_at=card.completed_at,
        duration_seconds=card.duration_seconds,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.get("/{card_id}", response_model=FlowCardResponse)
async def get_flow_card(
    card_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific flow card."""
    result = await db.execute(
        select(FlowCard).where(FlowCard.id == card_id)
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow card not found",
        )

    return FlowCardResponse(
        id=card.id,
        name=card.name,
        card_type=card.card_type,
        status=card.status,
        target_id=card.target_id,
        parent_id=card.parent_id,
        description=card.description,
        card_metadata=card.card_metadata,
        position_x=card.position_x,
        position_y=card.position_y,
        results=card.results,
        logs=card.logs,
        error=card.error,
        started_at=card.started_at,
        completed_at=card.completed_at,
        duration_seconds=card.duration_seconds,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.put("/{card_id}", response_model=FlowCardResponse)
async def update_flow_card(
    card_id: str,
    card_data: FlowCardUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update a flow card."""
    result = await db.execute(
        select(FlowCard).where(FlowCard.id == card_id)
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow card not found",
        )

    update_data = card_data.model_dump(exclude_unset=True)

    if "status" in update_data:
        new_status = CardStatus(update_data["status"])
        if new_status == CardStatus.RUNNING:
            card.mark_running()
        elif new_status == CardStatus.DONE:
            card.mark_done(update_data.get("results"))
        elif new_status == CardStatus.FAILED:
            card.mark_failed(update_data.get("error", "Unknown error"))
        else:
            setattr(card, "status", new_status)

    for key, value in update_data.items():
        if key not in ("status") and hasattr(card, key):
            setattr(card, key, value)

    await db.commit()
    await db.refresh(card)

    return FlowCardResponse(
        id=card.id,
        name=card.name,
        card_type=card.card_type,
        status=card.status,
        target_id=card.target_id,
        parent_id=card.parent_id,
        description=card.description,
        card_metadata=card.card_metadata,
        position_x=card.position_x,
        position_y=card.position_y,
        results=card.results,
        logs=card.logs,
        error=card.error,
        started_at=card.started_at,
        completed_at=card.completed_at,
        duration_seconds=card.duration_seconds,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.post("/{card_id}/start", response_model=FlowCardResponse)
async def start_flow_card(
    card_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a flow card as running."""
    result = await db.execute(
        select(FlowCard).where(FlowCard.id == card_id)
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow card not found",
        )

    card.mark_running()
    await db.commit()
    await db.refresh(card)

    return FlowCardResponse(
        id=card.id,
        name=card.name,
        card_type=card.card_type,
        status=card.status,
        target_id=card.target_id,
        parent_id=card.parent_id,
        description=card.description,
        card_metadata=card.card_metadata,
        position_x=card.position_x,
        position_y=card.position_y,
        results=card.results,
        logs=card.logs,
        error=card.error,
        started_at=card.started_at,
        completed_at=card.completed_at,
        duration_seconds=card.duration_seconds,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.post("/{card_id}/done", response_model=FlowCardResponse)
async def complete_flow_card(
    card_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    results: dict | None = None,
):
    """Mark a flow card as done."""
    result = await db.execute(
        select(FlowCard).where(FlowCard.id == card_id)
    )
    card = result.scalar_one_or_none()

    if not card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Flow card not found",
        )

    card.mark_done(results)
    await db.commit()
    await db.refresh(card)

    return FlowCardResponse(
        id=card.id,
        name=card.name,
        card_type=card.card_type,
        status=card.status,
        target_id=card.target_id,
        parent_id=card.parent_id,
        description=card.description,
        card_metadata=card.card_metadata,
        position_x=card.position_x,
        position_y=card.position_y,
        results=card.results,
        logs=card.logs,
        error=card.error,
        started_at=card.started_at,
        completed_at=card.completed_at,
        duration_seconds=card.duration_seconds,
        created_at=card.created_at,
        updated_at=card.updated_at,
    )


@router.get("/target/{target_id}/dag", response_model=FlowDAGResponse)
async def get_flow_dag(
    target_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get flow DAG for a target."""
    result = await db.execute(
        select(FlowCard).where(FlowCard.target_id == target_id)
    )
    cards = result.scalars().all()

    edges = []
    for card in cards:
        if card.parent_id:
            edges.append({
                "id": f"{card.parent_id}-{card.id}",
                "source": card.parent_id,
                "target": card.id,
            })

    stats = {
        "total": len(cards),
        "not_started": sum(1 for c in cards if c.status == CardStatus.NOT_STARTED),
        "running": sum(1 for c in cards if c.status == CardStatus.RUNNING),
        "done": sum(1 for c in cards if c.status == CardStatus.DONE),
        "failed": sum(1 for c in cards if c.status == CardStatus.FAILED),
    }

    return FlowDAGResponse(
        target_id=target_id,
        cards=[
            FlowCardResponse(
                id=c.id,
                name=c.name,
                card_type=c.card_type,
                status=c.status,
                target_id=c.target_id,
                parent_id=c.parent_id,
                description=c.description,
                card_metadata=c.card_metadata,
                position_x=c.position_x,
                position_y=c.position_y,
                results=c.results,
                logs=c.logs,
                error=c.error,
                started_at=c.started_at,
                completed_at=c.completed_at,
                duration_seconds=c.duration_seconds,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in cards
        ],
        edges=edges,
        stats=stats,
    )
