"""
Integration Tests for Alembic Migrations (workvision-db).
"""

from pathlib import Path
from alembic import command
from alembic.config import Config


def get_test_alembic_config() -> Config:
    """Helper to load root alembic.ini for testing."""
    root_ini = Path(__file__).resolve().parent.parent / "alembic.ini"
    assert root_ini.exists(), "Root alembic.ini must exist"
    return Config(str(root_ini))


def test_alembic_config_resolution():
    """Verify that Alembic configuration can be resolved successfully."""
    config = get_test_alembic_config()
    assert config is not None
    assert "alembic.ini" in config.config_file_name


def test_alembic_offline_sql_generation(capsys):
    """Verify that Alembic upgrade base:head --sql compiles valid SQL without errors."""
    config = get_test_alembic_config()
    # Runs offline SQL upgrade from base to head
    command.upgrade(config, "base:head", sql=True)
    captured = capsys.readouterr()
    sql_output = captured.out

    # Check key DDL components exist in output
    assert "CREATE TABLE departments" in sql_output
    assert "CREATE TABLE employees" in sql_output
    assert "CREATE TABLE cameras" in sql_output
    assert "location_events" in sql_output
    assert "PARTITION BY RANGE" in sql_output
    assert "CREATE TABLE work_sessions" in sql_output
