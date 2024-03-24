"""
Validate Incoming requests using the JWT server
"""

import logging
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from yumi import NotAuthorized, Scopes, UserInfo

from .deps import get_jwt_client, get_settings


def validate_jwt(
    auth: Annotated[
        HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))
    ],
    token: Annotated[str | None, Cookie()] = None,
) -> UserInfo:
    """Validate the token and return the users information"""
    try:
        if get_settings().dev_mode:
            logging.warning(
                "WARNING: Running server in dev mode. No API authentication required"
            )
            return UserInfo(
                username="test_user", scopes=[scope.value for scope in Scopes]
            )
        return get_jwt_client().validate_jwt(auth.credentials if auth else token)
    except NotAuthorized as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "could not verify token"
        ) from exc


def has_admin_scope():
    """Check the user has the admin scope"""
    return has_scope(Scopes.ADMIN)


def has_scope(scope: Scopes):
    """Check the user has the provided scope"""

    def _has_scope(user_info: Annotated[UserInfo, Depends(validate_jwt)]):
        if scope.value not in user_info.scopes:
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        return user_info

    return _has_scope
