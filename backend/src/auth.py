import os
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ADMIN_JWT_SECRET = os.getenv("ADMIN_JWT_SECRET", "change-me-in-production")
ADMIN_JWT_ALGORITHM = "HS256"
ADMIN_TOKEN_TTL = timedelta(seconds=5)

bearer_scheme = HTTPBearer(auto_error=True)


def create_access_token() -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": "admin",
        "iat": int(now.timestamp()),
        "exp": int((now + ADMIN_TOKEN_TTL).timestamp()),
    }
    return jwt.encode(
        payload,
        ADMIN_JWT_SECRET,
        algorithm=ADMIN_JWT_ALGORITHM,
    )    


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            ADMIN_JWT_SECRET,
            algorithms=[ADMIN_JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
    if payload.get("sub") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid subject",
        )
    return payload
