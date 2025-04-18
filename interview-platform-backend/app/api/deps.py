from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError

from app.core.config import settings
from app.db.session import get_db, get_async_db
from app.models.user import User
from app.schemas.token import TokenPayload
from app.core import security

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

# Synchronous DB dependency (for compatibility)
def get_db_session() -> Session:
    return next(get_db())

# Asynchronous DB dependency (for new code)
async def get_async_db_session() -> AsyncSession:
    async for session in get_async_db():
        return session

# Current user dependency for synchronous endpoints (existing)
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
        raise credentials_exception

    if not user.is_active:
         raise HTTPException(status_code=400, detail="Inactive user")

    return user

# Current user dependency for async endpoints (new)
async def get_current_user_async(
    db: AsyncSession = Depends(get_async_db_session), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Async dependency to get the current authenticated user based on the JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_token(token)
    if payload is None:
        raise credentials_exception

    username: str | None = payload.get("sub")
    if username is None:
        raise credentials_exception

    token_data = TokenPayload(sub=username)
    
    # Async query using SQLAlchemy 2.0 style
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.email == token_data.sub))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception

    if not user.is_active:
         raise HTTPException(status_code=400, detail="Inactive user")

    return user

# Keep existing get_current_active_admin
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

# Add async version
async def get_current_active_admin_async(
    current_user: User = Depends(get_current_user_async),
) -> User:
    """
    Async dependency to ensure the current user is an active admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user