"""
Business Layer Models: Attendance, Work Sessions, Summaries, Overrides.
"""

from datetime import date, datetime
from typing import List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    Computed,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from workvision_db.base import Base
from workvision_db.models.enums import (
    AttendanceType,
    AttendanceTypeEnum,
    BusinessState,
    BusinessStateEnum,
)


class AttendanceEvent(Base):
    __tablename__ = "attendance_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    attendance_type: Mapped[AttendanceType] = mapped_column(
        AttendanceTypeEnum,
        nullable=False,
    )
    source_terminal: Mapped[str] = mapped_column(
        String(100),
        default="FACE_TERMINAL_MAIN",
        server_default=text("'FACE_TERMINAL_MAIN'"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", back_populates="attendance_events")


class WorkSession(Base):
    __tablename__ = "work_sessions"
    __table_args__ = (
        Index("idx_work_sessions_emp_time", "employee_id", "start_time", "end_time"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    state: Mapped[BusinessState] = mapped_column(
        BusinessStateEnum,
        nullable=False,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    end_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duration_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        Computed("EXTRACT(EPOCH FROM (end_time - start_time))::INT", persisted=True),
        nullable=True,
    )
    dominant_zone_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("zones.id", ondelete="SET NULL"),
        nullable=True,
    )
    confidence_score: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        server_default=text("1.0"),
        nullable=False,
    )
    is_overridden: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", back_populates="work_sessions")
    dominant_zone: Mapped[Optional["Zone"]] = relationship("Zone", back_populates="work_sessions")
    overrides: Mapped[List["EventOverride"]] = relationship(
        "EventOverride",
        back_populates="work_session",
        cascade="all, delete-orphan",
    )


class DailyWorkSummary(Base):
    __tablename__ = "daily_work_summaries"
    __table_args__ = (
        UniqueConstraint("employee_id", "date", name="uq_daily_work_summaries_employee_date"),
        Index("idx_daily_summaries_date", "date", "employee_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    clock_in_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    clock_out_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    total_presence_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    total_working_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    total_meeting_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    total_break_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    total_away_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    total_unknown_seconds: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", back_populates="daily_work_summaries")


class EventOverride(Base):
    __tablename__ = "event_overrides"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    work_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("work_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    operator_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
    )
    original_state: Mapped[BusinessState] = mapped_column(
        BusinessStateEnum,
        nullable=False,
    )
    new_state: Mapped[BusinessState] = mapped_column(
        BusinessStateEnum,
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    work_session: Mapped["WorkSession"] = relationship("WorkSession", back_populates="overrides")
