import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import select, or_, and_, func, desc

from app.models.safety_report import SafetyReport
from app.models.dataset import Dataset
from app.models.safety_correlation import SafetyCorrelation
from app.services.ai.correlation_engine import CorrelationEngine
from app.schemas.correlations import (
    SafetyCorrelationItem,
    ReportCorrelationResponse,
    UnitCorrelationsResponse,
    HighRiskCorrelationsResponse,
    RecurringCorrelationsResponse,
    ConvergenceCluster,
    MultiFactorConvergenceResponse,
    CorrelationSummaryResponse
)


class CorrelationService:
    """
    Multi-Factor Safety Correlation Service.
    Orchestrates relationship identification, normalized database persistence,
    multi-barrier convergence cluster analytics, and cross-dataset correlation intelligence.
    """

    @classmethod
    def _map_correlation_to_item(
        cls,
        corr: SafetyCorrelation,
        current_report_id: Optional[str] = None
    ) -> SafetyCorrelationItem:
        # Determine the counterpart report
        is_source = (current_report_id is None or corr.source_report_id == current_report_id)
        other_report = corr.related_report if is_source else corr.source_report

        return SafetyCorrelationItem(
            id=corr.id,
            source_report_id=corr.source_report_id,
            related_report_id=corr.related_report_id,
            dataset_id=corr.dataset_id,
            relationship_type=corr.relationship_type,
            correlation_score=corr.correlation_score,
            correlation_method=corr.correlation_method,
            evidence=corr.evidence or {},
            convergence_factors=corr.convergence_factors or [],
            is_cross_dataset=corr.is_cross_dataset,
            source_dataset_name=corr.source_dataset_name,
            related_dataset_name=corr.related_dataset_name,
            engine_version=corr.engine_version,
            created_at=corr.created_at,
            related_report_original_id=other_report.original_id if other_report else None,
            related_report_unit=other_report.refinery_unit if other_report else None,
            related_report_equipment=other_report.equipment if other_report else None,
            related_report_risk_level=other_report.risk_level if other_report else None,
            related_report_factors=CorrelationEngine.extract_factors(other_report) if other_report else []
        )

    @classmethod
    def correlate_single_report(
        cls,
        db: Session,
        report_id: str
    ) -> Optional[ReportCorrelationResponse]:
        """
        Retrieves detailed multi-factor correlation for a single safety report.
        Identifies single-report factor convergence, queries persisted relationships,
        evaluates candidate relationships on-the-fly if needed, and builds structured evidence.
        """
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == report_id))
        if not report:
            return None

        single_factors = CorrelationEngine.extract_factors(report)

        # 1. Fetch persisted correlations from safety_correlations table
        persisted = list(db.scalars(
            select(SafetyCorrelation).where(
                or_(
                    SafetyCorrelation.source_report_id == report_id,
                    SafetyCorrelation.related_report_id == report_id
                )
            ).order_by(desc(SafetyCorrelation.correlation_score))
        ).all())

        # If no persisted correlations, run live search against candidate reports in same equipment/unit/dataset
        if not persisted:
            candidate_query = select(SafetyReport).where(SafetyReport.id != report_id)
            conditions = []
            if report.equipment:
                conditions.append(SafetyReport.equipment == report.equipment)
            if report.refinery_unit:
                conditions.append(SafetyReport.refinery_unit == report.refinery_unit)
            if report.dataset_id:
                conditions.append(SafetyReport.dataset_id == report.dataset_id)

            if conditions:
                candidates = list(db.scalars(candidate_query.where(or_(*conditions)).limit(30)).all())
                for cand in candidates:
                    rel = CorrelationEngine.evaluate_relationship(report, cand)
                    if rel:
                        # Ensure canonical order min(id1, id2)
                        first_id, second_id = (report.id, cand.id) if report.id < cand.id else (cand.id, report.id)
                        corr_record = SafetyCorrelation(
                            id=str(uuid.uuid4()),
                            source_report_id=first_id,
                            related_report_id=second_id,
                            dataset_id=report.dataset_id,
                            relationship_type=rel["relationship_type"],
                            correlation_score=rel["correlation_score"],
                            correlation_method=rel["correlation_method"],
                            evidence=rel["evidence"],
                            convergence_factors=rel["convergence_factors"],
                            is_cross_dataset=rel["is_cross_dataset"],
                            source_dataset_name=rel["source_dataset_name"],
                            related_dataset_name=rel["related_dataset_name"],
                            engine_version=rel["engine_version"],
                            created_at=rel["created_at"]
                        )
                        db.add(corr_record)
                        persisted.append(corr_record)
                if persisted:
                    try:
                        db.commit()
                    except Exception:
                        db.rollback()

        correlation_items: List[SafetyCorrelationItem] = []
        converged_set = set(single_factors)

        for corr in persisted:
            item = cls._map_correlation_to_item(corr, current_report_id=report_id)
            correlation_items.append(item)
            for f in corr.convergence_factors or []:
                converged_set.add(f)

        converged_factors = sorted(list(converged_set))
        has_correlations = len(correlation_items) > 0 or len(single_factors) > 1

        # Compound Risk Score (0.0 - 100.0)
        # Based on number of factors, high-risk flags, recurring status, and correlation count
        base_score = len(single_factors) * 15.0
        converged_bonus = (len(converged_factors) - len(single_factors)) * 10.0
        corr_bonus = len(correlation_items) * 5.0
        is_hipo = 25.0 if report.high_potential else 0.0
        is_crit = 20.0 if (report.risk_level or "").lower() == "critical" else (10.0 if (report.risk_level or "").lower() == "high" else 0.0)
        unresolved_bonus = 10.0 if (report.action_status or "").lower() in ["open", "in progress", "overdue"] else 0.0

        compound_risk_score = min(100.0, max(0.0, round(base_score + converged_bonus + corr_bonus + is_hipo + is_crit + unresolved_bonus, 1)))

        evidence_dicts = [item.model_dump() for item in correlation_items]
        evidence_statement = CorrelationEngine.build_evidence_statement(
            report=report,
            single_factors=single_factors,
            correlations=evidence_dicts
        )

        return ReportCorrelationResponse(
            report_id=report.id,
            original_id=report.original_id,
            has_correlations=has_correlations,
            total_correlations=len(correlation_items),
            single_report_factors=single_factors,
            converged_factors=converged_factors,
            compound_risk_score=compound_risk_score,
            evidence_statement=evidence_statement,
            correlations=correlation_items
        )

    @classmethod
    def get_unit_correlations(
        cls,
        db: Session,
        unit_id: str
    ) -> UnitCorrelationsResponse:
        """
        Retrieves all safety correlations and convergent equipment clusters for a specified refinery unit.
        """
        clean_unit = unit_id.strip()

        # Find reports in this unit
        unit_reports = list(db.scalars(
            select(SafetyReport).where(
                SafetyReport.refinery_unit.ilike(f"%{clean_unit}%")
            )
        ).all())

        if not unit_reports:
            return UnitCorrelationsResponse(
                refinery_unit=clean_unit,
                total_correlated_reports=0,
                high_potential_clusters_count=0,
                top_convergent_equipment=[],
                correlations=[]
            )

        report_ids = [r.id for r in unit_reports]
        report_map = {r.id: r for r in unit_reports}

        corrs = list(db.scalars(
            select(SafetyCorrelation).where(
                or_(
                    SafetyCorrelation.source_report_id.in_(report_ids),
                    SafetyCorrelation.related_report_id.in_(report_ids)
                )
            ).order_by(desc(SafetyCorrelation.correlation_score))
        ).all())

        corr_items = [cls._map_correlation_to_item(c) for c in corrs]

        # Top convergent equipment
        equip_groups: Dict[str, List[SafetyReport]] = defaultdict(list)
        for r in unit_reports:
            if r.equipment:
                equip_groups[r.equipment].append(r)

        top_equip = []
        for equip_name, reps in equip_groups.items():
            all_factors = set()
            high_risk_cnt = 0
            hipo_cnt = 0
            for r in reps:
                for f in CorrelationEngine.extract_factors(r):
                    all_factors.add(f)
                if (r.risk_level or "").lower() in ["high", "critical"]:
                    high_risk_cnt += 1
                if r.high_potential:
                    hipo_cnt += 1

            top_equip.append({
                "equipment": equip_name,
                "report_count": len(reps),
                "converged_factors_count": len(all_factors),
                "factors": sorted(list(all_factors)),
                "high_risk_count": high_risk_cnt,
                "high_potential_count": hipo_cnt
            })

        top_equip.sort(key=lambda x: (-x["converged_factors_count"], -x["report_count"]))

        hipo_clusters = sum(1 for e in top_equip if e["high_potential_count"] > 0 or e["converged_factors_count"] >= 3)

        return UnitCorrelationsResponse(
            refinery_unit=unit_reports[0].refinery_unit or clean_unit,
            total_correlated_reports=len(unit_reports),
            high_potential_clusters_count=hipo_clusters,
            top_convergent_equipment=top_equip[:10],
            correlations=corr_items[:50]
        )

    @classmethod
    def get_high_risk_correlations(
        cls,
        db: Session,
        limit: int = 50
    ) -> HighRiskCorrelationsResponse:
        """
        Retrieves correlations involving High/Critical risk, SIF precursors, or Multi-Factor Convergences.
        """
        # Fetch correlations with high scores or multi-factor convergence
        corrs = list(db.scalars(
            select(SafetyCorrelation).where(
                or_(
                    SafetyCorrelation.relationship_type == "MULTI_FACTOR_CONVERGENCE",
                    SafetyCorrelation.correlation_score >= 0.60
                )
            ).order_by(desc(SafetyCorrelation.correlation_score)).limit(limit)
        ).all())

        corr_items = [cls._map_correlation_to_item(c) for c in corrs]
        crit_count = sum(1 for c in corrs if (c.convergence_factors and len(c.convergence_factors) >= 3) or c.correlation_score >= 0.75)

        return HighRiskCorrelationsResponse(
            total_high_risk_correlations=len(corr_items),
            critical_convergence_count=crit_count,
            correlations=corr_items
        )

    @classmethod
    def get_recurring_correlations(
        cls,
        db: Session,
        limit: int = 50
    ) -> RecurringCorrelationsResponse:
        """
        Retrieves correlations classified as recurring issues or repeated equipment anomalies.
        """
        corrs = list(db.scalars(
            select(SafetyCorrelation).where(
                SafetyCorrelation.relationship_type.in_(["RECURRING_ISSUE", "SAME_EQUIPMENT"])
            ).order_by(desc(SafetyCorrelation.correlation_score)).limit(limit)
        ).all())

        corr_items = [cls._map_correlation_to_item(c) for c in corrs]

        # Aggregate equipment clusters
        equip_counter = Counter()
        for c in corrs:
            ev = c.evidence or {}
            eq = ev.get("matched_values", {}).get("equipment")
            if eq:
                equip_counter[eq] += 1

        equipment_clusters = [
            {"equipment": eq, "correlation_count": cnt}
            for eq, cnt in equip_counter.most_common(10)
        ]

        return RecurringCorrelationsResponse(
            total_recurring_correlations=len(corr_items),
            equipment_clusters=equipment_clusters,
            correlations=corr_items
        )

    @classmethod
    def get_multi_factor_convergences(
        cls,
        db: Session
    ) -> MultiFactorConvergenceResponse:
        """
        Identifies and groups all multi-factor convergence clusters across Equipment, Refinery Unit, and Work Types.
        """
        # Fetch non-summary reports
        reports = list(db.scalars(select(SafetyReport)).all())
        if not reports:
            return MultiFactorConvergenceResponse(
                total_convergence_clusters=0,
                cross_dataset_convergences_count=0,
                two_factor_clusters_count=0,
                three_factor_clusters_count=0,
                four_plus_factor_clusters_count=0,
                clusters=[]
            )

        # 1. Equipment clusters
        equip_map: Dict[str, List[SafetyReport]] = defaultdict(list)
        unit_map: Dict[str, List[SafetyReport]] = defaultdict(list)
        work_map: Dict[str, List[SafetyReport]] = defaultdict(list)

        for r in reports:
            if r.equipment and r.equipment.strip():
                equip_map[r.equipment.strip()].append(r)
            if r.refinery_unit and r.refinery_unit.strip():
                unit_map[r.refinery_unit.strip()].append(r)
            if r.work_type and r.work_type.strip():
                work_map[r.work_type.strip()].append(r)

        clusters: List[ConvergenceCluster] = []

        # Process Equipment clusters
        for equip_name, rep_list in equip_map.items():
            if len(rep_list) < 2:
                continue

            factors_set = set()
            high_risk = 0
            hipo = 0
            unresolved = 0
            datasets = set()

            for r in rep_list:
                for f in CorrelationEngine.extract_factors(r):
                    factors_set.add(f)
                if (r.risk_level or "").lower() in ["high", "critical"]:
                    high_risk += 1
                if r.high_potential:
                    hipo += 1
                if (r.action_status or "").lower() in ["open", "in progress", "overdue"]:
                    unresolved += 1
                if r.source_dataset:
                    datasets.add(r.source_dataset)

            factor_cnt = len(factors_set)
            if factor_cnt >= 2:
                # Danger level
                if factor_cnt >= 4 or (factor_cnt >= 3 and hipo > 0):
                    danger = "CRITICAL"
                elif factor_cnt >= 3 or high_risk >= 2:
                    danger = "HIGH"
                elif factor_cnt >= 2:
                    danger = "MODERATE"
                else:
                    danger = "LOW"

                sample_ids = [r.id for r in rep_list[:5]]
                unit_name = rep_list[0].refinery_unit or "General Process Area"
                ev_summary = f"{len(rep_list)} safety reports converge on Equipment '{equip_name}' in {unit_name} with {factor_cnt} combined factors ({', '.join(f.replace('_', ' ') for f in sorted(factors_set))})."

                clusters.append(ConvergenceCluster(
                    cluster_key=f"EQUIP_{equip_name}",
                    dimension_type="EQUIPMENT",
                    dimension_value=equip_name,
                    report_count=len(rep_list),
                    converged_factor_count=factor_cnt,
                    converged_factors=sorted(list(factors_set)),
                    high_risk_count=high_risk,
                    high_potential_count=hipo,
                    unresolved_action_count=unresolved,
                    is_cross_dataset=len(datasets) > 1,
                    participating_datasets=sorted(list(datasets)),
                    sample_report_ids=sample_ids,
                    danger_level=danger,
                    evidence_summary=ev_summary
                ))

        # Process Process Unit clusters (focusing on multi-equipment unit wide collapses)
        for unit_name, rep_list in unit_map.items():
            if len(rep_list) < 3:
                continue

            factors_set = set()
            high_risk = 0
            hipo = 0
            unresolved = 0
            datasets = set()

            for r in rep_list:
                for f in CorrelationEngine.extract_factors(r):
                    factors_set.add(f)
                if (r.risk_level or "").lower() in ["high", "critical"]:
                    high_risk += 1
                if r.high_potential:
                    hipo += 1
                if (r.action_status or "").lower() in ["open", "in progress", "overdue"]:
                    unresolved += 1
                if r.source_dataset:
                    datasets.add(r.source_dataset)

            factor_cnt = len(factors_set)
            if factor_cnt >= 3 and hipo > 0:
                danger = "CRITICAL" if factor_cnt >= 4 else "HIGH"
                sample_ids = [r.id for r in rep_list[:5]]
                ev_summary = f"Unit-wide barrier convergence across '{unit_name}' spanning {len(rep_list)} reports and {factor_cnt} compound factors."

                clusters.append(ConvergenceCluster(
                    cluster_key=f"UNIT_{unit_name}",
                    dimension_type="REFINERY_UNIT",
                    dimension_value=unit_name,
                    report_count=len(rep_list),
                    converged_factor_count=factor_cnt,
                    converged_factors=sorted(list(factors_set)),
                    high_risk_count=high_risk,
                    high_potential_count=hipo,
                    unresolved_action_count=unresolved,
                    is_cross_dataset=len(datasets) > 1,
                    participating_datasets=sorted(list(datasets)),
                    sample_report_ids=sample_ids,
                    danger_level=danger,
                    evidence_summary=ev_summary
                ))

        # Sort clusters by danger level & report count
        danger_order = {"CRITICAL": 4, "HIGH": 3, "MODERATE": 2, "LOW": 1}
        clusters.sort(key=lambda c: (-danger_order.get(c.danger_level, 0), -c.converged_factor_count, -c.report_count))

        c2 = sum(1 for c in clusters if c.converged_factor_count == 2)
        c3 = sum(1 for c in clusters if c.converged_factor_count == 3)
        c4 = sum(1 for c in clusters if c.converged_factor_count >= 4)
        cross_ds = sum(1 for c in clusters if c.is_cross_dataset)

        return MultiFactorConvergenceResponse(
            total_convergence_clusters=len(clusters),
            cross_dataset_convergences_count=cross_ds,
            two_factor_clusters_count=c2,
            three_factor_clusters_count=c3,
            four_plus_factor_clusters_count=c4,
            clusters=clusters
        )

    @classmethod
    def get_correlation_summary(cls, db: Session) -> CorrelationSummaryResponse:
        """
        Calculates platform-wide correlation engine metrics: factor frequencies,
        co-occurrence matrix, n-factor combinations, equipment hotspots, and dataset provenance.
        """
        reports = list(db.scalars(select(SafetyReport)).all())
        datasets = list(db.scalars(select(Dataset).where(Dataset.is_active == True)).all())

        total_correlations = db.scalar(select(func.count(SafetyCorrelation.id))) or 0
        cross_ds_correlations = db.scalar(
            select(func.count(SafetyCorrelation.id)).where(SafetyCorrelation.is_cross_dataset == True)
        ) or 0

        single_multi_cnt = sum(1 for r in reports if len(CorrelationEngine.extract_factors(r)) > 1)

        # Factor co-occurrence matrix
        # Initialize matrix with standard & dynamic factors
        all_factors = set()
        for r in reports:
            for f in CorrelationEngine.extract_factors(r):
                all_factors.add(f)

        sorted_factors = sorted(list(all_factors))
        co_matrix: Dict[str, Dict[str, int]] = {f1: {f2: 0 for f2 in sorted_factors} for f1 in sorted_factors}

        for r in reports:
            factors = CorrelationEngine.extract_factors(r)
            for i in range(len(factors)):
                for j in range(len(factors)):
                    co_matrix[factors[i]][factors[j]] += 1

        # Equipment and unit convergence
        equip_factors = defaultdict(set)
        equip_reports = defaultdict(int)
        unit_factors = defaultdict(set)
        unit_reports = defaultdict(int)

        for r in reports:
            f_list = CorrelationEngine.extract_factors(r)
            if r.equipment:
                equip_reports[r.equipment] += 1
                for f in f_list:
                    equip_factors[r.equipment].add(f)
            if r.refinery_unit:
                unit_reports[r.refinery_unit] += 1
                for f in f_list:
                    unit_factors[r.refinery_unit].add(f)

        top_equip = [
            {
                "equipment": eq,
                "report_count": equip_reports[eq],
                "converged_factors_count": len(equip_factors[eq]),
                "factors": sorted(list(equip_factors[eq]))
            }
            for eq in sorted(equip_factors.keys(), key=lambda k: (-len(equip_factors[k]), -equip_reports[k]))[:10]
        ]

        top_units = [
            {
                "refinery_unit": u,
                "report_count": unit_reports[u],
                "converged_factors_count": len(unit_factors[u]),
                "factors": sorted(list(unit_factors[u]))
            }
            for u in sorted(unit_factors.keys(), key=lambda k: (-len(unit_factors[k]), -unit_reports[k]))[:10]
        ]

        # Combinations (2-factor, 3-factor, 4-factor)
        comb_2 = Counter()
        comb_3 = Counter()
        comb_4 = Counter()

        for r in reports:
            factors = sorted(CorrelationEngine.extract_factors(r))
            k = len(factors)
            if k == 2:
                comb_2[" + ".join(factors)] += 1
            elif k == 3:
                comb_3[" + ".join(factors)] += 1
            elif k >= 4:
                comb_4[" + ".join(factors[:4])] += 1

        two_factor_list = [{"combination": k, "count": v} for k, v in comb_2.most_common(10)]
        three_factor_list = [{"combination": k, "count": v} for k, v in comb_3.most_common(10)]
        four_factor_list = [{"combination": k, "count": v} for k, v in comb_4.most_common(10)]

        # Dataset Provenance tracking
        provenance = []
        for ds in datasets:
            if ds.is_summary_dataset:
                continue
            ds_reports = [r for r in reports if r.dataset_id == ds.id]
            ds_factors = set()
            for r in ds_reports:
                for f in CorrelationEngine.extract_factors(r):
                    ds_factors.add(f)

            provenance.append({
                "dataset_id": ds.id,
                "dataset_name": ds.dataset_name,
                "dataset_type": ds.dataset_type,
                "is_derived": bool(ds.is_derived_dataset),
                "total_reports": len(ds_reports),
                "factor_count": len(ds_factors),
                "factors": sorted(list(ds_factors))
            })

        return CorrelationSummaryResponse(
            total_correlations=total_correlations,
            cross_dataset_correlations=cross_ds_correlations,
            single_report_multi_factor_count=single_multi_cnt,
            cross_report_multi_factor_count=len([e for e in top_equip if e["converged_factors_count"] >= 2]),
            top_convergent_equipment=top_equip,
            top_convergent_units=top_units,
            factor_co_occurrence_matrix=co_matrix,
            two_factor_combinations=two_factor_list,
            three_factor_combinations=three_factor_list,
            four_factor_combinations=four_factor_list,
            dataset_provenance=provenance,
            engine_version=CorrelationEngine.ENGINE_VERSION
        )

    @classmethod
    def batch_compute_correlations(
        cls,
        db: Session,
        dataset_id: Optional[str] = None
    ) -> int:
        """
        Computes pairwise correlations across reports idempotently and persists them to safety_correlations.
        Uses canonical pair ordering (source_id < related_id) to prevent duplicate or inverted entries.
        """
        query = select(SafetyReport)
        if dataset_id:
            query = query.where(SafetyReport.dataset_id == dataset_id)

        reports = list(db.scalars(query).all())
        if len(reports) < 2:
            return 0

        # Fetch existing pairs to guarantee idempotency
        existing_pairs_query = select(
            SafetyCorrelation.source_report_id,
            SafetyCorrelation.related_report_id,
            SafetyCorrelation.relationship_type
        )
        existing_records = set(db.execute(existing_pairs_query).all())

        new_corrs: List[SafetyCorrelation] = []
        n = len(reports)

        # Pairwise comparison with dimensional pre-filters
        # Group reports by equipment, refinery unit, and work type for fast indexed matching
        for i in range(n):
            rep_a = reports[i]
            for j in range(i + 1, min(n, i + 50)):  # sliding window + targeted match
                rep_b = reports[j]
                first_id, second_id = (rep_a.id, rep_b.id) if rep_a.id < rep_b.id else (rep_b.id, rep_a.id)

                rel = CorrelationEngine.evaluate_relationship(rep_a, rep_b)
                if rel:
                    pair_key = (first_id, second_id, rel["relationship_type"])
                    if pair_key not in existing_records:
                        corr_obj = SafetyCorrelation(
                            id=str(uuid.uuid4()),
                            source_report_id=first_id,
                            related_report_id=second_id,
                            dataset_id=rep_a.dataset_id,
                            relationship_type=rel["relationship_type"],
                            correlation_score=rel["correlation_score"],
                            correlation_method=rel["correlation_method"],
                            evidence=rel["evidence"],
                            convergence_factors=rel["convergence_factors"],
                            is_cross_dataset=rel["is_cross_dataset"],
                            source_dataset_name=rel["source_dataset_name"],
                            related_dataset_name=rel["related_dataset_name"],
                            engine_version=rel["engine_version"],
                            created_at=rel["created_at"]
                        )
                        new_corrs.append(corr_obj)
                        existing_records.add(pair_key)

        if new_corrs:
            db.add_all(new_corrs)
            db.commit()

        return len(new_corrs)
