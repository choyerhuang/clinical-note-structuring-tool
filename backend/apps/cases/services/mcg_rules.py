DIABETES_MCG = {
    "condition": "diabetes",
    "admission_criteria": [
        {
            "id": "diabetic_ketoacidosis",
            "description": "diabetic ketoacidosis requiring inpatient management",
            "category": "objective_data",
            "signals": [
                "hyperglycemia >= 200 mg/dL",
                "ketonemia or ketonuria",
                "pH < 7.30",
                "bicarbonate <= 18 mEq/L",
                "anion gap > 12",
            ],
        },
        {
            "id": "severe_dka_or_instability",
            "description": "severe metabolic instability or complications from DKA",
            "category": "clinical_instability",
            "signals": [
                "pH <= 7.25",
                "bicarbonate < 15",
                "hypotension",
                "altered mental status",
                "acute kidney injury (creatinine 2x baseline)",
                "persistent dehydration",
                "electrolyte abnormality",
                "cannot tolerate oral intake",
            ],
        },
        {
            "id": "hyperosmolar_hyperglycemic_state",
            "description": "hyperglycemic hyperosmolar state (HHS)",
            "category": "objective_data",
            "signals": [
                "glucose > 600 mg/dL",
                "serum osmolality > 320 mOsm/kg",
            ],
        },
        {
            "id": "severe_hyperglycemia",
            "description": "hyperglycemia requiring inpatient care",
            "category": "clinical_instability",
            "signals": [
                "hemodynamic instability",
                "severe or persistent altered mental status",
                "severe or persistent dehydration",
                "significant electrolyte abnormality",
                "cannot maintain oral hydration",
                "glucose not controlled despite observation",
            ],
        },
        {
            "id": "failed_observation_or_outpatient",
            "description": "failure of observation or outpatient management",
            "category": "treatment_failure",
            "signals": [
                "persistent acidosis despite observation",
                "persistent dehydration",
                "persistent electrolyte abnormality",
                "glucose not stabilized after treatment",
            ],
        },
        {
            "id": "underlying_condition_requires_inpatient",
            "description": "underlying cause requires inpatient treatment",
            "category": "systemic_risk",
            "signals": [
                "infection requiring IV treatment",
                "sepsis",
                "pancreatitis",
                "myocardial infarction",
                "stroke",
            ],
        },
        {
            "id": "diagnostic_or_management_uncertainty",
            "description": "unclear diagnosis or inability to manage outpatient",
            "category": "systemic_risk",
            "signals": [
                "unclear cause of DKA",
                "newly diagnosed diabetes",
                "no established insulin regimen",
            ],
        },
        {
            "id": "special_population_risk",
            "description": "high-risk populations requiring inpatient monitoring",
            "category": "systemic_risk",
            "signals": [
                "pregnancy",
                "chronic liver disease",
                "chronic kidney disease",
                "SGLT2 inhibitor use",
                "prolonged starvation",
                "alcohol use",
            ],
        },
    ],
    "support_logic": (
        "admission is indicated when severe metabolic derangement, hemodynamic "
        "instability, failure of outpatient management, or high-risk conditions "
        "are present; multiple criteria significantly increase the necessity for "
        "inpatient care"
    ),
}
