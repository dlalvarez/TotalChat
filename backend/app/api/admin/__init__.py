from fastapi import APIRouter

from app.api.admin.appointments import router as appointments_router
from app.api.admin.availability import router as availability_router
from app.api.admin.bookings import router as bookings_router
from app.api.admin.payments import router as payments_router
from app.api.admin.resources import router as resources_router

router = APIRouter(prefix="/api/admin")
router.include_router(appointments_router)
router.include_router(availability_router)
router.include_router(bookings_router)
router.include_router(payments_router)
router.include_router(resources_router)
