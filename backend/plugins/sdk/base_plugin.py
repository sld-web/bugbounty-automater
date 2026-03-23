"""Base plugin class for Bug Bounty Automator plugins."""
from abc import ABC, abstractmethod
from typing import Any, Optional
import argparse
import json
import logging
import os
import sys

from .credential_manager import CredentialManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """Base class for all plugins.
    
    Plugins should:
    1. Inherit from this class
    2. Implement the `run` method
    3. Define their input/output schemas
    
    Example:
        class MyPlugin(BasePlugin):
            def get_name(self) -> str:
                return "my-plugin"
            
            def get_version(self) -> str:
                return "1.0.0"
            
            def get_inputs(self) -> dict:
                return {
                    "target": {"type": "string", "required": True}
                }
            
            def get_outputs(self) -> dict:
                return {
                    "results": {"type": "array"}
                }
            
            def run(self, target: str, params: dict) -> dict:
                # Plugin logic here
                return {"results": []}
    """

    def __init__(self):
        self._cred_manager: Optional[CredentialManager] = None
        self._target = ""
        self._params = {}

    @property
    def credential_manager(self) -> CredentialManager:
        """Lazy-load the credential manager."""
        if self._cred_manager is None:
            server_address = os.environ.get(
                "CREDENTIAL_SERVER",
                "host.docker.internal:50051"
            )
            self._cred_manager = CredentialManager(server_address=server_address)
        return self._cred_manager

    @abstractmethod
    def get_name(self) -> str:
        """Return the plugin name."""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Return the plugin version."""
        pass

    @abstractmethod
    def get_inputs(self) -> dict:
        """Return input schema definition."""
        pass

    @abstractmethod
    def get_outputs(self) -> dict:
        """Return output schema definition."""
        pass

    @abstractmethod
    def run(self, target: str, params: dict) -> dict:
        """Execute the plugin logic.
        
        Args:
            target: The target (domain, IP, URL, etc.)
            params: Additional parameters
            
        Returns:
            dict with results matching the output schema
        """
        pass

    def get_credential(
        self,
        credential_id: str,
        target_id: str = "",
        purpose: str = "",
    ) -> Optional[dict]:
        """Get a credential from the vault.
        
        Args:
            credential_id: The credential ID
            target_id: Optional target ID for audit
            purpose: Optional purpose description
            
        Returns:
            Credential dict or None
        """
        return self.credential_manager.get_credential(
            credential_id=credential_id,
            target_id=target_id,
            purpose=purpose,
        )

    def parse_args(self) -> tuple[str, dict]:
        """Parse command line arguments.
        
        Returns:
            Tuple of (target, params)
        """
        parser = argparse.ArgumentParser(description=self.get_name())
        parser.add_argument("--target", required=True, help="Target to scan")
        parser.add_argument(
            "--params",
            default="{}",
            help="JSON-encoded parameters"
        )
        parser.add_argument(
            "--credentials",
            default="[]",
            help="JSON-encoded list of credential IDs"
        )
        
        args = parser.parse_args()
        
        params = json.loads(args.params)
        params["_target"] = args.target
        params["_credentials"] = json.loads(args.credentials)
        
        return args.target, params

    def execute(self) -> dict:
        """Execute the plugin with CLI arguments.
        
        Returns:
            Result dict to output as JSON
        """
        try:
            target, params = self.parse_args()
            logger.info(f"Running {self.get_name()} v{self.get_version()} on {target}")
            
            result = self.run(target, params)
            
            logger.info(f"Completed {self.get_name()}: {result}")
            return result
            
        except Exception as e:
            logger.exception(f"Error in {self.get_name()}: {e}")
            return {
                "error": str(e),
                "plugin": self.get_name(),
                "version": self.get_version(),
            }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.get_name()} version={self.get_version()}>"


def run_plugin(plugin_class: type[BasePlugin]) -> None:
    """Run a plugin class.
    
    Usage:
        if __name__ == "__main__":
            run_plugin(MyPlugin)
    """
    plugin = plugin_class()
    result = plugin.execute()
    print(json.dumps(result, indent=2))
    sys.exit(0)
