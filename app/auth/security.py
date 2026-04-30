import bcrypt


def hash_password(password: str) -> str:
    # bcrypt has a 72-byte limit on the input; truncate defensively for
    # very long passwords so hashpw doesn't raise.
    return bcrypt.hashpw(password.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:72], password_hash.encode("utf-8"))
    except ValueError:
        return False
