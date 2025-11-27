"""User domain models."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, Any

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


class UserRole(str, Enum):
    """User roles for authorization."""
    admin = "admin"
    project_manager = "project_manager"
    computista = "computista"
    viewer = "viewer"


class User(SQLModel, table=True):
    """User model for authentication and authorization."""
    __tablename__ = "app_user"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = Field(default=UserRole.viewer)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(SQLModel, table=True):
    """Extended user profile with preferences and settings."""
    __tablename__ = "user_profile"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", unique=True, index=True)
    company: Optional[str] = None
    language: str = Field(default="it-IT")
    settings: Optional[dict[str, Any]] = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RefreshToken(SQLModel, table=True):
    """Refresh token for JWT authentication."""
    __tablename__ = "refresh_token"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id")
    token_fingerprint: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    revoked: bool = Field(default=False)
    replaced_by_id: Optional[int] = Field(default=None, foreign_key="refresh_token.id")


class AuditLog(SQLModel, table=True):
    """Audit log for tracking user actions."""
    __tablename__ = "audit_log"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="app_user.id")
    action: str
    method: Optional[str] = None
    endpoint: Optional[str] = None
    ip_address: Optional[str] = None
    payload_hash: Optional[str] = None
    outcome: Optional[str] = Field(
        default=None, description="success|failure in base alle risposte HTTP"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
