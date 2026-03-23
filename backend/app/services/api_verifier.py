"""Service to verify external API connectivity."""
import asyncio
import logging
from typing import Any
from dataclasses import dataclass

import httpx

from app.external_config import get_external_apis

logger = logging.getLogger(__name__)


@dataclass
class APIStatus:
    name: str
    category: str
    configured: bool
    status: str
    message: str | None = None
    response_time_ms: int | None = None
    details: dict | None = None


class APIVerifier:
    """Verify connectivity and functionality of external APIs."""

    def __init__(self):
        self.external_apis = get_external_apis()

    async def verify_all(self) -> list[APIStatus]:
        """Verify all configured external APIs."""
        tasks = [
            ("openai", self.verify_openai()),
            ("shodan", self.verify_shodan()),
            ("censys", self.verify_censys()),
            ("nvd", self.verify_nvd()),
            ("github", self.verify_github()),
            ("virustotal", self.verify_virustotal()),
            ("alienvault", self.verify_alienvault()),
            ("securitytrails", self.verify_securitytrails()),
            ("hunterio", self.verify_hunterio()),
            ("leaklookup", self.verify_leaklookup()),
            ("slack", self.verify_slack()),
        ]
        
        verified = []
        for name, task in tasks:
            try:
                result = await task
                if result:
                    verified.append(result)
            except Exception as e:
                logger.error(f"API verification error for {name}: {e}")
                verified.append(APIStatus(
                    name=name.replace("_", " ").title(),
                    category="Intelligence",
                    configured=True,
                    status="error",
                    message=str(e)
                ))
        
        return sorted(verified, key=lambda x: (x.category, x.name))

    async def verify_openai(self) -> APIStatus:
        """Verify OpenAI API connectivity."""
        api_key = self.external_apis.openai_api_key
        
        if not api_key:
            return APIStatus(
                name="OpenAI",
                category="AI",
                configured=False,
                status="not_configured",
                message="No API key configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = asyncio.get_event_loop().time()
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 5
                    }
                )
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                
                if response.status_code == 200:
                    return APIStatus(
                        name="OpenAI",
                        category="AI",
                        configured=True,
                        status="healthy",
                        response_time_ms=elapsed,
                        details={"model": "gpt-4o-mini"}
                    )
                else:
                    return APIStatus(
                        name="OpenAI",
                        category="AI",
                        configured=True,
                        status="error",
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return APIStatus(
                name="OpenAI",
                category="AI",
                configured=True,
                status="error",
                message=str(e)
            )

    async def verify_shodan(self) -> APIStatus:
        """Verify Shodan API connectivity."""
        api_key = self.external_apis.shodan_api_key
        
        if not api_key:
            return APIStatus(
                name="Shodan",
                category="Intelligence",
                configured=False,
                status="not_configured",
                message="No API key configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = asyncio.get_event_loop().time()
                response = await client.get(
                    f"https://api.shodan.io/api-info?key={api_key}"
                )
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    plan = data.get("plan", "unknown")
                    return APIStatus(
                        name="Shodan",
                        category="Intelligence",
                        configured=True,
                        status="healthy",
                        response_time_ms=elapsed,
                        details={"plan": plan}
                    )
                else:
                    return APIStatus(
                        name="Shodan",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return APIStatus(
                name="Shodan",
                category="Intelligence",
                configured=True,
                status="error",
                message=str(e)
            )

    async def verify_censys(self) -> APIStatus:
        """Verify Censys Platform API connectivity.
        
        Uses the new Censys Platform API v3 with Bearer token authentication.
        Verifies by performing a host lookup (which works on free tier).
        """
        api_id = self.external_apis.censys_api_id
        api_secret = self.external_apis.censys_api_secret
        
        # Use the full token format for Bearer auth
        token = f"censys_{api_id}_{api_secret}" if api_id and api_secret else ""
        
        if not token or not api_id:
            return APIStatus(
                name="Censys",
                category="Intelligence",
                configured=False,
                status="not_configured",
                message="API token not configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = asyncio.get_event_loop().time()
                # Use a well-known IP to verify connectivity
                response = await client.get(
                    "https://api.platform.censys.io/v3/global/asset/host/8.8.8.8",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.censys.api.v3.host.v1+json"
                    }
                )
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    ip = data.get("result", {}).get("resource", {}).get("ip", "unknown")
                    return APIStatus(
                        name="Censys",
                        category="Intelligence",
                        configured=True,
                        status="healthy",
                        response_time_ms=elapsed,
                        details={"verified_ip": ip, "api": "Platform v3"}
                    )
                elif response.status_code == 401:
                    return APIStatus(
                        name="Censys",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message="Invalid token"
                    )
                elif response.status_code == 403:
                    return APIStatus(
                        name="Censys",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message="Access denied - check permissions"
                    )
                else:
                    return APIStatus(
                        name="Censys",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return APIStatus(
                name="Censys",
                category="Intelligence",
                configured=True,
                status="error",
                message=str(e)
            )

    async def verify_nvd(self) -> APIStatus:
        """Verify NVD API connectivity."""
        api_key = self.external_apis.nvd_api_key
        
        if not api_key:
            return APIStatus(
                name="NVD",
                category="Intelligence",
                configured=False,
                status="not_configured",
                message="No API key configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = asyncio.get_event_loop().time()
                headers = {"apiKey": api_key} if api_key else {}
                response = await client.get(
                    "https://services.nvd.nist.gov/rest/json/cves/2.0",
                    headers=headers,
                    params={"resultsPerPage": 1}
                )
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    return APIStatus(
                        name="NVD",
                        category="Intelligence",
                        configured=True,
                        status="healthy",
                        response_time_ms=elapsed,
                        details={"vulnerabilities": data.get("totalResults", 0)}
                    )
                elif response.status_code == 403:
                    return APIStatus(
                        name="NVD",
                        category="Intelligence",
                        configured=True,
                        status="rate_limited",
                        response_time_ms=elapsed,
                        message="Rate limited (403). An API key helps."
                    )
                else:
                    return APIStatus(
                        name="NVD",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return APIStatus(
                name="NVD",
                category="Intelligence",
                configured=True,
                status="error",
                message=str(e)
            )

    async def verify_github(self) -> APIStatus:
        """Verify GitHub API connectivity."""
        token = self.external_apis.github_token
        
        if not token:
            return APIStatus(
                name="GitHub",
                category="Intelligence",
                configured=False,
                status="not_configured",
                message="No token configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = asyncio.get_event_loop().time()
                response = await client.get(
                    "https://api.github.com/rate_limit",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json"
                    }
                )
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    core_limit = data.get("resources", {}).get("core", {})
                    return APIStatus(
                        name="GitHub",
                        category="Intelligence",
                        configured=True,
                        status="healthy",
                        response_time_ms=elapsed,
                        details={
                            "rate_limit": core_limit.get("limit"),
                            "remaining": core_limit.get("remaining")
                        }
                    )
                elif response.status_code == 401:
                    return APIStatus(
                        name="GitHub",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message="Invalid or expired token"
                    )
                else:
                    return APIStatus(
                        name="GitHub",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return APIStatus(
                name="GitHub",
                category="Intelligence",
                configured=True,
                status="error",
                message=str(e)
            )

    async def verify_virustotal(self) -> APIStatus:
        """Verify VirusTotal API connectivity."""
        api_key = self.external_apis.virustotal_api_key
        
        if not api_key:
            return APIStatus(
                name="VirusTotal",
                category="Intelligence",
                configured=False,
                status="not_configured",
                message="No API key configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = asyncio.get_event_loop().time()
                response = await client.get(
                    "https://www.virustotal.com/api/v3/users/current",
                    headers={"x-apikey": api_key}
                )
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    return APIStatus(
                        name="VirusTotal",
                        category="Intelligence",
                        configured=True,
                        status="healthy",
                        response_time_ms=elapsed,
                        details=data.get("data", {}).get("attributes", {})
                    )
                elif response.status_code == 404:
                    return APIStatus(
                        name="VirusTotal",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message="API key not found"
                    )
                else:
                    return APIStatus(
                        name="VirusTotal",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return APIStatus(
                name="VirusTotal",
                category="Intelligence",
                configured=True,
                status="error",
                message=str(e)
            )

    async def verify_alienvault(self) -> APIStatus:
        """Verify AlienVault OTX API connectivity."""
        api_key = self.external_apis.alienvault_api_key
        
        if not api_key:
            return APIStatus(
                name="AlienVault OTX",
                category="Intelligence",
                configured=False,
                status="not_configured",
                message="No API key configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = asyncio.get_event_loop().time()
                response = await client.get(
                    "https://otx.alienvault.com/api/v1/user/me",
                    headers={"X-OTX-API-KEY": api_key}
                )
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    return APIStatus(
                        name="AlienVault OTX",
                        category="Intelligence",
                        configured=True,
                        status="healthy",
                        response_time_ms=elapsed,
                        details={
                            "username": data.get("username"),
                            "rate_limit_remaining": response.headers.get("X-OTX-RATE-LIMIT-REMAINING")
                        }
                    )
                elif response.status_code == 401:
                    return APIStatus(
                        name="AlienVault OTX",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message="Invalid API key"
                    )
                else:
                    return APIStatus(
                        name="AlienVault OTX",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return APIStatus(
                name="AlienVault OTX",
                category="Intelligence",
                configured=True,
                status="error",
                message=str(e)
            )

    async def verify_securitytrails(self) -> APIStatus:
        """Verify SecurityTrails API connectivity."""
        api_key = self.external_apis.securitytrails_api_key
        
        if not api_key:
            return APIStatus(
                name="SecurityTrails",
                category="Intelligence",
                configured=False,
                status="not_configured",
                message="No API key configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = asyncio.get_event_loop().time()
                response = await client.get(
                    "https://api.securitytrails.com/v1/ping",
                    headers={"APIKEY": api_key}
                )
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    return APIStatus(
                        name="SecurityTrails",
                        category="Intelligence",
                        configured=True,
                        status="healthy",
                        response_time_ms=elapsed,
                        details=data
                    )
                else:
                    return APIStatus(
                        name="SecurityTrails",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return APIStatus(
                name="SecurityTrails",
                category="Intelligence",
                configured=True,
                status="error",
                message=str(e)
            )

    async def verify_hunterio(self) -> APIStatus:
        """Verify Hunter.io API connectivity."""
        api_key = self.external_apis.hunterio_api_key
        
        if not api_key:
            return APIStatus(
                name="Hunter.io",
                category="Intelligence",
                configured=False,
                status="not_configured",
                message="No API key configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = asyncio.get_event_loop().time()
                response = await client.get(
                    "https://api.hunter.io/v2/account",
                    params={"api_key": api_key}
                )
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    return APIStatus(
                        name="Hunter.io",
                        category="Intelligence",
                        configured=True,
                        status="healthy",
                        response_time_ms=elapsed,
                        details={
                            "email_quota": data.get("data", {}).get("email_quota"),
                            "calls_quota": data.get("data", {}).get("calls_quota")
                        }
                    )
                else:
                    return APIStatus(
                        name="Hunter.io",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return APIStatus(
                name="Hunter.io",
                category="Intelligence",
                configured=True,
                status="error",
                message=str(e)
            )

    async def verify_leaklookup(self) -> APIStatus:
        """Verify LeakLookup API connectivity.
        
        Uses the stats endpoint to verify API key validity.
        Endpoint: https://leak-lookup.com/api/stats
        """
        api_key = self.external_apis.leaklookup_api_key
        
        if not api_key:
            return APIStatus(
                name="LeakLookup",
                category="Intelligence",
                configured=False,
                status="not_configured",
                message="No API key configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = asyncio.get_event_loop().time()
                response = await client.post(
                    "https://leak-lookup.com/api/stats",
                    data={"key": api_key}
                )
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("error") == "false":
                        stats = data.get("message", {})
                        return APIStatus(
                            name="LeakLookup",
                            category="Intelligence",
                            configured=True,
                            status="healthy",
                            response_time_ms=elapsed,
                            details={
                                "status": stats.get("status"),
                                "type": stats.get("type"),
                                "requests": stats.get("requests"),
                                "limit": stats.get("limit")
                            }
                        )
                    else:
                        return APIStatus(
                            name="LeakLookup",
                            category="Intelligence",
                            configured=True,
                            status="error",
                            message=data.get("message", "Unknown error")
                        )
                elif response.status_code == 401:
                    return APIStatus(
                        name="LeakLookup",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message="Invalid API key"
                    )
                else:
                    return APIStatus(
                        name="LeakLookup",
                        category="Intelligence",
                        configured=True,
                        status="error",
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return APIStatus(
                name="LeakLookup",
                category="Intelligence",
                configured=True,
                status="error",
                message=str(e)
            )

    async def verify_slack(self) -> APIStatus:
        """Verify Slack API connectivity."""
        bot_token = self.external_apis.slack_bot_token
        
        if not bot_token:
            return APIStatus(
                name="Slack",
                category="Notifications",
                configured=False,
                status="not_configured",
                message="No bot token configured"
            )
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                start = asyncio.get_event_loop().time()
                response = await client.get(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {bot_token}"}
                )
                elapsed = int((asyncio.get_event_loop().time() - start) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return APIStatus(
                            name="Slack",
                            category="Notifications",
                            configured=True,
                            status="healthy",
                            response_time_ms=elapsed,
                            details={
                                "team": data.get("team"),
                                "user": data.get("user")
                            }
                        )
                    else:
                        return APIStatus(
                            name="Slack",
                            category="Notifications",
                            configured=True,
                            status="error",
                            message=data.get("error", "Unknown error")
                        )
                else:
                    return APIStatus(
                        name="Slack",
                        category="Notifications",
                        configured=True,
                        status="error",
                        message=f"HTTP {response.status_code}"
                    )
        except Exception as e:
            return APIStatus(
                name="Slack",
                category="Notifications",
                configured=True,
                status="error",
                message=str(e)
            )


api_verifier = APIVerifier()
