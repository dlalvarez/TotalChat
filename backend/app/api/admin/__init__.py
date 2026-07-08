from fastapi import APIRouter

from app.api.admin.availability import router as availability_router

router = APIRouter(prefix="/api/admin")
router.include_router(availability_router)
