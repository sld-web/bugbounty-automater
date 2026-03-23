"""Orchestrator for managing testing workflow state machine."""
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import async_session_maker
from app.core.approval_manager import ApprovalManager
from app.core.plugin_runner import PluginRunner
from app.core.scope_guard import ScopeGuard
from app.models.flow_card import CardStatus, CardType, FlowCard
from app.models.plugin_run import PluginStatus, PluginRun
from app.models.target import Target, TargetStatus

logger = logging.getLogger(__name__)
settings = get_settings()


class PhaseType(str, Enum):
    RECON = "RECON"
    SCANNING = "SCANNING"
    VULN_DETECTION = "VULN_DETECTION"
    EXPLOITATION = "EXPLOITATION"
    REPORTING = "REPORTING"
    INTELLIGENCE = "INTELLIGENCE"
    APPROVAL = "APPROVAL"


DEFAULT_DAG = {
    PhaseType.RECON: {
        "plugins": ["subfinder", "amass"],
        "outputs": ["subdomains"],
        "requires_approval": False,
    },
    PhaseType.SCANNING: {
        "plugins": ["nmap", "httpx"],
        "inputs": ["subdomains"],
        "outputs": ["endpoints", "technologies", "ports"],
        "requires_approval": False,
    },
    PhaseType.VULN_DETECTION: {
        "plugins": ["nuclei"],
        "inputs": ["endpoints"],
        "outputs": ["findings"],
        "requires_approval": False,
        "risk_level": "MEDIUM",
    },
    PhaseType.APPROVAL: {
        "type": "manual",
        "requires_approval": True,
    },
    PhaseType.EXPLOITATION: {
        "plugins": [],
        "inputs": ["findings"],
        "outputs": ["confirmed_findings"],
        "requires_approval": True,
        "risk_level": "HIGH",
    },
    PhaseType.REPORTING: {
        "type": "submit",
        "requires_approval": True,
    },
}


