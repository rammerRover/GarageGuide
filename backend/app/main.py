from fastapi import FastAPI

from app.routes.health import router as health_router


def create_app() -> FastAPI:
    application = FastAPI(title="GarageGuide")
    application.include_router(health_router, prefix="/api")
    return application


app = create_app()
