"""
Organization & Employee Models.
"""

from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, LargeBinary, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from workvision_db.base import Base


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
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
    employees: Mapped[List["Employee"]] = relationship(
        "Employee",
        back_populates="department",
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    employee_code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
    face_embedding_encrypted: Mapped[Optional[bytes]] = mapped_column(
        LargeBinary,
        nullable=True,
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
    department: Mapped[Optional["Department"]] = relationship(
        "Department",
        back_populates="employees",
    )
    assigned_workstations: Mapped[List["Workstation"]] = relationship(
        "Workstation",
        back_populates="default_assigned_employee",
    )
    identity_associations: Mapped[List["IdentityAssociation"]] = relationship(
        "IdentityAssociation",
        back_populates="employee",
    )
    attendance_events: Mapped[List["AttendanceEvent"]] = relationship(
        "AttendanceEvent",
        back_populates="employee",
    )
    work_sessions: Mapped[List["WorkSession"]] = relationship(
        "WorkSession",
        back_populates="employee",
    )
    daily_work_summaries: Mapped[List["DailyWorkSummary"]] = relationship(
        "DailyWorkSummary",
        back_populates="employee",
    )
