# CredFlow Backend - Core Models

import enum
from datetime import datetime
from uuid import UUID, uuid4
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import Column, String, Text, Integer, DECIMAL, Date, DateTime, Enum, ForeignKey, Boolean, JSON, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, INET
from sqlalchemy.orm import relationship, declared_attr

from app.models.base import BaseModel, NonTenantBaseModel, TenantMixin, TimestampMixin, SoftDeleteMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey


class TenantStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    TRIAL = "trial"


class UserRole(str, enum.Enum):
    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"


class AgentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    OFFLINE = "offline"
    UPDATING = "updating"


class SyncStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class InvoiceStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    DISPUTED = "disputed"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    RECONCILED = "reconciled"


class PaymentMode(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    CARD = "card"
    CHEQUE = "cheque"
    RAZORPAY = "razorpay"
    OTHER = "other"


class ReminderChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"


class CommunicationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"


class PaymentLinkStatus(str, enum.Enum):
    ACTIVE = "active"
    PAID = "paid"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class TaskType(str, enum.Enum):
    CALL = "call"
    EMAIL = "email"
    VISIT = "visit"
    WHATSAPP = "whatsapp"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DisputeStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class NotificationChannel(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"


class ProviderType(str, enum.Enum):
    TWILIO = "twilio"
    GUPSHUP = "gupshup"
    WATI = "wati"
    SENDGRID = "sendgrid"
    SES = "ses"
    SMTP = "smtp"
    MSG91 = "msg91"
    MOCK = "mock"


# ============================================
# TENANTS & USERS
# ============================================

class Tenant(NonTenantBaseModel):
    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    subdomain: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    status: Mapped[TenantStatus] = mapped_column(Enum(TenantStatus), default=TenantStatus.TRIAL, nullable=False)
    settings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    billing_plan: Mapped[str] = mapped_column(String(50), default="starter", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="tenant", lazy="dynamic")
    agents: Mapped[List["Agent"]] = relationship("Agent", back_populates="tenant", lazy="dynamic")
    companies: Mapped[List["TallyCompany"]] = relationship("TallyCompany", back_populates="tenant", lazy="dynamic")
    customers: Mapped[List["Customer"]] = relationship("Customer", back_populates="tenant", lazy="dynamic")


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    status: Mapped[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship("RefreshToken", back_populates="user", lazy="dynamic")
    assigned_tasks: Mapped[List["CollectionTask"]] = relationship("CollectionTask", back_populates="assignee", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_user_tenant_email"),
        Index("ix_user_tenant_status", "tenant_id", "status"),
    )


class Invitation(BaseModel):
    __tablename__ = "invitations"

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_invitation_token", "token"),
        Index("ix_invitation_tenant_email", "tenant_id", "email"),
    )


class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    user_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("ix_refresh_token_user", "user_id"),
        Index("ix_refresh_token_hash", "token_hash"),
        Index("ix_refresh_token_expires", "expires_at"),
    )


# ============================================
# TALLY INTEGRATION
# ============================================

class Agent(BaseModel):
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    status: Mapped[AgentStatus] = mapped_column(Enum(AgentStatus), default=AgentStatus.INACTIVE, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="agents")
    companies: Mapped[List["TallyCompany"]] = relationship("TallyCompany", back_populates="agent", lazy="dynamic")
    sync_logs: Mapped[List["SyncLog"]] = relationship("SyncLog", back_populates="agent", lazy="dynamic")

    __table_args__ = (
        Index("ix_agent_tenant", "tenant_id"),
        Index("ix_agent_api_key", "api_key_hash"),
        Index("ix_agent_status", "status"),
    )


class TallyCompany(BaseModel):
    __tablename__ = "tally_companies"

    agent_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    tally_guid: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    financial_year_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="companies")
    agent: Mapped["Agent"] = relationship("Agent", back_populates="companies")
    sync_logs: Mapped[List["SyncLog"]] = relationship("SyncLog", back_populates="company", lazy="dynamic")

    __table_args__ = (
        Index("ix_tally_company_tenant", "tenant_id"),
        Index("ix_tally_company_agent", "agent_id"),
        Index("ix_tally_company_guid", "tally_guid"),
    )


class SyncLog(BaseModel):
    __tablename__ = "sync_logs"

    agent_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    company_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("tally_companies.id", ondelete="SET NULL"), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)  # companies, customers, invoices, payments
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[SyncStatus] = mapped_column(Enum(SyncStatus), default=SyncStatus.PENDING, nullable=False)
    error_details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    agent: Mapped["Agent"] = relationship("Agent", back_populates="sync_logs")
    company: Mapped[Optional["TallyCompany"]] = relationship("TallyCompany", back_populates="sync_logs")

    __table_args__ = (
        Index("ix_sync_log_tenant", "tenant_id"),
        Index("ix_sync_log_agent", "agent_id"),
        Index("ix_sync_log_company", "company_id"),
        Index("ix_sync_log_started", "started_at"),
        Index("ix_sync_log_tenant_started", "tenant_id", "started_at"),
    )


