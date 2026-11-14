import logging

import psycopg
from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from app import authentication, vehicle_queries
from app.config import AuthConfigurationError, Settings, get_settings
from app.session_queries import AuthenticatedSession
from app.vehicle_schemas import READING_ERROR, Vehicle, VehicleCreate, VehicleListResponse


logger = logging.getLogger(__name__)
_FIELDS = frozenset({"year", "make", "model", "engine", "vehicle_type", "mileage", "operating_hours"})
_MESSAGES = {
    "missing": "Field required.",
    "string_type": "Enter text.",
    "int_type": "Enter a whole model year.",
    "extra_forbidden": "Unexpected fields are not allowed.",
    "json_invalid": "Provide valid JSON.",
    "model_type": "Provide a JSON object.",
    "model_attributes_type": "Provide a JSON object.",
    "value_error": "Enter a valid value.",
}
_FIELD_MESSAGES = {
    "year": "Enter a model year from 1886 through next calendar year.",
    "make": "Enter nonblank text with valid Unicode and no NUL.",
    "model": "Enter nonblank text with valid Unicode and no NUL.",
    "vehicle_type": "Enter nonblank text with valid Unicode and no NUL.",
    "engine": "Enter valid Unicode characters without NUL.",
    "mileage": READING_ERROR,
    "operating_hours": READING_ERROR,
}


def _validation_response(errors):
    details = []
    for error in errors:
        location = error.get("loc", ())
        field = (
            location[1] if isinstance(location, (tuple, list)) and len(location) == 2
            and location[0] == "body" and isinstance(location[1], str)
            and location[1] in _FIELDS else None
        )
        error_type = error.get("type")
        if not isinstance(error_type, str) or error_type not in _MESSAGES:
            error_type = "value_error"
        message = _MESSAGES[error_type]
        if error_type == "value_error" and field is not None:
            message = _FIELD_MESSAGES[field]
        details.append({
            "loc": ["body", field] if field is not None else ["body"],
            "msg": message, "type": error_type,
        })
    return JSONResponse(status_code=422, content={"detail": details})


def _internal_error():
    logger.error("Vehicle request failed unexpectedly")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


class VehicleRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request: Request):
            response = await safe_response(request)
            response.headers["Cache-Control"] = "no-store"
            return response

        async def safe_response(request: Request):
            try:
                settings = await run_in_threadpool(authentication.request_auth_settings, request)
                if request.method == "POST":
                    authentication.require_mutation_policy(request, settings)
                return await handler(request)
            except authentication.AuthenticationFailure as error:
                return JSONResponse(
                    status_code=error.status_code, content={"detail": error.detail}, headers=error.headers,
                )
            except authentication.RequestPolicyError:
                return JSONResponse(status_code=403, content={"detail": "Request not allowed."})
            except RequestValidationError as error:
                return _validation_response(error.errors())
            except AuthConfigurationError:
                return JSONResponse(
                    status_code=503, content={"detail": "Authentication unavailable. Please try again."},
                )
            except (vehicle_queries.VehicleUnavailableError, psycopg.OperationalError,
                    psycopg.InterfaceError, psycopg.errors.QueryCanceled):
                logger.warning("Vehicle request unavailable")
                return JSONResponse(
                    status_code=503, content={"detail": "Vehicles unavailable. Please try again."},
                )
            except HTTPException as error:
                if error.status_code == 400:
                    return _validation_response([{"type": "json_invalid", "loc": ("body",)}])
                return _internal_error()
            except Exception:
                # Keep raw errors inside the boundary so server logs cannot expose their contents.
                return _internal_error()

        return safe_handler


router = APIRouter(prefix="/vehicles", tags=["vehicles"], route_class=VehicleRoute)


def _vehicle_response(
    result: Vehicle | VehicleListResponse, actor: AuthenticatedSession, status_code: int,
) -> Response:
    response = JSONResponse(status_code=status_code, content=result.model_dump(mode="json"))
    authentication.attach_session_deadline(response, actor)
    return response


@router.get("", response_model=VehicleListResponse)
def list_owned_vehicles(
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    prepared = None

    def prepare(result):
        nonlocal prepared
        prepared = _vehicle_response(result, actor, 200)

    vehicle_queries.list_vehicles(settings, actor=actor, prepare_response=prepare)
    if prepared is None:
        raise RuntimeError("Vehicle list response was not prepared")
    return prepared


@router.post("", status_code=201, response_model=Vehicle)
def create_owned_vehicle(
    vehicle: VehicleCreate,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    prepared = None

    def prepare(result):
        nonlocal prepared
        prepared = _vehicle_response(result, actor, 201)

    vehicle_queries.create_vehicle(settings, actor=actor, vehicle=vehicle, prepare_response=prepare)
    if prepared is None:
        raise RuntimeError("Vehicle creation response was not prepared")
    return prepared
