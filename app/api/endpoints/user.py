from fastapi import APIRouter, Depends, HTTPException, status
from starlette.status import HTTP_200_OK
from typing import Literal, Annotated
from app.core.dependencies import (
    get_user_dep, get_users_dep, delete_user_dep, update_user_dep, create_user_dep, authenticate_user, get_user_id_dep
)
from app.core.authorization import (
    get_current_user, requires_admin, requires_read_users, requires_write_users, requires_delete_users
)
from app.schema.user import ListUsersResponse, UpdateUserResponse, User
from app.schema.auth import get_login_form, LoginForm
from app.model.user import UserDB
from app.schema.user import Token
from app.core.security import create_access_token, bearer_scheme
from datetime import timedelta
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES



router = APIRouter()


# Create a new user (Public endpoint - anyone can register)
@router.post(
    '/users',
    status_code=HTTP_200_OK,
    response_description='create user',
    name='user:create',
    response_model_exclude_none=True,
    response_model=User,
    tags=['USER V1']
)
def create_user(
    user_created: User= Depends(create_user_dep)
):
    """Create a new user account (Public registration)"""
    return user_created


# Login to generate access token (Public endpoint)
@router.post(
    '/token',
    tags=['Authentication']
)
async def login_for_access_token(
        form_data: LoginForm = Depends(get_login_form),
) -> Token:
    """Authenticate user and get access token - Only requires username and password"""
    user = authenticate_user(username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect ID or password',
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


# Get current logged-in user details (Protected - requires authentication)
@router.get(
    '/users/me/',
    response_model=User,
    summary="Get current user",
    description="Get current authenticated user information (requires Bearer token)",
    dependencies=[Depends(bearer_scheme)],
    tags=['USER V1']
)
async def read_users_me(
        current_user: UserDB = Depends(get_current_user),
):
    """Get current user's profile information"""
    return User(
        user_id=str(current_user.id),
        email=current_user.email,
        username=current_user.username,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )


# Get user by ID (Protected - requires read_users permission)
@router.get(
    '/users/{userId}',
    status_code=HTTP_200_OK,
    response_description='get user by id',
    name='user: get_by_id',
    response_model_exclude_none=True,
    response_model=User,
    summary="Get user by ID",
    description="Get user information by ID (requires Bearer token and read_users permission)",
    dependencies=[Depends(bearer_scheme)],
    tags=['USER V1']
)
def get_user_by_id(
        current_user: UserDB = Depends(requires_read_users),
        userId: str = Depends(get_user_id_dep),
):
    """Get user information by ID (requires read_users permission)"""
    return userId


# Sort options for user list
SortOrder = Literal["created_at_asc", "created_at_desc", "name_asc", "name_desc"]


# Get list of users with sorting options (Protected - requires read_users permission)
@router.get(
    '/users',
    status_code=HTTP_200_OK,
    response_description='get users list',
    name='user: list_users',
    response_model_exclude_none=True,
    response_model=ListUsersResponse,
    summary="List users",
    description="Get list of all users (requires Bearer token and read_users permission)",
    dependencies=[Depends(bearer_scheme)],
    tags=['USER V1']
)
def get_users_list(
    current_user: UserDB = Depends(requires_read_users),
    usersList: ListUsersResponse= Depends(get_users_dep),
):
    """Get list of all users (requires read_users permission)"""
    return usersList


# Delete user by ID (Protected - requires delete_users permission)
@router.delete(
    '/users/{userId}',
    status_code=HTTP_200_OK,
    response_description='delete user by id',
    name='user: delete_by_id',
    response_model_exclude_none=True,
    summary="Delete user",
    description="Delete user by ID (requires Bearer token and delete_users permission)",
    dependencies=[Depends(bearer_scheme)],
    tags=['USER V1']
)
def delete_user_by_id(
        current_user: UserDB = Depends(requires_delete_users),
        userId = Depends(delete_user_dep),
):
    """Delete user by ID (requires delete_users permission)"""
    return userId


# Update user by ID (Protected - requires write_users permission)
@router.patch(
    '/users/{userId}',
    status_code=HTTP_200_OK,
    response_description='update user',
    name='user: update',
    response_model_exclude_none=True,
    summary="Update user",
    description="Update user information by ID (requires Bearer token and write_users permission)",
    dependencies=[Depends(bearer_scheme)],
    tags=['USER V1']
)
def update_user(
        current_user: UserDB = Depends(requires_write_users),
        userId=Depends(update_user_dep),
) -> UpdateUserResponse:
    """Update user information by ID (requires write_users permission)"""
    return userId