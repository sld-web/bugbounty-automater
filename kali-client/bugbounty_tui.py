#!/usr/bin/env python3
"""
BugBounty Automator - Kali Linux Terminal Client
A cyber-glass themed CLI for the Bug Bounty Automation Platform

Usage:
    python3 bugbounty_tui.py              # Interactive TUI mode
    python3 bugbounty_tui.py --dashboard  # Dashboard view
    python3 bugbounty_tui.py --targets    # Targets list
    python3 bugbounty_tui.py --help       # Help
"""

import asyncio
import argparse
import sys
from typing import Optional, List, Dict, Any
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.style import Style
from rich import box
import httpx
import json
from datetime import datetime


# CyberGlass Cobalt Color Palette
STYLES = {
    "primary": "#b4c5ff",
    "secondary": "#00D4FF", 
    "tertiary": "#33FF66",
    "error": "#FF3366",
    "warning": "#FFB800",
    "surface": "#0c0e14",
}


class BugBountyClient:
    """Client for BugBounty Automator API"""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.console = Console()
        self.client = httpx.AsyncClient(base_url=api_url, timeout=30.0)
        
    async def close(self):
        await self.client.aclose()
    
    async def get_programs(self) -> List[Dict]:
        try:
            resp = await self.client.get("/api/programs")
            if resp.status_code == 200:
                data = resp.json()
                return data if isinstance(data, list) else data.get("items", [])
            return []
        except Exception as e:
            self.console.print(f"[red]Error fetching programs: {e}[/red]")
            return []
    
    async def get_targets(self) -> List[Dict]:
        try:
            resp = await self.client.get("/api/targets")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("items", []) if isinstance(data, dict) else data
            return []
        except Exception as e:
            self.console.print(f"[red]Error fetching targets: {e}[/red]")
            return []
    
    async def get_approvals(self) -> List[Dict]:
        try:
            resp = await self.client.get("/api/approvals/queue")
            if resp.status_code == 200:
                data = resp.json()
                return data.get("pending", []) if isinstance(data, dict) else []
            return []
        except Exception as e:
            self.console.print(f"[red]Error fetching approvals: {e}[/red]")
            return []
    
    async def get_plugins(self) -> List[Dict]:
        try:
            resp = await self.client.get("/api/plugins")
            if resp.status_code == 200:
                data = resp.json()
                return data if isinstance(data, list) else data.get("items", [])
            return []
        except Exception as e:
            self.console.print(f"[red]Error fetching plugins: {e}[/red]")
            return []


def create_header() -> Panel:
    """Create the application header"""
    header_text = Text()
    header_text.append("BugBounty ", style="bold cyan")
    header_text.append("Automator", style="bold #b4c5ff")
    header_text.append("  //  ", style="dim")
    header_text.append("Kali Linux Edition", style="dim cyan")
    
    return Panel(
        header_text,
        border_style="cyan",
        box=box.DOUBLE,
        style="on #0c0e14"
    )


def create_metrics_row(programs: int, targets: int, running: int, approvals: int) -> Table:
    """Create metrics display table"""
    table = Table(box=box.ROUNDED, show_header=False, border_style="cyan")
    table.add_column(style="cyan", no_wrap=True)
    table.add_column(style="white", justify="center")
    table.add_column(style="cyan", no_wrap=True)
    table.add_column(style="white", justify="center")
    table.add_column(style="cyan", no_wrap=True)
    table.add_column(style="white", justify="center")
    table.add_column(style="cyan", no_wrap=True)
    table.add_column(style="white", justify="center")
    
    table.add_row(
        "[bold]PROGRAMS[/bold]", str(programs),
        "[bold]TARGETS[/bold]", str(targets),
        "[bold]RUNNING[/bold]", str(running),
        "[bold]APPROVALS[/bold]", str(approvals)
    )
    return table


def create_targets_table(targets: List[Dict]) -> Table:
    """Create targets table"""
    table = Table(
        title="[cyan]Active Targets[/cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        title_style="bold cyan"
    )
    
    table.add_column("Target", style="cyan", no_wrap=True)
    table.add_column("Program", style="white")
    table.add_column("Status", style="white")
    table.add_column("Coverage", justify="right", style="#00D4FF")
    table.add_column("Findings", justify="right", style="#33FF66")
    
    for target in targets[:10]:  # Limit to 10
        status = target.get("status", "UNKNOWN")
        status_style = {
            "RUNNING": "[green]● RUNNING[/green]",
            "COMPLETED": "[blue]● COMPLETED[/blue]",
            "FAILED": "[red]● FAILED[/red]",
            "PENDING": "[yellow]● PENDING[/yellow]",
            "PAUSED": "[yellow]● PAUSED[/yellow]",
        }.get(status, status)
        
        table.add_row(
            target.get("name", "Unknown"),
            target.get("program_name", "Unknown"),
            status_style,
            f"{target.get('surface_coverage', 0)}%",
            str(target.get("findings_count", 0))
        )
    
    return table


