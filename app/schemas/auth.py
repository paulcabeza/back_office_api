import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---

class LoginRequest(BaseModel):
    email: str = Field(min_length=1)  # Accepts email or username
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


# --- User ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role_ids: list[uuid.UUID] = Field(default_factory=list)


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str | None
    email: str
    first_name: str
    last_name: str
    full_name: str
    is_active: bool
    is_superadmin: bool
    roles: list["RoleResponse"]
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None
    role_id: uuid.UUID | None = None


class UserListResponse(BaseModel):
    id: uuid.UUID
    username: str | None
    email: str
    full_name: str
    is_active: bool
    roles: list["RoleResponse"]
    created_at: datetime

    model_config = {"from_attributes": True}


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: str

    model_config = {"from_attributes": True}
