
from datetime import datetime, timedelta, timezone
from typing import Any
from dataclasses import dataclass
import jwt

from constants.constants import TOKEN_ALGO, TOKEN_SECRET, TOKEN_VALIDITY_DURATION_HOURS

@dataclass
class UserTokenInfo:
    user_id: int
    expiry: datetime

def make_user_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "uid": user_id,
        "exp": int((now + timedelta(hours=TOKEN_VALIDITY_DURATION_HOURS)).timestamp()),
    }
    return jwt.encode(payload, TOKEN_SECRET, algorithm=TOKEN_ALGO)

def decode_user_token(token: str) -> UserTokenInfo | None:
    try:
        decoded = jwt.decode(token, TOKEN_SECRET, algorithms=[TOKEN_ALGO])
        uid = decoded.get("uid")
        exp = decoded.get("exp")
        if uid is None or exp is None: return None
        return UserTokenInfo(user_id=uid, expiry=datetime.fromtimestamp(exp, timezone.utc))
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None