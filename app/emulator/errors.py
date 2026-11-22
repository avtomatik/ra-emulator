from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.storage.sqlite import WorkflowConflict, WorkflowNotFound


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

    @app.exception_handler(WorkflowConflict)
    async def workflow_conflict(request: Request, exc: WorkflowConflict):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(WorkflowNotFound)
    async def workflow_not_found(request: Request, exc: WorkflowNotFound):
        return JSONResponse(status_code=404, content={"detail": str(exc)})
