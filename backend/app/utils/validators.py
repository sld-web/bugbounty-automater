"""Domain and URL validators."""
import re
from urllib.parse import urlparse


def is_valid_domain(domain: str) -> bool:
    """Check if a string is a valid domain."""
    pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, domain))


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def is_ip_address(value: str) -> bool:
    """Check if a string is an IP address."""
    pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    return bool(re.match(pattern, value))


def normalize_url(url: str) -> str:
    """Normalize a URL."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"


def extract_domain(url_or_domain: str) -> str | None:
    """Extract domain from URL or domain string."""
    if is_ip_address(url_or_domain):
        return url_or_domain

    if not url_or_domain.startswith(("http://", "https://")):
        url_or_domain = f"https://{url_or_domain}"

    try:
        parsed = urlparse(url_or_domain)
        return parsed.netloc
    except Exception:
        return None


def is_private_ip(ip: str) -> bool:
    """Check if an IP is in private range."""
    private_ranges = [
        r"^10\.",
        r"^172\.(1[6-9]|2[0-9]|3[0-1])\.",
        r"^192\.168\.",
        r"^127\.",
        r"^localhost$",
        r"^::1$",
        r"^fe80:",
        r"^fc00:",
    ]

    for pattern in private_ranges:
        if re.match(pattern, ip):
            return True

    return False


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe filesystem usage."""
    return re.sub(r"[^\w\-_\. ]", "_", filename)
