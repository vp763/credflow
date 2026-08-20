# CredFlow Backend - API Router

from fastapi import APIRouter

from app.api.v1 import auth, agents, tally

api_router = APIRouter()

# Auth
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# Agents
api_router.include_router(agents.router, prefix="/agents", tags=["Agents"])

# Tally Sync
api_router.include_router(tally.router, prefix="/tally", tags=["Tally Sync"])