class Orchestrator:
    """Manage testing workflow as a state machine with DAG execution."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.plugin_runner = PluginRunner()
        self.approval_manager = ApprovalManager(db)

    async def start_target(
        self,
        target_id: str,
        dag: dict | None = None,
    ) -> Target:
        """Start the testing workflow for a target."""
        result = await self.db.execute(
            select(Target).where(Target.id == target_id)
        )
        target = result.scalar_one_or_none()

        if not target:
            raise ValueError(f"Target {target_id} not found")

        if target.status != TargetStatus.PENDING:
            raise ValueError(
                f"Target {target_id} is not in PENDING state (current: {target.status})"
            )

        target.status = TargetStatus.RUNNING
        await self.db.commit()
        await self.db.refresh(target)

        asyncio.create_task(self._execute_dag(target_id, dag or DEFAULT_DAG))

        return target

    async def pause_target(self, target_id: str) -> Target:
        """Pause a running target."""
        result = await self.db.execute(
            select(Target).where(Target.id == target_id)
        )
        target = result.scalar_one_or_none()

        if not target:
            raise ValueError(f"Target {target_id} not found")

        target.status = TargetStatus.PAUSED
        await self.db.commit()
        await self.db.refresh(target)

        return target

    async def resume_target(self, target_id: str) -> Target:
        """Resume a paused target."""
        result = await self.db.execute(
            select(Target).where(Target.id == target_id)
        )
        target = result.scalar_one_or_none()

        if not target:
            raise ValueError(f"Target {target_id} not found")

        if target.status != TargetStatus.PAUSED:
            raise ValueError(f"Target {target_id} is not PAUSED")

        target.status = TargetStatus.RUNNING
        await self.db.commit()
        await self.db.refresh(target)

        return target

    async def cancel_target(self, target_id: str) -> Target:
        """Cancel a target and all its flows."""
        result = await self.db.execute(
            select(Target).where(Target.id == target_id)
        )
        target = result.scalar_one_or_none()

        if not target:
            raise ValueError(f"Target {target_id} not found")

        target.status = TargetStatus.CANCELLED
        await self.db.commit()
        await self.db.refresh(target)

        return target

    async def _execute_dag(
        self,
        target_id: str,
        dag: dict,
    ) -> None:
        """Execute the testing DAG for a target."""
        async with async_session_maker() as session:
            try:
                result = await session.execute(
                    select(Target).where(Target.id == target_id)
                )
                target = result.scalar_one_or_none()
                
                if not target:
                    logger.error(f"Target {target_id} not found in _execute_dag")
                    return

                await self._create_flow_cards(session, target, dag)

                for phase_name, phase_config in dag.items():
                    result = await session.execute(
                        select(Target).where(Target.id == target_id)
                    )
                    target = result.scalar_one()

                    if target.status == TargetStatus.PAUSED:
                        logger.info(f"Target {target_id} paused, stopping execution")
                        return

                    if target.status == TargetStatus.CANCELLED:
                        logger.info(f"Target {target_id} cancelled, stopping execution")
                        return

                    phase_name_str = phase_name.value if isinstance(phase_name, PhaseType) else phase_name
                    logger.info(f"Starting phase: {phase_name_str} for target {target_id}")
                    await self._execute_phase(session, target, phase_name, phase_config)
                    logger.info(f"Completed phase: {phase_name_str} for target {target_id}")

                target.status = TargetStatus.COMPLETED
                await session.commit()
                logger.info(f"Target {target_id} completed successfully")

            except Exception as e:
                logger.exception(f"DAG execution failed for target {target_id}")
                try:
                    result = await session.execute(
                        select(Target).where(Target.id == target_id)
                    )
                    target = result.scalar_one_or_none()
                    if target:
                        target.status = TargetStatus.FAILED
                        target.error_message = str(e)
                        await session.commit()
                except Exception:
                    pass

    async def _create_flow_cards(
        self,
        session: AsyncSession,
        target: Target,
        dag: dict,
    ) -> None:
        """Create flow cards from DAG configuration."""
        position = {"x": 0, "y": 0}
        card_mapping = {}

        for i, (phase_name, phase_config) in enumerate(dag.items()):
            phase_name_str = phase_name.value if isinstance(phase_name, PhaseType) else phase_name
            card = FlowCard(
                name=phase_name_str,
                card_type=CardType.FLOW,
                target_id=target.id,
                position_x=position["x"],
                position_y=position["y"],
                card_metadata={"phase_config": phase_config, "plugins": phase_config.get("plugins", [])},
            )
            session.add(card)
            await session.flush()
            card_mapping[phase_name_str] = card.id

            position["y"] += 150

        for i, (phase_name_str, card_id) in enumerate(card_mapping.items()):
            if i > 0:
                prev_phase_name = list(card_mapping.keys())[i - 1]
                prev_card = await session.get(FlowCard, card_mapping[prev_phase_name])
                card = await session.get(FlowCard, card_id)
                if prev_card and card:
                    card.parent_id = prev_card.id

        await session.commit()

    async def _get_flow_card(self, session: AsyncSession, target_id: str, phase_name: str) -> FlowCard | None:
        """Get the flow card for a specific phase."""
        result = await session.execute(
            select(FlowCard).where(
                FlowCard.target_id == target_id,
                FlowCard.name == phase_name
            )
        )
        return result.scalar_one_or_none()

    async def _execute_phase(
        self,
        session: AsyncSession,
        target: Target,
        phase_name: str | PhaseType,
        phase_config: dict,
    ) -> None:
        """Execute a single phase of the DAG."""
        phase_name_str = phase_name.value if isinstance(phase_name, PhaseType) else phase_name
        plugins = phase_config.get("plugins", [])

        if not plugins:
            return

        card = await self._get_flow_card(session, target.id, phase_name_str)
        if card:
            card.mark_running()
            await session.commit()

        phase_results = {"plugins_run": [], "outputs": {}}

        try:
            requires_approval = phase_config.get("requires_approval", False)
            if requires_approval:
                logger.info(f"Phase {phase_name_str} requires approval, checking risk...")
                
                request, auto_approve = await self.approval_manager.assess_and_create(
                    action_type=phase_name_str,
                    action_description=f"Execute phase: {phase_name_str}",
                    target_id=target.id,
                    target=target.name,
                    plugin_permission=phase_config.get("permission", "LIMITED"),
                    scope_info={"domains": target.program.scope_domains if target.program else []},
                    evidence={"phase_config": phase_config},
                    context=f"Phase {phase_name_str} on {target.name}",
                )

                if not auto_approve and request:
                    logger.info(f"Approval request {request.id} created for phase {phase_name_str}")
                    if card:
                        card.status = card.status.REVIEW
                        card.logs.append(f"Waiting for approval: {request.id}")
                        await session.commit()

                    approved = await self._wait_for_approval(request.id)
                    if not approved:
                        logger.info(f"Approval denied/timeout for phase {phase_name_str}, skipping...")
                        if card:
                            card.status = card.status.BLOCKED
                            card.logs.append(f"Phase skipped due to approval denial/timeout")
                            await session.commit()
                        return

                    logger.info(f"Approval granted for phase {phase_name_str}, continuing...")

            for plugin_name in plugins:
                plugin_inputs = phase_config.get("inputs", [])
                plugin_target = target.name
                
                if "subdomains" in plugin_inputs and target.subdomains:
                    plugin_target = target.subdomains[0]
                elif "endpoints" in plugin_inputs and target.endpoints:
                    plugin_target = target.endpoints[0].get("url", target.name) if isinstance(target.endpoints[0], dict) else target.endpoints[0]
                
                plugin_params = phase_config.get("params", {})
                if "subdomains" in plugin_inputs:
                    plugin_params["subdomains"] = target.subdomains
                if "endpoints" in plugin_inputs:
                    plugin_params["endpoints"] = target.endpoints
                
                plugin_run = await self.plugin_runner.run_plugin(
                    plugin_name=plugin_name,
                    target=plugin_target,
                    params=plugin_params,
                )

                plugin_run.target_id = target.id
                session.add(plugin_run)
                await session.commit()
                await session.refresh(plugin_run)

                phase_results["plugins_run"].append({
                    "name": plugin_name,
                    "status": plugin_run.status.value,
                    "exit_code": plugin_run.exit_code,
                })

                if plugin_run.results:
                    await self._process_plugin_results(session, target, plugin_name, plugin_run.results)
                    phase_results["outputs"].update(plugin_run.results)

            if card:
                card.mark_done(results=phase_results)
                card.logs.append(f"Phase {phase_name_str} completed at {datetime.utcnow().isoformat()}")
                await session.commit()

        except Exception as e:
            logger.exception(f"Phase {phase_name_str} failed: {e}")
            if card:
                card.mark_failed(str(e))
                card.logs.append(f"Phase {phase_name_str} failed at {datetime.utcnow().isoformat()}: {str(e)}")
                await session.commit()
            raise

    async def _wait_for_approval(self, request_id: str, poll_interval: int = 2) -> bool:
        """Wait for approval request to be resolved.
        
        Returns:
            True if approved, False if denied or timed out.
        """
        max_wait = 3600
        waited = 0
        
        while waited < max_wait:
            await asyncio.sleep(poll_interval)
            waited += poll_interval
            
            request = await self.approval_manager.get_request(request_id)
            if not request:
                logger.warning(f"Approval request {request_id} not found")
                return False
                
            if request.status.value in ["APPROVED", "DENIED", "TIMED_OUT", "CANCELLED"]:
                return request.status.value == "APPROVED"
        
        logger.warning(f"Approval request {request_id} timed out after {max_wait}s")
        return False

    async def _process_plugin_results(
        self,
        session: AsyncSession,
        target: Target,
        plugin_name: str,
        results: dict,
    ) -> None:
        """Process results from plugin execution."""
        if "subdomains" in results:
            existing = set(target.subdomains or [])
            new = [s for s in results["subdomains"] if s not in existing]
            target.subdomains = list(existing) + new

        if "endpoints" in results:
            existing_urls = {e.get("url") for e in (target.endpoints or []) if isinstance(e, dict)}
            new = [e for e in results["endpoints"] if isinstance(e, dict) and e.get("url") not in existing_urls]
            target.endpoints = (target.endpoints or []) + new

        if "technologies" in results:
            existing = set(target.technologies or [])
            new = [t for t in results["technologies"] if t not in existing]
            target.technologies = list(existing) + new

        if "ports" in results:
            existing_ports = {p.get("port") for p in (target.ports or []) if isinstance(p, dict)}
            new = [p for p in results["ports"] if isinstance(p, dict) and p.get("port") not in existing_ports]
            target.ports = (target.ports or []) + new

        target.update_coverage()
        await session.commit()

    def get_available_plugins(self) -> list[str]:
        """Get list of available plugins."""
        return self.plugin_runner.list_available_plugins()
