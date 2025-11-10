import traceback
from enum import Enum

from fastapi import HTTPException


class ExcCode(str, Enum):
    """Enumeration of user-facing exception codes.

    These codes represent specific error conditions that
    can be communicated to the frontend for user feedback.

    Attributes:
        BOOK_NOT_FOUND: Indicates the requested book was not found in the database.
        NOT_ENOUGH_RATINGS: Indicates insufficient ratings to generate recommendations.
    """

    BOOK_NOT_FOUND = "BOOK_NOT_FOUND"
    NOT_ENOUGH_RATINGS = "NOT_ENOUGH_RATINGS"


class UserFacingException(HTTPException):
    """Custom exception for communicating user-facing errors via HTTP responses.

    This exception is meant to be raised when an error should be shown to the user.
    It provides structured details including the error code, message, user input,
    and (optionally) exception traceback for logging and debugging.

    Args:
        status_code: HTTP status code to return.
        exc_code: An `ExcCode` indicating the type of error.
        message: Human-readable message explaining the error.
        input: The input data that caused the error.
        exc: Optional underlying exception that triggered this error.
    """

    def __init__(
        self,
        status_code: int,
        exc_code: ExcCode,
        message: str,
        input: any,
        exc: Exception | None = None,
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "code": exc_code.value,
                "message": message,
                "input_type": str(type(input)),
                "input": input,
                "exception_type": str(type(exc)) if exc else None,
                "traceback": traceback.format_exc() if exc else None,
            },
        )
