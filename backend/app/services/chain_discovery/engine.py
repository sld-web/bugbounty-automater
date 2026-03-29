"""Basic chain discovery engine for finding potential exploit chains."""
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
from enum import Enum

from app.models.target import Target
from app.models.finding import Finding, Severity
from app.models.flow_card import FlowCard
from app.utils.logger import get_logger

logger = get_logger(__name__)

# String constants for finding types (since we store vuln_type as string)
class FindingTypes:
    SQL_INJECTION = "sql_injection"
    FILE_UPLOAD = "file_upload"
    CROSS_SITE_SCRIPTING = "xss"
    CROSS_SITE_REQUEST_FORGERY = "csrf"
    IDOR = "idor"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SERVER_SIDE_REQUEST_FORGERY = "ssrf"
    XML_EXTERNAL_ENTITY = "xxe"
    AUTHENTICATION_BYPASS = "authentication_bypass"
    REMOTE_CODE_EXECUTION = "rce"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    DESERIALIZATION = "deserialization"
    INFORMATION_DISCLOSURE = "information_disclosure"
    MISCONFIGURATION = "misconfiguration"


class ChainType(Enum):
    """Types of exploit chains we can detect."""
    SQLI_TO_FILE_UPLOAD = "sqli_to_file_upload"
    XSS_PLUS_CSRF = "xss_plus_csrf"
    IDOR_PLUS_PRIVILEGE_ESCALATION = "idor_plus_privilege_escalation"
    SSRF_PLUS_FILE_READ = "ssrf_plus_file_read"
    XXE_PLUS_SSRF = "xxe_plus_ssrf"
    AUTH_BYPASS_PLUS_ADMIN_ACCESS = "auth_bypass_plus_admin_access"
    INSECURE_DIRECT_OBJECT_REFERENCE = "idor"
    CROSS_SITE_SCRIPTING = "xss"
    CROSS_SITE_REQUEST_FORGERY = "csrf"
    SERVER_SIDE_REQUEST_FORGERY = "ssrf"
    XML_EXTERNAL_ENTITY = "xxe"
    SQL_INJECTION = "sqli"
    COMMAND_INJECTION = "cmd_inj"
    PATH_TRAVERSAL = "path_traversal"
    FILE_UPLOAD = "file_upload"
    AUTHENTICATION_BYPASS = "auth_bypass"
    PRIVILEGE_ESCALATION = "priv_esc"
    INFORMATION_DISCLOSURE = "info_disclosure"
    MISCONFIGURATION = "misconfig"


