"""
Time-Series Event Models (Partitioned Tables by Timestamp).
"""

from datetime import datetime
from typing import Any, Dict, Optional
import uuid

from sqlalchemy import (
    DateTime,
    Float,
    PrimaryKeyConstraint,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from workvision_db.base import Base
from workvision_db.models.enums import (
    BusinessState,
    BusinessStateEnum,
    ObservedActivity,
    ObservedActivityEnum,
)


class LocationEvent(Base):
    __tablename__ = "location_events"
    __table_args__ = (
        PrimaryKeyConstraint("id", "timestamp", name="pk_location_events"),
        {"postgresql_partition_by": "RANGE (timestamp)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    tracking_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    workstation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    foot_x: Mapped[float] = mapped_column(Float, nullable=False)
    foot_y: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class ActivityEvent(Base):
    __tablename__ = "activity_events"
    __table_args__ = (
        PrimaryKeyConstraint("id", "timestamp", name="pk_activity_events"),
        {"postgresql_partition_by": "RANGE (timestamp)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    tracking_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    activity: Mapped[ObservedActivity] = mapped_column(
        ObservedActivityEnum,
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        server_default=text("1.0"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class StateEvent(Base):
    __tablename__ = "state_events"
    __table_args__ = (
        PrimaryKeyConstraint("id", "timestamp", name="pk_state_events"),
        {"postgresql_partition_by": "RANGE (timestamp)"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    tracking_session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    state: Mapped[BusinessState] = mapped_column(
        BusinessStateEnum,
        nullable=False,
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        server_default=text("1.0"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )
