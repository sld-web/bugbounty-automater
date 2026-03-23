"""AI-driven workflow generator for bug bounty programs."""
import json
import logging
from typing import Any
from enum import Enum

logger = logging.getLogger(__name__)


class WorkflowPhase(str, Enum):
    RECON = "recon"
    ENUMERATION = "enumeration"
    VULN_DETECTION = "vulnerability_detection"
    EXPLOITATION = "exploitation"
    POST_EXPLOIT = "post_exploitation"
    REPORTING = "reporting"


class StepType(str, Enum):
    RECON = "recon"
    SCAN = "scan"
    ENUMERATE = "enumerate"
    TEST = "test"
    EXPLOIT = "exploit"
    MANUAL_REVIEW = "manual_review"
    APPROVAL = "approval"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


WORKFLOW_PHASES = [
    {
        "id": "recon",
        "name": "Reconnaissance",
        "description": "Passive and active information gathering",
        "order": 1,
        "steps": [
            {"type": "recon", "name": "Passive Subdomain Enumeration", "tool": "subfinder", "auto": True},
            {"type": "recon", "name": "Active Subdomain Discovery", "tool": "amass", "auto": True},
            {"type": "recon", "name": "Port Scanning", "tool": "nmap", "auto": True},
            {"type": "recon", "name": "Technology Fingerprinting", "tool": "httpx", "auto": True},
        ]
    },
    {
        "id": "enumeration",
        "name": "Enumeration",
        "description": "Deep discovery of services and endpoints",
        "order": 2,
        "steps": [
            {"type": "enumerate", "name": "Web Crawling", "tool": "katana", "auto": True},
            {"type": "enumerate", "name": "Directory Bruteforcing", "tool": "ffuf", "auto": True},
            {"type": "enumerate", "name": "Parameter Discovery", "tool": "arjun", "auto": True},
            {"type": "enumerate", "name": "API Endpoint Discovery", "tool": "swagger猎人", "auto": True},
        ]
    },
    {
        "id": "vulnerability_detection",
        "name": "Vulnerability Detection",
        "description": "Automated vulnerability scanning",
        "order": 3,
        "steps": [
            {"type": "scan", "name": "Template-based Vulnerability Scan", "tool": "nuclei", "auto": True},
            {"type": "scan", "name": "Web Application Scan", "tool": "zap", "auto": True},
            {"type": "manual_review", "name": "Manual Web Testing", "tool": "burpsuite", "auto": False},
        ]
    },
    {
        "id": "exploitation",
        "name": "Exploitation",
        "description": "Targeted exploitation of vulnerabilities",
        "order": 4,
        "steps": [
            {"type": "exploit", "name": "SQL Injection Testing", "tool": "sqlmap", "auto": True},
            {"type": "exploit", "name": "XSS Testing", "tool": "xsstrike", "auto": True},
            {"type": "exploit", "name": "CSRF Testing", "tool": "burpsuite", "auto": False},
        ]
    },
    {
        "id": "post_exploitation",
        "name": "Post-Exploitation",
        "description": "Data gathering and privilege escalation",
        "order": 5,
        "steps": [
            {"type": "test", "name": "Credential Testing", "tool": "hydra", "auto": True},
            {"type": "test", "name": "File Metadata Analysis", "tool": "exiftool", "auto": True},
        ]
    },
    {
        "id": "reporting",
        "name": "Reporting",
        "description": "Document findings and submit report",
        "order": 6,
        "steps": [
            {"type": "manual_review", "name": "Review Findings", "tool": None, "auto": False},
            {"type": "manual_review", "name": "Prepare PoC", "tool": None, "auto": False},
            {"type": "manual_review", "name": "Submit Report", "tool": None, "auto": False},
        ]
    },
]


