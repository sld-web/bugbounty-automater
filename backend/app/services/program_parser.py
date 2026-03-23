import re
import logging
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ParsedProgram(BaseModel):
    name: str
    platform: str = "hackerone"
    auth_level: str = "L1"
    scope_domains: list[str] = []
    scope_excluded: list[str] = []
    reward_tiers: dict = {}
    severity_mapping: dict = {}
    out_of_scope: list[str] = []
    rules: list[str] = []
    program_policy: str = ""
    testing_header: Optional[str] = None
    email_requirement: Optional[str] = None
    response_times: dict = {}
    ai_enhanced: bool = False
    confidence: float = 0.0
    assets: list[dict] = []
    attachments: list[dict] = []


async def parse_program_policy_ai(text: str) -> ParsedProgram:
    """Parse program policy using AI with fallback to regex."""
    try:
        from app.services.openai_service import openai_service
        
        if openai_service.is_available:
            logger.info("Using AI to parse program policy")
            ai_result = await openai_service.extract_program_config(text)
            
            if ai_result:
                confidence = openai_service.calculate_confidence(ai_result, text)
                
                return ParsedProgram(
                    name=ai_result.get("name", extract_name(text)),
                    platform=ai_result.get("platform", "hackerone"),
                    auth_level=ai_result.get("auth_level", "L1"),
                    scope_domains=ai_result.get("scope_domains", []),
                    scope_excluded=ai_result.get("scope_excluded", []),
                    reward_tiers=ai_result.get("reward_tiers", {}),
                    severity_mapping=ai_result.get("severity_mapping", {}),
                    out_of_scope=ai_result.get("out_of_scope", []),
                    rules=ai_result.get("rules", []),
                    program_policy=text,
                    testing_header=ai_result.get("special_requirements", {}).get("testing_note"),
                    ai_enhanced=True,
                    confidence=confidence,
                )
            else:
                logger.warning("AI returned empty result, falling back to regex")
        
    except Exception as e:
        logger.warning(f"AI parsing failed: {e}, falling back to regex")
    
    return parse_program_policy(text)


def parse_program_policy(text: str) -> ParsedProgram:
    """Parse raw program policy text into structured data."""
    
    text_lower = text.lower()
    
    # Extract program name
    name = extract_name(text)
    
    # Extract domains from scope section
    domains = extract_domains(text)
    excluded = extract_excluded(text)
    
    # Extract reward tiers
    rewards = extract_rewards(text)
    
    # Extract severity mappings
    severity_map = extract_severity_mapping(text)
    
    # Extract out of scope items
    out_of_scope = extract_out_of_scope(text)
    
    # Extract rules
    rules = extract_rules(text)
    
    # Extract testing header
    header = extract_testing_header(text)
    
    # Extract email requirement
    email = extract_email_requirement(text)
    
    # Extract response times
    response_times = extract_response_times(text)
    
    # Extract assets and attachments
    assets = extract_assets(text)
    attachments = extract_attachments(text)
    
    return ParsedProgram(
        name=name,
        scope_domains=domains,
        scope_excluded=excluded,
        reward_tiers=rewards,
        severity_mapping=severity_map,
        out_of_scope=out_of_scope,
        rules=rules,
        testing_header=header,
        email_requirement=email,
        response_times=response_times,
        assets=assets,
        attachments=attachments,
    )


def extract_name(text: str) -> str:
    """Extract program name from text."""
    lines = text.strip().split('\n')
    
    name_patterns = [
        r'Program\s*Name[:\s]*([^\n]+)',
        r'([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*)\s+Bug\s+Bounty',
        r'Bug\s*Bounty\s*Program[:\s]*([^\n]+)',
        r'(NetScaler\s*[A-Z]*|DoorDash|Shopify|Uber)[^\n]*',
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip() if match.group(1) else match.group(0).strip()
            if 2 < len(name) < 80:
                return name
    
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) > 3 and len(line) < 60:
            clean = re.sub(r'^[#\-*•]\s*', '', line)
            clean = clean.strip()
            if clean and not any(x in clean.lower() for x in ['highlights', 'rewards', 'rules', 'scope', 'introduction', 'overview', 'response']):
                return clean
    
    return "Bug Bounty Program"


