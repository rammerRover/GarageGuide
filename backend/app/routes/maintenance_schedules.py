import logging

from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import ValidationError
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from app import authentication, maintenance_schedule_queries as queries
from app.config import Settings, get_settings
from app.maintenance_schedule_schemas import (
    AT_LEAST_ONE_PAIR_ERROR, BASELINE_DATE_ERROR, EMPTY_PATCH_ERROR, REVIEW_IDS_ERROR,
    SCHEDULE_ID_ERROR, MaintenanceSchedule, MaintenanceScheduleCreate,
    MaintenanceScheduleListResponse, MaintenanceSchedulePatch, ScheduleId,
)
from app.maintenance_status import MaintenanceStatusResponse
from app.session_queries import AuthenticatedSession
from app.vehicle_queries import VehicleNotFoundError
from app.vehicle_schemas import READING_ERROR, TEXT_ERROR, VEHICLE_ID_ERROR, VehicleId


logger = logging.getLogger(__name__)
_PATH_ERRORS = {"vehicle_id": VEHICLE_ID_ERROR, "schedule_id": SCHEDULE_ID_ERROR}
_FIELD_ERRORS = {
    "name": TEXT_ERROR,
    "interval_days": "Enter a whole number from 1 through 2147483647.",
    "interval_miles": "Enter a positive decimal string with at most one decimal place, up to 99999999999.9.",
    "interval_hours": "Enter a positive decimal string with at most one decimal place, up to 99999999999.9.",
    "baseline_date": BASELINE_DATE_ERROR,
    "baseline_mileage": READING_ERROR,
    "baseline_hours": READING_ERROR,
    "source_notes": "Enter valid Unicode characters without NUL.",
    "reviewed_duplicate_ids": REVIEW_IDS_ERROR,
}
_COMPLETE_ERRORS = {
    "interval_days": AT_LEAST_ONE_PAIR_ERROR,
    "baseline_date": "Set both the day interval and its baseline date on or before today, or clear both.",
    "baseline_mileage": "Set both the mileage interval and its baseline, or clear both.",
    "baseline_hours": "Set both the operating-hour interval and its baseline, or clear both.",
}
_ERROR_MESSAGES = {
    "missing": "Field required.",
    "extra_forbidden": "Unexpected fields are not allowed.",
    "json_invalid": "Provide valid JSON.",
    "model_type": "Provide a JSON object.",
    "model_attributes_type": "Provide a JSON object.",
}


def _validation_response(errors) -> Response:
    details = []
    for error in errors:
        loc = tuple(error["loc"])
        kind = error["type"]
        if len(loc) == 2 and loc[0] == "path" and loc[1] in _PATH_ERRORS:
            details.append({"loc": list(loc), "msg": _PATH_ERRORS[loc[1]], "type": "value_error"})
            continue

        field = None
        if len(loc) >= 2 and loc[0] == "body" and loc[1] in _FIELD_ERRORS and kind != "extra_forbidden":
            field = loc[1]
        message = _ERROR_MESSAGES.get(kind)
        if message is None:
            if kind == "schedule_value" and field in _COMPLETE_ERRORS:
                message = _COMPLETE_ERRORS[field]
            elif loc == ("body",) and error.get("msg") == f"Value error, {EMPTY_PATCH_ERROR}":
                message = EMPTY_PATCH_ERROR
            else:
                message = _FIELD_ERRORS.get(field, "Enter a valid value.")
            kind = "value_error"
        details.append({"loc": ["body", field] if field else ["body"], "msg": message, "type": kind})
    return JSONResponse(status_code=422, content={"detail": details})


class MaintenanceScheduleRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request: Request):
            try:
                return await safe_response(request)
            except Exception:
                logger.error("Maintenance schedule request failed unexpectedly")
                return JSONResponse(status_code=500, content={"detail": "Internal server error"})

        async def safe_response(request: Request):
            try:
                if request.method in ("POST", "PATCH"):
                    settings = await run_in_threadpool(authentication.request_auth_settings, request)
                    authentication.require_mutation_policy(request, settings)
                return await handler(request)
            except authentication.AuthenticationFailure as error:
                return JSONResponse(status_code=error.status_code, content={"detail": error.detail}, headers=error.headers)
            except authentication.RequestPolicyError:
                return JSONResponse(status_code=403, content={"detail": "Request not allowed."})
            except RequestValidationError as error:
                return _validation_response(error.errors())
            except ValidationError as error:
                errors = error.errors(include_input=False, include_context=False, include_url=False)
                # Only the locked merge produces schedule_value errors here. Invalid
                # stored rows and response validation still use the generic 500.
                if request.method != "PATCH" or not errors or any(item["type"] != "schedule_value" for item in errors):
                    raise
                return _validation_response([
                    {**item, "loc": ("body", *item["loc"])} for item in errors
                ])
            except (VehicleNotFoundError, queries.MaintenanceScheduleNotFoundError):
                detail = "Maintenance schedule not found." if request.method == "PATCH" else "Vehicle not found."
                return JSONResponse(status_code=404, content={"detail": detail})
            except queries.DuplicateScheduleNameError as error:
                return JSONResponse(status_code=409, content=error.response.model_dump(mode="json"))
            except queries.MaintenanceScheduleUnavailableError:
                logger.warning("Maintenance schedule request unavailable")
                return JSONResponse(status_code=503, content={"detail": "Maintenance schedules unavailable. Please try again."})
            except HTTPException as error:
                if error.status_code == 400:
                    return _validation_response([{"type": "json_invalid", "loc": ("body",)}])
                raise

        return safe_handler


router = APIRouter(
    prefix="/vehicles/{vehicle_id}/maintenance-schedules",
    tags=["maintenance schedules"], route_class=MaintenanceScheduleRoute,
)


def _respond(query, settings, actor, vehicle_id, *, status_code=200, **values) -> Response:
    prepared = None

    def prepare(result):
        nonlocal prepared
        prepared = JSONResponse(status_code=status_code, content=result.model_dump(mode="json"))
        authentication.attach_session_deadline(prepared, actor)

    query(settings, actor=actor, vehicle_id=vehicle_id, prepare_response=prepare, **values)
    if prepared is None:
        raise RuntimeError("Maintenance schedule response was not prepared")
    return prepared


@router.get("", response_model=MaintenanceScheduleListResponse)
def list_owned_schedules(
    vehicle_id: VehicleId,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    return _respond(queries.list_maintenance_schedules, settings, actor, vehicle_id)


@router.get("/status", response_model=MaintenanceStatusResponse)
def get_owned_schedule_status(
    vehicle_id: VehicleId,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    return _respond(queries.get_maintenance_status, settings, actor, vehicle_id)


@router.post("", status_code=201, response_model=MaintenanceSchedule)
def create_owned_schedule(
    vehicle_id: VehicleId, schedule: MaintenanceScheduleCreate,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    return _respond(queries.create_maintenance_schedule, settings, actor, vehicle_id, schedule=schedule, status_code=201)


@router.patch("/{schedule_id}", response_model=MaintenanceSchedule)
def update_owned_schedule(
    vehicle_id: VehicleId, schedule_id: ScheduleId, patch: MaintenanceSchedulePatch,
    actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    return _respond(queries.update_maintenance_schedule, settings, actor, vehicle_id, schedule_id=schedule_id, patch=patch)
