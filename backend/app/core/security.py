import time
import jwt
import bcrypt

# Patch bcrypt for passlib compatibility with bcrypt >= 4.0/5.0
if not hasattr(bcrypt, "__about__"):
    class BcryptAbout:
        __version__ = getattr(bcrypt, "__version__", "4.0.0")
    bcrypt.__about__ = BcryptAbout()

_orig_hashpw = bcrypt.hashpw
def _safe_hashpw(password, salt):
    if isinstance(password, bytes) and len(password) > 72:
        password = password[:72]
    return _orig_hashpw(password, salt)
bcrypt.hashpw = _safe_hashpw

from passlib.context import CryptContext
from backend.app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies plaintext password against a stored bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generates a bcrypt hash for a plaintext password."""
    return pwd_context.hash(password)


def create_access_token(
    client_id: str,
    user_role: str = "Admin",
    assigned_tenants: list = None,
    expires_in_seconds: int = 86400
) -> str:
    """Creates a signed JWT with client_id, user_role, and assigned_tenants embedded as claims."""
    now = int(time.time())
    if assigned_tenants is None:
        assigned_tenants = ["client_abc", "client_xyz"]
    payload = {
        "sub": client_id,
        "client_id": client_id,
        "role": user_role,
        "user_role": user_role,
        "assigned_tenants": assigned_tenants,
        "iat": now,
        "exp": now + expires_in_seconds
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_access_token(token: str) -> dict:
    """Decodes and validates a signed JWT token."""
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
