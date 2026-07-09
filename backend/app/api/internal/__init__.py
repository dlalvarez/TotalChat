from fastapi import APIRouter

from app.api.internal.payments import router as payments_router

router = APIRouter(prefix="/api/internal")
router.include_router(payments_router)
