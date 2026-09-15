import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, func

from app.models.safety_report import SafetyReport
from app.models.safety_correlation import SafetyCorrelation
from app.models.sif_escalation_assessment import SIFEscalationAssessment
from app.services.ai.barrier_engine import BarrierEngine
from app.services.ai.bdi_engine import BDIEngine
from app.services.ai.sif_escalation_engine import SIFEscalationEngine
from app.schemas.sif_escalation import (
    ReportSIFEscalationResponse,
    EscalationItem,
    CriticalEscalationsResponse,
    HighEscalationsResponse,
    SIFEscalationSummaryResponse,
    UnitSIFEscalationResponse,
    PreventiveIntelligencePayload
)


class SIFEscalationService:
    """
    SIF Precursor Escalation Intelligence Service.
    Orchestrates multi-dimensional precursor evaluation, 7-stage conceptual escalation scenario modeling,
    critical hotspot identification, and persistent assessment logging.
    """

    @classmethod
    def get_report_escalation(
        cls,
        db: Session,
        report_id: str
    ) -> Optional[ReportSIFEscalationResponse]:
        """
        Retrieves comprehensive SIF Precursor Escalation evaluation for a specific safety report.
        """
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == report_id))
        if not report:
            return None

        # 1. Fetch cross-report correlations
        corrs = list(db.scalars(
            select(SafetyCorrelation).where(
                or_(
                    SafetyCorrelation.source_report_id == report_id,
                    SafetyCorrelation.related_report_id == report_id
                )
            )
        ).all())

        correlated_ids = set()
        for c in corrs:
            other_id = c.related_report_id if c.source_report_id == report_id else c.source_report_id
            correlated_ids.add(other_id)

        correlated_reports = []
        if correlated_ids:
            correlated_reports = list(db.scalars(
                select(SafetyReport).where(SafetyReport.id.in_(list(correlated_ids)))
            ).all())

        # 2. Extract barriers & BDI
        barriers = BarrierEngine.assess_report_barriers(report)
        bdi_res = BDIEngine.calculate_report_bdi(
            report=report,
            barriers=barriers,
            has_cross_report_correlation=len(correlated_reports) > 0
        )

        # 3. Evaluate SIF Escalation
        res = SIFEscalationEngine.evaluate_escalation(
            report=report,
            barriers=barriers,
            bdi_score=bdi_res["bdi_score"],
            bdi_classification=bdi_res["classification"],
            has_cross_report_correlation=len(correlated_reports) > 0,
            correlated_reports=correlated_reports
        )

        return ReportSIFEscalationResponse(
            report_id=report.id,
            original_id=report.original_id,
            refinery_unit=report.refinery_unit,
            equipment=report.equipment,
            severity=res["severity"],
            severity_color=res["severity_color"],
            sif_precursor_status=res["sif_precursor_status"],
            sif_category=res["sif_category"],
            bdi_score=bdi_res["bdi_score"],
            bdi_classification=bdi_res["classification"],
            why_escalated=res["why_escalated"],
            which_barriers=res["which_barriers"],
            which_factors=res["which_factors"],
            which_reports=res["which_reports"],
            what_exposure=res["what_exposure"],
            what_potential_consequence=res["what_potential_consequence"],
            what_remains_unresolved=res["what_remains_unresolved"],
            what_could_happen=res["what_could_happen"],
            barrier_summary=res["barrier_summary"],
            contributing_factors=res["contributing_factors"],
            escalation_scenario=res["escalation_scenario"],
            preventive_intelligence=res["preventive_intelligence"],
            recommended_immediate_action=res["recommended_immediate_action"],
            recommended_preventive_action=res["recommended_preventive_action"],
            confidence=res["confidence"],
            engine_version=res["engine_version"],
            created_at=res["created_at"]
        )

    @classmethod
    def get_critical_escalations(
        cls,
        db: Session,
        limit: int = 50
    ) -> CriticalEscalationsResponse:
        """
        Retrieves all safety reports categorized at CRITICAL escalation severity.
        """
        reports = list(db.scalars(select(SafetyReport)).all())
        items: List[EscalationItem] = []

        for r in reports:
            barriers = BarrierEngine.assess_report_barriers(r)
            bdi_res = BDIEngine.calculate_report_bdi(r, barriers)
            res = SIFEscalationEngine.evaluate_escalation(
                report=r,
                barriers=barriers,
                bdi_score=bdi_res["bdi_score"],
                bdi_classification=bdi_res["classification"]
            )
            if res["severity"] == "CRITICAL":
                items.append(EscalationItem(
                    report_id=r.id,
                    original_id=r.original_id,
                    refinery_unit=r.refinery_unit,
                    equipment=r.equipment,
                    severity="CRITICAL",
                    sif_category=res["sif_category"],
                    bdi_score=bdi_res["bdi_score"],
                    primary_precursor_hazard=res["what_potential_consequence"],
                    top_compromised_barriers=res["which_barriers"][:3],
                    escalation_scenario_summary=res["what_could_happen"],
                    immediate_containment=res["recommended_immediate_action"],
                    created_at=r.created_at or datetime.utcnow()
                ))

        items.sort(key=lambda x: -x.bdi_score)
        return CriticalEscalationsResponse(
            total_critical_count=len(items),
            items=items[:limit]
        )

    @classmethod
    def get_high_escalations(
        cls,
        db: Session,
        limit: int = 50
    ) -> HighEscalationsResponse:
        """
        Retrieves all safety reports categorized at HIGH escalation severity.
        """
        reports = list(db.scalars(select(SafetyReport)).all())
        items: List[EscalationItem] = []

        for r in reports:
            barriers = BarrierEngine.assess_report_barriers(r)
            bdi_res = BDIEngine.calculate_report_bdi(r, barriers)
            res = SIFEscalationEngine.evaluate_escalation(
                report=r,
                barriers=barriers,
                bdi_score=bdi_res["bdi_score"],
                bdi_classification=bdi_res["classification"]
            )
            if res["severity"] in ["HIGH", "CRITICAL"]:
                items.append(EscalationItem(
                    report_id=r.id,
                    original_id=r.original_id,
                    refinery_unit=r.refinery_unit,
                    equipment=r.equipment,
                    severity=res["severity"],
                    sif_category=res["sif_category"],
                    bdi_score=bdi_res["bdi_score"],
                    primary_precursor_hazard=res["what_potential_consequence"],
                    top_compromised_barriers=res["which_barriers"][:3],
                    escalation_scenario_summary=res["what_could_happen"],
                    immediate_containment=res["recommended_immediate_action"],
                    created_at=r.created_at or datetime.utcnow()
                ))

        items.sort(key=lambda x: (0 if x.severity == "CRITICAL" else 1, -x.bdi_score))
        return HighEscalationsResponse(
            total_high_count=len(items),
            items=items[:limit]
        )

    @classmethod
    def get_escalation_summary(cls, db: Session) -> SIFEscalationSummaryResponse:
        """
        Calculates platform-wide SIF Precursor escalation distribution, precursor rate,
        and top vulnerable refinery process units.
        """
        reports = list(db.scalars(select(SafetyReport)).all())
        tot = len(reports)
        if tot == 0:
            return SIFEscalationSummaryResponse(
                total_reports_evaluated=0,
                normal_count=0,
                watch_count=0,
                elevated_count=0,
                high_count=0,
                critical_count=0,
                sif_precursor_rate=0.0,
                top_escalation_categories=[],
                top_vulnerable_units=[],
                engine_version=SIFEscalationEngine.VERSION
            )

        counts = Counter()
        sif_yes_count = 0
        cat_counter = Counter()
        unit_crit_high: Dict[str, int] = defaultdict(int)

        for r in reports:
            barriers = BarrierEngine.assess_report_barriers(r)
            bdi_res = BDIEngine.calculate_report_bdi(r, barriers)
            res = SIFEscalationEngine.evaluate_escalation(
                report=r,
                barriers=barriers,
                bdi_score=bdi_res["bdi_score"],
                bdi_classification=bdi_res["classification"]
            )
            sev = res["severity"]
            counts[sev] += 1
            if res["sif_precursor_status"]:
                sif_yes_count += 1
                cat_counter[res["sif_category"]] += 1

            if sev in ["CRITICAL", "HIGH"] and r.refinery_unit:
                unit_crit_high[r.refinery_unit] += 1

        top_cats = [{"category": k, "count": v} for k, v in cat_counter.most_common(5)]
        top_units = [{"unit": k, "high_critical_count": v} for k, v in sorted(unit_crit_high.items(), key=lambda x: -x[1])[:5]]

        return SIFEscalationSummaryResponse(
            total_reports_evaluated=tot,
            normal_count=counts["NORMAL"],
            watch_count=counts["WATCH"],
            elevated_count=counts["ELEVATED"],
            high_count=counts["HIGH"],
            critical_count=counts["CRITICAL"],
            sif_precursor_rate=round((sif_yes_count / tot * 100), 1) if tot > 0 else 0.0,
            top_escalation_categories=top_cats,
            top_vulnerable_units=top_units,
            engine_version=SIFEscalationEngine.VERSION
        )

    @classmethod
    def get_unit_escalation(
        cls,
        db: Session,
        unit_id: str
    ) -> UnitSIFEscalationResponse:
        """
        Evaluates cumulative SIF Precursor escalation exposure for an entire refinery process unit.
        """
        clean_unit = unit_id.strip()
        reports = list(db.scalars(
            select(SafetyReport).where(SafetyReport.refinery_unit.ilike(f"%{clean_unit}%"))
        ).all())

        unit_name = reports[0].refinery_unit if reports else clean_unit

        if not reports:
            return UnitSIFEscalationResponse(
                refinery_unit=unit_name,
                unit_escalation_level="NORMAL",
                unit_escalation_color="green",
                total_reports=0,
                critical_reports_count=0,
                high_reports_count=0,
                average_bdi=0.0,
                dominant_sif_hazards=[],
                dominant_compromised_barriers=[],
                unit_preventive_imperative="No active safety observations recorded for this process unit."
            )

        crit_cnt = 0
        high_cnt = 0
        bdi_scores = []
        hazard_counter = Counter()
        barrier_counter = Counter()

        for r in reports:
            barriers = BarrierEngine.assess_report_barriers(r)
            bdi_res = BDIEngine.calculate_report_bdi(r, barriers)
            bdi_scores.append(bdi_res["bdi_score"])
            res = SIFEscalationEngine.evaluate_escalation(
                report=r,
                barriers=barriers,
                bdi_score=bdi_res["bdi_score"],
                bdi_classification=bdi_res["classification"]
            )
            if res["severity"] == "CRITICAL":
                crit_cnt += 1
            elif res["severity"] == "HIGH":
                high_cnt += 1

            if res["sif_precursor_status"]:
                hazard_counter[res["sif_category"]] += 1

            for b_name in res["which_barriers"]:
                barrier_counter[b_name] += 1

        avg_bdi = round(sum(bdi_scores) / len(bdi_scores), 1) if bdi_scores else 0.0

        if crit_cnt >= 1 or (high_cnt >= 2 and avg_bdi >= 50.0):
            unit_level = "CRITICAL"
            unit_color = "red"
            imperative = f"URGENT ESCALATION: Unit exhibits {crit_cnt} critical and {high_cnt} high SIF precursor events. Implement immediate operational barrier stand-down."
        elif high_cnt >= 1 or avg_bdi >= 40.0:
            unit_level = "HIGH"
            unit_color = "orange"
            imperative = f"ELEVATED RISK: Unit has {high_cnt} high-severity precursor observations. Reinforce supervisory oversight and expedite barrier remediation."
        elif avg_bdi >= 20.0:
            unit_level = "ELEVATED"
            unit_color = "amber"
            imperative = "MODERATE SUPERVISION: Monitor barrier health during upcoming routine shifts."
        else:
            unit_level = "NORMAL"
            unit_color = "green"
            imperative = "ROUTINE: Unit safety barriers operate within normal compliant parameters."

        return UnitSIFEscalationResponse(
            refinery_unit=unit_name,
            unit_escalation_level=unit_level,
            unit_escalation_color=unit_color,
            total_reports=len(reports),
            critical_reports_count=crit_cnt,
            high_reports_count=high_cnt,
            average_bdi=avg_bdi,
            dominant_sif_hazards=[{"hazard": k, "count": v} for k, v in hazard_counter.most_common(4)],
            dominant_compromised_barriers=[{"barrier": k, "count": v} for k, v in barrier_counter.most_common(4)],
            unit_preventive_imperative=imperative
        )

    @classmethod
    def batch_assess_escalations(
        cls,
        db: Session,
        dataset_id: Optional[str] = None
    ) -> int:
        """
        Computes and persists SIF Escalation assessments into sif_escalation_assessments table.
        """
        query = select(SafetyReport)
        if dataset_id:
            query = query.where(SafetyReport.dataset_id == dataset_id)

        reports = list(db.scalars(query).all())
        if not reports:
            return 0

        # Idempotency: delete existing assessments before repopulating
        report_ids = [r.id for r in reports]
        db.query(SIFEscalationAssessment).filter(
            SIFEscalationAssessment.report_id.in_(report_ids)
        ).delete(synchronize_session=False)

        new_records = []
        for r in reports:
            barriers = BarrierEngine.assess_report_barriers(r)
            bdi_res = BDIEngine.calculate_report_bdi(r, barriers)
            res = SIFEscalationEngine.evaluate_escalation(
                report=r,
                barriers=barriers,
                bdi_score=bdi_res["bdi_score"],
                bdi_classification=bdi_res["classification"]
            )

            record = SIFEscalationAssessment(
                id=str(uuid.uuid4()),
                report_id=r.id,
                dataset_id=r.dataset_id,
                refinery_unit=r.refinery_unit,
                equipment=r.equipment,
                severity=res["severity"],
                sif_precursor_status=res["sif_precursor_status"],
                sif_category=res["sif_category"],
                bdi_score=bdi_res["bdi_score"],
                bdi_classification=bdi_res["classification"],
                barrier_summary=res["barrier_summary"],
                reasoning={"why_escalated": res["why_escalated"], "what_could_happen": res["what_could_happen"]},
                evidence={"which_barriers": res["which_barriers"], "what_exposure": res["what_exposure"]},
                contributing_factors=res["contributing_factors"],
                unresolved_items=res["what_remains_unresolved"],
                escalation_scenario=[s.model_dump() for s in res["escalation_scenario"]],
                preventive_intelligence=res["preventive_intelligence"].model_dump() if res["preventive_intelligence"] else {},
                immediate_actions=[res["recommended_immediate_action"]],
                preventive_actions=[res["recommended_preventive_action"]],
                confidence=res["confidence"],
                source_report_ids=res["which_reports"],
                engine_version=res["engine_version"],
                created_at=datetime.utcnow()
            )
            new_records.append(record)

        if new_records:
            db.add_all(new_records)
            db.commit()

        return len(new_records)
