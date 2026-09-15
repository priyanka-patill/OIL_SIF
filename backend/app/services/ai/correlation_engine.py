import re
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from collections import Counter
from app.models.safety_report import SafetyReport


class CorrelationEngine:
    """
    Multi-Factor Safety Correlation Engine.
    Identifies single-report and cross-report multi-factor convergences,
    evaluates multi-dimensional relationships across available fields,
    computes correlation confidence scores (similarity indicators, not accident probability),
    and generates structured evidence without claiming causation.
    """

    ENGINE_VERSION = "v1.0.0"

    # Stopwords for text similarity
    STOPWORDS = {
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
        "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
        "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
        "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
        "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
        "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
        "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
        "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
        "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
        "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or",
        "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same",
        "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so",
        "some", "such", "than", "that", "that's", "the", "their", "theirs", "them",
        "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
        "they're", "they've", "this", "those", "through", "to", "too", "under", "until",
        "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've",
        "were", "weren't", "what", "what's", "when", "when's", "where", "where's",
        "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't",
        "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your",
        "yours", "yourself", "yourselves"
    }

    @classmethod
    def extract_factors(cls, report: SafetyReport) -> List[str]:
        """
        Dynamically extracts all active safety factors from a safety report.
        Supports standard factors, extended indicators, and dynamic future factors.
        """
        factors: Set[str] = set()

        # 1. Standard boolean indicators
        if getattr(report, "ppe_issue", False) is True:
            factors.add("PPE_NonCompliance")
        if getattr(report, "supervisor_factor", False) is True:
            factors.add("Supervisor_Negligence")
        if getattr(report, "maintenance_factor", False) is True:
            factors.add("Maintenance_Delay_or_Issue")
        if getattr(report, "repeated_issue", False) is True:
            factors.add("Repeated_Issue_Ignored")

        # 2. Dynamic factors from detected_factors JSON column
        if report.detected_factors and isinstance(report.detected_factors, list):
            for f in report.detected_factors:
                if f and isinstance(f, str) and f.strip():
                    factors.add(f.strip())

        # 3. High Potential Near Miss
        if getattr(report, "high_potential", False) is True:
            factors.add("High_Potential_Near_Miss")

        # 4. Previous Similar Reports
        if (report.previous_similar_reports or 0) > 0:
            factors.add("Previous_Similar_Reports")

        # 5. Unresolved Action
        status = (report.action_status or "").strip().lower()
        if status in ["open", "in progress", "overdue", "pending"]:
            factors.add("Unresolved_Action")

        return sorted(list(factors))

    @classmethod
    def calculate_text_similarity(cls, text_a: Optional[str], text_b: Optional[str]) -> float:
        """
        Calculates Jaccard / token-overlap similarity between two text snippets.
        Returns a float between 0.0 and 1.0.
        """
        if not text_a or not text_b:
            return 0.0

        def tokenize(text: str) -> Set[str]:
            tokens = re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", text.lower())
            return {t for t in tokens if t not in cls.STOPWORDS}

        tokens_a = tokenize(text_a)
        tokens_b = tokenize(text_b)

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b

        return len(intersection) / len(union) if union else 0.0

    @classmethod
    def evaluate_relationship(
        cls,
        report_a: SafetyReport,
        report_b: SafetyReport
    ) -> Optional[Dict[str, Any]]:
        """
        Evaluates cross-report correlation between report_a and report_b.
        Returns correlation attributes dictionary if reliable evidence exists, or None if insufficient.
        """
        if report_a.id == report_b.id:
            return None

        # 1. Field matching
        matched_fields: List[str] = []
        matched_values: Dict[str, Any] = {}

        equip_a = (report_a.equipment or "").strip()
        equip_b = (report_b.equipment or "").strip()
        same_equip = bool(equip_a and equip_b and equip_a.lower() == equip_b.lower())
        if same_equip:
            matched_fields.append("equipment")
            matched_values["equipment"] = report_a.equipment

        unit_a = (report_a.refinery_unit or "").strip()
        unit_b = (report_b.refinery_unit or "").strip()
        same_unit = bool(unit_a and unit_b and unit_a.lower() == unit_b.lower())
        if same_unit:
            matched_fields.append("refinery_unit")
            matched_values["refinery_unit"] = report_a.refinery_unit

        dept_a = (report_a.department or "").strip()
        dept_b = (report_b.department or "").strip()
        same_dept = bool(dept_a and dept_b and dept_a.lower() == dept_b.lower())
        if same_dept:
            matched_fields.append("department")
            matched_values["department"] = report_a.department

        work_a = (report_a.work_type or "").strip()
        work_b = (report_b.work_type or "").strip()
        same_work = bool(work_a and work_b and work_a.lower() == work_b.lower())
        if same_work:
            matched_fields.append("work_type")
            matched_values["work_type"] = report_a.work_type

        cause_a = (report_a.immediate_cause or "").strip()
        cause_b = (report_b.immediate_cause or "").strip()
        same_cause = bool(cause_a and cause_b and cause_a.lower() == cause_b.lower())
        if same_cause:
            matched_fields.append("immediate_cause")
            matched_values["immediate_cause"] = report_a.immediate_cause

        conseq_a = (report_a.potential_consequence or "").strip()
        conseq_b = (report_b.potential_consequence or "").strip()
        same_conseq = bool(conseq_a and conseq_b and conseq_a.lower() == conseq_b.lower())
        if same_conseq:
            matched_fields.append("potential_consequence")
            matched_values["potential_consequence"] = report_a.potential_consequence

        # 2. Factor convergence
        factors_a = cls.extract_factors(report_a)
        factors_b = cls.extract_factors(report_b)
        shared_factors = sorted(list(set(factors_a) & set(factors_b)))
        union_factors = sorted(list(set(factors_a) | set(factors_b)))

        # 3. Description / text similarity
        text_a = f"{report_a.description or ''} {report_a.hazard or ''} {report_a.unsafe_act or ''} {report_a.unsafe_condition or ''}"
        text_b = f"{report_b.description or ''} {report_b.hazard or ''} {report_b.unsafe_act or ''} {report_b.unsafe_condition or ''}"
        text_similarity = cls.calculate_text_similarity(text_a, text_b)

        # 4. Temporal proximity
        days_apart: Optional[int] = None
        if report_a.report_date and report_b.report_date:
            try:
                days_apart = abs((report_a.report_date - report_b.report_date).days)
            except Exception:
                pass

        # 5. Recurrence & Unresolved actions
        is_recurring = bool(
            report_a.repeated_issue or report_b.repeated_issue
            or (report_a.previous_similar_reports or 0) > 0
            or (report_b.previous_similar_reports or 0) > 0
        )
        status_a = (report_a.action_status or "").strip().lower()
        status_b = (report_b.action_status or "").strip().lower()
        has_unresolved_action = (status_a in ["open", "in progress", "overdue"] or status_b in ["open", "in progress", "overdue"])

        # Decide if relationship threshold is met
        # Require at least one concrete dimensional match (same equipment, unit, or text similarity >= 0.40, or same cause/consequence)
        has_anchor = same_equip or same_unit or same_dept or same_work or same_cause or same_conseq or (text_similarity >= 0.40)
        if not has_anchor and not (len(shared_factors) >= 2):
            return None

        # Determine Primary Relationship Type
        if same_equip and len(union_factors) >= 2:
            relationship_type = "MULTI_FACTOR_CONVERGENCE"
            method = "SAME_EQUIPMENT_MULTI_FACTOR_CONVERGENCE"
        elif same_equip:
            relationship_type = "SAME_EQUIPMENT"
            method = "EXACT_EQUIPMENT_MATCH"
        elif same_unit and len(union_factors) >= 2:
            relationship_type = "MULTI_FACTOR_CONVERGENCE"
            method = "SAME_UNIT_MULTI_FACTOR_CONVERGENCE"
        elif same_unit and is_recurring:
            relationship_type = "RECURRING_ISSUE"
            method = "UNIT_RECURRENCE_MATCH"
        elif same_unit and has_unresolved_action:
            relationship_type = "UNRESOLVED_ACTION"
            method = "UNIT_UNRESOLVED_ACTION_MATCH"
        elif text_similarity >= 0.45:
            relationship_type = "SIMILAR_DESCRIPTION"
            method = "SEMANTIC_TEXT_SIMILARITY"
        elif same_cause:
            relationship_type = "SAME_IMMEDIATE_CAUSE"
            method = "EXACT_CAUSE_MATCH"
        elif same_conseq:
            relationship_type = "SAME_POTENTIAL_CONSEQUENCE"
            method = "EXACT_CONSEQUENCE_MATCH"
        elif same_unit:
            relationship_type = "SAME_REFINERY_UNIT"
            method = "EXACT_UNIT_MATCH"
        elif same_dept:
            relationship_type = "SAME_DEPARTMENT"
            method = "EXACT_DEPARTMENT_MATCH"
        elif same_work:
            relationship_type = "SAME_WORK_TYPE"
            method = "EXACT_WORK_TYPE_MATCH"
        elif shared_factors:
            relationship_type = "SAME_FACTOR"
            method = "FACTOR_CO_OCCURRENCE"
        else:
            relationship_type = "MULTI_FACTOR_CONVERGENCE"
            method = "MULTI_DIMENSIONAL_CONVERGENCE"

        # Calculate Correlation Confidence Score (0.0 to 1.0)
        score = 0.0
        if same_equip:
            score += 0.40
        if same_unit:
            score += 0.20
        if same_dept:
            score += 0.10
        if same_work:
            score += 0.10
        if same_cause or same_conseq:
            score += 0.10
        if text_similarity > 0.3:
            score += min(0.20, text_similarity * 0.25)
        if len(shared_factors) > 0:
            score += min(0.20, len(shared_factors) * 0.08)
        if has_unresolved_action:
            score += 0.05
        if days_apart is not None and days_apart <= 30:
            score += 0.05

        correlation_score = min(1.0, max(0.1, round(score, 2)))

        # Build human-readable factual notes (NO causation claimed)
        notes_parts = []
        if same_equip:
            notes_parts.append(f"Both reports reference Equipment '{report_a.equipment}'")
        if same_unit:
            notes_parts.append(f"Located in refinery process unit '{report_a.refinery_unit}'")
        if union_factors:
            notes_parts.append(f"Converging factors observed: {', '.join(f.replace('_', ' ') for f in union_factors)}")
        if has_unresolved_action:
            notes_parts.append("Corrective action remaining unresolved on at least one report")
        if text_similarity >= 0.40:
            notes_parts.append(f"Narrative text similarity score of {round(text_similarity * 100, 1)}%")

        notes = ". ".join(notes_parts) + "." if notes_parts else "Correlated across operational dimensions."

        evidence = {
            "matched_fields": matched_fields,
            "matched_values": matched_values,
            "factors_combined": union_factors,
            "days_apart": days_apart,
            "similarity_score": round(text_similarity, 3) if text_similarity > 0 else None,
            "unresolved_actions": has_unresolved_action,
            "notes": notes
        }

        is_cross_dataset = (report_a.dataset_id != report_b.dataset_id)

        return {
            "source_report_id": report_a.id,
            "related_report_id": report_b.id,
            "dataset_id": report_a.dataset_id,
            "relationship_type": relationship_type,
            "correlation_score": correlation_score,
            "correlation_method": method,
            "evidence": evidence,
            "convergence_factors": union_factors,
            "is_cross_dataset": is_cross_dataset,
            "source_dataset_name": getattr(report_a, "source_dataset", None),
            "related_dataset_name": getattr(report_b, "source_dataset", None),
            "engine_version": cls.ENGINE_VERSION,
            "created_at": datetime.utcnow()
        }

    @classmethod
    def build_evidence_statement(
        cls,
        report: SafetyReport,
        single_factors: List[str],
        correlations: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesizes a clean, objective evidence statement for a safety report.
        """
        if not correlations and len(single_factors) <= 1:
            return "Insufficient evidence for reliable correlation."

        statements = []

        # Single-report convergence
        if len(single_factors) > 1:
            factor_labels = [f.replace("_", " ") for f in single_factors]
            statements.append(
                f"Single-report multi-factor convergence detected: {len(single_factors)} simultaneous barrier failures ({', '.join(factor_labels)})"
            )

        # Cross-report convergence
        if correlations:
            corr_count = len(correlations)
            equip_matches = set()
            units = set()
            all_converged = set(single_factors)
            has_unresolved = False

            for c in correlations:
                ev = c.get("evidence", {})
                if ev.get("matched_values", {}).get("equipment"):
                    equip_matches.add(ev["matched_values"]["equipment"])
                if ev.get("matched_values", {}).get("refinery_unit"):
                    units.add(ev["matched_values"]["refinery_unit"])
                for f in c.get("convergence_factors", []):
                    all_converged.add(f)
                if ev.get("unresolved_actions"):
                    has_unresolved = True

            cross_detail = f"Identified {corr_count} cross-report correlation(s)"
            if equip_matches:
                cross_detail += f" converging on equipment ({', '.join(equip_matches)})"
            elif units:
                cross_detail += f" across unit ({', '.join(units)})"

            statements.append(cross_detail)
            statements.append(f"Total converged factor profile across reports: {', '.join(f.replace('_', ' ') for f in sorted(all_converged))}")

            if has_unresolved:
                statements.append("Active unresolved corrective actions exist in this correlation cluster.")

        return ". ".join(statements) + "." if statements else "Insufficient evidence for reliable correlation."
