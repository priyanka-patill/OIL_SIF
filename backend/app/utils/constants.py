# Canonical safety report schema field definitions
CANONICAL_FIELDS = {
    "original_id": {"type": "STRING", "description": "Original report identifier from source system"},
    "report_date": {"type": "DATETIME", "description": "Date or timestamp when incident/observation occurred"},
    "location": {"type": "STRING", "description": "General plant/site location"},
    "refinery_unit": {"type": "STRING", "description": "Specific refinery process unit or plant section"},
    "equipment": {"type": "STRING", "description": "Equipment tag or machinery ID"},
    "work_type": {"type": "STRING", "description": "Type of work or operation being performed"},
    "department": {"type": "STRING", "description": "Department or contractor responsible"},
    "report_type": {"type": "STRING", "description": "Observation classification (e.g. Near Miss, Unsafe Act)"},
    "description": {"type": "TEXT", "description": "Full narrative description of the incident or unsafe event"},
    "hazard": {"type": "TEXT", "description": "Specific hazard identified"},
    "unsafe_act": {"type": "TEXT", "description": "Unsafe act performed by personnel"},
    "unsafe_condition": {"type": "TEXT", "description": "Unsafe physical condition in work environment"},
    "ppe_issue": {"type": "BOOLEAN", "description": "Indicates whether PPE non-compliance was involved"},
    "immediate_cause": {"type": "STRING", "description": "Direct/immediate factor causing event"},
    "potential_consequence": {"type": "STRING", "description": "Worst-case potential consequence if unmitigated"},
    "risk_level": {"type": "STRING", "description": "Assessed risk rating (e.g. Low, Medium, High)"},
    "sif_precursor": {"type": "BOOLEAN", "description": "Flag indicating Serious Injury or Fatality precursor"},
    "high_potential": {"type": "BOOLEAN", "description": "High Potential (HiPo) near miss flag"},
    "previous_similar_reports": {"type": "INTEGER", "description": "Count of prior similar incidents on record"},
    "repeated_issue": {"type": "BOOLEAN", "description": "Flag indicating repeated/recurring issue ignored"},
    "supervisor_factor": {"type": "BOOLEAN", "description": "Flag indicating supervisor negligence/factor"},
    "maintenance_factor": {"type": "BOOLEAN", "description": "Flag indicating maintenance delay/issue"},
    "corrective_action": {"type": "TEXT", "description": "Assigned or implemented corrective action"},
    "action_status": {"type": "STRING", "description": "Current status of action item (Open, Closed, etc.)"},
    "source_dataset": {"type": "STRING", "description": "Source dataset name"}
}

# Semantic mapping patterns for fuzzy and alias matching
SEMANTIC_PATTERNS = {
    "original_id": [
        r"^near[_\s-]?miss[_\s-]?id$", r"^incident[_\s-]?id$", r"^report[_\s-]?id$",
        r"^observation[_\s-]?id$", r"^record[_\s-]?id$", r"^id$"
    ],
    "report_date": [
        r"^date$", r"^incident[_\s-]?date$", r"^observation[_\s-]?date$",
        r"^report[_\s-]?date$", r"^event[_\s-]?date$", r"^timestamp$"
    ],
    "refinery_unit": [
        r"^refinery[_\s-]?unit$", r"^unit$", r"^plant[_\s-]?unit$",
        r"^process[_\s-]?unit$", r"^unit[_\s-]?name$", r"^facility[_\s-]?area$"
    ],
    "location": [
        r"^location$", r"^site$", r"^facility$", r"^plant$", r"^area$"
    ],
    "equipment": [
        r"^equipment[_\s-]?id$", r"^equipment$", r"^asset[_\s-]?id$",
        r"^tag[_\s-]?no$", r"^tag[_\s-]?number$", r"^machine[_\s-]?id$"
    ],
    "work_type": [
        r"^work[_\s-]?type$", r"^activity[_\s-]?type$", r"^task[_\s-]?type$",
        r"^operation[_\s-]?type$", r"^job[_\s-]?type$"
    ],
    "department": [
        r"^department$", r"^dept$", r"^group$", r"^contractor$", r"^team$", r"^section$"
    ],
    "description": [
        r"^near[_\s-]?miss[_\s-]?description$", r"^incident[_\s-]?description$",
        r"^description$", r"^observation$", r"^details$", r"^summary$",
        r"^event[_\s-]?description$", r"^narrative$"
    ],
    "ppe_issue": [
        r"^ppe[_\s-]?noncompliance$", r"^ppe[_\s-]?issue$", r"^ppe[_\s-]?violation$",
        r"^ppe[_\s-]?non[_\s-]?compliance$", r"^ppe$"
    ],
    "supervisor_factor": [
        r"^supervisor[_\s-]?negligence$", r"^supervisor[_\s-]?factor$",
        r"^supervision[_\s-]?failure$"
    ],
    "maintenance_factor": [
        r"^maintenance[_\s-]?delay[_\s-]?or[_\s-]?issue$", r"^maintenance[_\s-]?issue$",
        r"^maintenance[_\s-]?delay$", r"^maintenance[_\s-]?factor$"
    ],
    "repeated_issue": [
        r"^repeated[_\s-]?issue[_\s-]?ignored$", r"^repeat[_\s-]?issue$",
        r"^recurring[_\s-]?issue$"
    ],
    "previous_similar_reports": [
        r"^previous[_\s-]?similar[_\s-]?reports$", r"^prior[_\s-]?incidents$",
        r"^previous[_\s-]?reports$", r"^similar[_\s-]?events[_\s-]?count$"
    ],
    "immediate_cause": [
        r"^immediate[_\s-]?cause$", r"^direct[_\s-]?cause$", r"^cause$"
    ],
    "potential_consequence": [
        r"^potential[_\s-]?consequence$", r"^consequence$", r"^potential[_\s-]?severity$",
        r"^worst[_\s-]?case[_\s-]?outcome$"
    ],
    "risk_level": [
        r"^risk[_\s-]?level$", r"^risk[_\s-]?rating$", r"^severity[_\s-]?level$",
        r"^risk[_\s-]?category$", r"^risk$"
    ],
    "corrective_action": [
        r"^corrective[_\s-]?action$", r"^recommended[_\s-]?action$",
        r"^mitigation[_\s-]?action$", r"^action[_\s-]?plan$", r"^remediation$"
    ],
    "action_status": [
        r"^action[_\s-]?status$", r"^status$", r"^closure[_\s-]?status$",
        r"^state$", r"^progress[_\s-]?status$"
    ],
    "high_potential": [
        r"^high[_\s-]?potential[_\s-]?near[_\s-]?miss$", r"^high[_\s-]?potential$",
        r"^hipo$", r"^hipo[_\s-]?flag$"
    ]
}
