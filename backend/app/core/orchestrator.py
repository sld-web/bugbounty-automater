"""Orchestrator for managing testing workflow state machine."""
import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
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

        asyncio.create_task(self._execute_dag(target, dag or DEFAULT_DAG))

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
        target: Target,
        dag: dict,
    ) -> None:
        """Execute the testing DAG for a target."""
        try:
            await self._create_flow_cards(target, dag)

            for phase_name, phase_config in dag.items():
                if target.status == TargetStatus.PAUSED:
                    logger.info(f"Target {target.id} paused, stopping execution")
                    return

                if target.status == TargetStatus.CANCELLED:
                    logger.info(f"Target {target.id} cancelled, stopping execution")
                    return

                await self._execute_phase(target, phase_name, phase_config)

            target.status = TargetStatus.COMPLETED
            await self.db.commit()

        except Exception as e:
            logger.exception(f"DAG execution failed for target {target.id}")
            target.status = TargetStatus.FAILED
            target.error_message = str(e)
            await self.db.commit()

    async def _create_flow_cards(
        self,
        target: Target,
        dag: dict,
    ) -> None:
        """Create flow cards from DAG configuration."""
        position = {"x": 0, "y": 0}
        card_mapping = {}

        for i, (phase_name, phase_config) in enumerate(dag.items()):
            card = FlowCard(
                name=phase_name.value if isinstance(phase_name, PhaseType) else phase_name,
                card_type=CardType.FLOW,
                target_id=target.id,
                position_x=position["x"],
                position_y=position["y"],
                metadata={"phase_config": phase_config},
            )
            self.db.add(card)
            card_mapping[phase_name] = card.id

            position["y"] += 150

        await self.db.commit()

        for i, (phase_name, card_id) in enumerate(card_mapping.items()):
            if i > 0:
                prev_phase = list(card_mapping.keys())[i - 1]
                prev_card = await self.db.get(FlowCard, card_mapping[prev_phase])
                card = await self.db.get(FlowCard, card_id)
                if prev_card and card:
                    card.parent_id = prev_card.id

        await self.db.commit()

    async def _execute_phase(
        self,
        target: Target,
        phase_name: str,
        phase_config: dict,
    ) -> None:
        """Execute a single phase of the DAG."""
        plugins = phase_config.get("plugins", [])

        if not plugins:
            return

        for plugin_name in plugins:
            plugin_run = await self.plugin_runner.run_plugin(
                plugin_name=plugin_name,
                target=target.name,
                params=phase_config.get("params", {}),
            )

            plugin_run.target_id = target.id
            self.db.add(plugin_run)
            await self.db.commit()
            await self.db.refresh(plugin_run)

            if plugin_run.results:
                await self._process_plugin_results(target, plugin_name, plugin_run.results)

    async def _process_plugin_results(
        self,
        target: Target,
        plugin_name: str,
        results: dict,
    ) -> None:
        """Process results from plugin execution."""
        if "subdomains" in results:
            existing = set(target.subdomains)
            new = [s for s in results["subdomains"] if s not in existing]
            target.subdomains = list(existing) + new

        if "endpoints" in results:
            existing = {e.get("url") for e in target.endpoints}
            new = [e for e in results["endpoints"] if e.get("url") not in existing]
            target.endpoints = target.endpoints + new

        if "technologies" in results:
            existing = set(target.technologies)
            new = [t for t in results["technologies"] if t not in existing]
            target.technologies = list(existing) + new

        if "ports" in results:
            existing = set(target.ports)
            new = [p for p in results["ports"] if p not in existing]
            target.ports = list(existing) + new

        target.update_coverage()
        await self.db.commit()

    def get_available_plugins(self) -> list[str]:
        """Get list of available plugins."""
        return self.plugin_runner.list_available_plugins()
