"""API Dependencies - Dependency Injection"""
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.security import validate_api_key
from app.core.guest_auth import authenticate_guest_user
from app.models.guest_user import GuestUser

# Type aliases for cleaner code
DBSession = Annotated[AsyncSession, Depends(get_db)]
APIKey = Annotated[str, Depends(validate_api_key)]
GuestUserDep = Annotated[GuestUser, Depends(authenticate_guest_user)]
