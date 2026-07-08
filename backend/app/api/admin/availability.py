from __future__ import annotations

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.admin.dependencies import get_admin_tenant_context
from app.db.session import get_db_session
from app.services.availability import AvailableSlot, InternalSchedulingProvider, SchedulingProvider
from app.tenancy.context import TenantContext

router = APIRouter(prefix="/availability", tags=["admin-availability"])


def get_scheduling_provider() -> SchedulingProvider:
    return InternalSchedulingProvider()


def serialize_slot(slot: AvailableSlot) -> dict[str, object]:
    return {
        "starts_at": slot.starts_at.isoformat(),
        "ends_at": slot.ends_at.isoformat(),
        "practitioner_id": str(slot.practitioner_id),
        "location_id": str(slot.location_id) if slot.location_id is not None else None,
        "room_id": str(slot.room_id) if slot.room_id is not None else None,
        "modality": slot.modality,
        "source": slot.source,
    }


@router.get("/slots")
def list_availability_slots(
    practitioner_service_id: UUID,
    modality: str,
    date_from: date,
    date_to: date,
    practitioner_id: UUID | None = None,
    payer_plan_id: UUID | None = Query(default=None),
    location_id: UUID | None = None,
    room_id: UUID | None = None,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
    scheduling_provider: SchedulingProvider = Depends(get_scheduling_provider),
) -> dict[str, list[dict[str, object]]]:
    # payer_plan_id is intentionally accepted for API-contract compatibility; pricing
    # remains out of scope for availability slot lookup in this PR.
    _ = payer_plan_id
    slots = scheduling_provider.list_available_slots(
        session,
        tenant_context,
        practitioner_service_id=practitioner_service_id,
        practitioner_id=practitioner_id,
        modality=modality,
        start_date=date_from,
        end_date=date_to,
        location_id=location_id,
        room_id=room_id,
    )
    return {"data": [serialize_slot(slot) for slot in slots]}
