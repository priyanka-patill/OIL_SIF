import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_, func, desc

from app.models.safety_report import SafetyReport
from app.models.dataset import Dataset
from app.models.safety_correlation import SafetyCorrelation
from app.models.safety_barrier_assessment import SafetyBarrierAssessment
from app.services.ai.barrier_engine import BarrierEngine
from app.schemas.barriers import (
    BarrierExplainability,
    BarrierAssessmentItem,
    SwissCheeseLayer,
    SwissCheeseVisualization,
    ReportBarrierResponse,
    UnitBarrierResponse,
    CriticalBarrierConvergenceItem,
    CriticalBarriersResponse,
    BarrierSummaryResponse,
    BarrierConvergenceResponse
)


class BarrierService:
    """
    Reason's Swiss Cheese Barrier Intelligence Service.
    Evaluates defense layer degradation, orchestrates cross-report barrier convergence,
    generates explainable Swiss Cheese diagrams, and manages normalized barrier assessments.
    """

    @classmethod
    def get_report_barriers(
        cls,
        db: Session,
        report_id: str
    ) -> Optional[ReportBarrierResponse]:
        """
        Retrieves Swiss Cheese barrier model evaluation for a specific safety report.
        Integrates Phase 1 correlations to present multi-barrier convergence sequences.
        """
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == report_id))
        if not report:
            return None

        # 1. Fetch correlated reports using Phase 1 correlations
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

        # 2. Synthesize barrier assessments
        if correlated_reports:
            barriers = BarrierEngine.synthesize_cross_report_barriers(
                primary_report=report,
                correlated_reports=correlated_reports
            )
            cross_report_active = True
        else:
            barriers = BarrierEngine.assess_report_barriers(report)
            cross_report_active = False

        # 3. Build Swiss Cheese Model
        unit_str = report.refinery_unit or "Process Unit"
        equip_str = f" / Equipment {report.equipment}" if report.equipment else ""
        exposure_target = f"{unit_str}{equip_str} ({report.work_type or 'General Work'})"
        hazard_energy = report.potential_consequence or report.hazard or "Industrial Energy Exposure"

        swiss_cheese = BarrierEngine.build_swiss_cheese_model(
            barriers=barriers,
            exposure_target=exposure_target,
            hazard_energy=hazard_energy
        )

        return ReportBarrierResponse(
            report_id=report.id,
            original_id=report.original_id,
            refinery_unit=report.refinery_unit,
            equipment=report.equipment,
            barriers=barriers,
            swiss_cheese=swiss_cheese,
            cross_report_convergence_present=cross_report_active,
            related_reports_contributing=list(correlated_ids)
        )

    @classmethod
    def get_unit_barriers(
        cls,
        db: Session,
        unit_id: str
    ) -> UnitBarrierResponse:
        """
        Retrieves barrier health and critical equipment convergences for a refinery unit.
        """
        clean_unit = unit_id.strip()
        reports = list(db.scalars(
            select(SafetyReport).where(SafetyReport.refinery_unit.ilike(f"%{clean_unit}%"))
        ).all())

        if not reports:
            return UnitBarrierResponse(
                refinery_unit=clean_unit,
                total_assessments=0,
                degraded_barriers_count=0,
                failed_barriers_count=0,
                barrier_health_scores={},
                critical_equipment_convergences=[],
                recent_assessments=[]
            )

        all_assessments: List[BarrierAssessmentItem] = []
        barrier_status_counts: Dict[str, Counter] = defaultdict(Counter)

        for r in reports:
            b_list = BarrierEngine.assess_report_barriers(r)
            all_assessments.extend(b_list)
            for b in b_list:
                barrier_status_counts[b.barrier_name][b.status] += 1

        degraded_cnt = sum(1 for b in all_assessments if b.status == "DEGRADED")
        failed_cnt = sum(1 for b in all_assessments if b.status == "FAILED")

        # Barrier Health Scores (% Intact)
        health_scores = {}
        for b_name, counts in barrier_status_counts.items():
            tot = sum(counts.values())
            intact = counts.get("INTACT", 0)
            health_scores[b_name] = round((intact / tot * 100), 1) if tot > 0 else 0.0

        # Critical Equipment Convergences in Unit
        equip_reports = defaultdict(list)
        for r in reports:
            if r.equipment:
                equip_reports[r.equipment].append(r)

        equip_convergences = []
        for eq, rep_list in equip_reports.items():
            if len(rep_list) >= 2:
                syn_barriers = BarrierEngine.synthesize_cross_report_barriers(rep_list[0], rep_list[1:])
                holes = sum(1 for b in syn_barriers if b.status in ["DEGRADED", "FAILED"])
                if holes >= 2:
                    equip_convergences.append({
                        "equipment": eq,
                        "report_count": len(rep_list),
                        "holes_aligned_count": holes,
                        "failed_barriers": [b.barrier_name for b in syn_barriers if b.status == "FAILED"],
                        "degraded_barriers": [b.barrier_name for b in syn_barriers if b.status == "DEGRADED"]
                    })

        equip_convergences.sort(key=lambda x: -x["holes_aligned_count"])

        return UnitBarrierResponse(
            refinery_unit=reports[0].refinery_unit or clean_unit,
            total_assessments=len(all_assessments),
            degraded_barriers_count=degraded_cnt,
            failed_barriers_count=failed_cnt,
            barrier_health_scores=health_scores,
            critical_equipment_convergences=equip_convergences[:10],
            recent_assessments=all_assessments[:50]
        )

    @classmethod
    def get_critical_barriers(
        cls,
        db: Session,
        limit: int = 50
    ) -> CriticalBarriersResponse:
        """
        Retrieves critical multi-barrier convergences where 3+ defense layers are compromised.
        """
        reports = list(db.scalars(select(SafetyReport)).all())
        equip_map: Dict[str, List[SafetyReport]] = defaultdict(list)

        for r in reports:
            if r.equipment and r.equipment.strip():
                equip_map[r.equipment.strip()].append(r)

        critical_items: List[CriticalBarrierConvergenceItem] = []

        for equip_name, rep_list in equip_map.items():
            if len(rep_list) < 2:
                # Single report with multiple barrier failures
                barriers = BarrierEngine.assess_report_barriers(rep_list[0])
            else:
                barriers = BarrierEngine.synthesize_cross_report_barriers(rep_list[0], rep_list[1:])

            holes = sum(1 for b in barriers if b.status in ["DEGRADED", "FAILED"])
            failed = [b.barrier_name for b in barriers if b.status == "FAILED"]
            degraded = [b.barrier_name for b in barriers if b.status == "DEGRADED"]

            if holes >= 3 or len(failed) >= 2:
                unit_name = rep_list[0].refinery_unit or "General Process Area"
                exposure_target = f"{unit_name} / Equipment {equip_name}"
                swiss_diag = BarrierEngine.build_swiss_cheese_model(
                    barriers=barriers,
                    exposure_target=exposure_target,
                    hazard_energy=rep_list[0].potential_consequence or "Rotating Equipment Hydrocarbon Exposure"
                )

                critical_items.append(CriticalBarrierConvergenceItem(
                    cluster_key=f"CRIT_EQUIP_{equip_name}",
                    dimension_type="EQUIPMENT",
                    dimension_value=equip_name,
                    refinery_unit=unit_name,
                    holes_aligned_count=holes,
                    failed_barriers=failed,
                    degraded_barriers=degraded,
                    participating_reports_count=len(rep_list),
                    participating_report_ids=[r.id for r in rep_list[:5]],
                    danger_level="CRITICAL" if holes >= 4 or len(failed) >= 2 else "HIGH",
                    swiss_cheese_diagram=swiss_diag
                ))

        critical_items.sort(key=lambda x: (-x.holes_aligned_count, -len(x.failed_barriers)))

        return CriticalBarriersResponse(
            total_critical_convergences=len(critical_items),
            convergences=critical_items[:limit]
        )

    @classmethod
    def get_barrier_summary(cls, db: Session) -> BarrierSummaryResponse:
        """
        Calculates platform-wide barrier defense health metrics, degradation rates, and top weakened barriers.
        """
        reports = list(db.scalars(select(SafetyReport)).all())
        all_assessments: List[BarrierAssessmentItem] = []
        barrier_counter: Dict[str, Counter] = defaultdict(Counter)

        for r in reports:
            b_list = BarrierEngine.assess_report_barriers(r)
            all_assessments.extend(b_list)
            for b in b_list:
                barrier_counter[b.barrier_name][b.status] += 1

        tot_assessments = len(all_assessments)
        if tot_assessments == 0:
            return BarrierSummaryResponse(
                total_reports_analyzed=len(reports),
                total_barrier_assessments=0,
                intact_percentage=0.0,
                degraded_percentage=0.0,
                failed_percentage=0.0,
                unknown_percentage=0.0,
                barrier_breakdown=[],
                top_weakened_barriers=[],
                multi_barrier_convergence_count=0,
                engine_version=BarrierEngine.ENGINE_VERSION
            )

        intact_tot = sum(1 for b in all_assessments if b.status == "INTACT")
        degraded_tot = sum(1 for b in all_assessments if b.status == "DEGRADED")
        failed_tot = sum(1 for b in all_assessments if b.status == "FAILED")
        unknown_tot = sum(1 for b in all_assessments if b.status == "UNKNOWN")

        breakdown = []
        for b_name, cnts in barrier_counter.items():
            b_tot = sum(cnts.values())
            breakdown.append({
                "barrier_name": b_name,
                "total_assessments": b_tot,
                "intact_count": cnts.get("INTACT", 0),
                "degraded_count": cnts.get("DEGRADED", 0),
                "failed_count": cnts.get("FAILED", 0),
                "unknown_count": cnts.get("UNKNOWN", 0),
                "failure_rate": round(((cnts.get("DEGRADED", 0) + cnts.get("FAILED", 0)) / b_tot * 100), 1) if b_tot > 0 else 0.0
            })

        # Top weakened barriers
        top_weakened = sorted(breakdown, key=lambda x: -x["failure_rate"])

        # Count multi-barrier convergences (reports with >= 2 holes)
        multi_conv_count = sum(1 for r in reports if sum(1 for b in BarrierEngine.assess_report_barriers(r) if b.status in ["DEGRADED", "FAILED"]) >= 2)

        return BarrierSummaryResponse(
            total_reports_analyzed=len(reports),
            total_barrier_assessments=tot_assessments,
            intact_percentage=round((intact_tot / tot_assessments * 100), 1),
            degraded_percentage=round((degraded_tot / tot_assessments * 100), 1),
            failed_percentage=round((failed_tot / tot_assessments * 100), 1),
            unknown_percentage=round((unknown_tot / tot_assessments * 100), 1),
            barrier_breakdown=breakdown,
            top_weakened_barriers=top_weakened[:5],
            multi_barrier_convergence_count=multi_conv_count,
            engine_version=BarrierEngine.ENGINE_VERSION
        )

    @classmethod
    def get_barrier_convergences(cls, db: Session) -> BarrierConvergenceResponse:
        """
        Retrieves all multi-barrier convergence clusters across Equipment and Refinery Units.
        """
        crit_resp = cls.get_critical_barriers(db=db, limit=100)
        return BarrierConvergenceResponse(
            total_convergence_clusters=crit_resp.total_critical_convergences,
            critical_clusters_count=sum(1 for c in crit_resp.convergences if c.danger_level == "CRITICAL"),
            clusters=crit_resp.convergences
        )

    @classmethod
    def batch_assess_barriers(
        cls,
        db: Session,
        dataset_id: Optional[str] = None
    ) -> int:
        """
        Computes and persists normalized barrier assessments into safety_barrier_assessments.
        """
        query = select(SafetyReport)
        if dataset_id:
            query = query.where(SafetyReport.dataset_id == dataset_id)

        reports = list(db.scalars(query).all())
        if not reports:
            return 0

        # Idempotency: delete existing assessments for these reports before repopulating
        report_ids = [r.id for r in reports]
        db.query(SafetyBarrierAssessment).filter(
            SafetyBarrierAssessment.report_id.in_(report_ids)
        ).delete(synchronize_session=False)

        new_assessments = []
        for r in reports:
            b_list = BarrierEngine.assess_report_barriers(r)
            for b in b_list:
                record = SafetyBarrierAssessment(
                    id=str(uuid.uuid4()),
                    report_id=r.id,
                    dataset_id=r.dataset_id,
                    refinery_unit=r.refinery_unit,
                    equipment=r.equipment,
                    barrier_name=b.barrier_name,
                    barrier_category=b.barrier_category,
                    layer_index=b.layer_index,
                    status=b.status,
                    confidence=b.confidence,
                    evidence=b.evidence,
                    source_report_ids=b.source_report_ids,
                    source_fields=b.source_fields,
                    is_cross_report=b.is_cross_report,
                    engine_version=b.engine_version,
                    created_at=datetime.utcnow()
                )
                new_assessments.append(record)

        if new_assessments:
            db.add_all(new_assessments)
            db.commit()

        return len(new_assessments)
