import logging

import psycopg
from fastapi import APIRouter, Depends, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.exceptions import HTTPException
from starlette.concurrency import run_in_threadpool

from app import authentication, security, session_queries, user_queries
from app.config import AuthConfigurationError, AuthSettings, Settings, get_settings
from app.schemas import LoginRequest, LogoutRequest, RegistrationRequest, RegistrationResponse, SessionResponse


logger = logging.getLogger(__name__)
_FIELDS = frozenset({"email", "password", "password_confirmation"})
_VALIDATION_MESSAGES = {
    "missing": "Field required.",
    "string_type": "Enter text.",
    "value_error": "Enter a valid value.",
    "json_invalid": "Provide valid JSON.",
    "model_attributes_type": "Provide a JSON object.",
    "model_type": "Provide a JSON object.",
}
_CREDENTIAL_MESSAGES = {
    "Enter valid Unicode characters.": "Enter valid Unicode characters.",
    "Use between 15 and 128 characters.": "Use between 15 and 128 characters.",
    "Passwords must match.": "Passwords must match.",
}


def _invalid_entry(location, message, error_type="value_error"):
    return {"loc": location, "msg": message, "type": error_type}


def _validation_response(errors):
    details = []
    for error in errors:
        location = error.get("loc", ())
        field = (
            location[1]
            if isinstance(location, (list, tuple)) and len(location) == 2
            and location[0] == "body" and isinstance(location[1], str)
            else None
        )
        safe_location = ["body", field] if field in _FIELDS else ["body"]
        error_type = error.get("type")
        if not isinstance(error_type, str) or error_type not in _VALIDATION_MESSAGES:
            error_type = "value_error"
        message = _VALIDATION_MESSAGES[error_type]
        if field == "email" and error_type == "value_error":
            message = "Enter a valid email address."
        details.append(_invalid_entry(safe_location, message, error_type))
    return JSONResponse(status_code=422, content={"detail": details})


def _credential_response(error):
    field = error.field if isinstance(error.field, str) and error.field in _FIELDS else "password"
    # Choose a constant message; never reflect an arbitrary exception string.
    reason = error.args[0] if error.args else None
    message = (
        _CREDENTIAL_MESSAGES.get(reason, "Enter valid credentials.")
        if isinstance(reason, str) else "Enter valid credentials."
    )
    detail = _invalid_entry(["body", field], message)
    return JSONResponse(status_code=422, content={"detail": [detail]})


def _internal_error():
    logger.error("Authentication request failed unexpectedly")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


class AuthenticationRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def safe_handler(request: Request):
            response = await safe_response(request)
            response.headers["Cache-Control"] = "no-store"
            return response

        async def safe_response(request: Request):
            try:
                auth_settings = await run_in_threadpool(authentication.request_auth_settings, request)
                if request.method not in ("GET", "HEAD", "OPTIONS"):
                    authentication.require_mutation_policy(request, auth_settings)
                return await handler(request)
            except authentication.AuthenticationFailure as error:
                detail = (
                    "Registration unavailable. Please try again."
                    if error.status_code == 503 and self.path.endswith("/register") else error.detail
                )
                return JSONResponse(
                    status_code=error.status_code, content={"detail": detail}, headers=error.headers
                )
            except authentication.RequestPolicyError:
                return JSONResponse(status_code=403, content={"detail": "Request not allowed."})
            except RequestValidationError as error:
                return _validation_response(error.errors())
            except security.CredentialValidationError as error:
                return _credential_response(error)
            except user_queries.DuplicateEmailError:
                return JSONResponse(
                    status_code=409,
                    content={"detail": "An account with this email already exists."},
                )
            except (AuthConfigurationError, psycopg.OperationalError, psycopg.InterfaceError, psycopg.errors.QueryCanceled):
                logger.warning("Authentication request unavailable")
                return JSONResponse(
                    status_code=503,
                    content={"detail": (
                        "Registration unavailable. Please try again."
                        if self.path.endswith("/register") else "Authentication unavailable. Please try again."
                    )},
                )
            except HTTPException as error:
                if error.status_code == 400:
                    return _validation_response([{"type": "json_invalid", "loc": ("body",)}])
                return _internal_error()
            except Exception:
                # Handle inside the route so server middleware cannot log raw exceptions.
                return _internal_error()

        return safe_handler


router = APIRouter(
    prefix="/auth", tags=["auth"], route_class=AuthenticationRoute,
)


@router.post("/register", status_code=201, response_model=RegistrationResponse)
def register_account(
    account: RegistrationRequest, settings: Settings = Depends(get_settings)
) -> RegistrationResponse:
    password_hash = security.validate_and_hash_credentials(
        account.password, account.password_confirmation
    )
    user = user_queries.create_user(
        settings, email=account.email, password_hash=password_hash
    )
    return RegistrationResponse(id=user[0], email=user[1], created_at=user[2])


@router.post("/login", response_model=SessionResponse)
def login(
    credentials: LoginRequest, request: Request,
    settings: Settings = Depends(get_settings),
    auth_settings: AuthSettings = Depends(authentication.request_auth_settings),
) -> Response:
    user = user_queries.verify_user_credentials(settings, credentials)
    if user is None:
        return JSONResponse(status_code=401, content={"detail": "Invalid email or password."})
    prepared = None

    def prepare_response(issued: session_queries.IssuedSession):
        nonlocal prepared
        prepared = JSONResponse(content=issued.session.public_response().model_dump(mode="json"))
        authentication.set_session_cookie(prepared, issued.token, request, auth_settings)

    session_queries.create_session(
        settings, user=user, presented_token=authentication.read_session_token(request),
        prepare_response=prepare_response,
    )
    if prepared is None:
        raise RuntimeError("Session response was not prepared")
    return prepared


@router.get("/session", response_model=SessionResponse)
def current_session(
    actor: session_queries.AuthenticatedSession = Depends(authentication.require_authenticated_session),
) -> SessionResponse:
    return actor.public_response()


@router.post("/logout", status_code=204)
def logout(
    body: LogoutRequest, request: Request, settings: Settings = Depends(get_settings),
    auth_settings: AuthSettings = Depends(authentication.request_auth_settings),
) -> Response:
    response = Response(status_code=204)
    authentication.clear_session_cookie(response, request, auth_settings)
    session_queries.revoke_session(settings, authentication.read_session_token(request))
    return response