def extract_domains(text: str) -> list[str]:
    """Extract in-scope domains from text."""
    domains = []
    
    scope_section = re.search(r'(?:in.?scope|eligible|core assets?)[\s:]*\n(.*?)(?=\n\s*(?:out.?scope|excluded|ineligible)|$)', 
                             text, re.IGNORECASE | re.DOTALL)
    
    if scope_section:
        section_text = scope_section.group(1)
    else:
        section_text = text
    
    domain_patterns = [
        r'(?:https?://)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})*)',
        r'([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})*)',
        r'\*\.([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,})',
    ]
    
    for pattern in domain_patterns:
        matches = re.findall(pattern, section_text)
        for match in matches:
            if match and not any(x in match.lower() for x in ['example', 'localhost', 'yourdomain']):
                if match.endswith('.com') or match.endswith('.org') or match.endswith('.io') or match.endswith('.net') or match.endswith('.info'):
                    if match not in domains:
                        domains.append(match)
    
    asset_matches = re.findall(r'([a-zA-Z0-9][a-zA-Z0-9-]*\.(?:com|net|org|io|info|co))\b', text, re.IGNORECASE)
    for match in asset_matches:
        if match and not any(x in match.lower() for x in ['example', 'localhost', 'yourdomain']):
            if match not in domains:
                domains.append(match)
    
    return list(set(domains))[:20]


def extract_excluded(text: str) -> list[str]:
    """Extract excluded domains."""
    excluded = []
    
    exclude_section = re.search(r'(?:out.?scope|excluded|ineligible|not eligible)[\s:]*\n(.*?)(?=\n\s*\n|\Z)', 
                               text, re.IGNORECASE | re.DOTALL)
    
    if exclude_section:
        section_text = exclude_section.group(1)
        
        domain_patterns = [
            r'(?:https?://)?(?:www\.)?([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})*)',
            r'\*\.([a-zA-Z0-9][-a-zA-Z0-9]*\.[a-zA-Z]{2,})',
        ]
        
        for pattern in domain_patterns:
            matches = re.findall(pattern, section_text)
            for match in matches:
                if match and not any(x in match.lower() for x in ['example', 'localhost']):
                    full = f"*.{match}" if not match.startswith('*') else match
                    if full not in excluded:
                        excluded.append(full)
    
    return list(set(excluded))[:20]


def extract_rewards(text: str) -> dict:
    """Extract reward tiers from text."""
    rewards = {}
    
    try:
        amounts = re.findall(r'\$([\d,]+)', text)
        if amounts:
            amounts = [int(a.replace(',', '')) for a in amounts[:4]]
            amounts_sorted = sorted(amounts, reverse=True)
            
            if len(amounts_sorted) >= 4:
                rewards['critical'] = {'min': amounts_sorted[0], 'max': amounts_sorted[0]}
                rewards['high'] = {'min': amounts_sorted[1], 'max': amounts_sorted[1]}
                rewards['medium'] = {'min': amounts_sorted[2], 'max': amounts_sorted[2]}
                rewards['low'] = {'min': amounts_sorted[3], 'max': amounts_sorted[3]}
            elif len(amounts_sorted) >= 3:
                rewards['critical'] = {'min': amounts_sorted[0], 'max': amounts_sorted[0]}
                rewards['high'] = {'min': amounts_sorted[1], 'max': amounts_sorted[1]}
                rewards['medium'] = {'min': amounts_sorted[2], 'max': amounts_sorted[2]}
            elif len(amounts_sorted) >= 2:
                rewards['high'] = {'min': amounts_sorted[0], 'max': amounts_sorted[0]}
                rewards['medium'] = {'min': amounts_sorted[1], 'max': amounts_sorted[1]}
        
        reward_section = re.search(r'(?:reward|bounty|compensation)[\s:]*\n(.*?)(?=\n\s*\n|\Z)', 
                                 text, re.IGNORECASE | re.DOTALL)
        
        if reward_section:
            section_text = reward_section.group(1)
        else:
            section_text = text
        
        for severity in ['critical', 'high', 'medium', 'low']:
            severity_match = re.search(
                rf'{severity}[^\$]*\$([\d,]+)(?:\s*[-–to]+\s*\$?([\d,]+))?',
                section_text, re.IGNORECASE
            )
            
            if severity_match:
                min_val = int(severity_match.group(1).replace(',', ''))
                max_val = int(severity_match.group(2).replace(',', '')) if severity_match.group(2) else min_val
                rewards[severity] = {'min': min_val, 'max': max_val}
    except Exception as e:
        logger.warning(f"Failed to extract rewards: {e}")
    
    if not rewards:
        rewards = {
            'critical': {'min': 1000, 'max': 10000},
            'high': {'min': 500, 'max': 5000},
            'medium': {'min': 100, 'max': 1000},
            'low': {'min': 50, 'max': 250}
        }
    
    return rewards


