import traceback
from enum import Enum

from fastapi import HTTPException


class ExcCode(str, Enum):
    BOOK_NOT_FOUND = "BOOK_NOT_FOUND"
    NOT_ENOUGH_RATINGS = "NOT_ENOUGH_RATINGS"

class UserFacingException(HTTPException):
    def __init__(self, status_code: int, exc_code: ExcCode, message: str, input: any, exc: Exception | None = None):
        super().__init__(
            status_code=status_code,
            detail={
                "code": exc_code.value,
                "message": message,
                "input_type": str(type(input)),
                "input": input,
                "exception_type": str(type(exc)) if exc else None,
                "traceback": traceback.format_exc() if exc else None,
            }
        )
