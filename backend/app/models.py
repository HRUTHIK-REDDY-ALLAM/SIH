from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base, now_utc


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))  # msme | financier
    msme_id: Mapped[int | None] = mapped_column(ForeignKey("msmes.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)

    msme: Mapped["Msme | None"] = relationship()


class Token(Base):
    __tablename__ = "tokens"

    token: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)


class Msme(Base):
    __tablename__ = "msmes"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    short_name: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100), default="")
    gstin: Mapped[str] = mapped_column(String(15), unique=True)
    iec: Mapped[str] = mapped_column(String(20), default="")
    sector: Mapped[str] = mapped_column(String(100), default="")
    bank_account: Mapped[str] = mapped_column(String(100), default="")
    kyc_status: Mapped[str] = mapped_column(String(20), default="pending")  # verified | pending
    onboarding_status: Mapped[str] = mapped_column(String(20), default="active")


class Buyer(Base):
    __tablename__ = "buyers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    uen: Mapped[str] = mapped_column(String(20), unique=True)
    country: Mapped[str] = mapped_column(String(50), default="Singapore")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(primary_key=True)
    msme_id: Mapped[int] = mapped_column(ForeignKey("msmes.id"))
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"))
    code: Mapped[str] = mapped_column(String(30), unique=True)
    irn: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    amount: Mapped[int] = mapped_column(Integer)  # INR, whole rupees
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    issued_on: Mapped[date] = mapped_column(Date)
    due_on: Mapped[date] = mapped_column(Date)
    goods: Mapped[str] = mapped_column(String(255), default="")
    hsn: Mapped[str] = mapped_column(String(10), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    # pending | financed | repaid | declined

    buyer: Mapped[Buyer] = relationship()
    msme: Mapped[Msme] = relationship()


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[int] = mapped_column(primary_key=True)
    msme_id: Mapped[int] = mapped_column(ForeignKey("msmes.id"), index=True)
    ctype: Mapped[str] = mapped_column(String(10))  # gst | aa
    consent_ref: Mapped[str] = mapped_column(String(30))
    scope: Mapped[str] = mapped_column(Text, default="")
    granted_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | revoked


class FinancingRegistryEntry(Base):
    """Central receivables lien registry — the duplicate-financing moat.

    One row = one active claim on a receivable (by IRN). This table is REAL:
    the fraud node queries it, and accepting a deal writes to it.
    """

    __tablename__ = "financing_registry"

    id: Mapped[int] = mapped_column(primary_key=True)
    irn: Mapped[str] = mapped_column(String(80), index=True)
    lender: Mapped[str] = mapped_column(String(255))
    financed_on: Mapped[date] = mapped_column(Date)
    ref: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | released


class TradeHistory(Base):
    """Past settled shipments — buyer payment behaviour is computed from these rows."""

    __tablename__ = "trade_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    msme_id: Mapped[int] = mapped_column(ForeignKey("msmes.id"), index=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("buyers.id"), index=True)
    invoice_code: Mapped[str] = mapped_column(String(30))
    amount: Mapped[int] = mapped_column(Integer)
    due_on: Mapped[date] = mapped_column(Date)
    paid_on: Mapped[date] = mapped_column(Date)


class FinancingDeal(Base):
    __tablename__ = "financing_deals"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    msme_id: Mapped[int] = mapped_column(ForeignKey("msmes.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="running", index=True)
    # running | approved | conditional | manual_review | declined | financed | repaid | error
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    band: Mapped[str | None] = mapped_column(String(30), nullable=True)
    advance_pct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    advance_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fee_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    net_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    decision: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    features: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    override_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    financed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    repaid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    invoice: Mapped[Invoice] = relationship()
    msme: Mapped[Msme] = relationship()


class AuditEvent(Base):
    """Every pipeline step, trace line and decision — the explainability record."""

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    deal_id: Mapped[int] = mapped_column(ForeignKey("financing_deals.id"), index=True)
    seq: Mapped[int] = mapped_column(Integer)
    node: Mapped[str | None] = mapped_column(String(40), nullable=True)
    event: Mapped[str] = mapped_column(String(20))
    # node_start | line | node_complete | decision | override | settlement | sys
    status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    kind: Mapped[str | None] = mapped_column(String(10), nullable=True)  # req/res/calc/ok/warn/flag/sys
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_utc)
