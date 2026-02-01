import secrets
from starlette.requests import Request

CSRF_KEY = "csrf_token"

def ensure_csrf_token(request: Request) -> str:
    token = request.session.get(CSRF_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        request.session[CSRF_KEY] = token
    return token

def validate_csrf(request: Request, token_from_form: str) -> bool:
    token = request.session.get(CSRF_KEY)
    if not token or not token_from_form:
        return False
    return secrets.compare_digest(token, token_from_form)
