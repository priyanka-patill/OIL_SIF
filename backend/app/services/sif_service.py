import uuid
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc

from app.models.safety_report import SafetyReport
from app.models.dataset import Dataset
from app.models.report_analysis import ReportAnalysis
from app.models.ai_feedback import AIFeedback
from app.services.ai.nlp_engine import NLPEngine
from app.services.ai.sif_engine import SIFPrecursorEngine
from app.services.ai.preventive_engine import PreventiveIntelligenceEngine
from app.services.ai.recurrence_engine import RecurrenceEngine
from app.services.ai.iogp_engine import IOGPEngine
from app.schemas.sif import AIFeedbackCreate



class SIFService:
    """Service layer orchestrating AI/NLP analysis, SIF precursor detection, 
    preventive scenarios, recurrence aggregation, and feedback management."""

    @classmethod
    def analyze_report(
        cls,
        db: Session,
        report_id: str,
        recurrence_context: Optional[Dict[str, Any]] = None
    ) -> Optional[ReportAnalysis]:
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == report_id))
        if not report:
            return None

        # Build recurrence context if not passed
        if recurrence_context is None:
            recurrence_context = RecurrenceEngine.analyze_dataset_recurrence(db, report.dataset_id)

        # 1. NLP Text extraction & concept extraction
        text_fields = NLPEngine.extract_text_fields(report)
        primary_desc = text_fields.get("description", report.description or "Unsafe act / condition observed")
        combined_text = " ".join(text_fields.values())

        ppe_items = NLPEngine.extract_ppe_items(combined_text)
        violation_type = NLPEngine.detect_violation_modality(combined_text)
        hazard_identified, exposure_target = NLPEngine.identify_hazard_and_exposure(
            combined_text=combined_text,
            department=report.department,
            work_type=report.work_type,
            refinery_unit=report.refinery_unit,
            ppe_items=ppe_items
        )

        # 2. IOGP Life-Saving Rules Classification
        iogp_rule, secondary_iogp_rules, iogp_confidence, iogp_reasoning = IOGPEngine.classify_iogp_rules(
            text_content=combined_text,
            work_type=report.work_type,
            equipment=report.equipment,
            hazard=hazard_identified
        )

        # Barrier & Control Analysis
        barrier_failure = f"{violation_type} ({', '.join(ppe_items)})" if ppe_items else (
            f"Compromised barrier: {iogp_rule}" if iogp_rule != "No clear Life-Saving Rule match" else "Unsafe act / condition observed"
        )
        missing_control = ", ".join(ppe_items) if ppe_items else (
            f"Required {iogp_rule} controls" if iogp_rule != "No clear Life-Saving Rule match" else "Standard safe work procedure control"
        )
        existing_barrier = "Toolbox talk / standard procedure" if not report.supervisor_factor else "Inadequate supervisory oversight barrier"

        # 3. Recurrence evaluation
        is_recurring, rec_score, rec_details = RecurrenceEngine.evaluate_report_recurrence(
            report=report,
            recurrence_context=recurrence_context
        )

        # 4. SIF Precursor Evaluation & AI Risk (Recorded risk preserved)
        recorded_risk = report.risk_level or "Medium"
        sif_precursor, sif_category, ai_risk_level, confidence, reasoning, org_factors = SIFPrecursorEngine.evaluate_sif(
            hazard_identified=hazard_identified,
            ppe_items=ppe_items,
            violation_type=violation_type,
            recorded_risk=recorded_risk,
            potential_consequence=report.potential_consequence,
            immediate_cause=report.immediate_cause,
            work_type=report.work_type,
            refinery_unit=report.refinery_unit,
            previous_similar_reports=report.previous_similar_reports,
            action_status=report.action_status,
            supervisor_factor=report.supervisor_factor,
            maintenance_factor=report.maintenance_factor,
            repeated_issue=report.repeated_issue,
            high_potential_flag=report.high_potential
        )

        # 5. Immediate & Preventive Action synthesis
        immediate_action = PreventiveIntelligenceEngine.generate_immediate_action(
            observed_problem=primary_desc,
            ppe_items=ppe_items,
            violation_type=violation_type,
            work_type=report.work_type,
            department=report.department,
            sif_precursor=sif_precursor
        )

        preventive_action = PreventiveIntelligenceEngine.generate_preventive_action(
            observed_problem=primary_desc,
            ppe_items=ppe_items,
            immediate_cause=report.immediate_cause,
            potential_consequence=report.potential_consequence,
            work_type=report.work_type,
            action_status=report.action_status,
            is_recurring=is_recurring,
            previous_similar_reports=report.previous_similar_reports
        )

        # 6. Build 6-stage escalation scenario
        escalation_scenario = PreventiveIntelligenceEngine.build_escalation_scenario(
            observed_problem=primary_desc,
            hazard_identified=hazard_identified,
            ppe_items=ppe_items,
            work_type=report.work_type,
            refinery_unit=report.refinery_unit,
            potential_consequence=report.potential_consequence,
            sif_precursor=sif_precursor
        )

        # Check existing human feedback
        latest_feedback = db.scalar(
            select(AIFeedback)
            .where(AIFeedback.report_id == report_id)
            .order_by(desc(AIFeedback.submitted_at))
        )
        human_overridden = latest_feedback is not None
        human_risk_level = latest_feedback.human_risk_level if latest_feedback else None
        human_sif_precursor = latest_feedback.human_sif_precursor if latest_feedback else None
        human_feedback_reason = latest_feedback.feedback_reason if latest_feedback else None

        # 7. Upsert ReportAnalysis record
        existing_analysis = db.scalar(select(ReportAnalysis).where(ReportAnalysis.report_id == report_id))
        if existing_analysis:
            existing_analysis.analysis_timestamp = datetime.utcnow()
            existing_analysis.observed_problem = primary_desc
            existing_analysis.extracted_ppe_items = ppe_items
            existing_analysis.extracted_ppe_issue_type = violation_type
            existing_analysis.hazard_identified = hazard_identified
            existing_analysis.exposure_target = exposure_target
            existing_analysis.immediate_cause = report.immediate_cause
            existing_analysis.potential_consequence = report.potential_consequence
            existing_analysis.recorded_risk_level = recorded_risk
            existing_analysis.ai_risk_level = ai_risk_level
            existing_analysis.sif_precursor = sif_precursor
            existing_analysis.sif_category = sif_category
            existing_analysis.confidence_score = confidence
            existing_analysis.reasoning = reasoning
            existing_analysis.iogp_rule = iogp_rule
            existing_analysis.secondary_iogp_rules = secondary_iogp_rules
            existing_analysis.iogp_confidence = iogp_confidence
            existing_analysis.iogp_reasoning = iogp_reasoning
            existing_analysis.barrier_failure = barrier_failure
            existing_analysis.missing_control = missing_control
            existing_analysis.existing_barrier = existing_barrier
            existing_analysis.is_recurring = is_recurring
            existing_analysis.recurrence_score = rec_score
            existing_analysis.recurrence_details = rec_details
            existing_analysis.immediate_action_recommendation = immediate_action
            existing_analysis.preventive_action_recommendation = preventive_action
            existing_analysis.escalation_scenario = escalation_scenario
            existing_analysis.organizational_factors = org_factors
            existing_analysis.human_overridden = human_overridden
            existing_analysis.human_risk_level = human_risk_level
            existing_analysis.human_sif_precursor = human_sif_precursor
            existing_analysis.human_feedback_reason = human_feedback_reason
            db.commit()
            db.refresh(existing_analysis)
            return existing_analysis
        else:
            analysis = ReportAnalysis(
                id=str(uuid.uuid4()),
                report_id=report.id,
                dataset_id=report.dataset_id,
                analysis_timestamp=datetime.utcnow(),
                model_version="sif-nlp-v2.0",
                observed_problem=primary_desc,
                extracted_ppe_items=ppe_items,
                extracted_ppe_issue_type=violation_type,
                hazard_identified=hazard_identified,
                exposure_target=exposure_target,
                immediate_cause=report.immediate_cause,
                potential_consequence=report.potential_consequence,
                recorded_risk_level=recorded_risk,
                ai_risk_level=ai_risk_level,
                sif_precursor=sif_precursor,
                sif_category=sif_category,
                confidence_score=confidence,
                reasoning=reasoning,
                iogp_rule=iogp_rule,
                secondary_iogp_rules=secondary_iogp_rules,
                iogp_confidence=iogp_confidence,
                iogp_reasoning=iogp_reasoning,
                barrier_failure=barrier_failure,
                missing_control=missing_control,
                existing_barrier=existing_barrier,
                is_recurring=is_recurring,
                recurrence_score=rec_score,
                recurrence_details=rec_details,
                immediate_action_recommendation=immediate_action,
                preventive_action_recommendation=preventive_action,
                escalation_scenario=escalation_scenario,
                organizational_factors=org_factors,
                human_overridden=human_overridden,
                human_risk_level=human_risk_level,
                human_sif_precursor=human_sif_precursor,
                human_feedback_reason=human_feedback_reason
            )
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            return analysis

    @classmethod
    def batch_analyze_dataset(cls, db: Session, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        query = select(SafetyReport)
        if dataset_id:
            query = query.where(SafetyReport.dataset_id == dataset_id)
        
        reports = list(db.scalars(query).all())
        if not reports:
            return {
                "status": "empty",
                "dataset_id": dataset_id or "all",
                "total_reports": 0,
                "analyzed_count": 0,
                "sif_precursor_count": 0,
                "high_risk_count": 0
            }

        # Build recurrence map for fast dataset-wide context
        ds_id_to_use = dataset_id or reports[0].dataset_id
        recurrence_context = RecurrenceEngine.analyze_dataset_recurrence(db, ds_id_to_use)

        analyzed_count = 0
        sif_count = 0
        high_risk_count = 0

        for rep in reports:
            analysis = cls.analyze_report(db, rep.id, recurrence_context=recurrence_context)
            if analysis:
                analyzed_count += 1
                if analysis.sif_precursor == "YES":
                    sif_count += 1
                if analysis.ai_risk_level in ["HIGH", "CRITICAL"]:
                    high_risk_count += 1

        return {
            "status": "completed",
            "dataset_id": ds_id_to_use,
            "total_reports": len(reports),
            "analyzed_count": analyzed_count,
            "sif_precursor_count": sif_count,
            "high_risk_count": high_risk_count
        }

    @classmethod
    def get_analysis_by_report_id(cls, db: Session, report_id: str) -> Optional[ReportAnalysis]:
        analysis = db.scalar(select(ReportAnalysis).where(ReportAnalysis.report_id == report_id))
        if not analysis:
            # Run on-demand analysis if not yet analyzed
            analysis = cls.analyze_report(db, report_id)
        return analysis

    @classmethod
    def get_sif_summary(cls, db: Session, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        query = select(ReportAnalysis)
        if dataset_id:
            query = query.where(ReportAnalysis.dataset_id == dataset_id)

        analyses = list(db.scalars(query).all())
        if not analyses:
            # Auto-trigger batch analysis if empty
            cls.batch_analyze_dataset(db, dataset_id)
            analyses = list(db.scalars(query).all())

        total = len(analyses)
        by_sif = defaultdict(int)
        by_ai_risk = defaultdict(int)
        by_recorded_risk = defaultdict(int)
        by_category = defaultdict(int)
        by_ppe_type = defaultdict(int)
        upgrades = 0

        risk_order = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}

        for a in analyses:
            by_sif[a.sif_precursor] += 1
            by_ai_risk[a.ai_risk_level] += 1
            by_recorded_risk[a.recorded_risk_level] += 1
            by_category[a.sif_category] += 1
            by_ppe_type[a.extracted_ppe_issue_type] += 1

            rec_val = risk_order.get(a.recorded_risk_level.capitalize(), 2)
            ai_val = risk_order.get(a.ai_risk_level.capitalize(), 2)
            if ai_val > rec_val:
                upgrades += 1

        sif_yes = by_sif.get("YES", 0)
        sif_rate = round((sif_yes / total * 100), 1) if total > 0 else 0.0

        # Recurring units and equipment from reports
        reports_query = select(SafetyReport)
        if dataset_id:
            reports_query = reports_query.where(SafetyReport.dataset_id == dataset_id)
        reports = list(db.scalars(reports_query).all())

        unit_counter = defaultdict(int)
        equip_counter = defaultdict(int)
        for r in reports:
            if r.refinery_unit:
                unit_counter[r.refinery_unit] += 1
            if r.equipment:
                equip_counter[r.equipment] += 1

        top_units = [{"name": u, "reports_count": c} for u, c in sorted(unit_counter.items(), key=lambda x: x[1], reverse=True)[:5]]
        top_equipment = [{"name": eq, "reports_count": c} for eq, c in sorted(equip_counter.items(), key=lambda x: x[1], reverse=True)[:5]]

        return {
            "total_analyzed": total,
            "sif_precursors_detected": sif_yes,
            "sif_precursor_rate_percentage": sif_rate,
            "by_sif_precursor": dict(by_sif),
            "by_ai_risk_level": dict(by_ai_risk),
            "by_recorded_risk_level": dict(by_recorded_risk),
            "risk_level_upgrades": upgrades,
            "by_sif_category": dict(by_category),
            "by_ppe_issue_type": dict(by_ppe_type),
            "top_recurring_units": top_units,
            "top_recurring_equipment": top_equipment
        }

    @classmethod
    def get_high_risk_reports(
        cls,
        db: Session,
        dataset_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ReportAnalysis], int]:
        query = select(ReportAnalysis).where(
            (ReportAnalysis.sif_precursor == "YES") |
            (ReportAnalysis.ai_risk_level.in_(["HIGH", "CRITICAL"]))
        ).order_by(desc(ReportAnalysis.confidence_score))

        if dataset_id:
            query = query.where(ReportAnalysis.dataset_id == dataset_id)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        offset = (page - 1) * page_size
        items = list(db.scalars(query.offset(offset).limit(page_size)).all())

        return items, total

    @classmethod
    def get_recurring_issues(cls, db: Session, dataset_id: Optional[str] = None) -> Dict[str, Any]:
        query = select(ReportAnalysis)
        if dataset_id:
            query = query.where(ReportAnalysis.dataset_id == dataset_id)
        analyses = list(db.scalars(query).all())

        # If empty, run batch analysis
        if not analyses:
            cls.batch_analyze_dataset(db, dataset_id)
            analyses = list(db.scalars(query).all())

        # Group by Equipment, Unit, Department, Work Type
        equip_group = defaultdict(list)
        unit_group = defaultdict(list)
        dept_group = defaultdict(list)
        wt_group = defaultdict(list)

        for a in analyses:
            rep = a.report
            if not rep:
                continue
            if rep.equipment:
                equip_group[rep.equipment].append(a)
            if rep.refinery_unit:
                unit_group[rep.refinery_unit].append(a)
            if rep.department:
                dept_group[rep.department].append(a)
            if rep.work_type:
                wt_group[rep.work_type].append(a)

        def make_items(group_dict, cat_name):
            items = []
            for ident, a_list in sorted(group_dict.items(), key=lambda x: len(x[1]), reverse=True):
                if len(a_list) > 1 or cat_name in ["Refinery Unit", "Department"]:
                    sif_cnt = sum(1 for a in a_list if a.sif_precursor == "YES")
                    high_cnt = sum(1 for a in a_list if a.ai_risk_level in ["HIGH", "CRITICAL"])
                    sample_descs = [a.observed_problem for a in a_list[:3]]
                    sample_ids = [a.report.original_id or a.report_id for a in a_list[:3] if a.report]
                    items.append({
                        "category": cat_name,
                        "identifier": ident,
                        "count": len(a_list),
                        "sif_precursor_count": sif_cnt,
                        "high_risk_count": high_cnt,
                        "sample_descriptions": sample_descs,
                        "sample_report_ids": sample_ids
                    })
            return items

        equip_items = make_items(equip_group, "Equipment")
        unit_items = make_items(unit_group, "Refinery Unit")
        dept_items = make_items(dept_group, "Department")
        wt_items = make_items(wt_group, "Work Type")

        total_clusters = len(equip_items) + len(unit_items) + len(dept_items) + len(wt_items)

        return {
            "total_recurring_clusters": total_clusters,
            "by_equipment": equip_items,
            "by_refinery_unit": unit_items,
            "by_department": dept_items,
            "by_work_type": wt_items
        }

    @classmethod
    def submit_feedback(cls, db: Session, feedback_data: AIFeedbackCreate) -> AIFeedback:
        report = db.scalar(select(SafetyReport).where(SafetyReport.id == feedback_data.report_id))
        if not report:
            raise ValueError(f"Report {feedback_data.report_id} does not exist.")

        # Ensure analysis exists
        analysis = cls.get_analysis_by_report_id(db, feedback_data.report_id)

        feedback = AIFeedback(
            id=str(uuid.uuid4()),
            report_id=feedback_data.report_id,
            analysis_id=analysis.id,
            reviewer_name=feedback_data.reviewer_name,
            agrees_with_ai=feedback_data.agrees_with_ai,
            human_risk_level=feedback_data.human_risk_level,
            human_sif_precursor=feedback_data.human_sif_precursor,
            feedback_reason=feedback_data.feedback_reason,
            submitted_at=datetime.utcnow()
        )
        db.add(feedback)

        # Update Analysis record with human override details
        if analysis:
            analysis.human_overridden = True
            analysis.human_risk_level = feedback_data.human_risk_level
            analysis.human_sif_precursor = feedback_data.human_sif_precursor
            analysis.human_feedback_reason = feedback_data.feedback_reason

        db.commit()
        db.refresh(feedback)
        return feedback

    @classmethod
    def get_feedback_by_report_id(cls, db: Session, report_id: str) -> List[AIFeedback]:
        return list(db.scalars(
            select(AIFeedback)
            .where(AIFeedback.report_id == report_id)
            .order_by(desc(AIFeedback.submitted_at))
        ).all())