def create_findings_table() -> Table:
    """Create sample findings table"""
    table = Table(
        title="[cyan]Recent Findings[/cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        title_style="bold cyan"
    )
    
    table.add_column("Severity", style="white")
    table.add_column("Type", style="white")
    table.add_column("Target", style="white")
    table.add_column("Status", style="white")
    
    findings = [
        ("[red]CRITICAL[/red]", "SQL Injection", "api.example.com", "[yellow]PENDING[/yellow]"),
        ("[yellow]HIGH[/yellow]", "XSS Reflected", "app.example.com", "[green]APPROVED[/green]"),
        ("[blue]MEDIUM[/blue]", "CSRF", "portal.example.com", "[yellow]REVIEW[/yellow]"),
        ("[green]LOW[/green]", "Info Disclosure", "staging.example.com", "[green]APPROVED[/green]"),
    ]
    
    for finding in findings:
        table.add_row(*finding)
    
    return table


def create_approvals_table(approvals: List[Dict]) -> Table:
    """Create approvals queue table"""
    table = Table(
        title="[cyan]Pending Approvals[/cyan]",
        box=box.ROUNDED,
        border_style="warning",
        title_style="bold warning"
    )
    
    table.add_column("Action", style="white")
    table.add_column("Risk", style="white")
    table.add_column("Target", style="white")
    table.add_column("Plugin", style="white")
    
    if not approvals:
        # Demo data
        approvals = [
            {"action_type": "nuclei_scan.sh", "risk_level": "HIGH", "target": "api.example.com", "plugin_name": "nuclei"},
            {"action_type": "sqlmap_scan.sh", "risk_level": "CRITICAL", "target": "app.example.com", "plugin_name": "sqlmap"},
            {"action_type": "recon.sh", "risk_level": "LOW", "target": "portal.example.com", "plugin_name": "subfinder"},
        ]
    
    for approval in approvals:
        risk = approval.get("risk_level", "MEDIUM")
        risk_style = {
            "CRITICAL": "[red]CRITICAL[/red]",
            "HIGH": "[yellow]HIGH[/yellow]",
            "MEDIUM": "[blue]MEDIUM[/blue]",
            "LOW": "[green]LOW[/green]",
        }.get(risk, risk)
        
        table.add_row(
            approval.get("action_type", "Unknown"),
            risk_style,
            approval.get("target", "Unknown"),
            approval.get("plugin_name", "Unknown")
        )
    
    return table


def create_plugins_grid(plugins: List[Dict]) -> Table:
    """Create plugins status table"""
    table = Table(
        title="[cyan]Plugin Status[/cyan]",
        box=box.ROUNDED,
        border_style="cyan",
        title_style="bold cyan"
    )
    
    table.add_column("Plugin", style="cyan")
    table.add_column("Version", style="white")
    table.add_column("Permission", style="white")
    table.add_column("Status", style="white")
    
    if not plugins:
        # Demo data
        plugins = [
            {"name": "subfinder", "version": "2.6.1", "permission_level": "SAFE", "status": "READY"},
            {"name": "amass", "version": "3.23.0", "permission_level": "SAFE", "status": "READY"},
            {"name": "nmap", "version": "7.94", "permission_level": "LIMITED", "status": "READY"},
            {"name": "nuclei", "version": "3.1.0", "permission_level": "LIMITED", "status": "READY"},
            {"name": "sqlmap", "version": "1.8", "permission_level": "DANGEROUS", "status": "READY"},
        ]
    
    for plugin in plugins:
        perm = plugin.get("permission_level", "SAFE")
        perm_style = {
            "SAFE": "[green]SAFE[/green]",
            "LIMITED": "[yellow]LIMITED[/yellow]",
            "DANGEROUS": "[red]DANGEROUS[/red]",
        }.get(perm, perm)
        
        table.add_row(
            plugin.get("name", "Unknown"),
            plugin.get("version", "?"),
            perm_style,
            "[cyan]● READY[/cyan]"
        )
    
    return table


