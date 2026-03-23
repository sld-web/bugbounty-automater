"""Credential Manager for plugins with lazy loading and caching."""
from datetime import datetime, timedelta
from typing import Optional
import logging

try:
    import grpc
    from protos import credential_pb2
    from protos import credential_pb2_grpc
    GRPC_AVAILABLE = True
except ImportError:
    GRPC_AVAILABLE = False

logger = logging.getLogger(__name__)


class CredentialManager:
    """Manages credential fetching with lazy loading and caching.
    
    Usage:
        creds = CredentialManager()
        cred = creds.get_credential(credential_id="abc-123")
        if cred:
            print(f"Username: {cred.username}")
            print(f"Password: {cred.password}")
    """

    def __init__(
        self,
        server_address: str = "host.docker.internal:50051",
        ttl: int = 300,
        cache_dir: str = "/tmp/credentials",
    ):
        """Initialize the credential manager.
        
        Args:
            server_address: Address of the gRPC credential server
            ttl: Time-to-live for cached credentials in seconds
            cache_dir: Directory for encrypted credential cache
        """
        self._cache: dict[str, dict] = {}
        self._ttl = ttl
        self._cache_dir = cache_dir
        self._channel = None
        self._stub = None
        self._server_address = server_address
        
        self._use_mock = not GRPC_AVAILABLE

    def _ensure_connection(self) -> bool:
        """Ensure gRPC connection is established."""
        if self._use_mock:
            return False
            
        if self._stub is not None:
            return True
            
        try:
            self._channel = grpc.insecure_channel(
                self._server_address,
                options=[
                    ('grpc.max_send_message_length', 50 * 1024 * 1024),
                    ('grpc.max_receive_message_length', 50 * 1024 * 1024),
                ]
            )
            self._stub = credential_pb2_grpc.CredentialServiceStub(self._channel)
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to credential server: {e}")
            self._stub = None
            return False

    def _is_cache_valid(self, credential_id: str) -> bool:
        """Check if cached credential is still valid."""
        if credential_id not in self._cache:
            return False
        
        cached = self._cache[credential_id]
        if datetime.utcnow().timestamp() > cached.get("expires_at", 0):
            del self._cache[credential_id]
            return False
        
        return True

    def get_credential(
        self,
        credential_id: str,
        target_id: str = "",
        purpose: str = "",
    ) -> Optional[dict]:
        """Get a credential by ID with caching.
        
        Args:
            credential_id: The credential ID to fetch
            target_id: Optional target ID for audit logging
            purpose: Optional purpose description
            
        Returns:
            Credential dict with keys: id, type, username, password, 
            api_key, token, or None if not found/valid
        """
        if self._is_cache_valid(credential_id):
            return self._cache[credential_id]["credential"]

        if not self._ensure_connection():
            logger.warning("gRPC not available, returning None")
            return None

        try:
            request = credential_pb2.GetCredentialRequest(
                credential_id=credential_id,
                target_id=target_id,
                purpose=purpose,
            )
            
            response = self._stub.GetCredential(
                request,
                timeout=10,
            )
            
            if not response.success:
                logger.warning(f"Failed to get credential {credential_id}: {response.error}")
                return None

            cred_dict = {
                "id": response.credential.id,
                "type": response.credential.type,
                "username": response.credential.username,
                "password": response.credential.password,
                "api_key": response.credential.api_key,
                "token": response.credential.token,
            }
            
            self._cache[credential_id] = {
                "credential": cred_dict,
                "expires_at": response.expires_at,
            }
            
            logger.debug(f"Fetched credential {credential_id} from server")
            return cred_dict

        except grpc.RpcError as e:
            logger.error(f"gRPC error getting credential {credential_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting credential {credential_id}: {e}")
            return None

    def invalidate(self, credential_id: str) -> bool:
        """Invalidate a cached credential.
        
        Args:
            credential_id: The credential ID to invalidate
            
        Returns:
            True if successful, False otherwise
        """
        if credential_id in self._cache:
            del self._cache[credential_id]

        if not self._ensure_connection():
            return True

        try:
            request = credential_pb2.RefreshCredentialRequest(
                credential_id=credential_id,
            )
            self._stub.RefreshCredential(request, timeout=5)
            return True
        except Exception as e:
            logger.warning(f"Failed to invalidate credential: {e}")
            return False

    def health_check(self) -> bool:
        """Check if the credential server is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        if not self._ensure_connection():
            return False

        try:
            request = credential_pb2.HealthCheckRequest()
            response = self._stub.HealthCheck(request, timeout=5)
            return response.healthy
        except Exception:
            return False

    def clear_cache(self) -> None:
        """Clear all cached credentials."""
        self._cache.clear()
