from typing import Annotated
from fastapi import HTTPException, Header

class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status_code=401, detail=detail, headers={"WWW-Authenticate": "Bearer"})

VALID_TOKENS: dict[str, str] = {
    "alice-test-token-1": "u-001",
    "bob-test-token-2": "u-002"
    }

def get_current_user(authorization: Annotated[str | None, Header()] = None) -> str:
    # check 1: no authorization header
    if authorization is None:
        raise UnauthorizedException

    # check 2: authorization header doesn't have the expected format
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException

    # check 3: token isn't one we know
    if authorization.removeprefix("Bearer: ") not in VALID_TOKENS:
        raise UnauthorizedException

    # success
    authorization.removeprefix("Bearer: ")
    return VALID_TOKENS[authorization]