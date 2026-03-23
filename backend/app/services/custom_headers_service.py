"""Custom headers injection service for authenticated testing."""
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CustomHeader:
    """Represents a custom HTTP header."""
    name: str
    value: str
    source: str = "credential"


class CustomHeadersService:
    """Service for managing and injecting custom headers into requests."""

    _instance: Optional["CustomHeadersService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._headers: dict[str, CustomHeader] = {}
        self._initialized = True

    def add_header(self, name: str, value: str, source: str = "credential") -> None:
        """Add a custom header."""
        header = CustomHeader(name=name, value=value, source=source)
        self._headers[name.lower()] = header
        logger.debug(f"Added custom header: {name}")

    def remove_header(self, name: str) -> bool:
        """Remove a custom header."""
        key = name.lower()
        if key in self._headers:
            del self._headers[key]
            logger.debug(f"Removed custom header: {name}")
            return True
        return False

    def get_header(self, name: str) -> Optional[str]:
        """Get a specific header value."""
        return self._headers.get(name.lower())

    def get_all_headers(self) -> dict[str, str]:
        """Get all custom headers as a dictionary."""
        return {h.name: h.value for h in self._headers.values()}

    def get_headers_by_source(self, source: str) -> dict[str, str]:
        """Get headers filtered by source."""
        return {
            h.name: h.value 
            for h in self._headers.values() 
            if h.source == source
        }

    def clear_headers(self, source: Optional[str] = None) -> int:
        """Clear headers, optionally filtered by source."""
        if source is None:
            count = len(self._headers)
            self._headers.clear()
        else:
            to_remove = [
                key for key, h in self._headers.items() 
                if h.source == source
            ]
            count = len(to_remove)
            for key in to_remove:
                del self._headers[key]
        return count

    def apply_headers_from_policy(self, headers_config: dict[str, str], source: str = "policy") -> None:
        """Apply headers from a policy configuration."""
        for name, value_template in headers_config.items():
            resolved_value = self._resolve_template(value_template)
            self.add_header(name, resolved_value, source)

    def _resolve_template(self, template: str) -> str:
        """Resolve template variables in header values."""
        return template

    def inject_authentication_headers(
        self,
        credential_type: str,
        credential_data: dict,
        program_config: Optional[dict] = None
    ) -> dict[str, str]:
        """Generate authentication headers from credential data and program config."""
        headers = {}

        if credential_type == "user_pass":
            if program_config and "custom_headers" in program_config:
                for header_name, header_template in program_config["custom_headers"].items():
                    resolved = self._resolve_header_template(
                        header_template, 
                        credential_data
                    )
                    headers[header_name] = resolved

        elif credential_type == "session_token":
            token = credential_data.get("token", "")
            headers["Authorization"] = f"Bearer {token}"

        elif credential_type == "api_key":
            api_key = credential_data.get("api_key", "")
            key_header = program_config.get("api_key_header", "X-API-Key") if program_config else "X-API-Key"
            headers[key_header] = api_key

        return headers

    def _resolve_header_template(self, template: str, context: dict) -> str:
        """Resolve template variables like {username} in header values."""
        result = template
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        return result

    def get_injection_config(self) -> dict:
        """Get configuration for header injection."""
        return {
            "available_headers": list(self._headers.keys()),
            "total_count": len(self._headers),
            "by_source": {
                source: len(self.get_headers_by_source(source))
                for source in set(h.source for h in self._headers.values())
            }
        }


def get_headers_service() -> CustomHeadersService:
    """Get the singleton headers service instance."""
    return CustomHeadersService()
