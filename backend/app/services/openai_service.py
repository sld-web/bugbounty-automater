"""OpenAI service for AI-powered features with caching and retry."""
import asyncio
import hashlib
import json
import logging
from typing import Any, Optional

from openai import AsyncOpenAI
from openai import RateLimitError, APIError, Timeout as OpenAITimeout

from app.external_config import get_external_apis
from app.services.cache import openai_cache

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for AI-powered operations with caching and retry."""

    def __init__(self, max_retries: int = 3, timeout: int = 60):
        external_apis = get_external_apis()
        api_key = external_apis.openai_api_key
        
        if not api_key:
            logger.warning("OpenAI API key not configured")
            self.client = None
            self.enabled = False
        else:
            self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
            self.enabled = True
        
        self.model = "gpt-4o"
        self.max_retries = max_retries

    @property
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return self.enabled and self.client is not None

    async def _retry_with_backoff(
        self,
        func,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with exponential backoff retry."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except RateLimitError as e:
                last_error = e
                wait_time = min(2 ** attempt, 30)
                logger.warning(f"Rate limit hit, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(wait_time)
            except OpenAITimeout as e:
                last_error = e
                wait_time = min(2 ** attempt, 30)
                logger.warning(f"OpenAI timeout, retrying in {wait_time}s (attempt {attempt + 1}/{self.max_retries})")
                await asyncio.sleep(wait_time)
            except APIError as e:
                last_error = e
                wait_time = min(2 ** attempt, 30)
                logger.warning(f"OpenAI API error: {e}, retrying in {wait_time}s")
                await asyncio.sleep(wait_time)
            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error: {e}")
                break
        
        logger.error(f"OpenAI request failed after {self.max_retries} attempts: {last_error}")
        return None

    async def extract_program_config(
        self,
        raw_policy: str,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Extract structured configuration from raw program policy."""
        if not self.is_available:
            logger.warning("OpenAI not available, skipping extraction")
            return {}

        cache_key = self._hash_input(raw_policy)
        if use_cache:
            cached = openai_cache.get_cached_program(cache_key)
            if cached:
                logger.info("Using cached program config")
                return cached

        system_prompt = """You are a bug bounty program configuration extractor. 
Extract the key information from the provided bug bounty program policy and output a JSON object with this structure:

{
    "name": "Program Name (if found)",
    "scope_domains": ["list of in-scope domains (use * for wildcards)"],
    "scope_excluded": ["list of excluded domains"],
    "scope_mobile_apps": [{"platform": "ios/android", "id": "app_id_or_bundle"}],
    "scope_repositories": ["list of in-scope GitHub repositories"],
    "priority_areas": ["list of vulnerability types to focus on"],
    "out_of_scope": ["list of out-of-scope vulnerability types"],
    "severity_mapping": {
        "critical": ["vulnerability types"],
        "high": ["vulnerability types"],
        "medium": ["vulnerability types"],
        "low": ["vulnerability types"]
    },
    "reward_tiers": {
        "critical": {"min": 0, "max": 0, "currency": "USD"},
        "high": {"min": 0, "max": 0, "currency": "USD"},
        "medium": {"min": 0, "max": 0, "currency": "USD"},
        "low": {"min": 0, "max": 0, "currency": "USD"}
    },
    "auth_level": "L0|L1|L2|L3|L4",
    "campaigns": [{"name": "campaign name", "multiplier": 1.0, "end_date": "YYYY-MM-DD"}],
    "special_requirements": {
        "use_test_accounts": true/false,
        "custom_headers": {},
        "testing_note": "any special testing instructions"
    }
}

Be thorough and extract all relevant information. Use null for missing fields. Return ONLY valid JSON."""

        async def _call_api():
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": raw_policy},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            return {}

        result = await self._retry_with_backoff(_call_api)
        
        if result and use_cache:
            openai_cache.cache_program(cache_key, result)
        
        return result or {}

    async def enhance_finding(
        self,
        finding: dict,
        program_context: dict,
        use_cache: bool = True,
    ) -> dict:
        """Enhance a finding with AI-generated insights."""
        if not self.is_available:
            return finding

        finding_hash = self._hash_finding(finding)
        if use_cache:
            cached = openai_cache.get_cached_finding(finding_hash)
            if cached:
                logger.info("Using cached finding enhancement")
                return cached

        system_prompt = """You are a security researcher analyzing a bug bounty finding.
Given the finding details and program context, provide:
1. A more detailed description (2-3 sentences)
2. Potential impact analysis (1-2 sentences)
3. Suggested remediation steps (3-5 bullet points)
4. Related CVEs or references if applicable (optional)

Return a JSON object with these fields: enhanced_description, impact, remediation (array), related_cves (array), severity_notes"""

        async def _call_api():
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Finding: {json.dumps(finding, indent=2)}\n\nProgram: {json.dumps(program_context, indent=2)}",
                    },
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            return finding

        result = await self._retry_with_backoff(_call_api)
        
        if result and use_cache:
            openai_cache.cache_finding(finding_hash, result)
        
        return result or finding

    async def generate_test_hypothesis(
        self,
        target_info: dict,
        patterns: list[dict],
        use_cache: bool = True,
    ) -> list[dict]:
        """Generate test hypotheses based on patterns detected."""
        if not self.is_available:
            return []

        cache_key = self._hash_input(json.dumps({"target": target_info, "patterns": patterns}))
        if use_cache:
            cached = openai_cache.get(f"hypothesis:{cache_key}")
            if cached:
                logger.info("Using cached test hypotheses")
                return cached

        system_prompt = """You are a creative security researcher.
Given the target information and detected patterns/anomalies, generate specific test hypotheses
that could lead to vulnerability discovery. For each hypothesis, provide:
1. Hypothesis description (clear, actionable)
2. Attack technique (specific method)
3. Expected severity if proven (critical/high/medium/low)
4. Suggested verification steps (3-5 steps)

Return a JSON object with this structure:
{
    "hypotheses": [
        {
            "description": "test this specific behavior",
            "technique": "the attack method",
            "severity": "expected severity",
            "steps": ["step 1", "step 2", "step 3"]
        }
    ]
}

Generate 3-5 hypotheses per endpoint. Focus on most likely vulnerabilities."""

        async def _call_api():
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Target: {json.dumps(target_info, indent=2)}\n\nPatterns: {json.dumps(patterns, indent=2)}",
                    },
                ],
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content:
                result = json.loads(content)
                return result.get("hypotheses", [])
            return []

        hypotheses = await self._retry_with_backoff(_call_api)
        
        if hypotheses and use_cache:
            openai_cache.set(f"hypothesis:{cache_key}", hypotheses, ttl=86400)
        
        return hypotheses or []

    async def generate_report_summary(
        self,
        findings: list[dict],
        program_name: str = "Bug Bounty Program",
        use_cache: bool = True,
    ) -> str:
        """Generate executive summary for findings."""
        if not self.is_available:
            return self._generate_basic_summary(findings)

        cache_key = self._hash_findings(findings)
        if use_cache:
            cached = openai_cache.get_cached_summary(cache_key)
            if cached:
                logger.info("Using cached report summary")
                return cached

        findings_text = json.dumps(findings, indent=2)

        system_prompt = f"""You are a security analyst preparing an executive summary for {program_name}.
Given the list of security findings, generate a professional executive summary that includes:

1. **Overview**: Brief summary of the assessment scope and key findings
2. **Critical Findings**: List of critical/high severity issues (if any)
3. **Risk Assessment**: Overall risk level and business impact
4. **Key Recommendations**: Top 3-5 actionable recommendations
5. **Conclusion**: Summary statement

Keep it professional, concise (300-500 words), and business-focused.
Target audience: Security team and management."""

        async def _call_api():
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Findings:\n{findings_text}"},
                ],
                temperature=0.3,
            )
            content = response.choices[0].message.content
            return content if content else self._generate_basic_summary(findings)

        summary = await self._retry_with_backoff(_call_api)
        
        if summary and use_cache:
            openai_cache.cache_summary(cache_key, summary)
        
        return summary or self._generate_basic_summary(findings)

    async def extract_from_pdf(
        self,
        pdf_text: str,
        filename: str = "document",
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Extract structured data from PDF text using AI."""
        if not self.is_available:
            logger.warning("OpenAI not available, returning empty extraction")
            return {}

        cache_key = self._hash_input(f"pdf:{filename}:{pdf_text[:500]}")
        if use_cache:
            cached = openai_cache.get(f"pdf_extract:{cache_key}")
            if cached:
                logger.info("Using cached PDF extraction")
                return cached

        system_prompt = """You are a bug bounty security researcher analyzing program attachments.
Extract and return ONLY valid JSON with this exact structure:

{
    "credentials": [
        {"type": "username|email|password|api_key|token|secret", "value": "the credential", "context": "where found"}
    ],
    "certificates": [
        {"format": "PEM|DER|PKCS12", "subject": "CN=...", "purpose": "what it's for"}
    ],
    "ip_addresses": ["list of IP addresses found"],
    "domains": ["list of domains/hostnames found"],
    "endpoints": ["list of URLs/endpoints found"],
    "notes": ["any important notes about testing or credentials"],
    "test_accounts": [
        {"username": "...", "password": "...", "purpose": "..."}
    ]
}

Focus on extracting:
- Login credentials (username/password pairs)
- API keys and tokens
- Certificate details
- Test account information
- Target endpoints and IPs
- Any special testing notes

Return ONLY valid JSON, no markdown or explanation."""

        async def _call_api():
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Extract data from this document ({filename}):\n\n{pdf_text[:15000]}",
                    },
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            return {}

        result = await self._retry_with_backoff(_call_api)
        
        if result and use_cache:
            openai_cache.set(f"pdf_extract:{cache_key}", result, ttl=86400 * 7)
        
        return result or {}

    async def classify_vulnerability(
        self,
        description: str,
        use_cache: bool = True,
    ) -> dict:
        """Classify vulnerability type and severity."""
        if not self.is_available:
            return {"type": "unknown", "severity": "unknown", "confidence": 0}

        cache_key = self._hash_input(description)
        if use_cache:
            cached = openai_cache.get(f"classify:{cache_key}")
            if cached:
                return cached

        system_prompt = """Classify this security finding based on the description.
Return a JSON object with:
- type: vulnerability type (sql_injection, xss, idor, ssrf, rce, open_redirect, etc.)
- severity: suggested severity (critical/high/medium/low/informational)
- confidence: confidence level 0-1
- cwe_id: CWE ID if known (e.g., "CWE-89" for SQL injection)
- cvss_vector: suggested CVSS vector string if applicable"""

        async def _call_api():
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": description},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            return {"type": "unknown", "severity": "unknown", "confidence": 0}

        result = await self._retry_with_backoff(_call_api)
        
        if result and use_cache:
            openai_cache.set(f"classify:{cache_key}", result, ttl=86400 * 7)
        
        return result or {"type": "unknown", "severity": "unknown", "confidence": 0}

    def calculate_confidence(
        self,
        extracted_config: dict,
        raw_policy: str,
    ) -> float:
        """Calculate confidence score for extracted configuration."""
        if not extracted_config:
            return 0.0

        scope_domains = extracted_config.get("scope_domains", [])
        has_scope = len(scope_domains) > 0

        severity_mapping = extracted_config.get("severity_mapping", {})
        has_severity = len(severity_mapping) > 0

        reward_tiers = extracted_config.get("reward_tiers", {})
        has_rewards = len(reward_tiers) > 0

        confidence = 0.4
        if has_scope:
            confidence += 0.25
        if has_severity:
            confidence += 0.20
        if has_rewards:
            confidence += 0.15

        policy_length = len(raw_policy)
        if policy_length > 5000:
            confidence += 0.1
        elif policy_length < 500:
            confidence -= 0.1

        return min(max(confidence, 0.0), 1.0)

    def _hash_input(self, text: str) -> str:
        """Generate hash for caching."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def _hash_finding(self, finding: dict) -> str:
        """Generate hash for finding caching."""
        content = f"{finding.get('title', '')}:{finding.get('description', '')}:{finding.get('vuln_type', '')}"
        return self._hash_input(content)

    def _hash_findings(self, findings: list[dict]) -> str:
        """Generate hash for findings list caching."""
        content = json.dumps([f.get('id', f.get('title', '')) for f in findings], sort_keys=True)
        return self._hash_input(content)

    def _generate_basic_summary(self, findings: list[dict]) -> str:
        """Generate basic summary without AI."""
        if not findings:
            return "No findings to report."

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
        for f in findings:
            sev = f.get("severity", "unknown").lower()
            if sev in severity_counts:
                severity_counts[sev] += 1

        summary = f"Assessment Summary\n"
        summary += f"Total Findings: {len(findings)}\n\n"
        summary += f"Severity Breakdown:\n"
        for sev, count in severity_counts.items():
            if count > 0:
                summary += f"  - {sev.title()}: {count}\n"

        return summary

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return openai_cache.get_stats()


openai_service = OpenAIService()
