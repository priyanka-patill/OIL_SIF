from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_, and_, desc

from app.models.safety_report import SafetyReport
from app.models.dataset import Dataset
from app.models.report_analysis import ReportAnalysis
from app.schemas.factors import (
    FactorMetric,
    FactorSummaryResponse,
    FactorCombinationItem,
    FactorCombinationsResponse,
    DatasetComparisonResponse,
    HighPotentialIntelligenceResponse,
    HighPotentialPatternItem
)


class FactorService:
    """
    Safety Factor & Factor Combination Intelligence Service.
    Analyzes single-factor distributions, multi-factor compound risks,
    cross-dataset comparisons, and dedicated high-potential precursor patterns.
    """

    STANDARD_FACTOR_KEYS = [
        ("PPE_NonCompliance", "PPE Non-Compliance", "ppe_issue"),
        ("Supervisor_Negligence", "Supervisor Negligence", "supervisor_factor"),
        ("Maintenance_Delay_or_Issue", "Maintenance Delay / Issue", "maintenance_factor"),
        ("Repeated_Issue_Ignored", "Repeated Issue Ignored", "repeated_issue")
    ]

    @classmethod
    def get_factor_summary(
        cls,
        db: Session,
        dataset_id: Optional[str] = None
    ) -> FactorSummaryResponse:
        base_query = select(SafetyReport)
        if dataset_id:
            base_query = base_query.where(SafetyReport.dataset_id == dataset_id)

        reports = list(db.scalars(base_query).all())
        total_reports = len(reports)
        if total_reports == 0:
            return FactorSummaryResponse(
                total_reports_analyzed=0,
                active_dataset_count=0,
                single_factor_reports_count=0,
                multi_factor_reports_count=0,
                high_potential_reports_count=0,
                factors=[]
            )

        active_datasets = len(set(r.dataset_id for r in reports))
        single_factor_count = sum(1 for r in reports if (r.factor_count or 0) == 1)
        multi_factor_count = sum(1 for r in reports if (r.factor_count or 0) > 1)
        hipo_count = sum(1 for r in reports if bool(r.high_potential))

        factor_metrics: List[FactorMetric] = []

        # 1. Standard safety factors
        for factor_key, display_name, attr in cls.STANDARD_FACTOR_KEYS:
            matched = [r for r in reports if getattr(r, attr, False) is True or (r.detected_factors and factor_key in r.detected_factors)]
            cnt = len(matched)
            if cnt > 0:
                high_risk = sum(1 for r in matched if (r.risk_level or "").lower() in ["high", "critical"])
                crit_risk = sum(1 for r in matched if (r.risk_level or "").lower() == "critical")
                hipo = sum(1 for r in matched if bool(r.high_potential))
                recurring = sum(1 for r in matched if bool(r.repeated_issue) or (r.previous_similar_reports or 0) > 0)

                consequences = [r.potential_consequence for r in matched if r.potential_consequence]
                top_consequence = Counter(consequences).most_common(1)[0][0] if consequences else None

                units = [r.refinery_unit for r in matched if r.refinery_unit]
                top_unit = Counter(units).most_common(1)[0][0] if units else None

                factor_metrics.append(FactorMetric(
                    factor_name=factor_key,
                    display_name=display_name,
                    total_count=cnt,
                    percentage=round((cnt / total_reports) * 100, 1),
                    high_risk_count=high_risk,
                    critical_count=crit_risk,
                    high_potential_count=hipo,
                    recurring_count=recurring,
                    top_consequence=top_consequence,
                    top_refinery_unit=top_unit
                ))

        # 2. Dynamically detected extra factor keys
        all_detected = set()
        for r in reports:
            if r.detected_factors:
                for f in r.detected_factors:
                    if f not in [k[0] for k in cls.STANDARD_FACTOR_KEYS]:
                        all_detected.add(f)

        for extra_factor in sorted(all_detected):
            matched = [r for r in reports if r.detected_factors and extra_factor in r.detected_factors]
            cnt = len(matched)
            if cnt > 0:
                high_risk = sum(1 for r in matched if (r.risk_level or "").lower() in ["high", "critical"])
                crit_risk = sum(1 for r in matched if (r.risk_level or "").lower() == "critical")
                hipo = sum(1 for r in matched if bool(r.high_potential))
                recurring = sum(1 for r in matched if bool(r.repeated_issue) or (r.previous_similar_reports or 0) > 0)
                consequences = [r.potential_consequence for r in matched if r.potential_consequence]
                top_consequence = Counter(consequences).most_common(1)[0][0] if consequences else None
                units = [r.refinery_unit for r in matched if r.refinery_unit]
                top_unit = Counter(units).most_common(1)[0][0] if units else None

                factor_metrics.append(FactorMetric(
                    factor_name=extra_factor,
                    display_name=extra_factor.replace("_", " "),
                    total_count=cnt,
                    percentage=round((cnt / total_reports) * 100, 1),
                    high_risk_count=high_risk,
                    critical_count=crit_risk,
                    high_potential_count=hipo,
                    recurring_count=recurring,
                    top_consequence=top_consequence,
                    top_refinery_unit=top_unit
                ))

        return FactorSummaryResponse(
            total_reports_analyzed=total_reports,
            active_dataset_count=active_datasets,
            single_factor_reports_count=single_factor_count,
            multi_factor_reports_count=multi_factor_count,
            high_potential_reports_count=hipo_count,
            factors=factor_metrics
        )

    @classmethod
    def get_factor_combinations(
        cls,
        db: Session,
        dataset_id: Optional[str] = None
    ) -> FactorCombinationsResponse:
        base_query = select(SafetyReport)
        if dataset_id:
            base_query = base_query.where(SafetyReport.dataset_id == dataset_id)

        reports = list(db.scalars(base_query).all())
        total_reports = len(reports)
        if total_reports == 0:
            return FactorCombinationsResponse(
                total_reports_analyzed=0,
                level_1_count=0,
                level_2_count=0,
                level_3_count=0,
                level_4_count=0,
                combinations=[],
                danger_ranked_combinations=[]
            )

        level_1 = sum(1 for r in reports if (r.factor_count or 0) == 1)
        level_2 = sum(1 for r in reports if (r.factor_count or 0) == 2)
        level_3 = sum(1 for r in reports if (r.factor_count or 0) == 3)
        level_4 = sum(1 for r in reports if (r.factor_count or 0) >= 4)

        # Group reports by combination of factors
        comb_map: Dict[str, List[SafetyReport]] = defaultdict(list)
        for r in reports:
            factors = sorted(r.detected_factors or [])
            if not factors:
                factors = ["Unspecified"]
            comb_key = " + ".join([f.replace("_", " ") for f in factors])
            comb_map[comb_key].append(r)

        items: List[FactorCombinationItem] = []
        for comb_key, rep_list in comb_map.items():
            rep_count = len(rep_list)
            first_rep = rep_list[0]
            factor_names = sorted(first_rep.detected_factors or ["Unspecified"])
            factor_cnt = len(factor_names)

            high_risk = sum(1 for r in rep_list if (r.risk_level or "").lower() in ["high", "critical"])
            critical_cnt = sum(1 for r in rep_list if (r.risk_level or "").lower() == "critical")
            hipo_cnt = sum(1 for r in rep_list if bool(r.high_potential))

            high_risk_ratio = round(high_risk / rep_count, 3) if rep_count > 0 else 0.0

            # Calculated AI Danger Score (0 - 100)
            # Formula: (High/Crit Ratio * 40) + (Critical Ratio * 30) + (HiPo Ratio * 20) + (Factor Count * 2.5)
            crit_ratio = critical_cnt / rep_count if rep_count > 0 else 0.0
            hipo_ratio = hipo_cnt / rep_count if rep_count > 0 else 0.0
            score = (high_risk_ratio * 40.0) + (crit_ratio * 30.0) + (hipo_ratio * 20.0) + (min(factor_cnt, 4) * 2.5)
            score = min(100.0, max(0.0, round(score, 1)))

            if score >= 70.0:
                danger_lvl = "CRITICAL"
            elif score >= 45.0:
                danger_lvl = "HIGH"
            elif score >= 25.0:
                danger_lvl = "MODERATE"
            else:
                danger_lvl = "LOW"

            consequences = [r.potential_consequence for r in rep_list if r.potential_consequence]
            top_consequences = [c[0] for c in Counter(consequences).most_common(3)]

            causes = [r.immediate_cause for r in rep_list if r.immediate_cause]
            top_causes = [c[0] for c in Counter(causes).most_common(3)]

            sample_ids = [r.id for r in rep_list[:5]]

            items.append(FactorCombinationItem(
                combination_key=comb_key,
                factor_names=factor_names,
                factor_count=factor_cnt,
                report_count=rep_count,
                high_risk_count=high_risk,
                critical_count=critical_cnt,
                high_potential_count=hipo_cnt,
                high_risk_ratio=high_risk_ratio,
                danger_score=score,
                danger_level=danger_lvl,
                top_consequences=top_consequences,
                top_causes=top_causes,
                sample_report_ids=sample_ids
            ))

        # Sort standard combinations by factor_count then report_count desc
        standard_sorted = sorted(items, key=lambda x: (x.factor_count, -x.report_count))
        # Sort danger ranked combinations by danger_score desc, high_risk_count desc
        danger_sorted = sorted(items, key=lambda x: (-x.danger_score, -x.high_risk_count))

        return FactorCombinationsResponse(
            total_reports_analyzed=total_reports,
            level_1_count=level_1,
            level_2_count=level_2,
            level_3_count=level_3,
            level_4_count=level_4,
            combinations=standard_sorted,
            danger_ranked_combinations=danger_sorted
        )

    @classmethod
    def compare_datasets(
        cls,
        db: Session,
        dataset_id_a: str,
        dataset_id_b: str
    ) -> DatasetComparisonResponse:
        ds_a = db.scalar(select(Dataset).where(Dataset.id == dataset_id_a))
        ds_b = db.scalar(select(Dataset).where(Dataset.id == dataset_id_b))

        reports_a = list(db.scalars(select(SafetyReport).where(SafetyReport.dataset_id == dataset_id_a)).all())
        reports_b = list(db.scalars(select(SafetyReport).where(SafetyReport.dataset_id == dataset_id_b)).all())

        tot_a = len(reports_a)
        tot_b = len(reports_b)

        # 1. Risk distribution comparison
        risk_levels = ["Low", "Medium", "High", "Critical"]
        risk_comp = []
        for rl in risk_levels:
            cnt_a = sum(1 for r in reports_a if (r.risk_level or "").title() == rl.title())
            cnt_b = sum(1 for r in reports_b if (r.risk_level or "").title() == rl.title())
            pct_a = round((cnt_a / tot_a) * 100, 1) if tot_a > 0 else 0.0
            pct_b = round((cnt_b / tot_b) * 100, 1) if tot_b > 0 else 0.0
            risk_comp.append({
                "risk_level": rl,
                "count_a": cnt_a,
                "percentage_a": pct_a,
                "count_b": cnt_b,
                "percentage_b": pct_b,
                "delta_percentage": round(pct_b - pct_a, 1)
            })

        # 2. Factor presence comparison
        factor_comp = []
        for factor_key, display_name, attr in cls.STANDARD_FACTOR_KEYS:
            cnt_a = sum(1 for r in reports_a if getattr(r, attr, False) is True or (r.detected_factors and factor_key in r.detected_factors))
            cnt_b = sum(1 for r in reports_b if getattr(r, attr, False) is True or (r.detected_factors and factor_key in r.detected_factors))
            pct_a = round((cnt_a / tot_a) * 100, 1) if tot_a > 0 else 0.0
            pct_b = round((cnt_b / tot_b) * 100, 1) if tot_b > 0 else 0.0
            factor_comp.append({
                "factor_name": display_name,
                "count_a": cnt_a,
                "percentage_a": pct_a,
                "count_b": cnt_b,
                "percentage_b": pct_b,
                "delta_percentage": round(pct_b - pct_a, 1)
            })

        # 3. Top consequences
        conseq_a = Counter([r.potential_consequence for r in reports_a if r.potential_consequence]).most_common(5)
        conseq_b = Counter([r.potential_consequence for r in reports_b if r.potential_consequence]).most_common(5)

        # 4. Top causes
        cause_a = Counter([r.immediate_cause for r in reports_a if r.immediate_cause]).most_common(5)
        cause_b = Counter([r.immediate_cause for r in reports_b if r.immediate_cause]).most_common(5)

        hipo_a = sum(1 for r in reports_a if bool(r.high_potential))
        hipo_b = sum(1 for r in reports_b if bool(r.high_potential))

        open_a = sum(1 for r in reports_a if (r.action_status or "").lower() in ["open", "overdue"])
        open_b = sum(1 for r in reports_b if (r.action_status or "").lower() in ["open", "overdue"])

        # Generate comparative insights
        insights = []
        high_a = sum(1 for r in reports_a if (r.risk_level or "").lower() in ["high", "critical"])
        high_b = sum(1 for r in reports_b if (r.risk_level or "").lower() in ["high", "critical"])
        high_pct_a = (high_a / tot_a * 100) if tot_a > 0 else 0
        high_pct_b = (high_b / tot_b * 100) if tot_b > 0 else 0

        if high_pct_b > high_pct_a:
            diff = round(high_pct_b - high_pct_a, 1)
            insights.append(f"'{ds_b.dataset_name if ds_b else 'Dataset B'}' displays +{diff}% higher concentration of High/Critical risk compared to '{ds_a.dataset_name if ds_a else 'Dataset A'}'.")
        elif high_pct_a > high_pct_b:
            diff = round(high_pct_a - high_pct_b, 1)
            insights.append(f"'{ds_a.dataset_name if ds_a else 'Dataset A'}' displays +{diff}% higher concentration of High/Critical risk compared to '{ds_b.dataset_name if ds_b else 'Dataset B'}'.")

        if (ds_b and ds_b.factor_count > (ds_a.factor_count if ds_a else 0)):
            insights.append(f"Multi-factor compounding is evident: '{ds_b.dataset_name}' combines {ds_b.factor_count} barrier failures simultaneously, elevating incident severity potential.")

        if hipo_b > 0 and hipo_a == 0:
            insights.append(f"'{ds_b.dataset_name}' introduces {hipo_b} high-potential near-miss scenarios requiring priority management intervention.")

        return DatasetComparisonResponse(
            dataset_a={
                "id": ds_a.id if ds_a else dataset_id_a,
                "name": ds_a.dataset_name if ds_a else "Dataset A",
                "type": ds_a.dataset_type if ds_a else "standard",
                "factor_count": ds_a.factor_count if ds_a else 0,
                "factors": ds_a.factor_names if ds_a else []
            },
            dataset_b={
                "id": ds_b.id if ds_b else dataset_id_b,
                "name": ds_b.dataset_name if ds_b else "Dataset B",
                "type": ds_b.dataset_type if ds_b else "standard",
                "factor_count": ds_b.factor_count if ds_b else 0,
                "factors": ds_b.factor_names if ds_b else []
            },
            total_reports_a=tot_a,
            total_reports_b=tot_b,
            risk_distribution_comparison=risk_comp,
            factor_presence_comparison=factor_comp,
            top_consequences_a=[{"consequence": k, "count": v} for k, v in conseq_a],
            top_consequences_b=[{"consequence": k, "count": v} for k, v in conseq_b],
            top_causes_a=[{"cause": k, "count": v} for k, v in cause_a],
            top_causes_b=[{"cause": k, "count": v} for k, v in cause_b],
            high_potential_count_a=hipo_a,
            high_potential_count_b=hipo_b,
            open_actions_count_a=open_a,
            open_actions_count_b=open_b,
            comparative_insights=insights
        )

    @classmethod
    def get_high_potential_intelligence(cls, db: Session) -> HighPotentialIntelligenceResponse:
        """
        Extracts dedicated intelligence for all high-potential near misses across the platform.
        """
        hipo_reports = list(db.scalars(
            select(SafetyReport).where(
                or_(
                    SafetyReport.high_potential == True,
                    SafetyReport.source_dataset == "12_High_Potential"
                )
            )
        ).all())

        total_hipo = len(hipo_reports)
        if total_hipo == 0:
            return HighPotentialIntelligenceResponse(
                total_high_potential_incidents=0,
                critical_risk_count=0,
                high_risk_count=0,
                multi_barrier_failure_count=0,
                repeated_issue_co_occurrence_count=0,
                top_potential_consequences=[],
                top_immediate_causes=[],
                top_refinery_units=[],
                key_failure_patterns=[],
                preventive_imperatives=[]
            )

        crit_cnt = sum(1 for r in hipo_reports if (r.risk_level or "").lower() == "critical")
        high_cnt = sum(1 for r in hipo_reports if (r.risk_level or "").lower() == "high")
        multi_barrier = sum(1 for r in hipo_reports if (r.factor_count or 0) >= 3)
        repeated_co = sum(1 for r in hipo_reports if bool(r.repeated_issue) or (r.previous_similar_reports or 0) > 0)

        conseq = Counter([r.potential_consequence for r in hipo_reports if r.potential_consequence]).most_common(5)
        causes = Counter([r.immediate_cause for r in hipo_reports if r.immediate_cause]).most_common(5)
        units = Counter([r.refinery_unit for r in hipo_reports if r.refinery_unit]).most_common(5)

        patterns = [
            HighPotentialPatternItem(
                pattern_name="Simultaneous Multi-Control Collapse",
                incident_count=sum(1 for r in hipo_reports if (r.factor_count or 0) >= 4),
                factor_combination=["PPE_NonCompliance", "Supervisor_Negligence", "Maintenance_Delay_or_Issue", "Repeated_Issue_Ignored"],
                immediate_causes=["Unsafe condition", "Procedure not followed", "Inadequate supervision"],
                potential_consequences=["Multiple casualties and major fire", "Major fire", "Hydrocarbon release"],
                affected_units=[u[0] for u in units[:3]],
                severity_rating="CRITICAL PRECURSOR"
            ),
            HighPotentialPatternItem(
                pattern_name="Deferred Maintenance on Critical Process Lines",
                incident_count=sum(1 for r in hipo_reports if bool(r.maintenance_factor) and bool(r.repeated_issue)),
                factor_combination=["Maintenance_Delay_or_Issue", "Repeated_Issue_Ignored"],
                immediate_causes=["Deferred maintenance", "Equipment degradation", "Defective safety equipment"],
                potential_consequences=["Hydrocarbon release", "Explosion / BLEVE", "Toxic gas release"],
                affected_units=[u[0] for u in units[:3]],
                severity_rating="HIGH PRECURSOR"
            )
        ]

        imperatives = [
            "Enforce immediate supervisor verification on all hot work and confined space permits.",
            "Mandate zero-tolerance escalation for recurring equipment vibration and line leakage reports.",
            "Conduct joint HSE-Operations barrier audits across high-concentration refinery process units."
        ]

        return HighPotentialIntelligenceResponse(
            total_high_potential_incidents=total_hipo,
            critical_risk_count=crit_cnt,
            high_risk_count=high_cnt,
            multi_barrier_failure_count=multi_barrier,
            repeated_issue_co_occurrence_count=repeated_co,
            top_potential_consequences=[{"consequence": k, "count": v} for k, v in conseq],
            top_immediate_causes=[{"cause": k, "count": v} for k, v in causes],
            top_refinery_units=[{"unit": k, "count": v} for k, v in units],
            key_failure_patterns=patterns,
            preventive_imperatives=imperatives
        )
