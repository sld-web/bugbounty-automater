"""gRPC Credential Server for secure credential delivery to plugins."""
from concurrent import futures
import logging
from datetime import datetime
from typing import Optional

import grpc
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.credential import Credential

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "protos"))
from credential_pb2 import (
    GetCredentialRequest,
    GetCredentialResponse,
    Credential as ProtoCredential,
    ValidateCredentialRequest,
    ValidateCredentialResponse,
    RefreshCredentialRequest,
    RefreshCredentialResponse,
    HealthCheckRequest,
    HealthCheckResponse,
)
import credential_pb2
import credential_pb2_grpc
from credential_pb2_grpc import CredentialServiceServicer

logger = logging.getLogger(__name__)


class CredentialServicer(credential_pb2_grpc.CredentialServiceServicer):
    """gRPC service for delivering credentials to plugins."""

    def __init__(self):
        self._cache: dict[str, dict] = {}
        self._cache_ttl = 300  # 5 minutes

    def _is_cache_valid(self, credential_id: str) -> bool:
        """Check if cached credential is still valid."""
        if credential_id not in self._cache:
            return False
        cached = self._cache[credential_id]
        if datetime.utcnow().timestamp() > cached.get("expires_at", 0):
            del self._cache[credential_id]
            return False
        return True

    def _cache_credential(self, credential_id: str, credential: dict) -> None:
        """Cache credential with expiration."""
        expires_at = datetime.utcnow().timestamp() + self._cache_ttl
        self._cache[credential_id] = {
            "credential": credential,
            "expires_at": expires_at,
        }

    def _invalidate_cache(self, credential_id: str) -> None:
        """Invalidate cached credential."""
        if credential_id in self._cache:
            del self._cache[credential_id]

    async def _get_credential_from_db(self, credential_id: str) -> Optional[Credential]:
        """Fetch credential from database."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Credential).where(Credential.id == credential_id)
            )
            return result.scalar_one_or_none()

    async def _update_usage(self, credential_id: str) -> None:
        """Update usage statistics."""
        async with async_session_maker() as session:
            result = await session.execute(
                select(Credential).where(Credential.id == credential_id)
            )
            credential = result.scalar_one_or_none()
            if credential:
                credential.last_used_at = datetime.utcnow()
                credential.use_count += 1
                await session.commit()

    async def GetCredential(self, request, context):
        """Get a credential by ID."""
        credential_id = request.credential_id

        if self._is_cache_valid(credential_id):
            cached = self._cache[credential_id]
            return credential_pb2.GetCredentialResponse(
                success=True,
                credential=cached["credential"],
                expires_at=int(cached["expires_at"]),
            )

        credential = await self._get_credential_from_db(credential_id)

        if not credential:
            return credential_pb2.GetCredentialResponse(
                success=False,
                error="Credential not found",
            )

        if not credential.is_active:
            return credential_pb2.GetCredentialResponse(
                success=False,
                error="Credential is inactive",
            )

        if credential.is_expired:
            return credential_pb2.GetCredentialResponse(
                success=False,
                error="Credential has expired",
            )

        await self._update_usage(credential_id)

        cred_dict = credential_pb2.Credential(
            id=credential.id,
            type=credential.credential_type.value,
            username=credential.username or "",
            password=credential.password or "",
            api_key=credential.api_key or "",
            token=credential.token or "",
        )

        expires_at = int(datetime.utcnow().timestamp() + self._cache_ttl)
        self._cache_credential(credential_id, cred_dict)

        logger.info(f"Delivered credential {credential_id} to plugin")

        return credential_pb2.GetCredentialResponse(
            success=True,
            credential=cred_dict,
            expires_at=expires_at,
        )

    async def ValidateCredential(self, request, context):
        """Validate if a credential exists and is valid."""
        credential_id = request.credential_id

        credential = await self._get_credential_from_db(credential_id)

        if not credential:
            return credential_pb2.ValidateCredentialResponse(
                valid=False,
                error="Credential not found",
            )

        if not credential.is_active:
            return credential_pb2.ValidateCredentialResponse(
                valid=False,
                error="Credential is inactive",
            )

        expires_at = int(credential.expires_at.timestamp()) if credential.expires_at else 0

        return credential_pb2.ValidateCredentialResponse(
            valid=True,
            expires_at=expires_at,
        )

    async def RefreshCredential(self, request, context):
        """Refresh/invalidate cached credential."""
        credential_id = request.credential_id

        self._invalidate_cache(credential_id)

        credential = await self._get_credential_from_db(credential_id)

        if not credential:
            return credential_pb2.RefreshCredentialResponse(
                success=False,
                error="Credential not found",
            )

        new_expires_at = int(datetime.utcnow().timestamp() + self._cache_ttl)

        return credential_pb2.RefreshCredentialResponse(
            success=True,
            new_expires_at=new_expires_at,
        )

    async def HealthCheck(self, request, context):
        """Health check endpoint."""
        return credential_pb2.HealthCheckResponse(
            healthy=True,
            version="1.0.0",
        )


def create_server(port: int = 50051) -> grpc.aio.Server:
    """Create and configure gRPC server."""
    server = grpc.aio.server(
        futures.ThreadPoolExecutor(max_workers=10),
        options=[
            ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ('grpc.max_receive_message_length', 50 * 1024 * 1024),
        ]
    )
    
    credential_pb2_grpc.add_CredentialServiceServicer_to_server(
        CredentialServicer(),
        server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    
    return server


async def serve(port: int = 50051) -> None:
    """Start the gRPC server."""
    server = create_server(port)
    await server.start()
    logger.info(f"Credential gRPC server started on port {port}")
    
    try:
        await server.wait_for_termination()
    except KeyboardInterrupt:
        await server.stop(5)
