"""External API configuration loader from api_keys.json."""
import json
from pathlib import Path
from functools import lru_cache


class ExternalAPIsConfig:
    """Configuration for external API services."""

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = Path(__file__).parent / "api_keys.json"
        
        self._config = self._load_config(config_path)

    def _load_config(self, config_path: str | Path) -> dict:
        """Load configuration from JSON file."""
        config_path = Path(config_path)
        
        if not config_path.exists():
            return self._get_empty_config()
        
        try:
            with open(config_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return self._get_empty_config()

    def _get_empty_config(self) -> dict:
        """Return empty config structure."""
        return {
            "openai": {"api_key": ""},
            "intelligence": {
                "shodan": {"api_key": ""},
                "censys": {"api_id": "", "api_secret": ""},
                "nvd": {"api_key": ""},
                "github": {"token": ""},
                "virustotal": {"api_key": ""},
                "alienvault": {"api_key": ""},
                "securitytrails": {"api_key": ""},
                "hunterio": {"api_key": ""},
                "leaklookup": {"api_key": ""},
            },
            "bug_bounty_platforms": {
                "hackerone": {"api_token": "", "api_url": "", "username": ""},
            },
            "notifications": {
                "slack": {"bot_token": "", "channel": "", "webhook_url": ""},
                "email": {"smtp_host": "", "smtp_port": 587, "smtp_user": "", "smtp_password": "", "from_address": ""},
            },
        }

    @property
    def openai_api_key(self) -> str:
        return self._config.get("openai", {}).get("api_key", "")

    @property
    def shodan_api_key(self) -> str:
        return self._config.get("intelligence", {}).get("shodan", {}).get("api_key", "")

    @property
    def censys_api_id(self) -> str:
        return self._config.get("intelligence", {}).get("censys", {}).get("api_id", "")

    @property
    def censys_api_secret(self) -> str:
        return self._config.get("intelligence", {}).get("censys", {}).get("api_secret", "")

    @property
    def nvd_api_key(self) -> str:
        return self._config.get("intelligence", {}).get("nvd", {}).get("api_key", "")

    @property
    def github_token(self) -> str:
        return self._config.get("intelligence", {}).get("github", {}).get("token", "")

    @property
    def virustotal_api_key(self) -> str:
        return self._config.get("intelligence", {}).get("virustotal", {}).get("api_key", "")

    @property
    def alienvault_api_key(self) -> str:
        return self._config.get("intelligence", {}).get("alienvault", {}).get("api_key", "")

    @property
    def securitytrails_api_key(self) -> str:
        return self._config.get("intelligence", {}).get("securitytrails", {}).get("api_key", "")

    @property
    def hunterio_api_key(self) -> str:
        return self._config.get("intelligence", {}).get("hunterio", {}).get("api_key", "")

    @property
    def leaklookup_api_key(self) -> str:
        return self._config.get("intelligence", {}).get("leaklookup", {}).get("api_key", "")

    @property
    def hackerone_api_token(self) -> str:
        return self._config.get("bug_bounty_platforms", {}).get("hackerone", {}).get("api_token", "")

    @property
    def hackerone_api_url(self) -> str:
        return self._config.get("bug_bounty_platforms", {}).get("hackerone", {}).get("api_url", "https://api.hackerone.com/v1")

    @property
    def hackerone_username(self) -> str:
        return self._config.get("bug_bounty_platforms", {}).get("hackerone", {}).get("username", "")

    @property
    def slack_bot_token(self) -> str:
        return self._config.get("notifications", {}).get("slack", {}).get("bot_token", "")

    @property
    def slack_channel(self) -> str:
        return self._config.get("notifications", {}).get("slack", {}).get("channel", "#bugbounty-approvals")

    @property
    def slack_webhook_url(self) -> str:
        return self._config.get("notifications", {}).get("slack", {}).get("webhook_url", "")

    @property
    def smtp_host(self) -> str:
        return self._config.get("notifications", {}).get("email", {}).get("smtp_host", "smtp.gmail.com")

    @property
    def smtp_port(self) -> int:
        return self._config.get("notifications", {}).get("email", {}).get("smtp_port", 587)

    @property
    def smtp_user(self) -> str:
        return self._config.get("notifications", {}).get("email", {}).get("smtp_user", "")

    @property
    def smtp_password(self) -> str:
        return self._config.get("notifications", {}).get("email", {}).get("smtp_password", "")

    @property
    def email_from(self) -> str:
        return self._config.get("notifications", {}).get("email", {}).get("from_address", "noreply@bugbounty.local")


@lru_cache
def get_external_apis() -> ExternalAPIsConfig:
    """Get cached external APIs configuration."""
    return ExternalAPIsConfig()
