from fastapi import status
from fastapi import Request
from fastapi.responses import JSONResponse

class AppException(Exception):
    def __init__(
        self,
        error_id: str,
        message: str,
        severity: str = "error",       
        category: str = "global",      
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ):
        self.error_id = error_id
        self.message = message
        self.severity = severity
        self.category = category
        self.status_code = status_code

async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "id": exc.error_id,
            "message": exc.message,
            "severity": exc.severity,
            "category": exc.category
        }
    )

