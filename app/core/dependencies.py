from typing import AsyncGenerator, Callable, Type, Optional, Literal
from fastapi import Depends, Body, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pymongo import MongoClient
import pymongo
from starlette.requests import Request
from pydantic import conint
import jwt
from jwt import InvalidTokenError

from app.repository.base import BaseRepository
from app.repository.user import UserRepository
from app.model.user import UserDB
from app.schema.user import (
    ListUsersResponse, DeleteUserResponse,
    CreateUserRequest, UpdateUserRequest,
    UpdateUserResponse, TokenData, User
)
from app.core.config import (
    MONGO_COLLECTION_USERS, SECRET_KEY, ALGORITHM, MONGODB_URL
)
from app.core.security import bearer_scheme, verify_password, get_password_hash


# ✅ Dependency: Get MongoDB client from app state
def _get_mongo_client(request: Request) -> MongoClient:
    return request.app.state.mongo_client


# ✅ Dependency: Proper async repo provider
def get_mongodb_repo(repo_type: Type[BaseRepository]) -> Callable:
    async def _get_repo(
        mongo_client: MongoClient = Depends(_get_mongo_client),
    ) -> AsyncGenerator[BaseRepository, None]:
        yield repo_type(mongo_client)

    return _get_repo


# ✅ Fetch user by username (used during authentication)
def get_user(username: str):
    mongo_client = MongoClient(MONGODB_URL)
    user_repo = UserRepository(mongo_client)
    return user_repo.get_by_name(MONGO_COLLECTION_USERS, username)


# ✅ Authenticate user credentials
def authenticate_user(username: str, password: str):
    user = get_user(username=username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# ✅ Create user (used in /users endpoint)
async def create_user_dep(
    create_req: CreateUserRequest = Body(...),
    user_repo: UserRepository = Depends(get_mongodb_repo(UserRepository))
) -> User:
    user_in_db = UserDB(
        email=create_req.email,
        hashed_password=get_password_hash(create_req.password),
        username=create_req.username,
        is_active=True
    )

    # Insert into MongoDB
    user_created = user_repo.create(model=user_in_db, collection=MONGO_COLLECTION_USERS)

    return User(
        user_id=str(user_created.id),
        email=user_created.email,
        username=user_created.username,
        is_active=user_created.is_active,
        created_at=user_created.created_at
    )


# ✅ Extract user from JWT token
async def get_user_dep(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception

    return User(
        user_id=str(user.id),
        email=user.email,
        username=user.username,
        created_at=user.created_at
    )


# ✅ Get user by ID
async def get_user_id_dep(
    ID: str,
    user_repo: UserRepository = Depends(get_mongodb_repo(UserRepository))
) -> User:
    user_in_db = user_repo.get_by_id(MONGO_COLLECTION_USERS, ID)
    if user_in_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found.')

    return User(
        user_id=str(user_in_db.id),
        email=user_in_db.email,
        username=user_in_db.username,
        is_active=user_in_db.is_active,
        created_at=user_in_db.created_at
    )


# ✅ List all users (with sorting/pagination)
async def get_users_dep(
    sort: Literal["created_at_asc", "created_at_desc", "name_asc", "name_desc"] = None,
    page: Optional[int] = 1,
    limit: int = 10,
    user_repo: UserRepository = Depends(get_mongodb_repo(UserRepository))
) -> ListUsersResponse:
    page = conint(ge=1)(page)
    limit = conint(ge=5, multiple_of=5)(limit)

    sort_field, sort_order = 'created_at', pymongo.DESCENDING
    if sort == "created_at_asc":
        sort_field, sort_order = 'created_at', pymongo.ASCENDING
    elif sort == "name_asc":
        sort_field, sort_order = 'name', pymongo.ASCENDING
    elif sort == "name_desc":
        sort_field, sort_order = 'name', pymongo.DESCENDING

    user_list_db, total = user_repo.get_list(
        collection=MONGO_COLLECTION_USERS,
        sort_field=sort_field,
        sort_order=sort_order,
        skip=(page - 1) * limit,
        limit=limit
    )

    return ListUsersResponse(
        users=[
            User(
                user_id=str(u.id),
                email=u.email,
                username=u.username,
                is_active=u.is_active,
                created_at=u.created_at
            )
            for u in user_list_db
        ],
        meta={"page": page, "limit": limit, "total": total}
    )


# ✅ Delete user by ID
async def delete_user_dep(
    ID: str,
    user_repo: UserRepository = Depends(get_mongodb_repo(UserRepository))
):
    user_in_db = user_repo.get_by_id(MONGO_COLLECTION_USERS, ID)
    if user_in_db is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found.')

    user_repo.delete(MONGO_COLLECTION_USERS, ID)
    delete_user_response = DeleteUserResponse(user_id=str(user_in_db.id))
    return f"User {delete_user_response} deleted successfully."


# ✅ Update user
async def update_user_dep(
    ID: str,
    user_repo: UserRepository = Depends(get_mongodb_repo(UserRepository)),
    req: UpdateUserRequest = None
) -> UpdateUserResponse:
    update_user = user_repo.update(MONGO_COLLECTION_USERS, id=ID, req=req)
    return UpdateUserResponse(
        user_id=str(update_user.id),
        email=update_user.email,
        name=update_user.name,
        created_at=update_user.created_at
    )
