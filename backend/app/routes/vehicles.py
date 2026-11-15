import logging
import re

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
from app.vehicle_schemas import (
    CONFIRMATION_ERROR, EMPTY_PATCH_ERROR, READING_ERROR, REQUIRED_PATCH_ERROR,
    VEHICLE_ID_ERROR, ReadingConfirmationRequired, Vehicle, VehicleCreate,
    VehicleId, VehicleListResponse, VehiclePatch,
)


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


def _validation_response(errors, *, patch=False):
    details = []
    for error in errors:
        location = error.get("loc", ())
        if location in (("path", "vehicle_id"), ["path", "vehicle_id"]):
            details.append({"loc": ["path", "vehicle_id"], "msg": VEHICLE_ID_ERROR, "type": "value_error"})
            continue
        fixed_message = error.get("msg")
        confirmation_location = (
            isinstance(location, (tuple, list)) and len(location) >= 2
            and location[:2] in (("body", "reading_confirmation"), ["body", "reading_confirmation"])
        )
        if patch and (confirmation_location or fixed_message == "Value error, " + CONFIRMATION_ERROR):
            details.append({"loc": ["body", "reading_confirmation"], "msg": CONFIRMATION_ERROR, "type": "value_error"})
            continue
        if patch and fixed_message == "Value error, " + EMPTY_PATCH_ERROR and location in ((), [], ("body",), ["body"]):
            details.append({"loc": ["body"], "msg": EMPTY_PATCH_ERROR, "type": "value_error"})
            continue
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
            if patch and field in {"year", "make", "model", "vehicle_type"} and fixed_message == "Value error, " + REQUIRED_PATCH_ERROR:
                message = REQUIRED_PATCH_ERROR
        details.append({
            "loc": ["body", field] if field is not None else ["body"],
            "msg": message, "type": error_type,
        })
    return JSONResponse(status_code=422, content={"detail": details})


def _internal_error():
    logger.error("Vehicle request failed unexpectedly")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


def _confirmation_response(error: ReadingConfirmationRequired) -> Response:
    fields = error.fields
    readings = error.current_readings
    allowed = ("mileage", "operating_hours")
    if (
        not isinstance(fields, tuple) or fields != tuple(name for name in allowed if name in fields)
        or not isinstance(readings, dict) or set(readings) != set(fields)
        or any(not isinstance(value, str) or re.fullmatch(r"(?:0|[1-9][0-9]{0,10})\.[0-9]", value) is None
               for value in readings.values())
    ):
        raise ValueError("Invalid reading confirmation outcome")
    return JSONResponse(status_code=409, content={
        "detail": "Reading changes require confirmation.",
        "fields": list(fields), "current_readings": readings,
    })


class VehicleRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request: Request):
            try:
                response = await safe_response(request)
            except Exception:
                # Response/error preparation is inside the same redaction boundary.
                response = _internal_error()
            response.headers["Cache-Control"] = "no-store"
            return response

        async def safe_response(request: Request):
            try:
                settings = await run_in_threadpool(authentication.request_auth_settings, request)
                if request.method in ("POST", "PATCH"):
                    authentication.require_mutation_policy(request, settings)
                return await handler(request)
            except authentication.AuthenticationFailure as error:
                return JSONResponse(
                    status_code=error.status_code, content={"detail": error.detail}, headers=error.headers,
                )
            except authentication.RequestPolicyError:
                return JSONResponse(status_code=403, content={"detail": "Request not allowed."})
            except RequestValidationError as error:
                return _validation_response(error.errors(), patch=request.method == "PATCH")
            except vehicle_queries.VehicleNotFoundError:
                return JSONResponse(status_code=404, content={"detail": "Vehicle not found."})
            except ReadingConfirmationRequired as error:
                return _confirmation_response(error)
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


@router.get("/{vehicle_id}", response_model=Vehicle)
def get_owned_vehicle(
    vehicle_id: VehicleId,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    prepared = None

    def prepare(result):
        nonlocal prepared
        prepared = _vehicle_response(result, actor, 200)

    vehicle_queries.get_vehicle(settings, actor=actor, vehicle_id=vehicle_id, prepare_response=prepare)
    if prepared is None:
        raise RuntimeError("Vehicle detail response was not prepared")
    return prepared


@router.patch("/{vehicle_id}", response_model=Vehicle)
def update_owned_vehicle(
    vehicle_id: VehicleId,
    patch: VehiclePatch,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    prepared = None

    def prepare(result):
        nonlocal prepared
        prepared = _vehicle_response(result, actor, 200)

    vehicle_queries.update_vehicle(
        settings, actor=actor, vehicle_id=vehicle_id, patch=patch, prepare_response=prepare,
    )
    if prepared is None:
        raise RuntimeError("Vehicle update response was not prepared")
    return prepared
