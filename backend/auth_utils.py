"""
Password hashing and user authentication helpers.

Passwords are hashed with bcrypt and never stored or returned in plaintext.
Legacy rows that predate hashing are migrated transparently on first login.
"""

import re

import bcrypt


BCRYPT_ROUNDS = 12
# bcrypt truncates at 72 bytes; reject longer input rather than silently ignoring it.
MAX_PASSWORD_BYTES = 72
MIN_PASSWORD_LENGTH = 6

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(password: str) -> str:
    """Hash a plaintext password. Returns a utf-8 bcrypt digest."""
    raw = password.encode("utf-8")
    if len(raw) > MAX_PASSWORD_BYTES:
        raise ValueError("Password must be at most 72 bytes")
    return bcrypt.hashpw(raw, bcrypt.gensalt(rounds=BCRYPT_ROUNDS)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Check a plaintext password against a bcrypt digest."""
    if not password or not hashed:
        return False
    raw = password.encode("utf-8")
    if len(raw) > MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(raw, hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # Not a valid bcrypt digest - e.g. a legacy plaintext row.
        return False


def is_hashed(value: str) -> bool:
    """True if the stored value looks like a bcrypt digest."""
    return isinstance(value, str) and value.startswith(("$2a$", "$2b$", "$2y$"))


def validate_credentials(email: str, password: str, name: str = None):
    """Validate signup input. Returns an error string, or None if valid."""
    if not email or not EMAIL_RE.match(email):
        return "Enter a valid email address"
    if not password or len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters"
    if len(password.encode("utf-8")) > MAX_PASSWORD_BYTES:
        return "Password must be at most 72 bytes"
    if name is not None and not name.strip():
        return "Name is required"
    return None


def public_user(doc: dict) -> dict:
    """Strip credentials and Mongo internals before returning a user to a client."""
    if not doc:
        return None
    return {
        "id": str(doc.get("_id", "")),
        "email": doc.get("email"),
        "name": doc.get("name"),
        "role": doc.get("role", "auditor"),
        "organization": doc.get("organization", "GST Audit Division"),
        "createdAt": doc.get("createdAt"),
    }


def migrate_plaintext_passwords(users_col) -> int:
    """Rehash any stored plaintext passwords in place.

    Existing installs seeded plaintext credentials. This runs at startup so an
    upgrade does not lock those accounts out or leave readable passwords in the
    database.
    """
    migrated = 0
    for user in users_col.find({}, {"_id": 1, "password": 1}):
        stored = user.get("password")
        if stored and not is_hashed(stored):
            users_col.update_one(
                {"_id": user["_id"]},
                {"$set": {"password": hash_password(stored)}},
            )
            migrated += 1
    if migrated:
        print(f"[OK] Migrated {migrated} plaintext password(s) to bcrypt")
    return migrated
