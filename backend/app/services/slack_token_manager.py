"""Slack token management with automatic refresh."""
import json
import logging
import time
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

import httpx

from app.external_config import get_external_apis

logger = logging.getLogger(__name__)


@dataclass
class SlackTokens:
    access_token: str
    refresh_token: str
    expires_at: float
    client_id: str = ""
    client_secret: str = ""


class SlackTokenManager:
    """Manages Slack OAuth tokens with automatic refresh.
    
    Slack OAuth tokens expire and need to be refreshed using the refresh_token.
    This manager handles automatic refresh when tokens are about to expire.
    """
    
    TOKEN_FILE = Path(__file__).parent.parent / "slack_tokens.json"
    REFRESH_THRESHOLD = 3600  # Refresh if less than 1 hour remaining
    
    def __init__(self):
        self.external_apis = get_external_apis()
        self._tokens: Optional[SlackTokens] = None
        self._load_tokens()
    
    def _load_tokens(self):
        """Load tokens from file or config."""
        if self.TOKEN_FILE.exists():
            try:
                with open(self.TOKEN_FILE) as f:
                    data = json.load(f)
                    self._tokens = SlackTokens(
                        access_token=data.get("access_token", ""),
                        refresh_token=data.get("refresh_token", ""),
                        expires_at=data.get("expires_at", 0),
                        client_id=data.get("client_id", ""),
                        client_secret=data.get("client_secret", ""),
                    )
                    logger.info("Loaded Slack tokens from file")
                    return
            except Exception as e:
                logger.warning(f"Failed to load tokens from file: {e}")
        
        # Fall back to config
        self._tokens = SlackTokens(
            access_token=self.external_apis.slack_bot_token,
            refresh_token=self.external_apis._config.get("notifications", {}).get("slack", {}).get("refresh_token", ""),
            expires_at=0,  # Unknown, assume valid
        )
    
    def _save_tokens(self):
        """Save tokens to file."""
        if self._tokens:
            try:
                with open(self.TOKEN_FILE, "w") as f:
                    json.dump({
                        "access_token": self._tokens.access_token,
                        "refresh_token": self._tokens.refresh_token,
                        "expires_at": self._tokens.expires_at,
                        "client_id": self._tokens.client_id,
                        "client_secret": self._tokens.client_secret,
                    }, f)
                logger.info("Saved Slack tokens to file")
            except Exception as e:
                logger.error(f"Failed to save tokens: {e}")
    
    async def refresh_tokens(self) -> bool:
        """Refresh the Slack access token using the refresh token.
        
        Returns True if refresh was successful.
        """
        if not self._tokens or not self._tokens.refresh_token:
            logger.warning("No refresh token available")
            return False
        
        client_id = self._tokens.client_id
        client_secret = self._tokens.client_secret
        
        # If we don't have client_id/secret, try to get them from Slack config
        if not client_id or not client_secret:
            # These are typically part of your Slack app config
            # For now, we'll try without them
            pass
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # OAuth token refresh endpoint
                response = await client.post(
                    "https://slack.com/api/oauth.v2.access",
                    data={
                        "client_id": client_id or "",
                        "client_secret": client_secret or "",
                        "grant_type": "refresh_token",
                        "refresh_token": self._tokens.refresh_token,
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        self._tokens.access_token = data.get("access_token", "")
                        self._tokens.refresh_token = data.get("refresh_token", self._tokens.refresh_token)
                        self._tokens.expires_at = time.time() + data.get("expires_in", 0)
                        
                        # Save to file
                        self._save_tokens()
                        
                        # Also update the api_keys.json
                        self._update_config()
                        
                        logger.info("Successfully refreshed Slack tokens")
                        return True
                    else:
                        logger.error(f"Slack token refresh failed: {data.get('error')}")
                        return False
                else:
                    logger.error(f"Slack token refresh HTTP error: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Slack token refresh exception: {e}")
            return False
    
    def _update_config(self):
        """Update the api_keys.json with new tokens."""
        try:
            config_path = Path(__file__).parent.parent / "api_keys.json"
            with open(config_path) as f:
                config = json.load(f)
            
            config["notifications"]["slack"]["bot_token"] = self._tokens.access_token
            config["notifications"]["slack"]["refresh_token"] = self._tokens.refresh_token
            
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)
            
            logger.info("Updated api_keys.json with new tokens")
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
    
    async def ensure_valid_token(self) -> Optional[str]:
        """Get a valid access token, refreshing if necessary.
        
        Returns the access token if available and valid, None otherwise.
        """
        if not self._tokens:
            return None
        
        # Check if token needs refresh
        time_remaining = self._tokens.expires_at - time.time()
        
        if time_remaining < self.REFRESH_THRESHOLD:
            logger.info(f"Token expires in {time_remaining}s, refreshing...")
            success = await self.refresh_tokens()
            if not success:
                return self._tokens.access_token  # Return current token anyway
        
        return self._tokens.access_token
    
    @property
    def current_token(self) -> str:
        """Get the current access token (may be expired)."""
        return self._tokens.access_token if self._tokens else ""
    
    async def verify_token(self) -> tuple[bool, str]:
        """Verify the current token is valid.
        
        Returns (is_valid, message).
        """
        token = await self.ensure_valid_token()
        
        if not token:
            return False, "No token available"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://slack.com/api/auth.test",
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        return True, "Token valid"
                    else:
                        error = data.get("error", "Unknown error")
                        if error == "token_expired":
                            # Try to refresh
                            success = await self.refresh_tokens()
                            if success:
                                return True, "Token refreshed"
                            return False, "Token expired, refresh failed"
                        return False, error
                else:
                    return False, f"HTTP {response.status_code}"
        except Exception as e:
            return False, str(e)


# Singleton instance
slack_token_manager = SlackTokenManager()
