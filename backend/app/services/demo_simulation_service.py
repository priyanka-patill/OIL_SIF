import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.models.safety_report import SafetyReport
from app.models.safety_action import SafetyAction
from app.models.safety_hold import SafetyHold
from app.models.dataset import Dataset
from app.schemas.demo import (
    DemoStatusResponse,
    DemoPipelineStepItem,
    DemoScenarioExecutionResponse
)
from app.services.ai.correlation_engine import CorrelationEngine
from app.services.ai.barrier_engine import BarrierEngine
from app.services.ai.bdi_engine import BDIEngine
from app.services.ai.sif_escalation_engine import SIFEscalationEngine
from app.services.ai.orchestration_engine import OrchestrationEngine
from app.services.safety_hold_service import SafetyHoldService
from app.services.sla_service import SLAService
from app.services.audit_service import AuditService
from app.services.admin_config_service import AdminConfigService


class DemoSimulationService:
    """
    Simulation & Demonstration Engine for hackathon presentation and safe validation.
    Provides realistic refinery scenarios, fast-forward time travel, SLA breach simulation,
    step-by-step pipeline visualization, and zero real external notification risk.
    """

    _simulated_time_offset_minutes: int = 0
    _active_scenario: Optional[str] = None
    _loaded_report_id: Optional[str] = None
    _loaded_action_id: Optional[str] = None
    _loaded_hold_id: Optional[str] = None

    SCENARIO_TEMPLATES = {
        "NORMAL": {
            "refinery_unit": "Offsites & Storage",
            "equipment": "TK-104 Floating Roof Tank",
            "work_type": "Routine Inspection",
            "description": "Routine daily walkdown of tank farm bund area. Clean work area, drainage valves closed, zero defects observed.",
            "risk_level": "Low",
            "potential_consequence": "Standard Operations",
            "action_status": "Closed",
            "h2s_toxic_gas": False,
            "flammable_gas": False,
            "hot_work": False,
            "confined_space": False,
            "working_at_height": False,
            "ppe_issue": False,
            "maintenance_factor": False,
            "supervision_factor": False,
            "interlock_bypass": False,
            "line_break": False,
            "heavy_lifting": False,
            "high_potential": False,
            "repeated_issue": False,
            "previous_similar_reports": 0
        },
        "MINOR_PRECURSOR": {
            "refinery_unit": "Utilities Unit",
            "equipment": "BLR-2 Steam Header",
            "work_type": "Routine Maintenance Walkdown",
            "description": "Scaffold inspection tag expired by 2 days; crew noticed minor toe-board misalignment before climbing.",
            "risk_level": "Medium",
            "potential_consequence": "Potential minor slip or trip hazard",
            "action_status": "Open",
            "h2s_toxic_gas": False,
            "flammable_gas": False,
            "hot_work": False,
            "confined_space": False,
            "working_at_height": False,
            "ppe_issue": False,
            "maintenance_factor": False,
            "supervision_factor": False,
            "interlock_bypass": False,
            "line_break": False,
            "heavy_lifting": False,
            "high_potential": False,
            "repeated_issue": False,
            "previous_similar_reports": 0
        },
        "MULTI_FACTOR_CONVERGENCE": {
            "refinery_unit": "DHT (Diesel Hydrotreater)",
            "equipment": "V-201 Reactor Separator",
            "work_type": "Pump Strainer Cleaning",
            "description": "Process pump line strainer replacement. Trace acid residue observed at flange joint during night shift with degraded local exhaust ventilation; maintenance review completed with corrective action closed.",
            "risk_level": "Medium",
            "potential_consequence": "Localized fluid dispersion and operational delay",
            "action_status": "Closed",
            "h2s_toxic_gas": False,
            "flammable_gas": False,
            "hot_work": False,
            "confined_space": False,
            "working_at_height": False,
            "ppe_issue": False,
            "maintenance_factor": True,
            "supervision_factor": False,
            "interlock_bypass": False,
            "line_break": False,
            "heavy_lifting": False,
            "high_potential": False,
            "repeated_issue": False,
            "previous_similar_reports": 0
        },
        "HIGH_SIF_PRECURSOR": {
            "refinery_unit": "FCCU (Fluid Catalytic Cracker)",
            "equipment": "RX-301 Regenerator Riser",
            "work_type": "Hot Work / Welding",
            "description": "Welding torch ignited adjacent to catalyst transfer line with hydrocarbon residual. High pressure alarm bypassed on standby relief valve with absence of dedicated fire watch supervisor.",
            "risk_level": "High",
            "potential_consequence": "Major fire / explosion with secondary containment loss",
            "action_status": "Open",
            "h2s_toxic_gas": False,
            "flammable_gas": True,
            "hot_work": True,
            "confined_space": False,
            "working_at_height": True,
            "ppe_issue": False,
            "maintenance_factor": True,
            "supervision_factor": True,
            "interlock_bypass": True,
            "line_break": False,
            "heavy_lifting": False,
            "high_potential": False,
            "repeated_issue": False,
            "previous_similar_reports": 0
        },
        "CRITICAL_SIF_PRECURSOR": {
            "refinery_unit": "CDU-1 (Crude Distillation Unit)",
            "equipment": "C-101 Crude Column Overhead Receiver",
            "work_type": "Hot Work & Confined Space Maintenance",
            "description": "Toxic H2S sour gas accumulation (45 ppm) and hydrocarbon vapor release detected inside column overhead spool during live hot work welding. Multiple barriers compromised: PPE canister expired, ventilation blower tripped, permit fire watch supervisor departed area, and safety interlock valve tagged out without isolation verification.",
            "risk_level": "High",
            "potential_consequence": "Catastrophic toxic gas exposure, vapor cloud ignition, and multi-fatality SIF event",
            "action_status": "Overdue",
            "h2s_toxic_gas": True,
            "flammable_gas": True,
            "hot_work": True,
            "confined_space": True,
            "working_at_height": True,
            "ppe_issue": True,
            "maintenance_factor": True,
            "supervision_factor": True,
            "interlock_bypass": True,
            "line_break": True,
            "heavy_lifting": False,
            "high_potential": True,
            "repeated_issue": True,
            "previous_similar_reports": 2
        }
    }

    @classmethod
    def get_status(cls, db: Session) -> DemoStatusResponse:
        settings = AdminConfigService.get_settings(db)
        sim_time = datetime.utcnow() + timedelta(minutes=cls._simulated_time_offset_minutes)
        return DemoStatusResponse(
            demo_mode_active=settings.demo_mode_active,
            status_label="SIMULATION MODE ACTIVE" if settings.demo_mode_active else "PRODUCTION MODE (LIVE)",
            current_simulated_time=sim_time.strftime("%Y-%m-%d %H:%M:%S UTC"),
            simulated_time_offset_minutes=cls._simulated_time_offset_minutes,
            active_scenario=cls._active_scenario,
            loaded_report_id=cls._loaded_report_id,
            loaded_action_id=cls._loaded_action_id,
            loaded_hold_id=cls._loaded_hold_id,
            external_notifications_suppressed=True
        )

    @classmethod
    def set_demo_mode(cls, db: Session, enabled: bool) -> DemoStatusResponse:
        from app.schemas.admin_config import AdminSettingsUpdate
        AdminConfigService.update_settings(
            db,
            AdminSettingsUpdate(demo_mode_active=enabled, updated_by="Demo Controller")
        )
        if not enabled:
            cls._simulated_time_offset_minutes = 0
            cls._active_scenario = None

        AuditService.log_event(
            db=db,
            event_type="DEMO_SIMULATION",
            trigger=f"Simulation Mode toggled to {'ENABLED' if enabled else 'DISABLED'}",
            actor="Demo Controller",
            is_simulated=True
        )
        return cls.get_status(db)

    @classmethod
    def execute_scenario(
        cls,
        db: Session,
        scenario_type: str,
        custom_unit: Optional[str] = None
    ) -> DemoScenarioExecutionResponse:
        """
        Executes a complete, synchronized demonstration scenario from detection
        through barrier degradation, BDI, SIF escalation, action drafting, email preview,
        safety hold dispatch, and SLA countdown initiation.
        """
        scenario_type = scenario_type.upper()
        template = cls.SCENARIO_TEMPLATES.get(scenario_type, cls.SCENARIO_TEMPLATES["CRITICAL_SIF_PRECURSOR"])
        
        # Ensure demo mode is enabled
        cls.set_demo_mode(db, True)
        cls._simulated_time_offset_minutes = 0
        cls._active_scenario = scenario_type

        # Ensure demo dataset exists
        demo_dataset = db.scalars(select(Dataset).where(Dataset.dataset_name == "SIMULATED_DEMO_DATASET")).first()
        if not demo_dataset:
            demo_dataset = Dataset(
                id="SIMULATED-DATASET-001",
                dataset_name="SIMULATED_DEMO_DATASET",
                original_filename="simulated_refinery_exposures.xlsx",
                file_type="xlsx",
                status="ready",
                sheet_name="RefineryObservations",
                dataset_type="multi_factor",
                row_count=50,
                column_count=18,
                data_quality_status="PASSED",
                is_derived_dataset=False
            )
            db.add(demo_dataset)
            db.commit()


        # Step 1: Create simulated safety report
        unit_name = custom_unit or template.get("refinery_unit", "CDU-1")
        report_id = f"SIM-REP-{datetime.utcnow().strftime('%H%M%S%f')[:10]}"
        factors_list = []
        # Only add physical/process hazard factors to detected_factors.
        # Organizational factors (maintenance, supervision) are handled by boolean fields
        # on the report and have their own dedicated barrier rules - do NOT duplicate them here.
        if template.get("h2s_toxic_gas"): factors_list.append("Toxic Gas (H2S)")
        if template.get("flammable_gas"): factors_list.append("Flammable Gas / Vapor")
        if template.get("hot_work"): factors_list.append("Hot Work / Ignition")
        if template.get("confined_space"): factors_list.append("Confined Space Entry")
        if template.get("working_at_height"): factors_list.append("Working at Height")
        if template.get("interlock_bypass"): factors_list.append("Interlock Bypass")
        if template.get("line_break"): factors_list.append("Line Break / Containment")
        if template.get("ppe_issue"): factors_list.append("PPE Deficit")

        report = SafetyReport(
            id=report_id,
            dataset_id=demo_dataset.id,
            report_date=datetime.utcnow(),
            refinery_unit=unit_name,
            equipment=template["equipment"],
            work_type=template["work_type"],
            description=template["description"],
            risk_level=template["risk_level"],
            potential_consequence=template["potential_consequence"],
            ppe_issue=template.get("ppe_issue", False),
            maintenance_factor=template.get("maintenance_factor", False),
            supervisor_factor=template.get("supervision_factor", False),
            high_potential=template.get("high_potential", False),
            repeated_issue=template.get("repeated_issue", False),
            previous_similar_reports=template.get("previous_similar_reports", 0),
            detected_factors=factors_list,
            factor_count=len(factors_list),
            action_status=template.get("action_status", "Open"),
            raw_data={"is_simulated": True, "scenario": scenario_type, **template}
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        cls._loaded_report_id = report.id


        pipeline_steps: List[DemoPipelineStepItem] = []
        now_str = datetime.utcnow().strftime("%H:%M:%S")

        # Log Detection Audit
        AuditService.log_event(
            db=db,
            event_type="DETECTION",
            trigger=f"Simulated Safety Report Ingested for Unit {unit_name}",
            report_id=report.id,
            dataset_id=demo_dataset.id,
            actor="Simulation Ingest Engine",
            is_simulated=True,
            evidence={"unit": unit_name, "equipment": template["equipment"], "work_type": template["work_type"]}
        )
        pipeline_steps.append(
            DemoPipelineStepItem(
                step_number=1,
                step_key="DETECTION",
                step_title="1. Safety Observation Detection",
                status="COMPLETED",
                summary=f"Ingested report {report.id} at {unit_name} ({template['equipment']})",
                timestamp=now_str
            )
        )

        # Step 2: Multi-Factor Correlation
        detected_factors = CorrelationEngine.extract_factors(report)
        corr_result = {
            "total_factors_detected": len(detected_factors),
            "detected_factor_names": detected_factors,
            "convergence_identified": len(detected_factors) >= 2
        }
        AuditService.log_event(
            db=db,
            event_type="CORRELATION",
            trigger=f"Multi-Factor Correlation identified {len(detected_factors)} converging factors",
            report_id=report.id,
            actor="Multi-Factor Correlation Engine",
            is_simulated=True,
            evidence=corr_result
        )
        pipeline_steps.append(
            DemoPipelineStepItem(
                step_number=2,
                step_key="CORRELATION",
                step_title="2. Factor Convergence Analysis",
                status="COMPLETED",
                summary=f"Detected {len(detected_factors)} factors: {', '.join(detected_factors)}",
                details={"factors": detected_factors},
                timestamp=now_str
            )
        )


        # Step 3: Swiss Cheese Barrier Degradation
        barriers_list = BarrierEngine.assess_report_barriers(report)
        failed_count = sum(1 for b in barriers_list if b.status == "FAILED")
        degraded_count = sum(1 for b in barriers_list if b.status == "DEGRADED")
        intact_count = sum(1 for b in barriers_list if b.status == "INTACT")
        compromised_count = failed_count + degraded_count
        summary_counts = {
            "failed": failed_count,
            "degraded": degraded_count,
            "intact": intact_count,
            "total": len(barriers_list)
        }
        AuditService.log_event(
            db=db,
            event_type="BARRIER_ASSESSMENT",
            trigger=f"Swiss Cheese Barrier Defense Evaluated ({compromised_count} compromised layers)",
            report_id=report.id,
            actor="Swiss Cheese Barrier Engine",
            is_simulated=True,
            evidence=summary_counts
        )
        pipeline_steps.append(
            DemoPipelineStepItem(
                step_number=3,
                step_key="BARRIER_ASSESSMENT",
                step_title="3. Swiss Cheese Barrier Defense",
                status="COMPLETED",
                summary=f"{compromised_count} of {len(barriers_list)} barrier defense layers compromised",
                details=summary_counts,
                timestamp=now_str
            )
        )

        # Step 4: BDI Calculation
        bdi_res = BDIEngine.calculate_report_bdi(report, barriers_list)
        bdi_score = bdi_res.get("bdi_score", 0.0)
        bdi_class = bdi_res.get("classification", "NORMAL")
        AuditService.log_event(
            db=db,
            event_type="BDI_CALCULATION",
            trigger=f"BDI Calculated: {bdi_score:.1f} ({bdi_class})",
            report_id=report.id,
            bdi=bdi_score,
            actor="BDI Analytical Engine",
            is_simulated=True,
            evidence=bdi_res.get("factor_breakdown", {})
        )
        pipeline_steps.append(
            DemoPipelineStepItem(
                step_number=4,
                step_key="BDI_CALCULATION",
                step_title="4. Barrier Degradation Index (BDI)",
                status="COMPLETED",
                summary=f"BDI Score: {bdi_score:.1f} / 100 ({bdi_class})",
                details={"bdi_score": bdi_score, "classification": bdi_class},
                timestamp=now_str
            )
        )

        # Step 5: SIF Precursor Escalation & Preventive Intelligence
        sif_res = SIFEscalationEngine.evaluate_escalation(report, barriers_list, bdi_score, bdi_class)
        sev = sif_res.get("severity", "NORMAL")
        sif_stat = "YES" if sif_res.get("sif_precursor_status") else "NO"
        AuditService.log_event(
            db=db,
            event_type="SIF_ESCALATION",
            trigger=f"SIF Precursor Evaluated at {sev} ({sif_stat})",
            report_id=report.id,
            bdi=bdi_score,
            sif_status=sif_stat,
            severity=sev,
            actor="SIF Escalation Engine",
            is_simulated=True,
            evidence={"severity": sev, "why_escalated": sif_res.get("why_escalated", [])}
        )
        pipeline_steps.append(
            DemoPipelineStepItem(
                step_number=5,
                step_key="SIF_ESCALATION",
                step_title="5. SIF Precursor & 7-Stage Escalation",
                status="COMPLETED",
                summary=f"Escalation Severity: {sev} (Precursor: {sif_stat})",
                details={"severity": sev, "consequence": sif_res.get("what_potential_consequence")},
                timestamp=now_str
            )
        )

        # Step 6: Action Package Generation
        act_pkg = OrchestrationEngine.generate_action_package(
            report=report,
            barriers=barriers_list,
            bdi_result=bdi_res,
            escalation_result=sif_res
        )
        email_draft = OrchestrationEngine.generate_email_draft(act_pkg["action_package"])

        # Determine SLA minutes
        sla_mins = 60 if sev == "CRITICAL" else (240 if sev == "HIGH" else (1440 if sev == "ELEVATED" else 4320))
        sla_deadline = datetime.utcnow() + timedelta(minutes=sla_mins)

        action_id = f"SIM-ACT-{datetime.utcnow().strftime('%H%M%S%f')[:10]}"
        safety_action = SafetyAction(
            id=action_id,
            report_id=report.id,
            dataset_id=demo_dataset.id,
            action_type=act_pkg["action_type"],
            severity=sev,
            title=act_pkg["title"],
            description=act_pkg["description"],
            assigned_role=act_pkg["assigned_role"],
            sla_hours=act_pkg["sla_hours"],
            sla_minutes=sla_mins,
            sla_deadline=sla_deadline,
            sla_state="NORMAL",
            escalation_level=0,
            status="OPEN",
            approval_status="APPROVED",
            action_package=act_pkg["action_package"],
            ai_recommendation=act_pkg["ai_recommendation"],
            created_at=datetime.utcnow()
        )
        db.add(safety_action)
        db.commit()
        db.refresh(safety_action)
        cls._loaded_action_id = safety_action.id

        AuditService.log_event(
            db=db,
            event_type="ACTION_CREATION",
            trigger=f"Safety Action {safety_action.id} generated with {sla_mins}m SLA for {safety_action.assigned_role}",
            report_id=report.id,
            action_id=safety_action.id,
            severity=sev,
            recommended_action=act_pkg["action_package"].get("immediate_containment_recommendation"),
            actor="AI Safety Action Orchestrator",
            is_simulated=True
        )
        pipeline_steps.append(
            DemoPipelineStepItem(
                step_number=6,
                step_key="ACTION_CREATION",
                step_title="6. AI Action Package & Email Draft",
                status="COMPLETED",
                summary=f"Action {safety_action.id} drafted for {safety_action.assigned_role} ({sla_mins}m SLA)",
                details={"assigned_role": safety_action.assigned_role, "action_type": safety_action.action_type},
                timestamp=now_str
            )
        )

        # Step 7: Notification Dispatch (MOCK SAFE)
        AuditService.log_event(
            db=db,
            event_type="NOTIFICATION",
            trigger=f"Context-Aware Alert Dispatched (Safe Simulation Mode) to {safety_action.assigned_role}",
            report_id=report.id,
            action_id=safety_action.id,
            notification_status="SIMULATED_MOCK_DELIVERED",
            actor="Notification Dispatcher",
            is_simulated=True
        )
        pipeline_steps.append(
            DemoPipelineStepItem(
                step_number=7,
                step_key="NOTIFICATION",
                step_title="7. Safe Notification Dispatch",
                status="COMPLETED",
                summary="Email draft formatted with separate source data vs AI recommendations (External sending suppressed)",
                timestamp=now_str
            )
        )

        # Step 8: Digital Safety Hold (if Critical or High)
        hold_id = None
        if sev in ["CRITICAL", "HIGH"]:
            from app.schemas.safety_hold import SafetyHoldCreateRequest
            hold = SafetyHoldService.request_safety_hold(
                db=db,
                req=SafetyHoldCreateRequest(
                    report_id=report.id,
                    action_id=safety_action.id,
                    permit_id="PTW-2026-CDU1-0982",
                    jsa_id="JSA-CDU1-HOTWORK-041",
                    refinery_unit=unit_name,
                    equipment=template["equipment"],
                    trigger=f"{sev} SIF Precursor",
                    reason=f"Automated stop-work freeze triggered by {sev} SIF Precursor at {unit_name}",
                    bdi=bdi_score,
                    sif_status=sif_stat,
                    requested_by="AI Safety Action Orchestrator"
                )
            )
            hold_id = hold.id
            cls._loaded_hold_id = hold.id

            AuditService.log_event(
                db=db,
                event_type="SAFETY_HOLD",
                trigger=f"Digital Safety Hold {hold.id} Requested — Permit/JSA Frozen",
                report_id=report.id,
                action_id=safety_action.id,
                hold_id=hold.id,
                actor="Safety Hold Engine",
                is_simulated=True
            )
            pipeline_steps.append(
                DemoPipelineStepItem(
                    step_number=8,
                    step_key="SAFETY_HOLD",
                    step_title="8. Digital Safety Hold Requested",
                    status="COMPLETED",
                    summary=f"Hold {hold.id} initiated: Permit PTW-2026-CDU1-0982 & JSA Frozen",
                    details={"hold_status": hold.status, "permit": hold.permit_id},
                    timestamp=now_str
                )
            )

        # Step 9: SLA Countdown Active
        pipeline_steps.append(
            DemoPipelineStepItem(
                step_number=9,
                step_key="SLA_COUNTDOWN",
                step_title="9. Active SLA Countdown",
                status="ACTIVE",
                summary=f"Target Response: {sla_mins}m • Role: {safety_action.assigned_role} • State: NORMAL",
                details={"sla_minutes": sla_mins, "deadline": sla_deadline.isoformat()},
                timestamp=now_str
            )
        )

        return DemoScenarioExecutionResponse(
            scenario_type=scenario_type,
            status="READY_FOR_SIMULATION",
            summary=f"Scenario {scenario_type} initialized at unit {unit_name}. Use time travel controls to simulate SLA breach, escalation, containment, and closure.",
            report_id=report.id,
            action_id=safety_action.id,
            hold_id=hold_id,
            bdi_score=bdi_score,
            sif_status=sif_stat,
            severity=sev,
            pipeline_steps=pipeline_steps,
            email_preview=email_draft.model_dump(),
            sla_info={
                "action_id": safety_action.id,
                "sla_minutes": sla_mins,
                "sla_deadline": sla_deadline.isoformat(),
                "assigned_role": safety_action.assigned_role,
                "sla_state": safety_action.sla_state
            }
        )

    @classmethod
    def time_travel(cls, db: Session, advance_minutes: int, action_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Advances virtual simulation time without making evaluators wait real minutes.
        Shifts SLA deadlines backwards to simulate SLA reminders, warnings, breaches, and escalations.
        """
        cls._simulated_time_offset_minutes += advance_minutes
        target_action_id = action_id or cls._loaded_action_id

        action = None
        if target_action_id:
            action = db.scalars(select(SafetyAction).where(SafetyAction.id == str(target_action_id))).first()

        if action and action.created_at and action.status not in ["CLOSED", "COMPLETED", "VERIFIED"]:
            # Shift action created_at and sla_deadline backwards by the advance amount
            action.created_at = action.created_at - timedelta(minutes=advance_minutes)
            if action.sla_deadline:
                action.sla_deadline = action.sla_deadline - timedelta(minutes=advance_minutes)
            db.commit()
            db.refresh(action)

        # Run background evaluation to trigger SLA states & multi-tier escalations
        eval_res = SLAService.evaluate_and_escalate_actions(db)

        # Refresh action state
        if action:
            db.refresh(action)

        # Log Time Travel Audit Event
        AuditService.log_event(
            db=db,
            event_type="DEMO_SIMULATION",
            trigger=f"Time Travel: Virtual clock advanced by +{advance_minutes}m (Total simulated offset: +{cls._simulated_time_offset_minutes}m)",
            action_id=action.id if action else None,
            report_id=action.report_id if action else None,
            actor="Demo Time Controller",
            is_simulated=True,
            evidence={"advanced_minutes": advance_minutes, "sla_state": action.sla_state if action else "N/A"}
        )

        return {
            "status": "TIME_ADVANCED",
            "advanced_minutes": advance_minutes,
            "total_offset_minutes": cls._simulated_time_offset_minutes,
            "action_sla_state": action.sla_state if action else "N/A",
            "escalation_level": action.escalation_level if action else 0,
            "sla_evaluation_result": eval_res
        }

    @classmethod
    def simulate_step(
        cls,
        db: Session,
        step: str,
        action_id: Optional[str] = None,
        actor_name: str = "Safety Officer",
        actor_role: str = "Safety Officer",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulates individual lifecycle steps: ACKNOWLEDGE, CONTAIN, VERIFY, CLOSE, ESCALATE, TRIGGER_BREACH.
        """
        target_action_id = action_id or cls._loaded_action_id
        if not target_action_id:
            raise ValueError("No active action loaded to simulate step.")

        action = db.scalars(select(SafetyAction).where(SafetyAction.id == str(target_action_id))).first()
        if not action:
            raise ValueError(f"Action {target_action_id} not found.")

        step = step.upper()

        if step == "TRIGGER_BREACH":
            # Force SLA breach and Level 1 escalation
            action.sla_state = "BREACHED"
            action.escalation_level = max(action.escalation_level, 1)
            action.status = "ESCALATED"
            db.commit()

            AuditService.log_event(
                db=db,
                event_type="SLA_BREACH",
                trigger=f"Simulated SLA breach: Window elapsed without response. Escalated to Level 1 (HSE Head)",
                report_id=action.report_id,
                action_id=action.id,
                severity=action.severity,
                escalation_level=1,
                actor="SLA Monitoring Engine",
                is_simulated=True
            )
            return {"status": "BREACH_SIMULATED", "sla_state": "BREACHED", "escalation_level": 1}

        elif step == "ACKNOWLEDGE":
            action.acknowledged_at = datetime.utcnow()
            action.sla_state = "ACKNOWLEDGED"
            action.status = "ACKNOWLEDGED"
            db.commit()

            AuditService.log_event(
                db=db,
                event_type="ACKNOWLEDGEMENT",
                trigger=f"Action acknowledged by {actor_name} ({actor_role}). SLA breach countdown halted.",
                report_id=action.report_id,
                action_id=action.id,
                actor=f"{actor_name} ({actor_role})",
                human_decision="ACKNOWLEDGED",
                is_simulated=True
            )
            return {"status": "ACKNOWLEDGED", "sla_state": "ACKNOWLEDGED"}

        elif step == "CONTAIN":
            action.containment_started_at = datetime.utcnow()
            action.sla_state = "CONTAINED"
            action.status = "CONTAINED"
            db.commit()

            AuditService.log_event(
                db=db,
                event_type="CONTAINMENT",
                trigger=f"Field containment completed: {notes or 'Barriers isolated and hot work suspended'}",
                report_id=action.report_id,
                action_id=action.id,
                actor=f"{actor_name} ({actor_role})",
                human_decision="CONTAINMENT_COMPLETED",
                is_simulated=True
            )
            return {"status": "CONTAINED", "sla_state": "CONTAINED"}

        elif step == "VERIFY":
            action.verified_at = datetime.utcnow()
            action.verified_by = f"{actor_name} ({actor_role})"
            action.sla_state = "VERIFIED"
            action.status = "VERIFIED"
            db.commit()

            AuditService.log_event(
                db=db,
                event_type="VERIFICATION",
                trigger=f"Mandatory physical walkdown verified by {actor_name} ({actor_role}). Controls confirmed intact.",
                report_id=action.report_id,
                action_id=action.id,
                actor=f"{actor_name} ({actor_role})",
                human_decision="VERIFIED",
                is_simulated=True
            )
            return {"status": "VERIFIED", "sla_state": "VERIFIED"}

        elif step == "CLOSE":
            action.closed_at = datetime.utcnow()
            action.sla_state = "CLOSED"
            action.status = "CLOSED"
            db.commit()

            # Release safety hold if active
            hold = db.scalars(select(SafetyHold).where(SafetyHold.action_id == action.id)).first()
            if hold and hold.status != "RELEASED":
                hold.status = "RELEASED"
                hold.release_notes = "Action containment verified. Hold released."
                hold.released_by = actor_name
                hold.released_at = datetime.utcnow()
                db.commit()

            AuditService.log_event(
                db=db,
                event_type="CLOSURE",
                trigger=f"Safety action formally closed and Digital Safety Hold released by {actor_name}",
                report_id=action.report_id,
                action_id=action.id,
                hold_id=hold.id if hold else None,
                actor=f"{actor_name} ({actor_role})",
                human_decision="CLOSED",
                final_resolution="All barrier degradation remediated, walkdown sign-off completed, safety hold released.",
                is_simulated=True
            )
            return {"status": "CLOSED", "sla_state": "CLOSED", "hold_released": True if hold else False}

        elif step == "ESCALATE":
            new_lvl = min(action.escalation_level + 1, 3)
            action.escalation_level = new_lvl
            action.sla_state = "ESCALATED"
            action.status = "ESCALATED"
            db.commit()

            AuditService.log_event(
                db=db,
                event_type="ESCALATION",
                trigger=f"Manual supervisor escalation triggered to Level {new_lvl}",
                report_id=action.report_id,
                action_id=action.id,
                escalation_level=new_lvl,
                actor=f"{actor_name} ({actor_role})",
                is_simulated=True
            )
            return {"status": "ESCALATED", "escalation_level": new_lvl}

        else:
            raise ValueError(f"Unknown step: {step}")

    @classmethod
    def reset_demo_state(cls, db: Session) -> Dict[str, Any]:
        """
        Clears demo simulation cache state.
        """
        cls._simulated_time_offset_minutes = 0
        cls._active_scenario = None
        cls._loaded_report_id = None
        cls._loaded_action_id = None
        cls._loaded_hold_id = None
        return {"status": "DEMO_STATE_RESET"}
