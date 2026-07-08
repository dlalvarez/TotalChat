from fastapi import APIRouter

from app.api.admin.availability import router as availability_router
from app.api.admin.bookings import router as bookings_router

router = APIRouter(prefix="/api/admin")
router.include_router(availability_router)
router.include_router(bookings_router)
