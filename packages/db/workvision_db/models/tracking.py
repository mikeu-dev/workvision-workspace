"""
Vision Tracking & Identity Association Models.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from workvision_db.base import Base
from workvision_db.models.enums import IdentityStatus, IdentityStatusEnum


class TrackingSession(Base):
    __tablename__ = "tracking_sessions"
    __table_args__ = (
        Index("idx_tracking_sessions_cam_track", "camera_id", "local_track_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
    )
    local_track_id: Mapped[int] = mapped_column(Integer, nullable=False)
    global_track_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    total_frames_tracked: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default=text("1"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="ACTIVE",
        server_default=text("'ACTIVE'"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    camera: Mapped["Camera"] = relationship("Camera", back_populates="tracking_sessions")
    identity_associations: Mapped[List["IdentityAssociation"]] = relationship(
        "IdentityAssociation",
        back_populates="tracking_session",
        cascade="all, delete-orphan",
    )


class IdentityAssociation(Base):
    __tablename__ = "identity_associations"
    __table_args__ = (
        Index("idx_identity_assoc_employee", "employee_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    tracking_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tracking_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    identity_status: Mapped[IdentityStatus] = mapped_column(
        IdentityStatusEnum,
        default=IdentityStatus.UNASSIGNED,
        server_default=text("'UNASSIGNED'::identity_status_enum"),
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        server_default=text("0.0"),
        nullable=False,
    )
    association_method: Mapped[str] = mapped_column(String(50), nullable=False)
    associated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    evidence_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Relationships
    tracking_session: Mapped["TrackingSession"] = relationship(
        "TrackingSession",
        back_populates="identity_associations",
    )
    employee: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        back_populates="identity_associations",
    )
