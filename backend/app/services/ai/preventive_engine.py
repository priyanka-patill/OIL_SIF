from typing import Dict, Any, List, Optional


class PreventiveIntelligenceEngine:
    """Generates actionable immediate actions, long-term preventive strategies, 
    and structured 6-stage risk-escalation scenarios."""

    @classmethod
    def generate_immediate_action(
        cls,
        observed_problem: str,
        ppe_items: List[str],
        violation_type: str,
        work_type: Optional[str],
        department: Optional[str],
        sif_precursor: str
    ) -> str:
        ppe_name = ", ".join(ppe_items) if ppe_items else "specified personal protective equipment"
        
        if "welder" in observed_problem.lower() or (work_type and "hot work" in work_type.lower()):
            return f"Immediately pause hot work operations. Remove personnel from active ignition exposure zone. Issue certified {ppe_name} and verify permit-to-work compliance before restarting task."
        
        if "confined" in (work_type or "").lower():
            return f"Temporarily halt confined space entry. Evacuate personnel to safe atmospheric zone, verify continuous gas monitoring, and ensure full mandatory {ppe_name} is donned."

        if violation_type == "DAMAGED_PPE":
            return f"Immediately withdraw defective {ppe_name} from service. Provide certified replacement from site PPE inventory and inspect fitment before permitting task resumption."

        if sif_precursor == "YES":
            return f"Promptly pause ongoing {work_type or 'activity'}. Escort affected {department or 'worker'} to a safe designated area, mandate donning of required {ppe_name}, and obtain supervisor sign-off prior to re-entry."

        return f"Instruct personnel to immediately don mandatory {ppe_name} before proceeding with work. Verify supervisor field check on site."

    @classmethod
    def generate_preventive_action(
        cls,
        observed_problem: str,
        ppe_items: List[str],
        immediate_cause: Optional[str],
        potential_consequence: Optional[str],
        work_type: Optional[str],
        action_status: Optional[str],
        is_recurring: bool,
        previous_similar_reports: Optional[int]
    ) -> str:
        ppe_name = ", ".join(ppe_items) if ppe_items else "mandatory PPE"
        actions = []

        # Recurrence / systemic actions
        if is_recurring or (previous_similar_reports and previous_similar_reports > 0):
            actions.append(f"Conduct a focused HSE compliance audit across {work_type or 'operating activities'} to eliminate recurring non-compliance patterns.")
            actions.append("Implement pre-task physical PPE verification gate at daily shift toolbox talks.")
        else:
            actions.append(f"Incorporate specific briefing on {ppe_name} critical barriers into pre-job safety risk assessments.")

        # Overdue action closure
        if action_status and action_status.lower() == "overdue":
            actions.append("Escalate overdue corrective action items to plant management for immediate resource allocation and closure.")

        # Cause-specific prevention
        if immediate_cause and "equipment" in immediate_cause.lower():
            actions.append("Perform maintenance integrity review and replace aging protective equipment stock.")
        elif immediate_cause and "procedure" in immediate_cause.lower():
            actions.append("Review standard operating procedures (SOPs) with workforce and reinforce stop-work authority.")
        else:
            actions.append("Establish random supervisory PPE spot-checks during critical process maintenance windows.")

        return " ".join(actions)

    @classmethod
    def build_escalation_scenario(
        cls,
        observed_problem: str,
        hazard_identified: str,
        ppe_items: List[str],
        work_type: Optional[str],
        refinery_unit: Optional[str],
        potential_consequence: Optional[str],
        sif_precursor: str
    ) -> Dict[str, str]:
        """
        Builds the 6-stage risk-escalation scenario:
        CURRENT CONDITION -> CONTINUED EXPOSURE -> LOSS OF CONTROL -> INCIDENT -> SERIOUS CONSEQUENCE -> POTENTIAL FATAL CONSEQUENCE
        """
        ppe_desc = ", ".join(ppe_items) if ppe_items else "mandatory PPE"
        unit_desc = refinery_unit if refinery_unit else "process unit"
        consequence_desc = potential_consequence if potential_consequence else "Severe physical trauma"

        step_1_condition = f"Personnel performing {work_type or 'operational task'} in {unit_desc} without required {ppe_desc}."
        step_2_exposure = f"Worker remains exposed in active process operating area with energy hazard ({hazard_identified}) present and personal barrier bypassed."
        step_3_loss_of_control = f"Unexpected process disturbance occurs—such as a pressurized line leak, hot spark dispersion, dropped object, or sudden tool slippage."
        step_4_incident = f"Energy release directly contacts unprotected anatomical region (head, face, eyes, or torso) with zero secondary physical barrier to absorb impact."
        step_5_serious = f"Immediate severe event occurs resulting in {consequence_desc.lower()}, severe burns, traumatic brain injury, or extensive lost-time injury."
        step_6_fatal = f"Potential SIF escalation: In the event of catastrophic energy transfer, delayed emergency rescue, or secondary explosion/toxic asphyxiation, the incident poses credible potential for permanent life-altering impairment or fatality."

        return {
            "current_condition": step_1_condition,
            "continued_exposure": step_2_exposure,
            "loss_of_control": step_3_loss_of_control,
            "incident_event": step_4_incident,
            "serious_consequence": step_5_serious,
            "potential_fatal_consequence": step_6_fatal
        }
