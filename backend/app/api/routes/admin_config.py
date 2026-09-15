from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.admin_config import (
    AdminSettingsResponse,
    AdminSettingsUpdate
)
from app.services.admin_config_service import AdminConfigService

router = APIRouter(prefix="/admin", tags=["Admin Settings & Governance"])


@router.get("/settings", response_model=AdminSettingsResponse)
def get_admin_settings(
    db: Session = Depends(get_db)
):
    """
    Retrieve platform governance settings, BDI thresholds, SLA policies, and masked security credentials.
    """
    return AdminConfigService.get_settings(db)


@router.put("/settings", response_model=AdminSettingsResponse)
def update_admin_settings(
    payload: AdminSettingsUpdate,
    db: Session = Depends(get_db)
):
    """
    Update platform governance parameters, BDI methodology, SIF cutoffs, and notification configurations.
    """
    return AdminConfigService.update_settings(db, payload)
