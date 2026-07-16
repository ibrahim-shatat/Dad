from fastapi import APIRouter

from app.api.v1.endpoints import (
    approvals,
    auth,
    dashboard,
    documents,
    email,
    meetings,
    notifications,
    presentations,
    push,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(approvals.router, prefix="/approvals", tags=["approvals"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(presentations.router, prefix="/presentations", tags=["presentations"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(email.router, prefix="/email", tags=["email"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(push.router, prefix="/push", tags=["push"])
