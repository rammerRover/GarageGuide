import logging

import psycopg
from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException

from app import authentication, service_part_queries as queries
from app.config import AuthConfigurationError, Settings, get_settings
from app.service_part_schemas import (
    PART_REMOVAL_ERROR, SERVICE_PART_ID_ERROR, CatalogPartLookup, CatalogPartPreview,
    ServicePartCreate, ServicePartId, ServicePartListResponse, ServicePartRemovalRequest,
    ServicePartRemovalResponse, ServicePartSnapshot,
)
from app.service_queries import ServiceNotFoundError
from app.service_schemas import SERVICE_ID_ERROR, ServiceId
from app.session_queries import AuthenticatedSession
from app.vehicle_queries import VehicleNotFoundError
from app.vehicle_schemas import VEHICLE_ID_ERROR, VehicleId


logger = logging.getLogger(__name__)
_PATH_ERRORS = {"vehicle_id": VEHICLE_ID_ERROR, "service_id": SERVICE_ID_ERROR, "snapshot_id": SERVICE_PART_ID_ERROR}
_FIELDS = {
    "source": "Choose manual or catalog entry.",
    "name": "Enter nonblank text with valid Unicode and no NUL.",
    "part_number": "Enter valid Unicode characters without NUL.",
    "manufacturer": "Enter valid Unicode characters without NUL.",
    "quantity": "Enter a whole number from 1 through 2147483647.",
    "notes": "Enter valid Unicode characters without NUL.",
    "preview": "Look up and review a catalog part before saving.",
    "confirm_removal": PART_REMOVAL_ERROR,
}
_PREVIEW_FIELDS = frozenset({"id", "manufacturer", "part_number", "name", "category"})
_TYPES = {
    "missing": "Field required.", "string_type": "Enter text.",
    "extra_forbidden": "Unexpected fields are not allowed.",
    "json_invalid": "Provide valid JSON.", "model_type": "Provide a JSON object.",
    "model_attributes_type": "Provide a JSON object.", "value_error": "Enter a valid value.",
}


def _validation_response(errors) -> Response:
    details = []
    for error in errors:
        loc = error.get("loc", ())
        if len(loc) == 2 and loc[0] == "path" and loc[1] in _PATH_ERRORS:
            details.append({"loc": ["path", loc[1]], "msg": _PATH_ERRORS[loc[1]], "type": "value_error"})
            continue
        kind = error.get("type")
        location = ["body"]
        field = None
        tail = list(loc[1:]) if loc and loc[0] == "body" else []
        if tail and tail[0] in ("manual", "catalog"):
            tail = tail[1:]
        if kind in ("union_tag_invalid", "union_tag_not_found"):
            field, kind = "source", "value_error"
            location.append(field)
        elif len(tail) == 1 and tail[0] in _FIELDS:
            field = tail[0]
            location.append(field)
        elif len(tail) == 2 and tail[0] == "preview" and tail[1] in _PREVIEW_FIELDS:
            field = "preview"
            location.extend(tail)
        if kind not in _TYPES:
            kind = "value_error"
        message = _FIELDS[field] if field and kind == "value_error" else _TYPES[kind]
        details.append({"loc": location, "msg": message, "type": kind})
    return JSONResponse(status_code=422, content={"detail": details})


def _internal_error() -> Response:
    logger.error("Service parts request failed unexpectedly")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


class ServicePartRoute(APIRoute):
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
                if request.method in ("POST", "DELETE"):
                    authentication.require_mutation_policy(request, settings)
                return await handler(request)
            except authentication.AuthenticationFailure as error:
                return JSONResponse(status_code=error.status_code, content={"detail": error.detail}, headers=error.headers)
            except authentication.RequestPolicyError:
                return JSONResponse(status_code=403, content={"detail": "Request not allowed."})
            except RequestValidationError as error:
                return _validation_response(error.errors())
            except (VehicleNotFoundError, ServiceNotFoundError, queries.ServicePartNotFoundError,
                    queries.CatalogPartNotFoundError) as error:
                return JSONResponse(status_code=404, content={"detail": str(error)})
            except queries.CatalogPreviewConflictError as error:
                return JSONResponse(status_code=409, content={"detail": str(error)})
            except AuthConfigurationError:
                return JSONResponse(status_code=503, content={"detail": "Authentication unavailable. Please try again."})
            except (queries.ServicePartsUnavailableError, psycopg.OperationalError,
                    psycopg.InterfaceError, psycopg.errors.QueryCanceled):
                logger.warning("Service parts request unavailable")
                return JSONResponse(status_code=503, content={"detail": "Service parts unavailable. Please try again."})
            except HTTPException as error:
                if error.status_code == 400:
                    return _validation_response([{"type": "json_invalid", "loc": ("body",)}])
                return _internal_error()
            except Exception:
                return _internal_error()

        return safe_handler


router = APIRouter(prefix="/vehicles/{vehicle_id}/services/{service_id}/parts",
                   tags=["service parts"], route_class=ServicePartRoute)


def _respond(query, settings, actor, vehicle_id, service_id, *, status_code=200, **values):
    prepared = None
    def prepare(result):
        nonlocal prepared
        prepared = JSONResponse(status_code=status_code, content=result.model_dump(mode="json"))
        authentication.attach_session_deadline(prepared, actor)
    query(settings, actor=actor, vehicle_id=vehicle_id, service_id=service_id,
          prepare_response=prepare, **values)
    if prepared is None:
        raise RuntimeError("Service parts response was not prepared")
    return prepared


@router.get("", response_model=ServicePartListResponse)
def list_owned_parts(vehicle_id: VehicleId, service_id: ServiceId,
                     actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
                     settings: Settings = Depends(get_settings)) -> Response:
    return _respond(queries.list_service_parts, settings, actor, vehicle_id, service_id)


@router.post("/lookup", response_model=CatalogPartPreview)
def lookup_owned_service_part(vehicle_id: VehicleId, service_id: ServiceId, lookup: CatalogPartLookup,
                              actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
                              settings: Settings = Depends(get_settings)) -> Response:
    return _respond(queries.lookup_catalog_part, settings, actor, vehicle_id, service_id, lookup=lookup)


@router.post("", status_code=201, response_model=ServicePartSnapshot)
def attach_owned_part(vehicle_id: VehicleId, service_id: ServiceId, part: ServicePartCreate,
                      actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
                      settings: Settings = Depends(get_settings)) -> Response:
    return _respond(queries.attach_service_part, settings, actor, vehicle_id, service_id, part=part, status_code=201)


@router.delete("/{snapshot_id}", response_model=ServicePartRemovalResponse)
def remove_owned_part(vehicle_id: VehicleId, service_id: ServiceId, snapshot_id: ServicePartId,
                      confirmation: ServicePartRemovalRequest,
                      actor: AuthenticatedSession = Depends(authentication.require_authenticated_session),
                      settings: Settings = Depends(get_settings)) -> Response:
    return _respond(queries.remove_service_part, settings, actor, vehicle_id, service_id,
                    snapshot_id=snapshot_id, confirmation=confirmation)