class WorkflowGenerator:
    """Generate detailed workflows based on program analysis and targets."""

    def __init__(self):
        self.phases = WORKFLOW_PHASES

    def generate_workflow(
        self,
        program_analysis: dict,
        available_tools: list[str],
    ) -> dict:
        """Generate a complete workflow for the program."""
        targets = program_analysis.get("targets", [])
        rules = program_analysis.get("rules", [])
        out_of_scope = program_analysis.get("out_of_scope", [])
        testing_notes = program_analysis.get("testing_notes", "")

        workflow = {
            "id": f"workflow_{program_analysis.get('program_name', 'unknown')}",
            "program_name": program_analysis.get("introduction", "")[:100],
            "phases": [],
            "rules": rules,
            "out_of_scope": out_of_scope,
            "testing_notes": testing_notes,
            "total_steps": 0,
            "auto_steps": 0,
            "manual_steps": 0,
            "approval_points": [],
        }

        for idx, target in enumerate(targets):
            target_type = target.get("type", "webapp")
            target_domains = target.get("scope_domains", [])
            target_ips = target.get("scope_ips", [])
            
            target_phases = self._generate_target_phases(
                target=target,
                target_type=target_type,
                available_tools=available_tools,
                rule_context=rules,
            )

            target_workflow = {
                "target_id": f"target_{idx + 1}",
                "target_name": target.get("name", f"Target {idx + 1}"),
                "target_type": target_type,
                "domains": target_domains,
                "ips": target_ips,
                "phases": target_phases,
                "risk_score": self._calculate_risk_score(target),
                "estimated_duration": self._estimate_duration(target_phases),
            }

            workflow["phases"].append(target_workflow)
            workflow["total_steps"] += sum(len(p["steps"]) for p in target_phases)
            workflow["auto_steps"] += sum(
                sum(1 for s in p["steps"] if s.get("auto")) 
                for p in target_phases
            )
            workflow["manual_steps"] += sum(
                sum(1 for s in p["steps"] if not s.get("auto")) 
                for p in target_phases
            )
            
            for phase in target_phases:
                for step in phase["steps"]:
                    if step.get("requires_approval"):
                        workflow["approval_points"].append({
                            "step": step["name"],
                            "phase": phase["name"],
                            "target": target.get("name"),
                            "reason": step.get("approval_reason", "High risk operation"),
                        })

        return workflow

    def _generate_target_phases(
        self,
        target: dict,
        target_type: str,
        available_tools: list[str],
        rule_context: list[str],
    ) -> list[dict]:
        """Generate phases for a specific target."""
        phases = []
        
        base_phases = self._get_base_phases_for_type(target_type)
        
        for base_phase in base_phases:
            phase = {
                "id": f"{target['name']}_{base_phase['id']}",
                "name": base_phase["name"],
                "description": base_phase["description"],
                "order": base_phase["order"],
                "steps": [],
                "status": "pending",
            }

            for base_step in base_phase["steps"]:
                step = self._create_step(
                    base_step=base_step,
                    target=target,
                    available_tools=available_tools,
                    rule_context=rule_context,
                )
                phase["steps"].append(step)

            phases.append(phase)

        return phases

    def _get_base_phases_for_type(self, target_type: str) -> list[dict]:
        """Get base phases based on target type."""
        if target_type == "network":
            return [p for p in self.phases if p["id"] in ["recon", "enumeration", "vulnerability_detection", "exploitation", "reporting"]]
        elif target_type == "api":
            return [p for p in self.phases if p["id"] in ["recon", "enumeration", "vulnerability_detection", "exploitation", "reporting"]]
        elif target_type == "mobile":
            return [p for p in self.phases if p["id"] in ["recon", "enumeration", "vulnerability_detection", "exploitation", "post_exploitation", "reporting"]]
        elif target_type == "hardware":
            return [p for p in self.phases if p["id"] in ["recon", "enumeration", "vulnerability_detection", "exploitation", "reporting"]]
        else:
            return self.phases

    def _create_step(
        self,
        base_step: dict,
        target: dict,
        available_tools: list[str],
        rule_context: list[str],
    ) -> dict:
        """Create a workflow step with all metadata."""
        tool_name = base_step.get("tool")
        is_auto = base_step.get("auto", False)
        
        tool_available = bool(tool_name and any(
            t.lower() == tool_name.lower() 
            for t in available_tools
        ))

        step = {
            "id": f"step_{base_step['type']}_{target['name']}",
            "type": base_step["type"],
            "name": base_step["name"],
            "tool": tool_name,
            "tool_available": tool_available,
            "auto": is_auto if tool_available else False,
            "status": "pending",
            "command": self._build_command(tool_name, target) if tool_name and tool_available else None,
            "risk_level": self._assess_risk(base_step["type"], rule_context),
            "requires_approval": self._requires_approval(base_step["type"], rule_context),
            "approval_reason": None,
            "payloads": self._get_payloads(base_step["type"]),
            "validation": self._get_validation(base_step["type"]),
            "blockers": self._check_blockers(base_step["type"], rule_context),
        }

        if step["requires_approval"]:
            step["approval_reason"] = self._get_approval_reason(step["risk_level"], rule_context)

        return step

    def _build_command(self, tool: str, target: dict) -> str:
        """Build the command for a tool based on target."""
        domains = target.get("scope_domains", [])
        ips = target.get("scope_ips", [])
        
        target_str = domains[0] if domains else (ips[0] if ips else "TARGET")
        
        commands = {
            "nmap": f"nmap -sV -sC -oA nmap_scan {target_str}",
            "subfinder": f"subfinder -d {target_str} -o subdomains.txt",
            "amass": f"amass enum -passive -d {target_str} -o amass.txt",
            "httpx": f"cat subdomains.txt | httpx -title -tech-detect -o httpx_results.json",
            "nuclei": f"nuclei -l targets.txt -t vulnerabilities/ -o nuclei_findings.txt",
            "ffuf": f"ffuf -w wordlist.txt -u {target_str}/FUZZ -o ffuf_results.json",
            "zap": f"zap-baseline.py -t {target_str} -J zap_report.json",
            "sqlmap": f"sqlmap -u '{target_str}' --batch --risk=2",
            "exiftool": f"exiftool -json uploaded_files/*.pdf",
        }
        
        return commands.get(tool.lower(), f"# {tool} - configure manually")

    def _assess_risk(self, step_type: str, rules: list[str]) -> str:
        """Assess risk level for a step."""
        high_risk_types = ["exploit", "test"]
        medium_risk_types = ["scan", "enumerate"]
        
        rule_text = " ".join(rules).lower()
        
        if step_type in high_risk_types:
            if "no exploitation" in rule_text or "read only" in rule_text:
                return RiskLevel.HIGH.value
            return RiskLevel.HIGH.value
        elif step_type in medium_risk_types:
            if "rate limit" in rule_text or "throttle" in rule_text:
                return RiskLevel.MEDIUM.value
            return RiskLevel.MEDIUM.value
        return RiskLevel.LOW.value

    def _requires_approval(self, step_type: str, rules: list[str]) -> bool:
        """Check if step requires human approval."""
        rule_text = " ".join(rules).lower()
        
        if step_type in ["exploit", "test"]:
            if "requires approval" in rule_text or "manual only" in rule_text:
                return True
            if "no exploitation" in rule_text or "read only" in rule_text:
                return True
            return True
        
        return False

    def _get_approval_reason(self, risk_level: str, rules: list[str]) -> str:
        """Get the reason for approval requirement."""
        if risk_level in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]:
            return "High-risk operation - requires human review"
        return "Manual verification required before proceeding"

    def _get_payloads(self, step_type: str) -> list[dict]:
        """Get test payloads for the step type."""
        payloads = {
            "test": [
                {"name": "SQL Injection", "category": "injection", "severity": "high"},
                {"name": "XSS Reflected", "category": "xss", "severity": "medium"},
                {"name": "XSS Stored", "category": "xss", "severity": "high"},
                {"name": "IDOR", "category": "auth", "severity": "high"},
                {"name": "SSRF", "category": "injection", "severity": "high"},
                {"name": "Open Redirect", "category": "redirect", "severity": "medium"},
            ],
            "scan": [
                {"name": "Nuclei Templates", "category": "template", "severity": "varies"},
                {"name": "Custom Payloads", "category": "custom", "severity": "varies"},
            ],
            "exploit": [
                {"name": "RCE Test", "category": "command_injection", "severity": "critical"},
                {"name": "SQLi Exploit", "category": "sql_injection", "severity": "high"},
            ],
        }
        return payloads.get(step_type, [])

    def _get_validation(self, step_type: str) -> dict:
        """Get validation criteria for the step."""
        validations = {
            "recon": {"check": "hosts_found", "min": 1},
            "scan": {"check": "vulnerabilities_found", "min": 0},
            "test": {"check": "test_cases_executed", "min": 1},
            "exploit": {"check": "exploit_successful", "min": 0},
        }
        return validations.get(step_type, {"check": "completed", "min": 0})

    def _check_blockers(self, step_type: str, rules: list[str]) -> list[str]:
        """Check for rule-based blockers."""
        blockers = []
        rule_text = " ".join(rules).lower()
        
        if step_type == "exploit":
            if "no exploitation" in rule_text:
                blockers.append("Program policy prohibits active exploitation")
            if "read only" in rule_text:
                blockers.append("Program requires read-only testing only")
        
        if "rate limit" in rule_text or "throttle" in rule_text:
            blockers.append("Rate limiting in effect - slow down scans")
        
        if "business hours" in rule_text:
            blockers.append("Testing restricted to business hours")
        
        return blockers

    def _calculate_risk_score(self, target: dict) -> dict:
        """Calculate risk score for a target."""
        domains = len(target.get("scope_domains", []))
        ips = len(target.get("scope_ips", []))
        target_type = target.get("type", "webapp")
        
        base_score = 50
        base_score += domains * 5
        base_score += ips * 3
        
        if target_type in ["api", "mobile"]:
            base_score += 10
        elif target_type == "network":
            base_score += 15
        elif target_type == "hardware":
            base_score += 20
        
        return {
            "score": min(base_score, 100),
            "level": "high" if base_score > 70 else "medium" if base_score > 40 else "low",
        }

    def _estimate_duration(self, phases: list[dict]) -> dict:
        """Estimate duration for the workflow."""
        auto_minutes = 0
        manual_minutes = 0
        
        for phase in phases:
            for step in phase["steps"]:
                if step.get("auto"):
                    auto_minutes += 10
                else:
                    manual_minutes += 30
        
        total_hours = (auto_minutes + manual_minutes) // 60
        
        return {
            "auto_minutes": auto_minutes,
            "manual_minutes": manual_minutes,
            "total_hours": total_hours,
            "estimated": f"~{total_hours} hours",
        }


workflow_generator = WorkflowGenerator()
