"""Credential API endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.credential import Credential
from app.schemas.credential import (
    CredentialCreate,
    CredentialResponse,
    CredentialUpdate,
    CredentialListResponse,
)

router = APIRouter(prefix="/credentials", tags=["credentials"])

SessionDep = Annotated[AsyncSession, Depends(get_db)]


@router.get("", response_model=CredentialListResponse)
async def list_credentials(session: SessionDep):
    result = await session.execute(select(Credential).order_by(Credential.created_at.desc()))
    credentials = result.scalars().all()
    return CredentialListResponse(
        items=[CredentialResponse.model_validate(c) for c in credentials],
        total=len(credentials),
        page=1,
        page_size=100,
    )


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(credential_id: str, session: SessionDep):
    result = await session.execute(select(Credential).where(Credential.id == credential_id))
    credential = result.scalar_one_or_none()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    return credential


@router.post("", response_model=CredentialResponse, status_code=status.HTTP_201_CREATED)
async def create_credential(credential_data: CredentialCreate, session: SessionDep):
    credential = Credential(
        name=credential_data.name,
        credential_type=credential_data.credential_type,
        username=credential_data.username,
        password=credential_data.password,
        api_key=credential_data.api_key,
        token=credential_data.token,
        expires_at=credential_data.expires_at,
        is_active=credential_data.is_active,
        program_id=credential_data.program_id,
    )
    session.add(credential)
    await session.commit()
    await session.refresh(credential)
    return credential


@router.patch("/{credential_id}", response_model=CredentialResponse)
async def update_credential(credential_id: str, credential_data: CredentialUpdate, session: SessionDep):
    result = await session.execute(select(Credential).where(Credential.id == credential_id))
    credential = result.scalar_one_or_none()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    update_data = credential_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(credential, key, value)
    
    await session.commit()
    await session.refresh(credential)
    return credential


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(credential_id: str, session: SessionDep):
    result = await session.execute(select(Credential).where(Credential.id == credential_id))
    credential = result.scalar_one_or_none()
    if not credential:
        raise HTTPException(status_code=404, detail="Credential not found")
    
    await session.delete(credential)
    await session.commit()
