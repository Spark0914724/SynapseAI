from fastapi import APIRouter
from app.api.v1.endpoints import auth

api_router = APIRouter()

# ── Health ─────────────────────────────────────────────────────────────────────
@api_router.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "SynapseAI API"}

# ── Auth ───────────────────────────────────────────────────────────────────────
api_router.include_router(auth.router)
