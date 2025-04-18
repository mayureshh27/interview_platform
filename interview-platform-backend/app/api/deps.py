# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenPayload
from app.core import security

# This points to the endpoint that issues the token (the login endpoint)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get the current authenticated user based on the JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_token(token)
    if payload is None:
        raise credentials_exception

    # 'sub' typically holds the user identifier (e.g., email or ID)
    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    token_data = TokenPayload(sub=username)

    user = db.query(User).filter(User.email == token_data.sub).first()
    if user is None:
        # Or if using ID in token: user = db.query(User).filter(User.id == token_data.sub).first()
        raise credentials_exception

    if not user.is_active:
         raise HTTPException(status_code=400, detail="Inactive user")

    return user

def get_current_active_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency to ensure the current user is an active admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user