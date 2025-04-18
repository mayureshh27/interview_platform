# app/api/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any

from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.models.user import User
from app.core import security
from app.api import deps # Import deps to use get_current_user

router = APIRouter()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
    # Optional: Make user creation require admin privileges
    # current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Create new user.
    """
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    hashed_password = security.get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_active=user_in.is_active,
        is_admin=False # Default new users are not admins
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    # Require authentication to list users
    current_user: User = Depends(deps.get_current_user)
    # Optional: Require admin privileges to list users
    # current_user: models.User = Depends(deps.get_current_active_admin),
) -> Any:
    """
    Retrieve users.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def read_user_by_id(
    user_id: int,
    db: Session = Depends(get_db),
    # Require authentication to get user details
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Get a specific user by id.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Optional: Add logic here if users should only be able to see their own profile
    # unless they are admin.
    # if user.id != current_user.id and not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="Not enough permissions")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
) -> Any:
    """
    Update a user. Only admins or the user themselves can update.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check permissions
    if user.id != current_user.id and not current_user.is_admin:
         raise HTTPException(status_code=403, detail="Not enough permissions to update this user")

    update_data = user_in.dict(exclude_unset=True)

    # Hash password if it's being updated
    if "password" in update_data and update_data["password"]:
        hashed_password = security.get_password_hash(update_data["password"])
        del update_data["password"] # remove plain password from dict
        user.hashed_password = hashed_password

    # Prevent non-admins from making themselves admin or changing others' admin status
    if "is_admin" in update_data and not current_user.is_admin:
        del update_data["is_admin"]

    for field, value in update_data.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user