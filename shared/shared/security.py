"""Password hashing using bcrypt.

Uses the ``bcrypt`` package directly (passlib is unmaintained and breaks with
bcrypt 4.x). bcrypt only considers the first 72 bytes of the password, so we
truncate explicitly to avoid backend errors on longer inputs.
"""

import bcrypt

_MAX_BYTES = 72


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_encode(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(_encode(password), hashed.encode("utf-8"))
