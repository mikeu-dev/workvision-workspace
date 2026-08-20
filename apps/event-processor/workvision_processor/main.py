"""
Event Processor Entry Point
Handles Identity Association, Temporal State Machine (Hysteresis Filter), and Work Session calculation.
"""

import logging
from workvision_config import get_settings

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("event-processor")


def main():
    logger.info(f"Initializing {settings.APP_NAME} - Event & State Processor ({settings.APP_ENV})...")
    logger.info(f"Subscribing to Redis: {settings.REDIS_URL}")
    logger.info(f"Consuming streams: '{settings.STREAM_VISION_EVENTS}' & '{settings.STREAM_ATTENDANCE_EVENTS}'")
    logger.info("Temporal Hysteresis Rules: Debounce=%ds, Away Timeout=%ds, Break Min=%ds, Meeting Min=%ds",
                settings.STATE_DEBOUNCE_SECONDS, settings.AWAY_TIMEOUT_SECONDS,
                settings.BREAK_MIN_SECONDS, settings.MEETING_MIN_SECONDS)
    logger.info(f"Database Persistence Target: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    logger.info("Event & State Processor is ready.")


if __name__ == "__main__":
    main()
