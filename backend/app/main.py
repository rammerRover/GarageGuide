from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from starlette.exceptions import HTTPException

from app.routes.auth import router as auth_router
from app.routes.health import router as health_router


def create_app() -> FastAPI:
    application = FastAPI(title="GarageGuide")
    application.include_router(health_router, prefix="/api")
    application.include_router(auth_router, prefix="/api")

    @application.exception_handler(HTTPException)
    async def safe_http_error(request: Request, error: HTTPException):
        response = await http_exception_handler(request, error)
        if request.url.path == "/api/auth" or request.url.path.startswith("/api/auth/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    return application


app = create_app()
