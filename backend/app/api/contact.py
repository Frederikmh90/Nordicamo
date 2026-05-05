"""Contact API endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.contact import ContactRequest, ContactResponse
from app.services.email_service import queue_contact_request, send_contact_email

router = APIRouter(prefix="/api/contact", tags=["contact"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ContactResponse)
async def send_contact(request: ContactRequest):
    """Send contact request via email."""
    try:
        send_contact_email(
            name=request.name,
            email=request.email,
            message=request.message,
        )
        return ContactResponse(status="sent")
    except RuntimeError:
        try:
            queued_path = queue_contact_request(
                name=request.name,
                email=request.email,
                message=request.message,
            )
            logger.warning("Contact email delivery failed; request queued at %s", queued_path)
            return ContactResponse(status="queued")
        except Exception as exc:
            logger.exception("Contact request queue fallback failed")
            raise HTTPException(status_code=503, detail=str(exc)) from exc
