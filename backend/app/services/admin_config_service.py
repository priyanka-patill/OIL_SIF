import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.admin_config import AdminConfig
from app.schemas.admin_config import (
    AdminSettingsResponse,
    AdminSettingsUpdate,
    BDIThresholdsConfig,
    BDIMethodologyConfig,
    SIFThresholdsConfig,
    SLAPolicyItemConfig,
    NotificationChannelsConfig
)
from app.services.audit_service import AuditService
from app.services.sla_service import SLAService


class AdminConfigService:
    """
    Manages persistent platform governance settings, BDI thresholds, SLA policies,
    and security credential masking.
    """

    CONFIG_KEYS = {
        "SETTINGS": "platform_governance_settings"
    }

    DEFAULT_SETTINGS = {
        "demo_mode_active": False,
        "ai_engine_version": "v2.0.0-phase8",
        "human_approval_required": True,
        "bdi_thresholds": {
            "normal_max": 20.0,
            "low_max": 40.0,
            "moderate_max": 60.0,
            "high_max": 80.0,
            "critical_max": 100.0
        },
        "bdi_methodology": {
            "methodology": "WEIGHTED_DEFENSE_IN_DEPTH",
            "include_historical_penalty": True,
            "near_miss_multiplier": 1.25
        },
        "sif_thresholds": {
            "high_bdi_cutoff": 60.0,
            "critical_bdi_cutoff": 80.0,
            "min_failed_barriers_for_critical": 2,
            "require_toxic_or_flammable_exposure": True
        },
        "notification_channels": {
            "mock_mode": True,
            "email_enabled": True,
            "webhook_enabled": True,
            "sms_enabled": False,
            "smtp_host": "smtp.refinery.internal",
            "smtp_port": 587,
            "smtp_user": "safety-orchestrator@refinery.internal",
            "smtp_password_masked": "••••••••",
            "webhook_url_masked": "https://hooks.refinery.internal/safety-alerts/••••••••"
        }
    }

    @classmethod
    def get_settings(cls, db: Session) -> AdminSettingsResponse:
        stmt = select(AdminConfig).where(AdminConfig.config_key == cls.CONFIG_KEYS["SETTINGS"])
        config_record = db.scalars(stmt).first()

        if not config_record:
            # Seed default
            config_record = AdminConfig(
                id=str(uuid.uuid4()),
                config_key=cls.CONFIG_KEYS["SETTINGS"],
                config_value=cls.DEFAULT_SETTINGS,
                description="Default platform governance and analytical parameters",
                updated_at=datetime.utcnow(),
                updated_by="System"
            )
            db.add(config_record)
            db.commit()
            db.refresh(config_record)

        val = config_record.config_value or {}

        # Fetch active SLA policies from SLAService
        policies = SLAService.get_or_create_policies(db)
        sla_items = [
            SLAPolicyItemConfig(
                severity=p.severity,
                target_sla_minutes=p.sla_minutes,
                reminder_interval_minutes=p.reminder_minutes,
                warning_interval_minutes=p.warning_minutes,
                level_0_role=p.escalation_level_0_role,
                level_1_role=p.escalation_level_1_role,
                level_2_role=p.escalation_level_2_role,
                level_3_role=p.escalation_level_3_role
            )
            for p in policies
        ]


        bdi_thresh = BDIThresholdsConfig(**val.get("bdi_thresholds", cls.DEFAULT_SETTINGS["bdi_thresholds"]))
        bdi_method = BDIMethodologyConfig(**val.get("bdi_methodology", cls.DEFAULT_SETTINGS["bdi_methodology"]))
        sif_thresh = SIFThresholdsConfig(**val.get("sif_thresholds", cls.DEFAULT_SETTINGS["sif_thresholds"]))
        notif = NotificationChannelsConfig(**val.get("notification_channels", cls.DEFAULT_SETTINGS["notification_channels"]))

        return AdminSettingsResponse(
            demo_mode_active=val.get("demo_mode_active", False),
            ai_engine_version=val.get("ai_engine_version", "v2.0.0-phase8"),
            human_approval_required=val.get("human_approval_required", True),
            bdi_thresholds=bdi_thresh,
            bdi_methodology=bdi_method,
            sif_thresholds=sif_thresh,
            sla_policies=sla_items,
            notification_channels=notif,
            last_updated_at=config_record.updated_at,
            last_updated_by=config_record.updated_by or "Administrator"
        )

    @classmethod
    def update_settings(cls, db: Session, payload: AdminSettingsUpdate) -> AdminSettingsResponse:
        stmt = select(AdminConfig).where(AdminConfig.config_key == cls.CONFIG_KEYS["SETTINGS"])
        config_record = db.scalars(stmt).first()

        if not config_record:
            config_record = AdminConfig(
                id=str(uuid.uuid4()),
                config_key=cls.CONFIG_KEYS["SETTINGS"],
                config_value=cls.DEFAULT_SETTINGS,
                updated_by=payload.updated_by
            )
            db.add(config_record)

        val = dict(config_record.config_value or cls.DEFAULT_SETTINGS)

        if payload.demo_mode_active is not None:
            val["demo_mode_active"] = payload.demo_mode_active
        if payload.human_approval_required is not None:
            val["human_approval_required"] = payload.human_approval_required
        if payload.bdi_thresholds is not None:
            val["bdi_thresholds"] = payload.bdi_thresholds.model_dump()
        if payload.bdi_methodology is not None:
            val["bdi_methodology"] = payload.bdi_methodology.model_dump()
        if payload.sif_thresholds is not None:
            val["sif_thresholds"] = payload.sif_thresholds.model_dump()
        if payload.notification_channels is not None:
            # Ensure masked values don't overwrite with raw secrets
            notif_dump = payload.notification_channels.model_dump()
            notif_dump["smtp_password_masked"] = "••••••••"
            notif_dump["webhook_url_masked"] = "https://hooks.refinery.internal/safety-alerts/••••••••"
            val["notification_channels"] = notif_dump

        # Update SLA policies if passed
        if payload.sla_policies:
            for p in payload.sla_policies:
                from app.schemas.sla import SLAPolicyUpdateRequest
                SLAService.update_policy(
                    db,
                    severity=p.severity,
                    update_data=SLAPolicyUpdateRequest(
                        target_sla_minutes=p.target_sla_minutes,
                        reminder_interval_minutes=p.reminder_interval_minutes,
                        warning_interval_minutes=p.warning_interval_minutes,
                        level_0_role=p.level_0_role,
                        level_1_role=p.level_1_role,
                        level_2_role=p.level_2_role,
                        level_3_role=p.level_3_role
                    )
                )

        config_record.config_value = val
        config_record.updated_at = datetime.utcnow()
        config_record.updated_by = payload.updated_by
        db.commit()
        db.refresh(config_record)

        # Log audit trail
        AuditService.log_event(
            db=db,
            event_type="ADMIN_CONFIG_UPDATE",
            trigger=f"Platform governance settings updated by {payload.updated_by}",
            actor=payload.updated_by,
            evidence={"demo_mode_active": val.get("demo_mode_active")}
        )

        return cls.get_settings(db)
