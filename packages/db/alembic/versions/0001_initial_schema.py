"""Initial database schema migration (WorkVision AI)

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-08-20 20:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. PostgreSQL Extensions
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # 2. Enum Types
    identity_status_enum = postgresql.ENUM(
        "UNASSIGNED", "CANDIDATE", "PROBABLE", "CONFIRMED", "UNKNOWN",
        name="identity_status_enum",
        create_type=False,
    )
    identity_status_enum.create(op.get_bind(), checkfirst=True)

    observed_activity_enum = postgresql.ENUM(
        "SITTING", "STANDING", "WALKING", "MOVING", "STATIONARY",
        "PERSON_INTERACTION", "OBJECT_INTERACTION", "UNKNOWN",
        name="observed_activity_enum",
        create_type=False,
    )
    observed_activity_enum.create(op.get_bind(), checkfirst=True)

    business_state_enum = postgresql.ENUM(
        "WORKING", "MEETING", "BREAK", "AWAY", "UNKNOWN",
        name="business_state_enum",
        create_type=False,
    )
    business_state_enum.create(op.get_bind(), checkfirst=True)

    attendance_type_enum = postgresql.ENUM(
        "CLOCK_IN", "CLOCK_OUT", "BREAK_OUT", "BREAK_IN",
        name="attendance_type_enum",
        create_type=False,
    )
    attendance_type_enum.create(op.get_bind(), checkfirst=True)

    zone_type_enum = postgresql.ENUM(
        "WORK_AREA", "MEETING_ROOM", "PANTRY", "CORRIDOR", "ENTRANCE", "EXIT", "RESTRICTED",
        name="zone_type_enum",
        create_type=False,
    )
    zone_type_enum.create(op.get_bind(), checkfirst=True)

    # 3. Master Tables: departments, employees, buildings, floors, rooms, cameras, zones, workstations, camera_topologies
    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "employees",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("employee_code", sa.String(100), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("face_embedding_encrypted", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "buildings",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "floors",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("building_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("buildings.id", ondelete="CASCADE"), nullable=False),
        sa.Column("floor_number", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("building_id", "floor_number", name="uq_floors_building_floor_number"),
    )

    op.create_table(
        "rooms",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("floor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("floors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("room_type", sa.String(50), server_default=sa.text("'OFFICE_SPACE'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("floor_id", "code", name="uq_rooms_floor_code"),
    )

    op.create_table(
        "cameras",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("camera_code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("room_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rooms.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rtsp_url", sa.Text(), nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("fps", sa.Integer(), server_default=sa.text("25"), nullable=False),
        sa.Column("resolution", sa.String(20), server_default=sa.text("'1920x1080'"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "zones",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zone_code", sa.String(50), nullable=False),
        sa.Column("zone_name", sa.String(255), nullable=False),
        sa.Column("zone_type", zone_type_enum, server_default=sa.text("'WORK_AREA'::zone_type_enum"), nullable=False),
        sa.Column("polygon_points", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("camera_id", "zone_code", name="uq_zones_camera_zone_code"),
    )

    op.create_table(
        "workstations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("zone_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("zones.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workstation_code", sa.String(50), nullable=False),
        sa.Column("polygon_points", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("default_assigned_employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("zone_id", "workstation_code", name="uq_workstations_zone_workstation_code"),
    )

    op.create_table(
        "camera_topologies",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("source_camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transit_time_min_seconds", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("transit_time_max_seconds", sa.Integer(), server_default=sa.text("30"), nullable=False),
        sa.Column("reid_similarity_threshold", sa.Float(), server_default=sa.text("0.75"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("source_camera_id", "target_camera_id", name="uq_camera_topologies_source_target"),
    )

    # 4. Tracking Sessions & Identity
    op.create_table(
        "tracking_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("camera_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cameras.id", ondelete="CASCADE"), nullable=False),
        sa.Column("local_track_id", sa.Integer(), nullable=False),
        sa.Column("global_track_id", sa.String(100), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_frames_tracked", sa.Integer(), server_default=sa.text("1"), nullable=False),
        sa.Column("status", sa.String(50), server_default=sa.text("'ACTIVE'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "identity_associations",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("tracking_session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tracking_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="SET NULL"), nullable=True),
        sa.Column("identity_status", identity_status_enum, server_default=sa.text("'UNASSIGNED'::identity_status_enum"), nullable=False),
        sa.Column("confidence", sa.Float(), server_default=sa.text("0.0"), nullable=False),
        sa.Column("association_method", sa.String(50), nullable=False),
        sa.Column("associated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("evidence_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    # 5. Partitioned Time-Series Events (DDL with PostgreSQL Partition by RANGE)
    op.execute("""
    CREATE TABLE IF NOT EXISTS location_events (
        id UUID DEFAULT uuid_generate_v4(),
        tracking_session_id UUID NOT NULL,
        employee_id UUID,
        camera_id UUID NOT NULL,
        zone_id UUID,
        workstation_id UUID,
        event_type VARCHAR(50) NOT NULL,
        foot_x FLOAT NOT NULL,
        foot_y FLOAT NOT NULL,
        timestamp TIMESTAMPTZ NOT NULL,
        PRIMARY KEY (id, timestamp)
    ) PARTITION BY RANGE (timestamp);
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS activity_events (
        id UUID DEFAULT uuid_generate_v4(),
        tracking_session_id UUID NOT NULL,
        activity observed_activity_enum NOT NULL,
        confidence FLOAT NOT NULL DEFAULT 1.0,
        timestamp TIMESTAMPTZ NOT NULL,
        PRIMARY KEY (id, timestamp)
    ) PARTITION BY RANGE (timestamp);
    """)

    op.execute("""
    CREATE TABLE IF NOT EXISTS state_events (
        id UUID DEFAULT uuid_generate_v4(),
        employee_id UUID,
        tracking_session_id UUID,
        state business_state_enum NOT NULL,
        confidence FLOAT NOT NULL DEFAULT 1.0,
        timestamp TIMESTAMPTZ NOT NULL,
        evidence JSONB,
        PRIMARY KEY (id, timestamp)
    ) PARTITION BY RANGE (timestamp);
    """)

    # Default Partitions (2026_08, 2026_09)
    op.execute("""
    CREATE TABLE IF NOT EXISTS location_events_2026_08 PARTITION OF location_events
        FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00');
    CREATE TABLE IF NOT EXISTS location_events_2026_09 PARTITION OF location_events
        FOR VALUES FROM ('2026-09-01 00:00:00+00') TO ('2026-10-01 00:00:00+00');

    CREATE TABLE IF NOT EXISTS activity_events_2026_08 PARTITION OF activity_events
        FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00');
    CREATE TABLE IF NOT EXISTS activity_events_2026_09 PARTITION OF activity_events
        FOR VALUES FROM ('2026-09-01 00:00:00+00') TO ('2026-10-01 00:00:00+00');

    CREATE TABLE IF NOT EXISTS state_events_2026_08 PARTITION OF state_events
        FOR VALUES FROM ('2026-08-01 00:00:00+00') TO ('2026-09-01 00:00:00+00');
    CREATE TABLE IF NOT EXISTS state_events_2026_09 PARTITION OF state_events
        FOR VALUES FROM ('2026-09-01 00:00:00+00') TO ('2026-10-01 00:00:00+00');
    """)

    # 6. Business Layer & Aggregations
    op.create_table(
        "attendance_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("attendance_type", attendance_type_enum, nullable=False),
        sa.Column("source_terminal", sa.String(100), server_default=sa.text("'FACE_TERMINAL_MAIN'"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "work_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("state", business_state_enum, nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "duration_seconds",
            sa.Integer(),
            sa.Computed("EXTRACT(EPOCH FROM (end_time - start_time))::INT", persisted=True),
            nullable=True,
        ),
        sa.Column("dominant_zone_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("zones.id", ondelete="SET NULL"), nullable=True),
        sa.Column("confidence_score", sa.Float(), server_default=sa.text("1.0"), nullable=False),
        sa.Column("is_overridden", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "daily_work_summaries",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("employee_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("employees.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("clock_in_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("clock_out_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_presence_seconds", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_working_seconds", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_meeting_seconds", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_break_seconds", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_away_seconds", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_unknown_seconds", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("employee_id", "date", name="uq_daily_work_summaries_employee_date"),
    )

    op.create_table(
        "event_overrides",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("work_session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("work_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("operator_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("original_state", business_state_enum, nullable=False),
        sa.Column("new_state", business_state_enum, nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), primary_key=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 7. Performance Indexes
    op.create_index("idx_employees_code", "employees", ["employee_code"])
    op.create_index("idx_tracking_sessions_cam_track", "tracking_sessions", ["camera_id", "local_track_id"])
    op.create_index("idx_identity_assoc_employee", "identity_associations", ["employee_id"])
    op.create_index("idx_work_sessions_emp_time", "work_sessions", ["employee_id", "start_time", "end_time"])
    op.create_index("idx_daily_summaries_date", "daily_work_summaries", ["date", "employee_id"])

    # BRIN & B-Tree Indexes on Partitioned Tables
    op.execute("CREATE INDEX IF NOT EXISTS idx_loc_events_time ON location_events USING BRIN(timestamp);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_loc_events_session ON location_events(tracking_session_id, timestamp);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_act_events_time ON activity_events USING BRIN(timestamp);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_state_events_time ON state_events USING BRIN(timestamp);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_state_events_emp_time ON state_events(employee_id, timestamp);")


def downgrade() -> None:
    # Drop Business Layer
    op.drop_table("audit_logs")
    op.drop_table("event_overrides")
    op.drop_table("daily_work_summaries")
    op.drop_table("work_sessions")
    op.drop_table("attendance_events")

    # Drop Event Partitions & Partitioned Tables
    op.execute("DROP TABLE IF EXISTS state_events CASCADE")
    op.execute("DROP TABLE IF EXISTS activity_events CASCADE")
    op.execute("DROP TABLE IF EXISTS location_events CASCADE")

    # Drop Tracking & Spatial & Organization
    op.drop_table("identity_associations")
    op.drop_table("tracking_sessions")
    op.drop_table("camera_topologies")
    op.drop_table("workstations")
    op.drop_table("zones")
    op.drop_table("cameras")
    op.drop_table("rooms")
    op.drop_table("floors")
    op.drop_table("buildings")
    op.drop_table("employees")
    op.drop_table("departments")

    # Drop Enums
    op.execute("DROP TYPE IF EXISTS zone_type_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS attendance_type_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS business_state_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS observed_activity_enum CASCADE")
    op.execute("DROP TYPE IF EXISTS identity_status_enum CASCADE")
