import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_, func, desc

from app.models.safety_report import SafetyReport
from app.models.safety_correlation import SafetyCorrelation
from app.models.safety_barrier_assessment import SafetyBarrierAssessment
from app.models.barrier_degradation_assessment import BarrierDegradationAssessment
from app.services.ai.barrier_engine import BarrierEngine
from app.services.ai.bdi_engine import BDIEngine
from app.schemas.bdi import (
    BDIComponentContribution,
    BDIExplainability,
    IndependentMetrics,
    ReportBDIResponse,
    UnitBDIResponse,
    HighBDIItem,
    HighBDIResponse,
    BDISummaryResponse,
    BDITrendPoint,
    BDITrendsResponse,
    BDIConfigResponse
)


class BDIService:
    """
    Barrier Degradation Index (BDI) Intelligence Service.
    Orchestrates analytical scoring of defense barrier erosion across individual reports,
    refinery units, and equipment hotspots with transparent explainability.
    """

    @classmethod
    def get_report_bdi(
        cls,
        db: Session,
        report_id: str
    ) -> Optional[ReportBDIResponse]:
        """
        Calculates and returns the BDI evaluation for a specific safety report.
        """
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == report_id))
        if not report:
            return None

        # 1. Check for cross-report correlations
        corrs_count = db.scalar(
            select(func.count(SafetyCorrelation.id)).where(
                or_(
                    SafetyCorrelation.source_report_id == report_id,
                    SafetyCorrelation.related_report_id == report_id
                )
            )
        ) or 0
        has_cross_report = (corrs_count > 0)

        # 2. Extract barrier assessments
        barriers = BarrierEngine.assess_report_barriers(report)

        # 3. Calculate BDI
        res = BDIEngine.calculate_report_bdi(
            report=report,
            barriers=barriers,
            has_cross_report_correlation=has_cross_report
        )

        return ReportBDIResponse(
            report_id=report.id,
            original_id=report.original_id,
            refinery_unit=report.refinery_unit,
            equipment=report.equipment,
            bdi_score=res["bdi_score"],
            classification=res["classification"],
            classification_color=res["classification_color"],
            independent_metrics=res["independent_metrics"],
            component_contributions=res["component_contributions"],
            barrier_states_summary=res["barrier_states_summary"],
            explainability=res["explainability"],
            source_reports_count=res["source_reports_count"],
            source_report_ids=res["source_report_ids"],
            calculation_version=res["calculation_version"],
            calculated_at=res["calculated_at"]
        )

    @classmethod
    def get_unit_bdi(
        cls,
        db: Session,
        unit_id: str
    ) -> UnitBDIResponse:
        """
        Calculates and returns the BDI evaluation for an entire refinery process unit.
        """
        clean_unit = unit_id.strip()
        reports = list(db.scalars(
            select(SafetyReport).where(SafetyReport.refinery_unit.ilike(f"%{clean_unit}%"))
        ).all())

        unit_name = reports[0].refinery_unit if reports else clean_unit

        # Extract all barrier assessments across reports
        all_barriers = []
        for r in reports:
            all_barriers.extend(BarrierEngine.assess_report_barriers(r))

        res = BDIEngine.calculate_unit_bdi(
            unit_name=unit_name,
            reports=reports,
            unit_barriers=all_barriers
        )

        return UnitBDIResponse(**res)

    @classmethod
    def get_high_bdi(
        cls,
        db: Session,
        limit: int = 50,
        threshold: float = 60.0
    ) -> HighBDIResponse:
        """
        Retrieves all safety exposures with elevated or severe barrier degradation (BDI >= threshold).
        """
        reports = list(db.scalars(select(SafetyReport)).all())
        items: List[HighBDIItem] = []

        for r in reports:
            barriers = BarrierEngine.assess_report_barriers(r)
            bdi_res = BDIEngine.calculate_report_bdi(report=r, barriers=barriers)
            score = bdi_res["bdi_score"]
            if score >= threshold:
                items.append(HighBDIItem(
                    report_id=r.id,
                    original_id=r.original_id,
                    refinery_unit=r.refinery_unit,
                    equipment=r.equipment,
                    bdi_score=score,
                    classification=bdi_res["classification"],
                    top_contributors=bdi_res["explainability"].top_contributors,
                    created_at=r.created_at or datetime.utcnow()
                ))

        # Sort descending by BDI score
        items.sort(key=lambda x: -x.bdi_score)

        severe_cnt = sum(1 for item in items if item.bdi_score >= 80.1)
        high_cnt = sum(1 for item in items if 60.1 <= item.bdi_score <= 80.0)

        return HighBDIResponse(
            total_high_bdi_count=len(items),
            severe_count=severe_cnt,
            high_count=high_cnt,
            items=items[:limit]
        )

    @classmethod
    def get_bdi_summary(cls, db: Session) -> BDISummaryResponse:
        """
        Calculates platform-wide BDI distributions, average score, and top degraded units.
        """
        reports = list(db.scalars(select(SafetyReport)).all())
        tot = len(reports)
        if tot == 0:
            cfg = BDIEngine.get_active_config()
            return BDISummaryResponse(
                total_reports_analyzed=0,
                average_bdi=0.0,
                minimal_count=0,
                low_count=0,
                moderate_count=0,
                high_count=0,
                severe_count=0,
                top_degraded_units=[],
                top_degraded_equipment=[],
                active_weights=cfg["weights"],
                active_thresholds=cfg["thresholds"],
                calculation_version=BDIEngine.VERSION
            )

        scores: List[float] = []
        class_counts = Counter()
        unit_scores: Dict[str, List[float]] = defaultdict(list)
        equip_scores: Dict[str, List[float]] = defaultdict(list)

        for r in reports:
            barriers = BarrierEngine.assess_report_barriers(r)
            res = BDIEngine.calculate_report_bdi(r, barriers)
            score = res["bdi_score"]
            scores.append(score)
            class_counts[res["classification"]] += 1

            if r.refinery_unit:
                unit_scores[r.refinery_unit].append(score)
            if r.equipment:
                equip_scores[r.equipment].append(score)

        avg_bdi = round(sum(scores) / tot, 1)

        top_units = []
        for u, u_s in unit_scores.items():
            top_units.append({
                "unit": u,
                "report_count": len(u_s),
                "avg_bdi": round(sum(u_s) / len(u_s), 1),
                "high_severe_count": sum(1 for s in u_s if s >= 60.1)
            })
        top_units.sort(key=lambda x: -x["avg_bdi"])

        top_equip = []
        for eq, eq_s in equip_scores.items():
            top_equip.append({
                "equipment": eq,
                "report_count": len(eq_s),
                "avg_bdi": round(sum(eq_s) / len(eq_s), 1),
                "max_bdi": max(eq_s)
            })
        top_equip.sort(key=lambda x: -x["avg_bdi"])

        cfg = BDIEngine.get_active_config()

        return BDISummaryResponse(
            total_reports_analyzed=tot,
            average_bdi=avg_bdi,
            minimal_count=class_counts.get("MINIMAL", 0),
            low_count=class_counts.get("LOW", 0),
            moderate_count=class_counts.get("MODERATE", 0),
            high_count=class_counts.get("HIGH", 0),
            severe_count=class_counts.get("SEVERE", 0),
            top_degraded_units=top_units[:5],
            top_degraded_equipment=top_equip[:5],
            active_weights=cfg["weights"],
            active_thresholds=cfg["thresholds"],
            calculation_version=BDIEngine.VERSION
        )

    @classmethod
    def get_bdi_trends(cls, db: Session) -> BDITrendsResponse:
        """
        Calculates monthly and unit-level BDI trend trajectories.
        """
        reports = list(db.scalars(select(SafetyReport)).all())
        month_map: Dict[str, List[float]] = defaultdict(list)
        unit_month_map: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))

        for r in reports:
            date_val = r.report_date or r.created_at
            period = date_val.strftime("%Y-%m") if date_val else "2026-Q1"
            barriers = BarrierEngine.assess_report_barriers(r)
            res = BDIEngine.calculate_report_bdi(r, barriers)
            score = res["bdi_score"]

            month_map[period].append(score)
            if r.refinery_unit:
                unit_month_map[r.refinery_unit][period].append(score)

        monthly_trends: List[BDITrendPoint] = []
        for period, s_list in sorted(month_map.items()):
            monthly_trends.append(BDITrendPoint(
                period=period,
                average_bdi=round(sum(s_list) / len(s_list), 1),
                max_bdi=max(s_list),
                report_count=len(s_list),
                severe_count=sum(1 for s in s_list if s >= 80.1)
            ))

        unit_trends: Dict[str, List[BDITrendPoint]] = {}
        for unit, p_dict in unit_month_map.items():
            u_points = []
            for period, s_list in sorted(p_dict.items()):
                u_points.append(BDITrendPoint(
                    period=period,
                    refinery_unit=unit,
                    average_bdi=round(sum(s_list) / len(s_list), 1),
                    max_bdi=max(s_list),
                    report_count=len(s_list),
                    severe_count=sum(1 for s in s_list if s >= 80.1)
                ))
            unit_trends[unit] = u_points

        return BDITrendsResponse(
            monthly_trends=monthly_trends,
            unit_trends=unit_trends
        )

    @classmethod
    def get_bdi_config(cls) -> BDIConfigResponse:
        """
        Returns active weights, classification thresholds, and explanatory documentation.
        """
        cfg = BDIEngine.get_active_config()
        return BDIConfigResponse(
            weights=cfg["weights"],
            thresholds=cfg["thresholds"],
            version=cfg["version"],
            documentation=cfg["documentation"]
        )

    @classmethod
    def batch_assess_bdi(
        cls,
        db: Session,
        dataset_id: Optional[str] = None
    ) -> int:
        """
        Computes and persists BDI assessments into barrier_degradation_assessments.
        """
        query = select(SafetyReport)
        if dataset_id:
            query = query.where(SafetyReport.dataset_id == dataset_id)

        reports = list(db.scalars(query).all())
        if not reports:
            return 0

        # Idempotency: delete existing assessments for these reports before repopulating
        report_ids = [r.id for r in reports]
        db.query(BarrierDegradationAssessment).filter(
            BarrierDegradationAssessment.report_id.in_(report_ids)
        ).delete(synchronize_session=False)

        new_assessments = []
        for r in reports:
            barriers = BarrierEngine.assess_report_barriers(r)
            res = BDIEngine.calculate_report_bdi(r, barriers)
            
            record = BarrierDegradationAssessment(
                id=str(uuid.uuid4()),
                report_id=r.id,
                dataset_id=r.dataset_id,
                refinery_unit=r.refinery_unit,
                equipment=r.equipment,
                bdi_score=res["bdi_score"],
                classification=res["classification"],
                component_scores={c.component_name: c.points_added for c in res["component_contributions"]},
                contributing_factors=[c.component_name for c in res["component_contributions"]],
                barrier_states_summary=res["barrier_states_summary"],
                evidence=res["explainability"].dict(),
                source_report_ids=res["source_report_ids"],
                calculation_version=res["calculation_version"],
                created_at=datetime.utcnow()
            )
            new_assessments.append(record)

        if new_assessments:
            db.add_all(new_assessments)
            db.commit()

        return len(new_assessments)
