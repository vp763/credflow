# CredFlow Backend - Base Models

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy.sql import func

Base = declarative_base()


class TenantMixin:
    """Mixin for tenant-scoped models."""

    @declared_attr
    def tenant_id(cls):
        return Column(
            PG_UUID(as_uuid=True),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )


class TimestampMixin:
    """Mixin for created_at/updated_at timestamps."""

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SoftDeleteMixin:
    """Mixin for soft delete support."""

    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def soft_delete(self):
        self.deleted_at = datetime.utcnow()


class BaseModel(Base, TenantMixin, TimestampMixin, SoftDeleteMixin):
    """Base model with id, tenant_id, timestamps, soft delete."""

    __abstract__ = True

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    @declared_attr
    def __table_args__(cls):
        return (
            Index(f"ix_{cls.__tablename__}_tenant_deleted", "tenant_id", "deleted_at"),
        )


class NonTenantBaseModel(Base, TimestampMixin):
    """Base model for non-tenant-scoped tables (e.g., tenants table)."""

    __abstract__ = True

    id = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )