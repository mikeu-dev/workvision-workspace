"""
FastAPI Backend & WebSocket Gateway Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from workvision_config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Backend API and Realtime WebSocket Hub for WorkVision AI Workforce Monitoring Engine.",
    debug=settings.DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "workvision-api",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "timezone": settings.TIMEZONE,
        "debug": settings.DEBUG,
        "version": "1.0.0",
    }


def run():
    import uvicorn
    uvicorn.run(
        "workvision_api.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )


if __name__ == "__main__":
    run()