async def show_dashboard(client: BugBountyClient, console: Console):
    """Display the main dashboard"""
    console.clear()
    console.print(create_header())
    console.print()
    
    # Fetch data concurrently
    programs, targets, approvals, plugins = await asyncio.gather(
        client.get_programs(),
        client.get_targets(),
        client.get_approvals(),
        client.get_plugins()
    )
    
    running_count = sum(1 for t in targets if t.get("status") == "RUNNING")
    
    # Metrics
    console.print(create_metrics_row(len(programs), len(targets), running_count, len(approvals)))
    console.print()
    
    # Pipeline status
    pipeline = Table(box=box.SIMPLE, show_header=False)
    pipeline.add_column()
    pipeline.add_row("[cyan]PIPELINE:[/cyan]  [green]4[/] Recon  [blue]2[/] Scanning  [yellow]1[/] Analyzing  [red]3[/] Review")
    console.print(pipeline)
    console.print()
    
    # Two column layout simulation
    with console.screen():
        console.print(create_targets_table(targets))
        console.print()
        console.print(create_findings_table())


async def show_targets(client: BugBountyClient, console: Console):
    """Display targets view"""
    console.clear()
    console.print(create_header())
    console.print()
    
    targets = await client.get_targets()
    
    if not targets:
        # Demo data
        targets = [
            {"name": "api.example.com", "program_name": "HackerOne Example", "status": "RUNNING", "surface_coverage": 78, "findings_count": 3},
            {"name": "app.example.com", "program_name": "Bugcrowd Demo", "status": "COMPLETED", "surface_coverage": 100, "findings_count": 7},
            {"name": "staging.example.com", "program_name": "Private Alpha", "status": "PENDING", "surface_coverage": 0, "findings_count": 0},
            {"name": "portal.example.com", "program_name": "HackerOne Example", "status": "RUNNING", "surface_coverage": 45, "findings_count": 1},
        ]
    
    console.print(create_targets_table(targets))


async def show_approvals(client: BugBountyClient, console: Console):
    """Display approvals queue"""
    console.clear()
    console.print(create_header())
    console.print()
    
    approvals = await client.get_approvals()
    console.print(create_approvals_table(approvals))


async def show_plugins(client: BugBountyClient, console: Console):
    """Display plugins status"""
    console.clear()
    console.print(create_header())
    console.print()
    
    plugins = await client.get_plugins()
    console.print(create_plugins_grid(plugins))


async def interactive_mode(client: BugBountyClient, console: Console):
    """Interactive menu mode"""
    while True:
        console.clear()
        console.print(create_header())
        console.print()
        
        menu = Table(box=box.ROUNDED, show_header=False)
        menu.add_column(style="cyan")
        menu.add_row("[1] Dashboard")
        menu.add_row("[2] Targets")
        menu.add_row("[3] Approvals")
        menu.add_row("[4] Plugins")
        menu.add_row("[5] Settings")
        menu.add_row("")
        menu.add_row("[Q] Quit")
        console.print(menu)
        
        choice = console.input("\n[cyan]Select option > [/cyan]").strip().lower()
        
        if choice == '1' or choice == 'd':
            await show_dashboard(client, console)
            console.input("\n[dim]Press Enter to continue...[/dim]")
        elif choice == '2' or choice == 't':
            await show_targets(client, console)
            console.input("\n[dim]Press Enter to continue...[/dim]")
        elif choice == '3' or choice == 'a':
            await show_approvals(client, console)
            console.input("\n[dim]Press Enter to continue...[/dim]")
        elif choice == '4' or choice == 'p':
            await show_plugins(client, console)
            console.input("\n[dim]Press Enter to continue...[/dim]")
        elif choice == 'q':
            break


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="BugBounty Automator - Kali Linux Terminal Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 bugbounty_tui.py              # Interactive mode
  python3 bugbounty_tui.py --dashboard # Show dashboard
  python3 bugbounty_tui.py --targets   # Show targets
  python3 bugbounty_tui.py --api http://localhost:8000

Keybindings (Interactive Mode):
  1/d - Dashboard
  2/t - Targets
  3/a - Approvals
  4/p - Plugins
  q   - Quit
        """
    )
    
    parser.add_argument(
        '--api', '-a',
        default='http://localhost:8000',
        help='API URL (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--dashboard', '-d',
        action='store_true',
        help='Show dashboard'
    )
    parser.add_argument(
        '--targets', '-t',
        action='store_true',
        help='Show targets'
    )
    parser.add_argument(
        '--approvals',
        action='store_true',
        help='Show approvals queue'
    )
    parser.add_argument(
        '--plugins',
        action='store_true',
        help='Show plugins'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output raw JSON'
    )
    
    args = parser.parse_args()
    
    client = BugBountyClient(api_url=args.api)
    console = Console(
        force_terminal=True,
        color_system="auto",
        theme=None,
        width=120
    )
    
    try:
        if args.dashboard:
            await show_dashboard(client, console)
        elif args.targets:
            await show_targets(client, console)
        elif args.approvals:
            await show_approvals(client, console)
        elif args.plugins:
            await show_plugins(client, console)
        else:
            await interactive_mode(client, console)
    finally:
        await client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[cyan]Exiting BugBounty Automator...[/cyan]")
        sys.exit(0)
