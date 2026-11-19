import logging

import psycopg
from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from app import authentication, service_queries
from app.config import AuthConfigurationError, Settings, get_settings
from app.service_schemas import (
    COST_ERROR, EMPTY_PATCH_ERROR, REMOVAL_ERROR, REQUIRED_PATCH_ERROR, SERVICE_DATE_ERROR,
    SERVICE_ID_ERROR, ServiceCreate, ServiceId, ServiceListResponse, ServicePatch,
    ServiceRecord, ServiceRemovalRequest, ServiceRemovalResponse,
)
from app.session_queries import AuthenticatedSession
from app.vehicle_queries import VehicleNotFoundError
from app.vehicle_schemas import READING_ERROR, VEHICLE_ID_ERROR, VehicleId


logger = logging.getLogger(__name__)
_FIELDS = frozenset({"service_date", "service_type", "description", "mileage", "operating_hours", "cost", "notes"})
_MESSAGES = {
    "missing": "Field required.",
    "string_type": "Enter text.",
    "extra_forbidden": "Unexpected fields are not allowed.",
    "json_invalid": "Provide valid JSON.",
    "model_type": "Provide a JSON object.",
    "model_attributes_type": "Provide a JSON object.",
    "value_error": "Enter a valid value.",
}
_FIELD_MESSAGES = {
    "service_date": SERVICE_DATE_ERROR,
    "service_type": "Choose maintenance, repair, inspection, or diagnostic.",
    "description": "Enter nonblank text with valid Unicode and no NUL.",
    "mileage": READING_ERROR,
    "operating_hours": READING_ERROR,
    "cost": COST_ERROR,
    "notes": "Enter valid Unicode characters without NUL.",
    "confirm_removal": REMOVAL_ERROR,
}


def _validation_response(errors, *, patch=False, removal=False) -> Response:
    details = []
    for error in errors:
        location = error.get("loc", ())
        path_field = (
            location[1] if isinstance(location, (tuple, list)) and len(location) == 2
            and location[0] == "path" and location[1] in ("vehicle_id", "service_id") else None
        )
        if path_field:
            details.append({"loc": ["path", path_field], "msg": VEHICLE_ID_ERROR if path_field == "vehicle_id" else SERVICE_ID_ERROR, "type": "value_error"})
            continue
        if patch and location in ((), [], ("body",), ["body"]) and error.get("msg") == "Value error, " + EMPTY_PATCH_ERROR:
            details.append({"loc": ["body"], "msg": EMPTY_PATCH_ERROR, "type": "value_error"})
            continue
        fields = {"confirm_removal"} if removal else _FIELDS
        field = (
            location[1] if isinstance(location, (tuple, list)) and len(location) == 2
            and location[0] == "body" and isinstance(location[1], str) and location[1] in fields else None
        )
        error_type = error.get("type")
        if not isinstance(error_type, str) or error_type not in _MESSAGES:
            error_type = "value_error"
        message = _FIELD_MESSAGES[field] if error_type == "value_error" and field else _MESSAGES[error_type]
        if patch and field in {"service_date", "service_type", "description"} and error.get("msg") == "Value error, " + REQUIRED_PATCH_ERROR:
            message = REQUIRED_PATCH_ERROR
        details.append({"loc": ["body", field] if field else ["body"], "msg": message, "type": error_type})
    return JSONResponse(status_code=422, content={"detail": details})


def _internal_error() -> Response:
    logger.error("Service history request failed unexpectedly")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


class ServiceRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request: Request):
            try:
                response = await safe_response(request)
            except Exception:
                response = _internal_error()
            response.headers["Cache-Control"] = "no-store"
            return response

        async def safe_response(request: Request):
            try:
                settings = await run_in_threadpool(authentication.request_auth_settings, request)
                if request.method in ("POST", "PATCH", "DELETE"):
                    authentication.require_mutation_policy(request, settings)
                return await handler(request)
            except authentication.AuthenticationFailure as error:
                return JSONResponse(status_code=error.status_code, content={"detail": error.detail}, headers=error.headers)
            except authentication.RequestPolicyError:
                return JSONResponse(status_code=403, content={"detail": "Request not allowed."})
            except RequestValidationError as error:
                return _validation_response(error.errors(), patch=request.method == "PATCH", removal=request.method == "DELETE")
            except VehicleNotFoundError:
                return JSONResponse(status_code=404, content={"detail": "Vehicle not found."})
            except service_queries.ServiceNotFoundError:
                return JSONResponse(status_code=404, content={"detail": "Service record not found."})
            except service_queries.ServiceEditBlockedError:
                return JSONResponse(status_code=409, content={"detail": "Service record is linked to maintenance completion and cannot be changed."})
            except service_queries.ServiceRemovalBlockedError:
                return JSONResponse(status_code=409, content={"detail": "Service record has linked data and cannot be removed."})
            except AuthConfigurationError:
                return JSONResponse(status_code=503, content={"detail": "Authentication unavailable. Please try again."})
            except (service_queries.ServiceUnavailableError, psycopg.OperationalError,
                    psycopg.InterfaceError, psycopg.errors.QueryCanceled):
                logger.warning("Service history request unavailable")
                return JSONResponse(status_code=503, content={"detail": "Service history unavailable. Please try again."})
            except HTTPException as error:
                if error.status_code == 400:
                    return _validation_response([{"type": "json_invalid", "loc": ("body",)}])
                return _internal_error()
            except Exception:
                return _internal_error()

        return safe_handler


router = APIRouter(prefix="/vehicles/{vehicle_id}/services", tags=["services"], route_class=ServiceRoute)


def _service_response(
    result: ServiceRecord | ServiceListResponse | ServiceRemovalResponse, actor: AuthenticatedSession, status_code: int,
) -> Response:
    response = JSONResponse(status_code=status_code, content=result.model_dump(mode="json"))
    authentication.attach_session_deadline(response, actor)
    return response


@router.get("", response_model=ServiceListResponse)
def list_owned_services(
    vehicle_id: VehicleId,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    prepared = None

    def prepare(result):
        nonlocal prepared
        prepared = _service_response(result, actor, 200)

    service_queries.list_services(settings, actor=actor, vehicle_id=vehicle_id, prepare_response=prepare)
    if prepared is None:
        raise RuntimeError("Service list response was not prepared")
    return prepared


@router.get("/{service_id}", response_model=ServiceRecord)
def get_owned_service(
    vehicle_id: VehicleId,
    service_id: ServiceId,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    prepared = None

    def prepare(result):
        nonlocal prepared
        prepared = _service_response(result, actor, 200)

    service_queries.get_service(settings, actor=actor, vehicle_id=vehicle_id, service_id=service_id, prepare_response=prepare)
    if prepared is None:
        raise RuntimeError("Service detail response was not prepared")
    return prepared


@router.patch("/{service_id}", response_model=ServiceRecord)
def update_owned_service(
    vehicle_id: VehicleId,
    service_id: ServiceId,
    patch: ServicePatch,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    prepared = None

    def prepare(result):
        nonlocal prepared
        prepared = _service_response(result, actor, 200)

    service_queries.update_service(settings, actor=actor, vehicle_id=vehicle_id, service_id=service_id,
                                   patch=patch, prepare_response=prepare)
    if prepared is None:
        raise RuntimeError("Service update response was not prepared")
    return prepared


@router.delete("/{service_id}", response_model=ServiceRemovalResponse)
def remove_owned_service(
    vehicle_id: VehicleId,
    service_id: ServiceId,
    confirmation: ServiceRemovalRequest,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    prepared = None

    def prepare(result):
        nonlocal prepared
        prepared = _service_response(result, actor, 200)

    service_queries.remove_service(settings, actor=actor, vehicle_id=vehicle_id, service_id=service_id,
                                   confirmation=confirmation, prepare_response=prepare)
    if prepared is None:
        raise RuntimeError("Service removal response was not prepared")
    return prepared


@router.post("", status_code=201, response_model=ServiceRecord)
def create_owned_service(
    vehicle_id: VehicleId,
    service: ServiceCreate,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    prepared = None

    def prepare(result):
        nonlocal prepared
        prepared = _service_response(result, actor, 201)

    service_queries.create_service(settings, actor=actor, vehicle_id=vehicle_id, service=service, prepare_response=prepare)
    if prepared is None:
        raise RuntimeError("Service creation response was not prepared")
    return prepared