class ChainDiscoveryEngine:
    """Discover potential exploit chains from individual findings."""
    
    def __init__(self):
        # Define chain templates: (finding1_type, finding2_type) -> chain_type, description, impact
        self.chain_templates = {
            # (finding1_type, finding2_type): (chain_type, description, impact_score)
            (FindingTypes.SQL_INJECTION, FindingTypes.FILE_UPLOAD): (
                ChainType.SQLI_TO_FILE_UPLOAD,
                "SQL injection can extract database credentials or write files, combined with file upload can lead to RCE",
                9.0  # High impact
            ),
            (FindingTypes.FILE_UPLOAD, FindingTypes.SQL_INJECTION): (
                ChainType.SQLI_TO_FILE_UPLOAD,
                "File upload can write webshell, SQL injection can be used to locate web root or credentials",
                9.0
            ),
            (FindingTypes.CROSS_SITE_SCRIPTING, FindingTypes.CROSS_SITE_REQUEST_FORGERY): (
                ChainType.XSS_PLUS_CSRF,
                "XSS can steal CSRF tokens or perform actions as the victim user",
                8.0
            ),
            (FindingTypes.CROSS_SITE_REQUEST_FORGERY, FindingTypes.CROSS_SITE_SCRIPTING): (
                ChainType.XSS_PLUS_CSRF,
                "CSRF can force user to perform XSS-triggering action",
                8.0
            ),
            (FindingTypes.IDOR, FindingTypes.PRIVILEGE_ESCALATION): (
                ChainType.IDOR_PLUS_PRIVILEGE_ESCALATION,
                "IDOR can access sensitive data, privilege escalation can gain higher access levels",
                8.5
            ),
            (FindingTypes.PRIVILEGE_ESCALATION, FindingTypes.IDOR): (
                ChainType.IDOR_PLUS_PRIVILEGE_ESCALATION,
                "Privilege escalation gains access, IDOR can then access specific sensitive resources",
                8.5
            ),
            (FindingTypes.SERVER_SIDE_REQUEST_FORGERY, FindingTypes.FILE_UPLOAD): (  # Changed FILE_READ to FILE_UPLOAD as we don't have FILE_READ
                ChainType.SSRF_PLUS_FILE_READ,
                "SSRF can make internal requests, combined with file upload can lead to RCE",
                7.5
            ),
            (FindingTypes.XML_EXTERNAL_ENTITY, FindingTypes.SERVER_SIDE_REQUEST_FORGERY): (
                ChainType.XXE_PLUS_SSRF,
                "XXE can read local files, SSRF can make external requests - combined for data exfiltration",
                8.0
            ),
            (FindingTypes.AUTHENTICATION_BYPASS, FindingTypes.PRIVILEGE_ESCALATION): (
                ChainType.AUTH_BYPASS_PLUS_ADMIN_ACCESS,
                "Authentication bypass gains access, privilege escalation can reach admin levels",
                9.0
            ),
        }
        
        # Single finding chains (high severity findings that are dangerous on their own)
        self.high_risk_single_findings = {
            FindingTypes.REMOTE_CODE_EXECUTION: 10.0,
            FindingTypes.SQL_INJECTION: 7.5,
            FindingTypes.FILE_UPLOAD: 7.0,
            FindingTypes.COMMAND_INJECTION: 8.5,
            FindingTypes.PATH_TRAVERSAL: 6.0,
            FindingTypes.DESERIALIZATION: 8.0,
            FindingTypes.SERVER_SIDE_REQUEST_FORGERY: 6.5,
            FindingTypes.XML_EXTERNAL_ENTITY: 7.0,
        }
    
    def discover_chains_for_target(self, target: Target) -> List[Dict[str, Any]]:
        """
        Discover potential exploit chains for a target based on its findings.
        
        Returns:
            List of chain discoveries with details
        """
        chains = []
        
        # Get findings for this target
        findings = getattr(target, 'findings', [])
        if not findings:
            return chains
        
        # Convert findings to tuples of (type, severity, description, finding_id)
        finding_tuples = []
        for finding in findings:
            # The vuln_type field stores the finding type as string
            vuln_type = getattr(finding, 'vuln_type', '')
            severity = getattr(finding, 'severity', None)
            description = getattr(finding, 'description', '')
            finding_id = str(getattr(finding, 'id', ''))
            if vuln_type:
                finding_tuples.append((
                    vuln_type,
                    severity,
                    description,
                    finding_id
                ))
        
        # Check for chain templates
        for i, (type1, severity1, desc1, id1) in enumerate(finding_tuples):
            for j, (type2, severity2, desc2, id2) in enumerate(finding_tuples):
                if i >= j:  # Avoid duplicate checks and self-checking
                    continue
                    
                # Check both orders (type1+type2 and type2+type1)
                chain_info = self._check_chain_template(type1, type2, desc1, desc2, id1, id2)
                if chain_info:
                    # Add severity information from the findings
                    chain_info['findings'] = [
                        {
                            'type': type1,
                            'severity': severity1.value if hasattr(severity1, 'value') else str(severity1),
                            'description': desc1[:200],
                            'id': id1
                        },
                        {
                            'type': type2,
                            'severity': severity2.value if hasattr(severity2, 'value') else str(severity2),
                            'description': desc2[:200],
                            'id': id2
                        }
                    ]
                    chains.append(chain_info)
                
                chain_info = self._check_chain_template(type2, type1, desc2, desc1, id2, id1)
                if chain_info:
                    # Add severity information from the findings
                    chain_info['findings'] = [
                        {
                            'type': type2,
                            'severity': severity2.value if hasattr(severity2, 'value') else str(severity2),
                            'description': desc2[:200],
                            'id': id2
                        },
                        {
                            'type': type1,
                            'severity': severity1.value if hasattr(severity1, 'value') else str(severity1),
                            'description': desc1[:200],
                            'id': id1
                        }
                    ]
                    chains.append(chain_info)
        
        # Check for high-risk single findings
        for finding_type, severity, desc, fid in finding_tuples:
            if finding_type in self.high_risk_single_findings:
                impact = self.high_risk_single_findings[finding_type]
                chains.append({
                    'chain_type': f"single_{finding_type}",
                    'description': f"High-risk single finding: {finding_type.upper()} - {desc[:100]}...",
                    'impact_score': impact,
                    'findings': [
                        {
                            'type': finding_type,
                            'severity': severity.value if hasattr(severity, 'value') else str(severity),
                            'description': desc,
                            'id': fid
                        }
                    ],
                    'chain_description': f"Single {finding_type} finding with high impact potential",
                    'recommended_action': f"Prioritize exploitation of this {finding_type} finding"
                })
        
        # Sort by impact score (descending)
        chains.sort(key=lambda x: x.get('impact_score', 0), reverse=True)
        
        return chains
    
    def _check_chain_template(self, 
                             type1: str, 
                             type2: str, 
                             desc1: str, 
                             desc2: str, 
                             id1: str, 
                             id2: str) -> Optional[Dict[str, Any]]:
        """Check if two findings match a chain template."""
        # Normalize types for comparison
        key1 = (type1, type2)
        key2 = (type2, type1)
        
        chain_info = None
        if key1 in self.chain_templates:
            chain_type, description, impact = self.chain_templates[key1]
            chain_info = {
                'chain_type': chain_type.value,
                'description': description,
                'impact_score': impact,
                'findings': [
                    {
                        'type': type1,
                        'severity': 'unknown',  # We don't have severity in the tuple for chain templates
                        'description': desc1[:200],
                        'id': id1
                    },
                    {
                        'type': type2,
                        'severity': 'unknown',  # We don't have severity in the tuple for chain templates
                        'description': desc2[:200],
                        'id': id2
                    }
                ],
                'chain_description': f"Chain: {type1.upper()} + {type2.upper()}",
                'recommended_action': f"Test for chaining {type1} with {type2}"
            }
        elif key2 in self.chain_templates:
            chain_type, description, impact = self.chain_templates[key2]
            chain_info = {
                'chain_type': chain_type.value,
                'description': description,
                'impact_score': impact,
                'findings': [
                    {
                        'type': type2,
                        'severity': 'unknown',
                        'description': desc2[:200],
                        'id': id2
                    },
                    {
                        'type': type1,
                        'severity': 'unknown',
                        'description': desc1[:200],
                        'id': id1
                    }
                ],
                'chain_description': f"Chain: {type2.upper()} + {type1.upper()}",
                'recommended_action': f"Test for chaining {type2} with {type1}"
            }
        
        return chain_info
    
    def create_chain_flow_card(self, target: Target, chain_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a flow card representation of a discovered chain.
        
        Returns:
            Flow card data or None if creation fails
        """
        try:
            return {
                'id': f"chain_{chain_info['chain_type']}_{target.id}",
                'type': 'chain',
                'name': f"Potential Exploit Chain: {chain_info['chain_type'].replace('_', ' ').title()}",
                'description': chain_info['description'],
                'tool': 'chain_discovery',
                'tool_available': True,
                'auto': False,  # Chains require manual verification
                'status': 'pending',
                'command': f"Manual verification required for chain: {chain_info['chain_description']}",
                'risk_level': 'high' if chain_info.get('impact_score', 0) >= 8.0 else 'medium',
                'requires_approval': True,
                'approval_reason': f"Chain exploit requires manual verification before reporting",
                'payloads': [],
                'validation': {
                    'check': 'manual_verification',
                    'min': 1
                },
                'blockers': [],
                'metadata': {
                    'chain_type': chain_info['chain_type'],
                    'impact_score': chain_info.get('impact_score', 0),
                    'findings': chain_info.get('findings', []),
                    'target_id': str(target.id)
                }
            }
        except Exception as e:
            logger.error(f"Error creating chain flow card: {e}")
            return None


# Global instance
chain_discovery_engine = ChainDiscoveryEngine()