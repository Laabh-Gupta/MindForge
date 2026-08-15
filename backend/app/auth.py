import os

import jwt
from dotenv import load_dotenv
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient


load_dotenv()

security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL")

if not SUPABASE_URL:
    raise RuntimeError("SUPABASE_URL is not set")


SUPABASE_JWKS_URL = (
    f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
)

SUPABASE_JWT_ISSUER = (
    f"{SUPABASE_URL}/auth/v1"
)

jwks_client = PyJWKClient(SUPABASE_JWKS_URL)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> str:

    token = credentials.credentials

    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
            issuer=SUPABASE_JWT_ISSUER,
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: user ID missing",
            )

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Token has expired",
        )

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )

    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Could not verify authentication token",
        )