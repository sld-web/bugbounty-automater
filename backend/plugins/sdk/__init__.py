"""Bug Bounty Plugin SDK."""
from .base_plugin import BasePlugin, run_plugin
from .credential_manager import CredentialManager

__all__ = ["BasePlugin", "run_plugin", "CredentialManager"]