def extract_severity_mapping(text: str) -> dict:
    """Extract severity to vulnerability type mapping."""
    mapping = {}
    
    lines = text.split('\n')
    current_severity = None
    
    severity_keywords = {
        'critical': ['critical'],
        'high': ['high'],
        'medium': ['medium'],
        'low': ['low'],
    }
    
    vuln_types = []
    
    for line in lines:
        line_lower = line.lower().strip()
        
        for sev, keywords in severity_keywords.items():
            if any(kw in line_lower for kw in keywords):
                if vuln_types and current_severity:
                    if current_severity not in mapping:
                        mapping[current_severity] = []
                    mapping[current_severity].extend(vuln_types)
                    vuln_types = []
                current_severity = sev
                break
        
        if current_severity:
            if line.strip().startswith(('•', '-', '*', '+')) or line.strip().startswith(('Remote', 'SQL', 'IDOR', 'XSS', 'CSRF', 'SSRF', 'Service', 'Unrestricted', 'Directory', 'Self', 'Any', 'Enterprise', 'Misconfigured')):
                if len(line.strip()) > 10 and len(line.strip()) < 200:
                    clean_vuln = line.strip().lstrip('•-*+ ').strip()
                    if clean_vuln and not any(s in clean_vuln.lower() for s in ['out of scope', 'eligible', 'severity', 'attachments', 'update', 'sep ', 'nov ', 'oct ']):
                        if clean_vuln not in vuln_types:
                            vuln_types.append(clean_vuln)
    
    if vuln_types and current_severity:
        if current_severity not in mapping:
            mapping[current_severity] = []
        mapping[current_severity].extend(vuln_types)
    
    return mapping


def extract_out_of_scope(text: str) -> list[str]:
    """Extract out of scope items."""
    out_of_scope = []
    
    excluded_section = re.search(r'(?:excluded|vulnerabilit(?:y|ies)\s*out\s*of\s*scope|out\s*of\s*scope)[:\s]*\n(.*?)(?=\n\s*\n[A-Z]|$\Z|\n\n(?:NetScaler|Asset|Attachments))',
                                text, re.IGNORECASE | re.DOTALL)
    
    if excluded_section:
        section_text = excluded_section.group(1)
        
        items = re.findall(r'(?:^\s*[-•*]\s*(.+)$|^\s*([A-Z][^.!?\n]{10,100})$)', section_text, re.MULTILINE)
        
        for match in items:
            item = match[0] if match[0] else match[1]
            item = item.strip()
            if len(item) > 10 and len(item) < 200:
                if not any(x in item.lower() for x in ['attachments', 'eligible', 'update', '2024', '2025']):
                    if item not in out_of_scope:
                        out_of_scope.append(item)
    
    return out_of_scope[:15]


def extract_rules(text: str) -> list[str]:
    """Extract program rules."""
    rules = []
    
    rules_section = re.search(r'(?:general\s*terms|testing\s*instructions|rules?)[:\s]*\n(.*?)(?=\n\s*\n|\Z)',
                             text, re.IGNORECASE | re.DOTALL)
    
    if rules_section:
        section_text = rules_section.group(1)
        
        items = re.findall(r'(?:^\s*[-•*]\s*(.+)$|\b(No\s+[A-Z][^.!?\n]{10,80})\b)', section_text, re.MULTILINE)
        
        for match in items:
            rule = match[0] if match[0] else match[1]
            rule = rule.strip()
            if len(rule) > 10 and len(rule) < 150:
                if rule not in rules:
                    rules.append(rule)
    
    return rules[:20]


def extract_testing_header(text: str) -> Optional[str]:
    """Extract testing header requirement."""
    header_match = re.search(r'(?:testing\s*header|header\s*format)[:\s]*\n?\s*X-[\w-]+:\s*([^\n]+)', text, re.IGNORECASE)
    if header_match:
        return header_match.group(0).strip()
    return None


def extract_email_requirement(text: str) -> Optional[str]:
    """Extract email domain requirement."""
    email_match = re.search(r'@?([a-zA-Z0-9]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})*)\s*(?:email|address)', text, re.IGNORECASE)
    if not email_match:
        email_match = re.search(r'(?:email|use)\s+([a-zA-Z0-9]+@?[a-zA-Z0-9]+\.[a-zA-Z]{2,})', text, re.IGNORECASE)
    if email_match:
        return email_match.group(1)
    return None


