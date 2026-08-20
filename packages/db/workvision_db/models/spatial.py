"""
Spatial & Infrastructure Models: Buildings, Floors, Rooms, Cameras, Zones, Workstations, Topologies.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from workvision_db.base import Base
from workvision_db.models.enums import ZoneType, ZoneTypeEnum


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    floors: Mapped[List["Floor"]] = relationship(
        "Floor",
        back_populates="building",
        cascade="all, delete-orphan",
    )


class Floor(Base):
    __tablename__ = "floors"
    __table_args__ = (
        UniqueConstraint("building_id", "floor_number", name="uq_floors_building_floor_number"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    building_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("buildings.id", ondelete="CASCADE"),
        nullable=False,
    )
    floor_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    building: Mapped["Building"] = relationship("Building", back_populates="floors")
    rooms: Mapped[List["Room"]] = relationship(
        "Room",
        back_populates="floor",
        cascade="all, delete-orphan",
    )


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint("floor_id", "code", name="uq_rooms_floor_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    floor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("floors.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    room_type: Mapped[str] = mapped_column(
        String(50),
        default="OFFICE_SPACE",
        server_default=text("'OFFICE_SPACE'"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    floor: Mapped["Floor"] = relationship("Floor", back_populates="rooms")
    cameras: Mapped[List["Camera"]] = relationship("Camera", back_populates="room")


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    camera_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    room_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rooms.id", ondelete="SET NULL"),
        nullable=True,
    )
    rtsp_url: Mapped[str] = mapped_column(Text, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(INET, nullable=True)
    fps: Mapped[int] = mapped_column(
        Integer,
        default=25,
        server_default=text("25"),
        nullable=False,
    )
    resolution: Mapped[str] = mapped_column(
        String(20),
        default="1920x1080",
        server_default=text("'1920x1080'"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
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
    room: Mapped[Optional["Room"]] = relationship("Room", back_populates="cameras")
    zones: Mapped[List["Zone"]] = relationship(
        "Zone",
        back_populates="camera",
        cascade="all, delete-orphan",
    )
    source_topologies: Mapped[List["CameraTopology"]] = relationship(
        "CameraTopology",
        foreign_keys="CameraTopology.source_camera_id",
        back_populates="source_camera",
        cascade="all, delete-orphan",
    )
    target_topologies: Mapped[List["CameraTopology"]] = relationship(
        "CameraTopology",
        foreign_keys="CameraTopology.target_camera_id",
        back_populates="target_camera",
        cascade="all, delete-orphan",
    )
    tracking_sessions: Mapped[List["TrackingSession"]] = relationship(
        "TrackingSession",
        back_populates="camera",
        cascade="all, delete-orphan",
    )


class Zone(Base):
    __tablename__ = "zones"
    __table_args__ = (
        UniqueConstraint("camera_id", "zone_code", name="uq_zones_camera_zone_code"),
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
    zone_code: Mapped[str] = mapped_column(String(50), nullable=False)
    zone_name: Mapped[str] = mapped_column(String(255), nullable=False)
    zone_type: Mapped[ZoneType] = mapped_column(
        ZoneTypeEnum,
        default=ZoneType.WORK_AREA,
        server_default=text("'WORK_AREA'::zone_type_enum"),
        nullable=False,
    )
    polygon_points: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
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
    camera: Mapped["Camera"] = relationship("Camera", back_populates="zones")
    workstations: Mapped[List["Workstation"]] = relationship(
        "Workstation",
        back_populates="zone",
        cascade="all, delete-orphan",
    )
    work_sessions: Mapped[List["WorkSession"]] = relationship(
        "WorkSession",
        back_populates="dominant_zone",
    )


class Workstation(Base):
    __tablename__ = "workstations"
    __table_args__ = (
        UniqueConstraint("zone_id", "workstation_code", name="uq_workstations_zone_workstation_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("zones.id", ondelete="CASCADE"),
        nullable=False,
    )
    workstation_code: Mapped[str] = mapped_column(String(50), nullable=False)
    polygon_points: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
    )
    default_assigned_employee_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    zone: Mapped["Zone"] = relationship("Zone", back_populates="workstations")
    default_assigned_employee: Mapped[Optional["Employee"]] = relationship(
        "Employee",
        back_populates="assigned_workstations",
    )


class CameraTopology(Base):
    __tablename__ = "camera_topologies"
    __table_args__ = (
        UniqueConstraint(
            "source_camera_id",
            "target_camera_id",
            name="uq_camera_topologies_source_target",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
    )
    source_camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False,
    )
    transit_time_min_seconds: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default=text("1"),
        nullable=False,
    )
    transit_time_max_seconds: Mapped[int] = mapped_column(
        Integer,
        default=30,
        server_default=text("30"),
        nullable=False,
    )
    reid_similarity_threshold: Mapped[float] = mapped_column(
        Float,
        default=0.75,
        server_default=text("0.75"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    source_camera: Mapped["Camera"] = relationship(
        "Camera",
        foreign_keys=[source_camera_id],
        back_populates="source_topologies",
    )
    target_camera: Mapped["Camera"] = relationship(
        "Camera",
        foreign_keys=[target_camera_id],
        back_populates="target_topologies",
    )