# ============================================
# RECEIVABLES
# ============================================

class Customer(BaseModel):
    __tablename__ = "customers"

    tally_ledger_guid: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    address: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    credit_limit: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"), nullable=False)
    payment_terms_days: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    outstanding_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"), nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="customers")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="customer", lazy="dynamic")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="customer", lazy="dynamic")
    communications: Mapped[List["Communication"]] = relationship("Communication", back_populates="customer", lazy="dynamic")
    tasks: Mapped[List["CollectionTask"]] = relationship("CollectionTask", back_populates="customer", lazy="dynamic")
    disputes: Mapped[List["Dispute"]] = relationship("Dispute", back_populates="customer", lazy="dynamic")
    risk_scores: Mapped[List["CustomerRiskScore"]] = relationship("CustomerRiskScore", back_populates="customer", lazy="dynamic")
    payment_links: Mapped[List["PaymentLink"]] = relationship("PaymentLink", back_populates="customer", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint("tenant_id", "tally_ledger_guid", name="uq_customer_tally_guid"),
        Index("ix_customer_tenant", "tenant_id"),
        Index("ix_customer_tenant_name", "tenant_id", "name"),
        Index("ix_customer_tenant_gstin", "tenant_id", "gstin"),
        Index("ix_customer_tenant_status", "tenant_id", "status"),
        Index("ix_customer_tally_guid", "tally_ledger_guid"),
    )


class Invoice(BaseModel):
    __tablename__ = "invoices"

    customer_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    tally_voucher_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    voucher_number: Mapped[str] = mapped_column(String(100), nullable=False)
    voucher_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    due_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)  # Taxable amount
    tax_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"), nullable=False)
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    outstanding_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    status: Mapped[InvoiceStatus] = mapped_column(Enum(InvoiceStatus), default=InvoiceStatus.DRAFT, nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    place_of_supply: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tally_raw_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="invoices")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="invoice", lazy="dynamic")
    communications: Mapped[List["Communication"]] = relationship("Communication", back_populates="invoice", lazy="dynamic")
    tasks: Mapped[List["CollectionTask"]] = relationship("CollectionTask", back_populates="invoice", lazy="dynamic")
    disputes: Mapped[List["Dispute"]] = relationship("Dispute", back_populates="invoice", lazy="dynamic")
    payment_links: Mapped[List["PaymentLink"]] = relationship("PaymentLink", back_populates="invoice", lazy="dynamic")

    __table_args__ = (
        UniqueConstraint("tenant_id", "tally_voucher_id", name="uq_invoice_tally_voucher"),
        Index("ix_invoice_tenant", "tenant_id"),
        Index("ix_invoice_customer", "customer_id"),
        Index("ix_invoice_tenant_status_due", "tenant_id", "status", "due_date"),
        Index("ix_invoice_tenant_due_date", "tenant_id", "due_date"),
        Index("ix_invoice_tenant_voucher_date", "tenant_id", "voucher_date"),
        Index("ix_invoice_tally_voucher", "tally_voucher_id"),
        Index("ix_invoice_tenant_outstanding", "tenant_id", "outstanding_amount"),
    )


class Payment(BaseModel):
    __tablename__ = "payments"

    customer_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False)
    invoice_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    tally_receipt_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    payment_mode: Mapped[PaymentMode] = mapped_column(Enum(PaymentMode), default=PaymentMode.BANK_TRANSFER, nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    razorpay_link_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("payment_links.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="payments")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", back_populates="payments")
    payment_link: Mapped[Optional["PaymentLink"]] = relationship("PaymentLink", back_populates="payments")

    __table_args__ = (
        Index("ix_payment_tenant", "tenant_id"),
        Index("ix_payment_customer", "customer_id"),
        Index("ix_payment_invoice", "invoice_id"),
        Index("ix_payment_tenant_date", "tenant_id", "payment_date"),
        Index("ix_payment_razorpay", "razorpay_payment_id", unique=True, postgresql_where="razorpay_payment_id IS NOT NULL"),
    )


# ============================================
# COLLECTIONS
# ============================================

class ReminderTemplate(BaseModel):
    __tablename__ = "reminder_templates"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    channel: Mapped[ReminderChannel] = mapped_column(Enum(ReminderChannel), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    days_before_due: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    days_after_due: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    communications: Mapped[List["Communication"]] = relationship("Communication", back_populates="template", lazy="dynamic")

    __table_args__ = (
        Index("ix_reminder_template_tenant", "tenant_id"),
        Index("ix_reminder_template_tenant_channel", "tenant_id", "channel", "is_active"),
    )


class Communication(BaseModel):
    __tablename__ = "communications"

    customer_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    invoice_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    template_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("reminder_templates.id", ondelete="SET NULL"), nullable=True)
    channel: Mapped[ReminderChannel] = mapped_column(Enum(ReminderChannel), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[CommunicationStatus] = mapped_column(Enum(CommunicationStatus), default=CommunicationStatus.PENDING, nullable=False)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="communications")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", back_populates="communications")
    template: Mapped[Optional["ReminderTemplate"]] = relationship("ReminderTemplate", back_populates="communications")

    __table_args__ = (
        Index("ix_communication_tenant", "tenant_id"),
        Index("ix_communication_customer", "customer_id"),
        Index("ix_communication_invoice", "invoice_id"),
        Index("ix_communication_tenant_created", "tenant_id", "created_at"),
        Index("ix_communication_tenant_status", "tenant_id", "status"),
        # Deduplication: one reminder per (invoice, channel, date)
        UniqueConstraint("tenant_id", "invoice_id", "channel", "created_at", name="uq_communication_dedup"),
    )


class PaymentLink(BaseModel):
    __tablename__ = "payment_links"

    invoice_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[PaymentLinkStatus] = mapped_column(Enum(PaymentLinkStatus), default=PaymentLinkStatus.ACTIVE, nullable=False)
    razorpay_link_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    razorpay_link_url: Mapped[str] = mapped_column(String(500), nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="payment_links")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="payment_links")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="payment_link", lazy="dynamic")

    __table_args__ = (
        Index("ix_payment_link_tenant", "tenant_id"),
        Index("ix_payment_link_invoice", "invoice_id"),
        Index("ix_payment_link_customer", "customer_id"),
        Index("ix_payment_link_razorpay", "razorpay_link_id"),
        Index("ix_payment_link_tenant_status_expires", "tenant_id", "status", "expires_at"),
    )


