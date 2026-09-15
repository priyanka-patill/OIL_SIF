from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.common import PaginatedResponse
from app.schemas.notification import (
    NotificationConfigCreate,
    NotificationConfigUpdate,
    NotificationConfigResponse,
    EmailPreviewRequest,
    EmailPreviewResponse,
    SendEmailRequest,
    SendEmailResponse,
    EmailLogResponse
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["Management Escalations & Email System"])


# -------------------------------------------------------------
# ESCALATION CONFIGURATION
# -------------------------------------------------------------
@router.get("/config", response_model=List[NotificationConfigResponse])
def get_notification_configs(db: Session = Depends(get_db)):
    """
    Retrieve configurable escalation recipients across tiers (Safety/HSE -> Dept Head -> Management).
    """
    return NotificationService.get_configs(db=db)


@router.post("/config", response_model=NotificationConfigResponse, status_code=status.HTTP_201_CREATED)
def create_notification_config(
    req: NotificationConfigCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new escalation tier recipient.
    """
    return NotificationService.create_config(db=db, req=req)


@router.put("/config/{config_id}", response_model=NotificationConfigResponse)
def update_notification_config(
    config_id: str,
    req: NotificationConfigUpdate,
    db: Session = Depends(get_db)
):
    """
    Update escalation recipient parameters or notification triggers.
    """
    try:
        return NotificationService.update_config(db=db, config_id=config_id, req=req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/config/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification_config(
    config_id: str,
    db: Session = Depends(get_db)
):
    """
    Remove an escalation recipient from the configuration.
    """
    success = NotificationService.delete_config(db=db, config_id=config_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification config not found")
    return None


# -------------------------------------------------------------
# EMAIL PREVIEW & DISPATCH
# -------------------------------------------------------------
@router.post("/preview", response_model=EmailPreviewResponse)
def generate_email_preview(
    req: EmailPreviewRequest,
    db: Session = Depends(get_db)
):
    """
    Generate mandatory human-in-the-loop EMAIL PREVIEW before dispatching.
    Clearly distinguishes recorded field facts from AI-generated recommendations.
    """
    try:
        return NotificationService.generate_email_preview(db=db, req=req)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/send", response_model=SendEmailResponse)
def send_notification_email(
    req: SendEmailRequest,
    db: Session = Depends(get_db)
):
    """
    Dispatches reviewed email notification and records immutable entry in EmailLog.
    """
    return NotificationService.send_notification_email(db=db, req=req)


@router.get("/logs", response_model=PaginatedResponse[EmailLogResponse])
def get_email_logs(
    report_id: Optional[str] = Query(None, description="Filter logs by report ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieve audit trail of sent email notifications.
    """
    items, total = NotificationService.get_email_logs(
        db=db,
        report_id=report_id,
        page=page,
        page_size=page_size
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
