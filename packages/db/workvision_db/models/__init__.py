"""
WorkVision AI - SQLAlchemy 2.0 Domain Models Export Registry.
"""

from workvision_db.base import Base
from workvision_db.models.enums import (
    AttendanceType,
    AttendanceTypeEnum,
    BusinessState,
    BusinessStateEnum,
    IdentityStatus,
    IdentityStatusEnum,
    ObservedActivity,
    ObservedActivityEnum,
    ZoneType,
    ZoneTypeEnum,
)
from workvision_db.models.organization import Department, Employee
from workvision_db.models.spatial import (
    Building,
    Camera,
    CameraTopology,
    Floor,
    Room,
    Workstation,
    Zone,
)
from workvision_db.models.tracking import IdentityAssociation, TrackingSession
from workvision_db.models.events import ActivityEvent, LocationEvent, StateEvent
from workvision_db.models.business import (
    AttendanceEvent,
    DailyWorkSummary,
    EventOverride,
    WorkSession,
)
from workvision_db.models.audit import AuditLog

__all__ = [
    "Base",
    # Enums
    "IdentityStatus",
    "IdentityStatusEnum",
    "ObservedActivity",
    "ObservedActivityEnum",
    "BusinessState",
    "BusinessStateEnum",
    "AttendanceType",
    "AttendanceTypeEnum",
    "ZoneType",
    "ZoneTypeEnum",
    # Organization
    "Department",
    "Employee",
    # Spatial & Infra
    "Building",
    "Floor",
    "Room",
    "Camera",
    "Zone",
    "Workstation",
    "CameraTopology",
    # Tracking
    "TrackingSession",
    "IdentityAssociation",
    # Partitioned Events
    "LocationEvent",
    "ActivityEvent",
    "StateEvent",
    # Business
    "AttendanceEvent",
    "WorkSession",
    "DailyWorkSummary",
    "EventOverride",
    # Audit
    "AuditLog",
]