class CollectionTask(BaseModel):
    __tablename__ = "collection_tasks"

    assigned_to: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    customer_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    invoice_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    type: Mapped[TaskType] = mapped_column(Enum(TaskType), nullable=False)
    priority: Mapped[TaskPriority] = mapped_column(Enum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    due_date: Mapped[datetime] = mapped_column(Date, nullable=False)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    assignee: Mapped[Optional["User"]] = relationship("User", back_populates="assigned_tasks")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="tasks")
    invoice: Mapped[Optional["Invoice"]] = relationship("Invoice", back_populates="tasks")

    __table_args__ = (
        Index("ix_task_tenant", "tenant_id"),
        Index("ix_task_assigned", "assigned_to"),
        Index("ix_task_customer", "customer_id"),
        Index("ix_task_due_date", "due_date"),
        Index("ix_task_tenant_status", "tenant_id", "status"),
    )


class Dispute(BaseModel):
    __tablename__ = "disputes"

    invoice_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus), default=DisputeStatus.OPEN, nullable=False)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="disputes")
    customer: Mapped["Customer"] = relationship("Customer", back_populates="disputes")

    __table_args__ = (
        Index("ix_dispute_tenant", "tenant_id"),
        Index("ix_dispute_invoice", "invoice_id"),
        Index("ix_dispute_customer", "customer_id"),
        Index("ix_dispute_status", "status"),
    )


# ============================================
# AUDIT & ANALYTICS
# ============================================

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[Optional[UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", lazy="joined")

    __table_args__ = (
        Index("ix_audit_log_tenant", "tenant_id"),
        Index("ix_audit_log_user", "user_id"),
        Index("ix_audit_log_entity", "entity_type", "entity_id"),
        Index("ix_audit_log_tenant_created", "tenant_id", "created_at"),
        Index("ix_audit_log_action", "action"),
    )


class NotificationProvider(BaseModel):
    __tablename__ = "notification_providers"

    channel: Mapped[NotificationChannel] = mapped_column(Enum(NotificationChannel), nullable=False)
    provider_type: Mapped[ProviderType] = mapped_column(Enum(ProviderType), nullable=False)
    config_encrypted: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (
        UniqueConstraint("tenant_id", "channel", "is_default", name="uq_provider_default", deferrable=True, initially="DEFERRED"),
        Index("ix_notification_provider_tenant", "tenant_id"),
    )


class DashboardSnapshot(BaseModel):
    __tablename__ = "dashboard_snapshots"

    period: Mapped[str] = mapped_column(String(20), nullable=False)  # daily, weekly, monthly, fy
    total_outstanding: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"), nullable=False)
    overdue_amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"), nullable=False)
    dso: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)
    collection_efficiency: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2), nullable=True)
    top_debtors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    aging_breakdown: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    cash_flow_forecast: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_dashboard_snapshot_tenant_period", "tenant_id", "period", "created_at"),
    )


class CustomerRiskScore(BaseModel):
    __tablename__ = "customer_risk_scores"

    customer_id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False)
    factors: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship("Customer", back_populates="risk_scores")

    __table_args__ = (
        UniqueConstraint("tenant_id", "customer_id", "created_at", name="uq_risk_score_tenant_customer_time"),
        Index("ix_risk_score_tenant", "tenant_id"),
        Index("ix_risk_score_customer", "customer_id"),
        Index("ix_risk_score_level", "risk_level"),
    )