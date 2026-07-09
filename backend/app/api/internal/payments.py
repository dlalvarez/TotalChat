from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.api.admin.dependencies import get_admin_tenant_context
from app.api.admin.resources import serialize_payment_attempt
from app.db.session import get_db_session
from app.services.payments import PaymentExpiryService
from app.tenancy.context import TenantContext

router = APIRouter(tags=["internal-payments"])


class InternalPaymentAttemptActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    force: bool = False
    notes: str | None = None


@router.post("/payment-attempts/{payment_attempt_id}/expire-missing-evidence")
def expire_missing_evidence(
    payment_attempt_id: UUID,
    payload: InternalPaymentAttemptActionRequest | None = None,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    request = payload or InternalPaymentAttemptActionRequest()
    try:
        result = PaymentExpiryService(session, tenant_context).expire_missing_evidence(
            payment_attempt_id=payment_attempt_id,
            force=request.force,
            notes=request.notes,
        )
        session.flush()
        session.refresh(result.payment_attempt)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {
        "data": {
            "payment_attempt": serialize_payment_attempt(result.payment_attempt),
            "action": result.action,
            "booking_action": result.booking_action,
        }
    }


@router.post("/payment-attempts/{payment_attempt_id}/mark-review-overdue")
def mark_review_overdue(
    payment_attempt_id: UUID,
    payload: InternalPaymentAttemptActionRequest | None = None,
    tenant_context: TenantContext = Depends(get_admin_tenant_context),
    session: Session = Depends(get_db_session),
) -> dict[str, dict[str, object]]:
    request = payload or InternalPaymentAttemptActionRequest()
    try:
        result = PaymentExpiryService(session, tenant_context).mark_review_overdue(
            payment_attempt_id=payment_attempt_id,
            force=request.force,
            notes=request.notes,
        )
        session.flush()
        session.refresh(result.payment_attempt)
        session.commit()
    except Exception:
        session.rollback()
        raise
    return {
        "data": {
            "payment_attempt": serialize_payment_attempt(result.payment_attempt),
            "action": result.action,
            "booking_action": result.booking_action,
        }
    }
