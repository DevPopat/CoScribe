"""
FastAPI application entry point for the CoScribe backend.

Registers all routers and middleware. The app instance defined here
is the target for uvicorn when starting the server.
"""

from fastapi import FastAPI

from app.api import chat, drafts, sessions

app = FastAPI()
app.include_router(chat.router)
app.include_router(sessions.router)
app.include_router(drafts.router)


@app.get("/health")
async def health() -> dict:
    """
    Health check endpoint to verify the server is running.

    :returns: A JSON object with a status field set to "ok".
    """
    return {"status": "ok"}
