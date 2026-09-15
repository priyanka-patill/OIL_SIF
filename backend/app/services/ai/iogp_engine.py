import re
from typing import Dict, Any, List, Optional, Tuple


class IOGPEngine:
    """
    IOGP (International Association of Oil & Gas Producers) Life-Saving Rules Engine.
    Evaluates safety report narratives and metadata against the 9 official IOGP Life-Saving Rules:
      1. Bypassing Safety Controls
      2. Confined Space
      3. Driving
      4. Energy Isolation
      5. Hot Work
      6. Line of Fire
      7. Safe Mechanical Lifting
      8. Work Authorisation
      9. Working at Height
    """

    IOGP_RULE_PATTERNS = {
        "Energy Isolation": {
            "keywords": [
                r"\bisolat(ion|ed|ing)\b", r"\bloto\b", r"\blockout\b", r"\btagout\b",
                r"\benergized\b", r"\bde[\s-]energiz(ed|ation)\b", r"\bzero[\s-]energy\b",
                r"\bleakage\b", r"\bvalve\s+isolation\b", r"\bpressurized\s+line\b",
                r"\bswitchgear\b", r"\bcircuit\s+breaker\b", r"\belectrical\s+isolation\b"
            ],
            "description": "Verify isolation and zero energy state before work begins."
        },
        "Working at Height": {
            "keywords": [
                r"\bheight\b", r"\bscaffold(ing)?\b", r"\belevated\b", r"\bladder\b",
                r"\bharness\b", r"\bfall\s+arrest\b", r"\blanyard\b", r"\btoe\s?board\b",
                r"\bhandrail\b", r"\bguardrail\b", r"\btie[\s-]off\b", r"\bworking\s+above\b"
            ],
            "description": "Protect yourself against falling when working at height."
        },
        "Confined Space": {
            "keywords": [
                r"\bconfined\s+space\b", r"\bvessel\s+entry\b", r"\btank\s+entry\b",
                r"\bmanhole\b", r"\bentery\s+permit\b", r"\batmospheric\s+testing\b",
                r"\bgas\s+testing\b", r"\boxyg(en|ed)\s+level\b", r"\btrench\s+entry\b"
            ],
            "description": "Obtain authorization before entering a confined space."
        },
        "Hot Work": {
            "keywords": [
                r"\bhot\s+work\b", r"\bweld(ing)?\b", r"\bgrind(ing)?\b", r"\bspark(s)?\b",
                r"\bopen\s+flame\b", r"\bcutting\s+torch\b", r"\bbrazing\b", r"\bfire\s+watch\b",
                r"\bexplosive\s+atmosphere\b", r"\bflammable\s+gas\b"
            ],
            "description": "Control flammables and ignition sources during hot work."
        },
        "Line of Fire": {
            "keywords": [
                r"\bline\s+of\s+fire\b", r"\bsuspended\s+load\b", r"\bmoving\s+machinery\b",
                r"\bpinch\s+point\b", r"\bpressurized\s+hose\b", r"\bstored\s+energy\b",
                r"\bprojectile\b", r"\bfalling\s+object\b", r"\bcrush\s+zone\b"
            ],
            "description": "Keep yourself and others out of the line of fire."
        },
        "Bypassing Safety Controls": {
            "keywords": [
                r"\bbypass(ed|ing)?\b", r"\boverride\b", r"\bdisable(d|ing)?\b",
                r"\bsafety\s+interlock\b", r"\bsafety\s+device\b", r"\binterlock\s+bypassed\b",
                r"\bsafety\s+guard\s+removed\b", r"\balarm\s+disabled\b", r"\bunauthorized\s+change\b"
            ],
            "description": "Obtain authorization before overriding or disabling safety controls."
        },
        "Safe Mechanical Lifting": {
            "keywords": [
                r"\blift(ing)?\b", r"\bcrane\b", r"\bhoist\b", r"\brigging\b",
                r"\bsling\b", r"\bload\s+capacity\b", r"\blifting\s+gear\b", r"\brigger\b",
                r"\bcrane\s+boom\b", r"\bwinch\b"
            ],
            "description": "Plan lifting operations and control the area."
        },
        "Work Authorisation": {
            "keywords": [
                r"\bpermit\s+to\s+work\b", r"\bptw\b", r"\bwork\s+permit\b", r"\bjsa\b",
                r"\bjob\s+safety\s+analysis\b", r"\brisk\s+assessment\b", r"\bunauthorized\b",
                r"\bwithout\s+permit\b", r"\bpermit\s+expired\b"
            ],
            "description": "Work with a valid permit when required."
        },
        "Driving": {
            "keywords": [
                r"\bdriv(e|ing)\b", r"\bvehicle\b", r"\bseatbelt\b", r"\bspeed\s+limit\b",
                r"\bmobile\s+phone\b", r"\bfatigue\b", r"\bforklift\b", r"\btruck\b"
            ],
            "description": "Do not speed, use mobile phones, or drive without seatbelts."
        }
    }

    @classmethod
    def classify_iogp_rules(
        cls,
        text_content: str,
        work_type: Optional[str] = None,
        equipment: Optional[str] = None,
        hazard: Optional[str] = None
    ) -> Tuple[str, List[str], float, str]:
        """
        Returns:
            (primary_rule, secondary_rules, confidence_score, reasoning)
        """
        combined_text = f"{text_content} {work_type or ''} {equipment or ''} {hazard or ''}".lower()
        matches: List[Tuple[str, int, List[str]]] = []

        for rule_name, rule_data in cls.IOGP_RULE_PATTERNS.items():
            found_keywords = []
            score = 0
            for pattern in rule_data["keywords"]:
                matched = re.findall(pattern, combined_text)
                if matched:
                    found_keywords.append(pattern.replace(r"\b", "").replace(r"\s+", " "))
                    score += len(matched)

            # Context boost from work_type field
            if work_type:
                wt_lower = work_type.lower()
                if "hot work" in wt_lower and rule_name == "Hot Work":
                    score += 3
                elif "height" in wt_lower and rule_name == "Working at Height":
                    score += 3
                elif "confined" in wt_lower and rule_name == "Confined Space":
                    score += 3
                elif "isolation" in wt_lower and rule_name == "Energy Isolation":
                    score += 3

            if score > 0:
                matches.append((rule_name, score, found_keywords))

        if not matches:
            return (
                "No clear Life-Saving Rule match",
                [],
                0.0,
                "No explicit evidence matching the 9 IOGP Life-Saving Rules detected in the report narrative."
            )

        # Sort matches by score descending
        matches.sort(key=lambda x: x[1], reverse=True)

        primary_rule = matches[0][0]
        secondary_rules = [m[0] for m in matches[1:] if m[1] >= 1]
        top_score = matches[0][1]

        # Calculate confidence score
        confidence = min(0.96, max(0.65, round(0.60 + (top_score * 0.10), 2)))

        primary_desc = cls.IOGP_RULE_PATTERNS[primary_rule]["description"]
        matched_kw_str = ", ".join(set(matches[0][2]))
        reasoning = (
            f"Primary IOGP Rule '{primary_rule}' identified based on narrative indicators ({matched_kw_str}). "
            f"Rule Requirement: {primary_desc}"
        )

        return primary_rule, secondary_rules, confidence, reasoning
