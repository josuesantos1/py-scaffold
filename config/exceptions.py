"""Application exception types.

Framework-agnostic: no blacksheep or fastapi imports here.
Exception handlers are registered in main.py.
"""


class AppException(Exception):
    """Base exception for controlled application errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
