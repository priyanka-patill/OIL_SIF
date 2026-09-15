from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class BDIThresholdsConfig(BaseModel):
    normal_max: float = 20.0
    low_max: float = 40.0
    moderate_max: float = 60.0
    high_max: float = 80.0
    critical_max: float = 100.0


class BDIMethodologyConfig(BaseModel):
    methodology: str = Field(default="WEIGHTED_DEFENSE_IN_DEPTH", description="WEIGHTED_DEFENSE_IN_DEPTH or REASON_SWISS_CHEESE_MULTIPLICATIVE")
    include_historical_penalty: bool = True
    near_miss_multiplier: float = 1.25


class SIFThresholdsConfig(BaseModel):
    high_bdi_cutoff: float = 60.0
    critical_bdi_cutoff: float = 80.0
    min_failed_barriers_for_critical: int = 2
    require_toxic_or_flammable_exposure: bool = True


class SLAPolicyItemConfig(BaseModel):
    severity: str
    target_sla_minutes: int
    reminder_interval_minutes: int
    warning_interval_minutes: int
    level_0_role: str
    level_1_role: str
    level_2_role: str
    level_3_role: str


class NotificationChannelsConfig(BaseModel):
    mock_mode: bool = True
    email_enabled: bool = True
    webhook_enabled: bool = True
    sms_enabled: bool = False
    smtp_host: str = "smtp.refinery.internal"
    smtp_port: int = 587
    smtp_user: str = "safety-orchestrator@refinery.internal"
    smtp_password_masked: str = "••••••••"
    webhook_url_masked: str = "https://hooks.refinery.internal/safety-alerts/••••••••"


class AdminSettingsResponse(BaseModel):
    demo_mode_active: bool = False
    ai_engine_version: str = "v2.0.0-phase8"
    human_approval_required: bool = True
    bdi_thresholds: BDIThresholdsConfig
    bdi_methodology: BDIMethodologyConfig
    sif_thresholds: SIFThresholdsConfig
    sla_policies: List[SLAPolicyItemConfig]
    notification_channels: NotificationChannelsConfig
    last_updated_at: Optional[datetime] = None
    last_updated_by: str = "Administrator"


class AdminSettingsUpdate(BaseModel):
    demo_mode_active: Optional[bool] = None
    human_approval_required: Optional[bool] = None
    bdi_thresholds: Optional[BDIThresholdsConfig] = None
    bdi_methodology: Optional[BDIMethodologyConfig] = None
    sif_thresholds: Optional[SIFThresholdsConfig] = None
    sla_policies: Optional[List[SLAPolicyItemConfig]] = None
    notification_channels: Optional[NotificationChannelsConfig] = None
    updated_by: str = "Administrator"
