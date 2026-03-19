"""OpenAI service for program ingestion."""
import json
import logging
from typing import Any

from openai import AsyncOpenAI

from app.external_config import get_external_apis

logger = logging.getLogger(__name__)


class OpenAIService:
    """Service for AI-powered program ingestion."""

    def __init__(self):
        external_apis = get_external_apis()
        self.client = AsyncOpenAI(api_key=external_apis.openai_api_key)
        self.model = "gpt-4o"

    async def extract_program_config(
        self,
        raw_policy: str,
    ) -> dict[str, Any]:
        """Extract structured configuration from raw program policy."""
        system_prompt = """You are a bug bounty program configuration extractor. 
Extract the key information from the provided bug bounty program policy and output a JSON object with this structure:

{
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
        "critical": "amount or range",
        "high": "amount or range",
        "medium": "amount or range",
        "low": "amount or range"
    },
    "campaigns": [
        {"Name": "campaign name", "multiplier": 1.0, "end_date": "YYYY-MM-DD"}
    ],
    "special_requirements": {
        "use_test_accounts": true/false,
        "custom_headers": {},
        "rce_proof_commands": []
    }
}

Be thorough and extract all relevant information. Use null for missing fields."""

        try:
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

        except Exception as e:
            logger.error(f"OpenAI extraction failed: {e}")
            return {}

    async def enhance_finding(
        self,
        finding: dict,
        program_context: dict,
    ) -> dict:
        """Enhance a finding with AI-generated insights."""
        system_prompt = """You are a security researcher analyzing a bug bounty finding.
Given the finding details and program context, provide:
1. A more detailed description
2. Potential impact analysis
3. Suggested remediation steps
4. Related CVEs or references if applicable

Return a JSON object with these fields: enhanced_description, impact, remediation, related_cves"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Finding: {json.dumps(finding)}\n\nProgram: {json.dumps(program_context)}",
                    },
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content:
                return json.loads(content)
            return finding

        except Exception as e:
            logger.error(f"OpenAI enhancement failed: {e}")
            return finding

    async def generate_test_hypothesis(
        self,
        target_info: dict,
        patterns: list[dict],
    ) -> list[dict]:
        """Generate test hypotheses based on patterns detected."""
        system_prompt = """You are a creative security researcher.
Given the target information and detected patterns/anomalies, generate specific test hypotheses
that could lead to vulnerability discovery. For each hypothesis, provide:
1. Hypothesis description
2. Attack technique
3. Expected severity if proven
4. Suggested verification steps

Return a JSON array of hypotheses."""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Target: {json.dumps(target_info)}\n\nPatterns: {json.dumps(patterns)}",
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

        except Exception as e:
            logger.error(f"OpenAI hypothesis generation failed: {e}")
            return []

    async def calculate_confidence(
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

        confidence = 0.5
        if has_scope:
            confidence += 0.3
        if has_severity:
            confidence += 0.2

        return min(confidence, 1.0)
