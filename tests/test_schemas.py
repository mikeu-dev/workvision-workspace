"""
Unit Tests for Pydantic Data Contracts & DTOs (workvision-schemas).
"""

from datetime import datetime
from uuid import uuid4

from workvision_schemas import (
    AttendanceType,
    BoundingBox,
    BusinessState,
    DetectionEvent,
    FootPoint,
    IdentityStatus,
    ObservedActivity,
    TrackedPerson,
    ZoneEvent,
    ZoneType,
)


def test_foot_point_and_bounding_box():
    """Test geometry contracts."""
    bbox = BoundingBox(x1=100.0, y1=200.0, x2=200.0, y2=400.0, confidence=0.95)
    # Foot-point bottom center: [(100 + 200)/2, 400] = [150.0, 400.0]
    foot = FootPoint(x=(bbox.x1 + bbox.x2) / 2, y=bbox.y2)

    assert foot.x == 150.0
    assert foot.y == 400.0


def test_detection_event():
    """Test detection event serialization."""
    bbox = BoundingBox(x1=10.0, y1=20.0, x2=50.0, y2=100.0, confidence=0.9)
    foot = FootPoint(x=30.0, y=100.0)
    event = DetectionEvent(bbox=bbox, foot_point=foot, confidence=0.9)

    assert event.confidence == 0.9
    assert event.foot_point.x == 30.0


def test_tracked_person_contract():
    """Test TrackedPerson data structure and default values."""
    person = TrackedPerson(
        camera_id="CAM01",
        track_id=17,
        bbox=BoundingBox(x1=10.0, y1=10.0, x2=30.0, y2=50.0),
        foot_point=FootPoint(x=20.0, y=50.0),
    )

    assert person.identity_status == IdentityStatus.UNASSIGNED
    assert person.observed_activity == ObservedActivity.UNKNOWN
    assert person.identity_confidence == 0.0
    assert isinstance(person.timestamp, datetime)


def test_zone_event_contract():
    """Test ZoneEvent creation and validation."""
    zone_event = ZoneEvent(
        camera_id="CAM01",
        track_id=42,
        zone_id="WORK_AREA_01",
        zone_type=ZoneType.WORK_AREA,
        event_type="ZONE_ENTER",
        foot_point=FootPoint(x=150.0, y=300.0),
    )

    assert zone_event.zone_type == ZoneType.WORK_AREA
    assert zone_event.event_type == "ZONE_ENTER"
    assert zone_event.event_id is not None