def extract_response_times(text: str) -> dict:
    """Extract response time SLA."""
    response_times = {}
    
    time_patterns = [
        ('first_response', r'(?:first\s*(?:response|action))[:\s]*(\d+\s*(?:hours?|h|days?|d|week))',),
        ('triage', r'(?:average\s*time\s*to\s*triage|time\s*to\s*triage)[:\s]*(\d+\s*(?:hours?|h|days?|d|week))',),
        ('bounty', r'(?:average\s*time\s*to\s*bounty|time\s*to\s*bounty)[:\s]*(\d+\s*(?:hours?|h|days?|d|week))',),
        ('resolution', r'(?:time\s*to\s*resolution|resolution)[:\s]*(\d+\s*(?:hours?|h|days?|d|week))',),
    ]
    
    for key, pattern in time_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            response_times[key] = match.group(1)
    
    return response_times


def extract_assets(text: str) -> list[dict]:
    """Extract program assets/targets from text."""
    assets = []
    
    lines = text.split('\n')
    current_asset = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        if not line:
            continue
        
        asset_patterns = [
            r'^([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\s*$',
            r'^NetScaler\s*(AAA|ADC|Gateway)?',
            r'^([A-Z][a-zA-Z0-9]+(?:\s+[a-zA-Z0-9]+)*)\s*$',
        ]
        
        for pattern in asset_patterns:
            match = re.match(pattern, line)
            if match and len(line) < 50:
                current_asset = {
                    'name': match.group(0).strip(),
                    'type': 'Other',
                    'max_severity': None,
                    'eligible': True,
                    'vulnerabilities': []
                }
                
                if i + 1 < len(lines) and lines[i + 1].strip():
                    next_line = lines[i + 1].strip()
                    if next_line.lower() in ['critical', 'high', 'medium', 'low']:
                        current_asset['max_severity'] = next_line.lower()
                
                assets.append(current_asset)
                break
    
    severity_keywords = {
        'critical': ['critical'],
        'high': ['high'],
        'medium': ['medium'],
        'low': ['low'],
    }
    
    current_severity = None
    for line in lines:
        line_lower = line.lower().strip()
        
        for sev in severity_keywords:
            if sev in line_lower and len(line) < 20:
                current_severity = sev
                break
        
        if current_severity and current_asset:
            if line.strip().startswith(('Remote', 'SQL', 'IDOR', 'XSS', 'CSRF', 'SSRF', 'Service', 'Unrestricted', 'Directory', 'Command')):
                vuln = line.strip()
                if vuln and vuln not in [v.get('description', '') for v in current_asset.get('vulnerabilities', [])]:
                    current_asset.setdefault('vulnerabilities', []).append({
                        'severity': current_severity,
                        'description': vuln
                    })
    
    for i, asset in enumerate(assets):
        if i > 0 and not asset.get('max_severity'):
            prev = assets[i - 1]
            if prev.get('max_severity'):
                asset['max_severity'] = prev['max_severity']
                asset['vulnerabilities'] = prev.get('vulnerabilities', [])
    
    return assets[:10]


def extract_attachments(text: str) -> list[dict]:
    """Extract attachment references from program text."""
    attachments = []
    
    file_patterns = [
        r'([a-zA-Z0-9_.-]+\.pdf)\s*\(([\d.]+)\s*(MiB|KiB|B|MB|GB)\)',
        r'([a-zA-Z0-9_.-]+\.mp4)\s*\(([\d.]+)\s*(MiB|KiB|B|MB|GB)\)',
        r'([a-zA-Z0-9_.-]+\.pfx)\s*\(([\d.]+)\s*(MiB|KiB|B|MB|GB)\)',
        r'([a-zA-Z0-9_.-]+\.cer)\s*\(([\d.]+)\s*(MiB|KiB|B|MB|GB)\)',
        r'([a-zA-Z0-9_.-]+\.zip)\s*\(([\d.]+)\s*(MiB|KiB|B|MB|GB)\)',
        r'([a-zA-Z0-9_.-]+\.txt)\s*\(([\d.]+)\s*(MiB|KiB|B|MB|GB)\)',
    ]
    
    found_files = set()
    
    for pattern in file_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            filename, size, unit = match
            if filename not in found_files:
                found_files.add(filename)
                
                file_type = 'document'
                if filename.endswith('.pdf'):
                    file_type = 'document'
                elif filename.endswith('.mp4'):
                    file_type = 'video'
                elif filename.endswith('.pfx') or filename.endswith('.cer'):
                    file_type = 'certificate'
                elif filename.endswith('.zip'):
                    file_type = 'archive'
                
                attachments.append({
                    'name': filename,
                    'size': f"{size} {unit}",
                    'type': file_type,
                    'status': 'pending_upload'
                })
    
    return attachments
