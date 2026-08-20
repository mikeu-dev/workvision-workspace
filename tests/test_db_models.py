"""
Unit Tests for SQLAlchemy 2.0 Database Models (workvision-db).
"""

from datetime import date, datetime
import uuid

from workvision_db import (
    ActivityEvent,
    AttendanceEvent,
    AttendanceType,
    AuditLog,
    Base,
    Building,
    BusinessState,
    Camera,
    CameraTopology,
    DailyWorkSummary,
    Department,
    Employee,
    EventOverride,
    Floor,
    IdentityAssociation,
    IdentityStatus,
    LocationEvent,
    ObservedActivity,
    Room,
    StateEvent,
    TrackingSession,
    WorkSession,
    Workstation,
    Zone,
    ZoneType,
)


def test_metadata_tables_count():
    """Verify that all 19 database tables are correctly mapped and registered."""
    expected_tables = {
        "departments",
        "employees",
        "buildings",
        "floors",
        "rooms",
        "cameras",
        "zones",
        "workstations",
        "camera_topologies",
        "tracking_sessions",
        "identity_associations",
        "location_events",
        "activity_events",
        "state_events",
        "attendance_events",
        "work_sessions",
        "daily_work_summaries",
        "event_overrides",
        "audit_logs",
    }

    registered_tables = set(Base.metadata.tables.keys())
    assert expected_tables == registered_tables


def test_model_instantiation():
    """Test model object creation and attribute types."""
    dept_id = uuid.uuid4()
    dept = Department(
        id=dept_id,
        code="ENG",
        name="Engineering",
    )
    assert dept.code == "ENG"
    assert dept.name == "Engineering"

    emp = Employee(
        id=uuid.uuid4(),
        employee_code="EMP001",
        full_name="Budi Santoso",
        department_id=dept_id,
        email="budi@company.com",
        is_active=True,
    )
    assert emp.employee_code == "EMP001"
    assert emp.is_active is True

    cam_id = uuid.uuid4()
    cam = Camera(
        id=cam_id,
        camera_code="CAM01",
        name="Main Entrance Camera",
        rtsp_url="rtsp://192.168.1.50/stream1",
        fps=25,
        resolution="1920x1080",
    )
    assert cam.fps == 25
    assert cam.resolution == "1920x1080"

    zone = Zone(
        id=uuid.uuid4(),
        camera_id=cam_id,
        zone_code="WORK_01",
        zone_name="Work Area 1",
        zone_type=ZoneType.WORK_AREA,
        polygon_points=[{"x": 0, "y": 0}, {"x": 100, "y": 100}],
    )
    assert zone.zone_type == ZoneType.WORK_AREA
    assert len(zone.polygon_points) == 2


def test_time_series_partitioned_models():
    """Test partitioned models definition."""
    loc = LocationEvent(
        tracking_session_id=uuid.uuid4(),
        camera_id=uuid.uuid4(),
        event_type="ZONE_ENTER",
        foot_x=120.5,
        foot_y=340.0,
        timestamp=datetime.utcnow(),
    )
    assert loc.foot_x == 120.5
    assert loc.event_type == "ZONE_ENTER"

    act = ActivityEvent(
        tracking_session_id=uuid.uuid4(),
        activity=ObservedActivity.SITTING,
        confidence=0.98,
        timestamp=datetime.utcnow(),
    )
    assert act.activity == ObservedActivity.SITTING
    assert act.confidence == 0.98

    state_ev = StateEvent(
        state=BusinessState.WORKING,
        confidence=0.95,
        timestamp=datetime.utcnow(),
    )
    assert state_ev.state == BusinessState.WORKING


def test_business_and_audit_models():
    """Test Business and Audit model properties."""
    emp_id = uuid.uuid4()
    summary = DailyWorkSummary(
        employee_id=emp_id,
        date=date(2026, 8, 20),
        total_presence_seconds=28800,
        total_working_seconds=25200,
        total_meeting_seconds=3600,
    )
    assert summary.total_presence_seconds == 28800

    audit = AuditLog(
        actor_id=uuid.uuid4(),
        action="UPDATE_ZONE",
        entity_type="Zone",
        entity_id=uuid.uuid4(),
        metadata_={"reason": "Re-calibrated camera coordinates"},
    )
    assert audit.action == "UPDATE_ZONE"
    assert audit.metadata_["reason"] == "Re-calibrated camera coordinates"
