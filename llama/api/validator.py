from typing import Annotated
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from yumi import NotAuthorized, Scopes, UserInfo
from .deps import get_jwt_client


def validate_jwt(
    auth: Annotated[
        HTTPAuthorizationCredentials | None, Depends(HTTPBearer(auto_error=False))
    ],
    token: Annotated[str | None, Cookie()] = None,
) -> UserInfo:
    try:
        return get_jwt_client().validate_jwt(auth.credentials if auth else token)
    except NotAuthorized as exc:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "could not verify token"
        ) from exc


def has_admin_scope():
    return has_scope(Scopes.ADMIN)


def has_scope(scope: Scopes):
    def _has_scope(user_info: Annotated[UserInfo, Depends(validate_jwt)]):
        if scope.value not in user_info.scopes:
            raise HTTPException(status.HTTP_403_FORBIDDEN)
        return user_info

    return _has_scope
