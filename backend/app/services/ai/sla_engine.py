import math
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from app.models.safety_action import SafetyAction
from app.models.sla_policy import SLAPolicy


class SLAEngine:
    """
    AI SLA Monitoring and Countdown Engine.
    Computes real-time countdowns, SLA states, and multi-tier escalation triggers.
    Ensures configurable dynamic policy evaluation rather than hardcoded logic.
    """

    DEFAULT_POLICIES = {
        "CRITICAL": {
            "sla_minutes": 60,
            "reminder_minutes": 15,
            "warning_minutes": 30,
            "escalation_interval_minutes": 30,
            "level_0": "Unit In-Charge",
            "level_1": "HSE Head",
            "level_2": "Plant Management",
            "level_3": "Executive Management"
        },
        "HIGH": {
            "sla_minutes": 240,
            "reminder_minutes": 60,
            "warning_minutes": 120,
            "escalation_interval_minutes": 60,
            "level_0": "Safety Officer",
            "level_1": "HSE Head",
            "level_2": "Department Head",
            "level_3": "Plant Management"
        },
        "ELEVATED": {
            "sla_minutes": 1440,
            "reminder_minutes": 360,
            "warning_minutes": 720,
            "escalation_interval_minutes": 360,
            "level_0": "Unit In-Charge",
            "level_1": "Safety Officer",
            "level_2": "Department Head",
            "level_3": "Plant Management"
        },
        "WATCH": {
            "sla_minutes": 4320,
            "reminder_minutes": 1440,
            "warning_minutes": 2880,
            "escalation_interval_minutes": 1440,
            "level_0": "Safety Officer",
            "level_1": "Unit In-Charge",
            "level_2": "HSE Head",
            "level_3": "Plant Management"
        },
        "NORMAL": {
            "sla_minutes": 4320,
            "reminder_minutes": 1440,
            "warning_minutes": 2880,
            "escalation_interval_minutes": 1440,
            "level_0": "Safety Officer",
            "level_1": "Unit In-Charge",
            "level_2": "HSE Head",
            "level_3": "Plant Management"
        }
    }

    @classmethod
    def get_policy_config(cls, severity: str, db_policy: Optional[SLAPolicy] = None) -> Dict[str, Any]:
        """Returns policy parameters prioritizing database records with safe fallback."""
        sev = severity.upper()
        default = cls.DEFAULT_POLICIES.get(sev, cls.DEFAULT_POLICIES["HIGH"])

        if db_policy and db_policy.is_active:
            return {
                "sla_minutes": db_policy.sla_minutes,
                "reminder_minutes": db_policy.reminder_minutes,
                "warning_minutes": db_policy.warning_minutes,
                "escalation_interval_minutes": db_policy.escalation_interval_minutes,
                "level_0": db_policy.escalation_level_0_role,
                "level_1": db_policy.escalation_level_1_role,
                "level_2": db_policy.escalation_level_2_role,
                "level_3": db_policy.escalation_level_3_role
            }
        return default

    @classmethod
    def calculate_deadline(cls, start_time: datetime, sla_minutes: int) -> datetime:
        """Calculates precise deadline timestamp from start time."""
        return start_time + timedelta(minutes=sla_minutes)

    @classmethod
    def format_duration(cls, total_seconds: int) -> str:
        """Formats integer seconds into clean HH:MM:SS string."""
        abs_sec = abs(total_seconds)
        hours = abs_sec // 3600
        minutes = (abs_sec % 3600) // 60
        seconds = abs_sec % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @classmethod
    def compute_countdown(
        cls,
        action: SafetyAction,
        policy: Optional[SLAPolicy] = None,
        now: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculates live SLA countdown, remaining seconds, elapsed percentage, and active state.
        Supports simulated time for testing and background tick analysis.
        """
        curr = now or datetime.utcnow()
        start = action.created_at or curr
        pol = cls.get_policy_config(action.severity, policy)

        # Determine SLA minutes & deadline
        sla_mins = action.sla_minutes or pol["sla_minutes"]
        deadline = action.sla_deadline or cls.calculate_deadline(start, sla_mins)

        total_duration_sec = sla_mins * 60
        elapsed_sec = (curr - start).total_seconds()
        remaining_sec = int(round((deadline - curr).total_seconds()))

        pct_elapsed = max(0.0, min(999.9, round((elapsed_sec / total_duration_sec) * 100.0, 1))) if total_duration_sec > 0 else 100.0

        is_ack = action.acknowledged_at is not None
        is_breached = remaining_sec < 0

        # Determine formatted countdown display
        if remaining_sec >= 0:
            formatted_countdown = f"{cls.format_duration(remaining_sec)} remaining"
        else:
            formatted_countdown = f"BREACHED by {cls.format_duration(remaining_sec)}"

        # Determine SLA State
        if action.status == "CLOSED":
            sla_state = "CLOSED"
        elif action.status == "VERIFIED":
            sla_state = "VERIFIED"
        elif action.status == "CONTAINED":
            sla_state = "CONTAINED"
        elif action.status == "REJECTED":
            sla_state = "REJECTED"
        elif is_ack:
            sla_state = "ACKNOWLEDGED"
        elif action.escalation_level > 0:
            sla_state = "ESCALATED"
        elif is_breached:
            sla_state = "BREACHED"
        elif pct_elapsed >= 50.0:
            sla_state = "APPROACHING_DEADLINE"
        else:
            sla_state = "NORMAL"

        return {
            "action_id": action.id,
            "report_id": action.report_id,
            "severity": action.severity,
            "action_type": action.action_type,
            "assigned_role": action.assigned_role,
            "assigned_user": action.assigned_user or "Unassigned",
            "sla_minutes": sla_mins,
            "sla_deadline": deadline,
            "time_remaining_seconds": remaining_sec,
            "formatted_countdown": formatted_countdown,
            "percentage_elapsed": pct_elapsed,
            "sla_state": sla_state,
            "current_escalation_level": action.escalation_level,
            "is_acknowledged": is_ack,
            "is_breached": is_breached
        }

    @classmethod
    def evaluate_escalation_tier(
        cls,
        action: SafetyAction,
        policy: Optional[SLAPolicy] = None,
        now: Optional[datetime] = None
    ) -> Tuple[int, Optional[str], Optional[str]]:
        """
        Determines the target escalation level, responsible role, and justification reason.
        Level 0: Initial assignment
        Level 1: SLA breached without acknowledgement
        Level 2: Breached + escalation interval elapsed without acknowledgement
        Level 3: Breached + 2 * escalation interval elapsed without acknowledgement
        """
        if action.acknowledged_at or action.status in ["CLOSED", "VERIFIED", "REJECTED"]:
            return action.escalation_level, None, None

        curr = now or datetime.utcnow()
        start = action.created_at or curr
        pol = cls.get_policy_config(action.severity, policy)

        sla_mins = action.sla_minutes or pol["sla_minutes"]
        deadline = action.sla_deadline or cls.calculate_deadline(start, sla_mins)
        interval_mins = pol["escalation_interval_minutes"]

        overdue_sec = (curr - deadline).total_seconds()
        if overdue_sec < 0:
            # Not breached yet
            return 0, pol["level_0"], None

        overdue_mins = overdue_sec / 60.0

        if overdue_mins >= (2 * interval_mins):
            target_level = 3
            target_role = pol["level_3"]
            reason = f"Critical action overdue by {int(overdue_mins)}m (Level 3 escalation to {target_role})"
        elif overdue_mins >= interval_mins:
            target_level = 2
            target_role = pol["level_2"]
            reason = f"Critical action overdue by {int(overdue_mins)}m (Level 2 escalation to {target_role})"
        else:
            target_level = 1
            target_role = pol["level_1"]
            reason = f"SLA breached ({sla_mins}m elapsed without acknowledgement — Level 1 escalation to {target_role})"

        return target_level, target_role, reason
