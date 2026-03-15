import bcrypt
import base64

def hash_raw_password(raw_password: str, salt: str | None = None) -> tuple[str, str]:
    salt_raw = bcrypt.gensalt() if salt is None else base64.b64decode(salt.encode('utf-8'))
    hashed = bcrypt.hashpw(raw_password.encode('utf-8'), salt_raw)
    return hashed.decode('utf-8'), base64.b64encode(salt_raw).decode('utf-8')