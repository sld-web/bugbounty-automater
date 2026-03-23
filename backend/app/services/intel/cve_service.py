"""CVE Intelligence Service - NVD API integration and correlation."""
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

NVD_API_V2 = "https://services.nvd.nist.gov/rest/json/cves/2.0/"


class CVEService:
    """Service for fetching and correlating CVEs with targets."""

    TECH_PATTERNS = {
        "apache": r"apache|httpd",
        "nginx": r"nginx",
        "wordpress": r"wordpress|wp-",
        "drupal": r"drupal",
        "joomla": r"joomla",
        "react": r"react\.js|reactjs",
        "vue": r"vue\.js|vuejs",
        "angular": r"angular",
        "jquery": r"jquery",
        "django": r"django",
        "flask": r"flask",
        "express": r"express\.js",
        "nodejs": r"node\.js|nodejs",
        "python": r"python",
        "php": r"php",
        "mysql": r"mysql",
        "postgresql": r"postgresql|postgres",
        "mongodb": r"mongodb|mongo",
        "redis": r"redis",
        "elasticsearch": r"elasticsearch",
        "tomcat": r"tomcat",
        "jboss": r"jboss",
        "spring": r"spring(?!boot)|springframework",
        "springboot": r"spring\s*boot",
        "rails": r"ruby\s*on\s*rails|rails",
        "laravel": r"laravel",
        "codeigniter": r"codeigniter",
        "dotnet": r"\.net\s+framework|asp\.net",
        "iis": r"iis|microsoft-iis",
        "glassfish": r"glassfish",
        "weblogic": r"weblogic",
        "jenkins": r"jenkins",
        "gitlab": r"gitlab",
        "jenkins": r"jenkins",
        "docker": r"docker|container",
        "kubernetes": r"kubernetes|k8s",
        "aws": r"amazon\s*aws|aws",
        "azure": r"azure|microsoft\s*azure",
        "gcp": r"google\s*cloud|gcp",
        "openssh": r"openssh",
        "samba": r"samba",
        "proftpd": r"proftpd",
        "vsftpd": r"vsftpd",
        "bind": r"bind\s*(?:named)?",
        "sendmail": r"sendmail",
        "exim": r"exim",
        "postfix": r"postfix",
        "openvpn": r"openvpn",
        "ipsec": r"ipsec",
        "ssl": r"openssl|ssl|tls",
        "struts": r"apache\s*struts|struts",
        "log4j": r"log4j|log4shell",
        "shellshock": r"shellshock|bashdoor",
        "heartbleed": r"heartbleed",
    }

    CWE_MAPPINGS = {
        "sql_injection": ["CWE-89", "CWE-564", "CWE-65"],
        "xss": ["CWE-79", "CWE-80", "CWE-81", "CWE-83"],
        "rce": ["CWE-78", "CWE-94", "CWE-95"],
        "lfi": ["CWE-22", "CWE-23", "CWE-24", "CWE-25"],
        "rfi": ["CWE-98", "CWE-346"],
        "csrf": ["CWE-352"],
        "idor": ["CWE-639"],
        "ssrf": ["CWE-918"],
        "xxe": ["CWE-611", "CWE-827"],
        "ssti": ["CWE-1336"],
        "deserialization": ["CWE-502", "CWE-915"],
        "path_traversal": ["CWE-22", "CWE-23", "CWE-36"],
        "auth_bypass": ["CWE-287", "CWE-306", "CWE-862"],
        "buffer_overflow": ["CWE-119", "CWE-120", "CWE-121", "CWE-125"],
        "default_credentials": ["CWE-798", "CWE-259", "CWE-321"],
        "misconfiguration": ["CWE-16", "CWE-655", "CWE-1004"],
        "information_disclosure": ["CWE-200", "CWE-209", "CWE-532"],
        "csrf_token": ["CWE-352"],
        "clickjacking": ["CWE-693"],
        "open_redirect": ["CWE-601"],
        "command_injection": ["CWE-77", "CWE-78", "CWE-88"],
    }

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._client: Optional[httpx.AsyncClient] = None
        self._cache: dict[str, dict] = {}
        self._cache_ttl = 3600

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {"Accept": "application/json"}
            if self.api_key:
                headers["apiKey"] = self.api_key
            self._client = httpx.AsyncClient(
                base_url=NVD_API_V2,
                headers=headers,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()

    async def fetch_cves_for_product(
        self,
        product: str,
        vendor: Optional[str] = None,
        days_back: int = 30,
        limit: int = 50,
    ) -> list[dict]:
        """Fetch CVEs for a specific product."""
        cache_key = f"{vendor}:{product}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if datetime.utcnow().timestamp() - cached.get("fetched_at", 0) < self._cache_ttl:
                return cached.get("cves", [])

        params = {
            "keywordSearch": product,
            "resultsPerPage": min(limit, 100),
        }

        if vendor:
            params["keywordSearch"] = f"{vendor} {product}"

        try:
            response = await self.client.get("", params=params)
            response.raise_for_status()
            data = response.json()

            from datetime import timezone
            cutoff = datetime.now(timezone.utc) - timedelta(days=days_back)

            cves = []
            for item in data.get("vulnerabilities", []):
                cve = item.get("cve", {})
                cve_data = self._parse_cve(cve)
                if cve_data:
                    published_str = cve_data.get("published", "")
                    if published_str and days_back > 0:
                        try:
                            published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                            if published >= cutoff:
                                cves.append(cve_data)
                        except:
                            cves.append(cve_data)
                    else:
                        cves.append(cve_data)

            self._cache[cache_key] = {
                "cves": cves,
                "fetched_at": datetime.utcnow().timestamp(),
            }

            return cves

        except httpx.HTTPStatusError as e:
            logger.error(f"NVD API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching CVEs: {e}")
            return []

    def _parse_cve(self, cve: dict) -> Optional[dict]:
        """Parse CVE data from NVD response."""
        try:
            cve_id = cve.get("id", "")
            if not cve_id.startswith("CVE-"):
                return None

            descriptions = cve.get("descriptions", [])
            description = ""
            for desc in descriptions:
                if desc.get("lang") == "en":
                    description = desc.get("value", "")
                    break

            metrics = cve.get("metrics", {})
            cvss_v31 = metrics.get("cvssMetricV31", [])
            cvss_v30 = metrics.get("cvssMetricV30", [])
            cvss_v2 = metrics.get("cvssMetricV2", [])

            cvss_score = 0.0
            cvss_vector = ""
            cvss_severity = "UNKNOWN"

            if cvss_v31:
                cvss_data = cvss_v31[0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore", 0)
                cvss_vector = cvss_data.get("vectorString", "")
                cvss_severity = cvss_v31[0].get("baseSeverity", "UNKNOWN")
            elif cvss_v30:
                cvss_data = cvss_v30[0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore", 0)
                cvss_vector = cvss_data.get("vectorString", "")
                cvss_severity = cvss_v30[0].get("baseSeverity", "UNKNOWN")
            elif cvss_v2:
                cvss_data = cvss_v2[0].get("cvssData", {})
                cvss_score = cvss_data.get("baseScore", 0)
                cvss_vector = cvss_data.get("vectorString", "")
                if cvss_score >= 7.0:
                    cvss_severity = "HIGH"
                elif cvss_score >= 4.0:
                    cvss_severity = "MEDIUM"
                else:
                    cvss_severity = "LOW"

            configurations = cve.get("configurations", [])
            affected_products = []
            for config in configurations:
                for node in config.get("nodes", []):
                    for match in node.get("cpeMatch", []):
                        if match.get("vulnerable"):
                            cpe = match.get("criteria", "")
                            affected_products.append(cpe)

            references = cve.get("references", [])
            ref_urls = [ref.get("url", "") for ref in references[:5]]

            return {
                "cve_id": cve_id,
                "description": description,
                "cvss_score": cvss_score,
                "cvss_vector": cvss_vector,
                "cvss_severity": cvss_severity,
                "affected_products": affected_products,
                "references": ref_urls,
                "published": cve.get("published", ""),
                "last_modified": cve.get("lastModified", ""),
            }

        except Exception as e:
            logger.error(f"Error parsing CVE: {e}")
            return None

    def detect_technologies(self, content: str) -> list[str]:
        """Detect technologies from content (banner, HTML, etc)."""
        technologies = []
        content_lower = content.lower()

        for tech, pattern in self.TECH_PATTERNS.items():
            if re.search(pattern, content_lower, re.IGNORECASE):
                if tech not in technologies:
                    technologies.append(tech)

        return technologies

    def extract_versions(self, content: str) -> dict[str, str]:
        """Extract version numbers from content."""
        versions = {}

        version_patterns = {
            "apache": r"Apache[/\s]+([\d.]+)",
            "nginx": r"nginx/([\d.]+)",
            "openssl": r"OpenSSL[/\s]+([\d.]+[a-z]?)",
            "php": r"PHP/([\d.]+)",
            "python": r"Python[/\s]+([\d.]+)",
            "nodejs": r"Node\.js[/\s]+v?([\d.]+)",
            "wordpress": r"WordPress[/\s]+([\d.]+)",
        }

        for product, pattern in version_patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                versions[product] = match.group(1)

        return versions

    def correlate_cves_to_target(
        self,
        target: dict,
        cves: list[dict],
    ) -> list[dict]:
        """Correlate CVEs to a target based on detected technologies."""
        if not cves:
            return []

        target_url = target.get("url", "")
        technologies = target.get("technologies", [])
        versions = target.get("versions", {})

        matched_cves = []

        for cve in cves:
            cve_id = cve.get("cve_id", "")
            affected = cve.get("affected_products", [])
            description = cve.get("description", "").lower()

            is_match = False
            match_reason = ""

            for tech in technologies:
                tech_lower = tech.lower()

                if any(tech_lower in prod.lower() for prod in affected):
                    is_match = True
                    match_reason = f"Technology match: {tech}"
                    break

                if tech_lower in description:
                    is_match = True
                    match_reason = f"Description mentions: {tech}"
                    break

            if versions:
                for product, version in versions.items():
                    product_lower = product.lower()
                    if any(product_lower in prod.lower() for prod in affected):
                        if version and self._version_in_cve_range(version, affected):
                            is_match = True
                            match_reason = f"Version {version} matches affected range"
                            break

            if is_match:
                cve_with_context = cve.copy()
                cve_with_context["match_reason"] = match_reason
                cve_with_context["target_id"] = target.get("id", "")
                cve_with_context["attack_suggestions"] = self._generate_attack_suggestions(cve)
                matched_cves.append(cve_with_context)

        return matched_cves

    def _version_in_cve_range(self, version: str, affected_products: list[str]) -> bool:
        """Check if version falls within CVE affected range."""
        for prod in affected_products:
            if "versions" in str(prod):
                return True
        return False

    def _generate_attack_suggestions(self, cve: dict) -> list[str]:
        """Generate attack suggestions based on CVE details."""
        suggestions = []
        cve_id = cve.get("cve_id", "")
        description = cve.get("description", "").lower()
        cvss_score = cve.get("cvss_score", 0)

        if cvss_score >= 9.0:
            suggestions.append(f"CRITICAL: {cve_id} requires immediate testing")
            suggestions.append(f"Verify exploitability of {cve_id}")

        if "remote code execution" in description or "rce" in description:
            suggestions.append("Test for command injection vectors")
            suggestions.append("Check for eval() or system() calls in user input")
        elif "sql injection" in description:
            suggestions.append("Test all input fields for SQL injection")
            suggestions.append("Check for UNION, Boolean, Time-based blind injection")
        elif "cross-site scripting" in description or "xss" in description:
            suggestions.append("Test reflected, stored, and DOM XSS")
            suggestions.append("Check for proper input sanitization")
        elif "path traversal" in description:
            suggestions.append("Test for directory traversal payloads")
            suggestions.append("Check file inclusion vulnerabilities")
        elif "authentication" in description or "bypass" in description:
            suggestions.append("Test authentication mechanisms")
            suggestions.append("Check for session management issues")
        elif "information disclosure" in description:
            suggestions.append("Check for verbose error messages")
            suggestions.append("Test for directory listing")
        elif "denial of service" in description or "dos" in description:
            suggestions.append("Test resource exhaustion vectors")
            suggestions.append("Check for algorithmic complexity issues")

        suggestions.append(f"Review references: {cve.get('references', [''])[0] if cve.get('references') else 'N/A'}")

        return suggestions[:5]

    def get_cwe_from_description(self, description: str) -> list[str]:
        """Extract CWE IDs from CVE description."""
        cwe_ids = []
        description_lower = description.lower()

        for vuln_type, cwes in self.CWE_MAPPINGS.items():
            if vuln_type.replace("_", " ") in description_lower:
                cwe_ids.extend(cwes)

        cwe_match = re.findall(r"CWE-(\d+)", description, re.IGNORECASE)
        for match in cwe_match:
            cwe_id = f"CWE-{match}"
            if cwe_id not in cwe_ids:
                cwe_ids.append(cwe_id)

        return list(set(cwe_ids))

    def calculate_risk_score(
        self,
        cvss_score: float,
        cvss_vector: str,
        data_sensitivity: str = "medium",
        asset_tier: int = 2,
    ) -> float:
        """Calculate adjusted risk score based on CVSS and context."""
        base_score = cvss_score

        tier_multipliers = {1: 1.5, 2: 1.2, 3: 1.0}
        tier_mult = tier_multipliers.get(asset_tier, 1.0)

        sensitivity_multipliers = {
            "critical": 1.3,
            "high": 1.2,
            "medium": 1.0,
            "low": 0.8,
        }
        sensitivity_mult = sensitivity_multipliers.get(data_sensitivity, 1.0)

        if "AV:N" in cvss_vector or "P/A:N" in cvss_vector:
            base_score *= 1.1

        if "C:H" in cvss_vector or "I:H" in cvss_vector or "A:H" in cvss_vector:
            base_score *= 1.15

        adjusted_score = min(base_score * tier_mult * sensitivity_mult, 10.0)
        return round(adjusted_score, 1)

    async def fetch_recent_cves(self, days: int = 7, limit: int = 100) -> list[dict]:
        """Fetch recent high-severity CVEs from NVD."""
        from datetime import timezone
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        search_terms = [
            "remote code execution vulnerability",
            "sql injection vulnerability",
            "cross-site scripting vulnerability",
            "authentication bypass vulnerability",
        ]

        all_cves = []

        try:
            for term in search_terms:
                params = {
                    "keywordSearch": term,
                    "resultsPerPage": min(limit, 100),
                }

                response = await self.client.get("", params=params)
                response.raise_for_status()
                data = response.json()

                for item in data.get("vulnerabilities", []):
                    cve = item.get("cve", {})
                    cve_data = self._parse_cve(cve)
                    if cve_data and cve_data.get("cvss_score", 0) >= 7.0:
                        published_str = cve_data.get("published", "")
                        if published_str:
                            try:
                                published = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                                if published >= cutoff_date:
                                    all_cves.append(cve_data)
                            except:
                                pass

            seen = set()
            unique_cves = []
            for cve in all_cves:
                if cve["cve_id"] not in seen:
                    seen.add(cve["cve_id"])
                    unique_cves.append(cve)

            return sorted(unique_cves, key=lambda x: x.get("cvss_score", 0), reverse=True)[:limit]

        except Exception as e:
            logger.error(f"Error fetching recent CVEs: {e}")
            return []


class TechStackDetector:
    """Detect technology stack from reconnaissance data."""

    BANNER_PATTERNS = {
        r"Apache[/\s]+([\d.]+)": "apache",
        r"nginx/([\d.]+)": "nginx",
        r"Microsoft-IIS[/\s]+([\d.]+)": "iis",
        r"Server:\s*([^\r\n]+)": "generic_server",
        r"X-Powered-By:\s*([^\r\n]+)": "powered_by",
        r"Set-Cookie:\s*(?:PHPSESSID|JSESSIONID|SESSION)": "session_cookie",
        r"X-Generator:\s*(WordPress[^\s]*)": "wordpress",
        r"<html[^>]+class=\"[^\"]*(?:drupal|joomla)[^\"]*\"": "cms",
    }

    HEADER_PATTERNS = {
        "server": "server",
        "x-powered-by": "powered_by",
        "x-generator": "generator",
        "strict-transport-security": "hsts",
        "content-security-policy": "csp",
    }

    def detect_from_response(self, response_text: str, headers: dict) -> dict:
        """Detect technologies from HTTP response."""
        technologies = []
        versions = {}

        combined = response_text + "\n" + str(headers)

        for pattern, tech in self.BANNER_PATTERNS.items():
            match = re.search(pattern, combined, re.IGNORECASE)
            if match:
                tech_name = tech
                version = match.group(1) if match.lastindex else None

                if tech_name not in technologies:
                    technologies.append(tech_name)
                    if version:
                        versions[tech_name] = version

        for header_key, header_value in headers.items():
            header_lower = header_key.lower()
            if header_lower in self.HEADER_PATTERNS:
                value = str(header_value)
                tech = self.HEADER_PATTERNS[header_lower]

                version_match = re.search(r"([\d.]+)", value)
                if tech not in technologies:
                    technologies.append(tech)
                    if version_match:
                        versions[tech] = version_match.group(1)

        js_patterns = {
            r"jquery[.-]([\d.]+)": "jquery",
            r"react[@.-]?([\d.]+)": "react",
            r"vue[@.-]?([\d.]+)": "vue",
            r"angular[@.-]?([\d.]+)": "angular",
            r"bootstrap[@.-]?([\d.]+)": "bootstrap",
            r"webpack[@.-]?([\d.]+)": "webpack",
        }

        for pattern, tech in js_patterns.items():
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                if tech not in technologies:
                    technologies.append(tech)
                    versions[tech] = match.group(1)

        return {
            "technologies": technologies,
            "versions": versions,
            "headers": list(headers.keys()),
        }
