"""
Shared Pydantic data contracts and DTOs for WorkVision AI.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


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


class Point2D(BaseModel):
    x: float
    y: float


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float = 1.0


class FootPoint(BaseModel):
    """
    Bottom-center of bounding box: [(x1 + x2)/2, y2].
    Represents physical ground anchor point on floor plane.
    """
    x: float
    y: float


class DetectionEvent(BaseModel):
    bbox: BoundingBox
    foot_point: FootPoint
    confidence: float
    class_id: int = 0


class TrackedPerson(BaseModel):
    camera_id: str
    track_id: int
    global_track_id: Optional[str] = None
    employee_id: Optional[str] = None
    identity_status: IdentityStatus = IdentityStatus.UNASSIGNED
    identity_confidence: float = 0.0
    bbox: BoundingBox
    foot_point: FootPoint
    current_zone_id: Optional[str] = None
    current_workstation_id: Optional[str] = None
    observed_activity: ObservedActivity = ObservedActivity.UNKNOWN
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ZoneEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    camera_id: str
    track_id: int
    employee_id: Optional[str] = None
    zone_id: str
    zone_type: ZoneType
    event_type: str  # ZONE_ENTER, ZONE_EXIT
    foot_point: FootPoint
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RawVisionFramePayload(BaseModel):
    camera_id: str
    frame_index: int
    timestamp: datetime
    active_tracks: List[TrackedPerson] = []
    zone_events: List[ZoneEvent] = []


class AttendanceEventPayload(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    employee_id: str
    attendance_type: AttendanceType
    source_terminal: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StateTransitionEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    employee_id: str
    previous_state: BusinessState
    new_state: BusinessState
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    evidence: Dict[str, Any] = {}


class WorkSessionPayload(BaseModel):
    session_id: UUID = Field(default_factory=uuid4)
    employee_id: str
    state: BusinessState
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    dominant_zone_id: Optional[str] = None
    confidence_score: float = 1.0
    is_overridden: bool = False


class DailySummaryPayload(BaseModel):
    summary_id: UUID = Field(default_factory=uuid4)
    employee_id: str
    date: str  # YYYY-MM-DD
    clock_in_time: Optional[datetime] = None
    clock_out_time: Optional[datetime] = None
    total_presence_seconds: int = 0
    total_working_seconds: int = 0
    total_meeting_seconds: int = 0
    total_break_seconds: int = 0
    total_away_seconds: int = 0
    total_unknown_seconds: int = 0
