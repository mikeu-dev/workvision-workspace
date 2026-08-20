"""
PostgreSQL Enum Types for WorkVision AI Models.
"""

from enum import Enum
from sqlalchemy.dialects.postgresql import ENUM


class IdentityStatus(str, Enum):
    UNASSIGNED = "UNASSIGNED"
    CANDIDATE = "CANDIDATE"
    PROBABLE = "PROBABLE"
    CONFIRMED = "CONFIRMED"
    UNKNOWN = "UNKNOWN"


class ObservedActivity(str, Enum):
    SITTING = "SITTING"
    STANDING = "STANDING"
    WALKING = "WALKING"
    MOVING = "MOVING"
    STATIONARY = "STATIONARY"
    PERSON_INTERACTION = "PERSON_INTERACTION"
    OBJECT_INTERACTION = "OBJECT_INTERACTION"
    UNKNOWN = "UNKNOWN"


class BusinessState(str, Enum):
    WORKING = "WORKING"
    MEETING = "MEETING"
    BREAK = "BREAK"
    AWAY = "AWAY"
    UNKNOWN = "UNKNOWN"


class AttendanceType(str, Enum):
    CLOCK_IN = "CLOCK_IN"
    CLOCK_OUT = "CLOCK_OUT"
    BREAK_OUT = "BREAK_OUT"
    BREAK_IN = "BREAK_IN"


class ZoneType(str, Enum):
    WORK_AREA = "WORK_AREA"
    MEETING_ROOM = "MEETING_ROOM"
    PANTRY = "PANTRY"
    CORRIDOR = "CORRIDOR"
    ENTRANCE = "ENTRANCE"
    EXIT = "EXIT"
    RESTRICTED = "RESTRICTED"


# PostgreSQL SQLAlchemy ENUM instances with exact SQL enum names
IdentityStatusEnum = ENUM(
    IdentityStatus,
    name="identity_status_enum",
    create_type=False,
    values_callable=lambda x: [e.value for e in x],
)

ObservedActivityEnum = ENUM(
    ObservedActivity,
    name="observed_activity_enum",
    create_type=False,
    values_callable=lambda x: [e.value for e in x],
)

BusinessStateEnum = ENUM(
    BusinessState,
    name="business_state_enum",
    create_type=False,
    values_callable=lambda x: [e.value for e in x],
)

AttendanceTypeEnum = ENUM(
    AttendanceType,
    name="attendance_type_enum",
    create_type=False,
    values_callable=lambda x: [e.value for e in x],
)

ZoneTypeEnum = ENUM(
    ZoneType,
    name="zone_type_enum",
    create_type=False,
    values_callable=lambda x: [e.value for e in x],
)
