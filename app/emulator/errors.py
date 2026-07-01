from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class InvalidPageToken(ValueError): ...


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(InvalidPageToken)
    async def invalid_page_token(request: Request, exc: InvalidPageToken):
        return JSONResponse(
            status_code=400,
            content={
                "error": "INVALID_PAGE_TOKEN",
                "message": str(exc),
            },
        )
