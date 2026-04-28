from typing import Any, Optional


class AppException(Exception):
    def __init__(self, message: str, code: int = 400, result: Optional[Any] = None):
        self.message = message
        self.code = code
        self.result = result
        super().__init__(self.message)
