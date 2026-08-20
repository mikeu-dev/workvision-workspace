"""
Vision Worker Entry Point
Handles RTSP Stream acquisition, GPU inference (YOLO), ByteTrack tracking, and Zone event generation.
"""

import logging
from workvision_config import get_settings

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("vision-worker")


def main():
    logger.info(f"Initializing {settings.APP_NAME} - Vision Worker ({settings.APP_ENV})...")
    logger.info(f"Inference Device: {settings.INFERENCE_DEVICE} | Model: {settings.YOLO_MODEL_PATH}")
    logger.info(f"Sampling FPS: {settings.INFERENCE_FPS} | Max Queue Size: {settings.MAX_FRAME_QUEUE_SIZE}")
    logger.info(f"Publishing Vision Events to Redis Stream: {settings.STREAM_VISION_EVENTS}")
    logger.info("ByteTrack Config: high_thresh=%.2f, match_thresh=%.2f, buffer=%d",
                settings.TRACK_HIGH_THRESH, settings.MATCH_THRESH, settings.TRACK_BUFFER)
    logger.info("Vision Worker is ready.")


if __name__ == "__main__":
    main()
