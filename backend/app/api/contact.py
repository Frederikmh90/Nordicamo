"""Contact API endpoints."""

from fastapi import APIRouter, HTTPException

from app.schemas.contact import ContactRequest, ContactResponse
from app.services.email_service import send_contact_email

router = APIRouter(prefix="/api/contact", tags=["contact"])


@router.post("", response_model=ContactResponse)
async def send_contact(request: ContactRequest):
    """Send contact request via email."""
    try:
        send_contact_email(
            name=request.name,
            email=request.email,
            message=request.message,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return ContactResponse(status="sent")
