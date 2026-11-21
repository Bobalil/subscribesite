import hashlib
import hmac
import secrets

from .config import settings


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"{salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        salt, digest = stored.split("$", 1)
    except ValueError:
        return False
    calc = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return hmac.compare_digest(calc, digest)


def sign_session(user_id: int) -> str:
    raw = f"{user_id}.{secrets.token_hex(8)}"
    sig = hmac.new(settings.app_secret.encode(), raw.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{raw}.{sig}"


def parse_session(token: str) -> int | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    user_id, nonce, sig = parts
    raw = f"{user_id}.{nonce}"
    expected = hmac.new(settings.app_secret.encode(), raw.encode(), hashlib.sha256).hexdigest()[:32]
    if not hmac.compare_digest(sig, expected):
        return None
    try:
        return int(user_id)
    except ValueError:
        return None