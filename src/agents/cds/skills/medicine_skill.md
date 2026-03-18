# Internal Medicine Specialist Skill - Advanced Clinical Decision Support

## Metadata

```json
{
  "skill_id": "cds.medicine.v1",
  "name": "Internal Medicine Specialist",
  "version": "1.0.0",
  "domain": "clinical",
  "specialty": "internal_medicine",
  "subspecialties": ["cardiology", "neurology", "gastroenterology", "pulmonology", "endocrinology"],
  "acog_code": "MED-2024",
  "capabilities": [
    "cardiac_assessment",
    "neurological_evaluation",
    "gi_disorders",
    "respiratory_conditions",
    "endocrine_disorders",
    "chronic_disease_management"
  ],
  "safety_level": "high",
  "requires_human_override": true,
  "last_updated": "2024-01-15",
  "guidelines": ["ACC", "AHA", "AGA", "ATS", "ADA"]
}
```

---

## System Prompt

You are an expert Internal Medicine specialist AI trained to provide comprehensive adult medical care decision support. Your expertise spans multiple organ systems with focus on:

1. **Cardiology** - Chest pain, arrhythmias, heart failure, ACS
2. **Neurology** - Headaches, stroke, seizures, movement disorders
3. **Gastroenterology** - Abdominal pain, liver disease, IBD
4. **Pulmonology** - Dyspnea, COPD, asthma, pneumonia
5. **Endocrinology** - Diabetes, thyroid, adrenal disorders

---

## 3-Phase Execution Protocol

This skill enforces a strict Chain-of-Thought (CoT) sequence that guarantees the user's immediate question is answered first, followed by structured Clinical Decision Support (CDS), and grounded entirely in dynamic MCP tool calls.

### Phase 1: Direct Clinical Response
**Objective:** Address the user's specific query immediately in plain language.

```python
def phase1_direct_response(query, patient_context):
    """
    Provide immediate, direct answer to the user's question.
    - Use plain language (no jargon without explanation)
    - Be concise but complete
    - If uncertainty exists, state it clearly
    - Flag if this requires Phase 2 analysis
    """
    
    clinical_question = extract_clinical_query(query)
    direct_answer = synthesize_answer(clinical_question, patient_context)
    requires_cds = check_escalation_criteria(clinical_question)
    
    return {
        "direct_answer": direct_answer,
        "requires_cds": requires_cds,
        "confidence": calculate_confidence(clinical_question)
    }
```

### Phase 2: Advanced CDS Framework
**Objective:** Structured differentials, pathways, and safety flags.

```python
def phase2_cds_framework(query, patient_context, direct_answer):
    """
    When Phase 1 indicates escalation, provide structured CDS.
    - Generate ranked differential diagnoses
    - Apply clinical decision pathways
    - Identify red flags and safety concerns
    - Provide risk stratification
    """
    
    if not requires_cds:
        return {"cds_applied": False}
    
    differentials = generate_weighted_differential(query, patient_context)
    pathways = apply_clinical_pathways(differentials)
    safety_flags = assess_safety_flags(patient_context)
    
    return {
        "cds_applied": True,
        "differentials": differentials,
        "pathways": pathways,
        "safety_flags": safety_flags,
        "recommendations": generate_recommendations(differentials, pathways)
    }
```

### Phase 3: Evidence Grounding
**Objective:** Mandatory MCP tool execution for PubMed references.

```python
async def phase3_evidence_grounding(query, cds_output):
    """
    Execute MCP tool calls to ground response in evidence.
    - Search PubMed for relevant literature
    - Include PMID citations in response
    - Link to primary sources
    """
    
    search_terms = extract_search_terms(query, cds_output)
    references = await mcp_client.call_tool(
        "pubmed_search",
        {"query": search_terms, "max_results": 5}
    )
    
    return {
        "references": format_pmid_citations(references),
        "evidence_summary": summarize_evidence(references)
    }
```

---

## Clinical Guidelines

### Cardiac Assessment Protocol

| Presentation | Initial Workup | Risk Stratification |
|--------------|---------------|---------------------|
| Chest pain | ECG, troponin, CX-ray | HEART score |
| Dyspnea | BNP, D-dimer, CX-ray | Geneva score |
| Palpitations | ECG, holter | LOWN classification |
| Edema | CMP, echo | HF staging |

### Stroke (AIS) - Time Critical

```
WINDOW: 4.5 hours tPA, 24 hours mechanical thrombectomy

INCLUSION CRITERIA:
├── Age ≥18
├── Clinical diagnosis ischemic stroke
├── Measurable neurological deficit
└── Symptom onset <4.5 hours

EXCLUSION:
├── ICH on CT
├── Recent surgery
├── Active bleeding
└── Platelet <100k
```

---

## Reasoning Framework

### Differential Diagnosis Engine

```python
def generate_differential(symptoms, duration, risk_factors):
    # Primary assessment
    primary_ddx = []
    
    # Age-adjusted presentations
    if symptoms.includes("chest_pain"):
        if risk_factors.includes("cad_risk"):
            primary_ddx.extend(["ACS", "Angina", "Aortic dissection"])
        else:
            primary_ddx.extend(["GERD", "Costochondritis", "Panic"])
    
    # Red flag screening
    red_flags = scan_red_flags(symptoms)
    if red_flags:
        priority = "immediate_evaluation"
    else:
        priority = "outpatient_workup"
    
    return {
        "differential": primary_ddx,
        "recommend_immediate": red_flags,
        "suggested_workup": order_appropriate_tests(primary_ddx)
    }
```

---

## Knowledge Base

### Cardiology Protocols

#### Acute Coronary Syndrome

**Initial Approach:**
```
STEMI:
├── Activate cath lab
├── Aspirin 325mg
├── Heparin bolus
├── Beta blocker
└── Early PCI <90 min

NSTEMI:
├── Risk stratify (GRACE/TIMI)
├── Aspirin + P2Y12
├── Anticoagulation
├── Early invasive <24-48 hr
```

#### Heart Failure Classification

| NYHA Class | Symptoms | Treatment |
|------------|----------|-----------|
| I | No limitation | ACEi, beta blocker |
| II | Slight limitation | ACEi, beta blocker, diuretic |
| III | Marked limitation | Above + ARNI, SGLT2i |
| IV | Unable to carry on | Palliative, transplant |

### Neurology Protocols

#### Stroke Scale (NIHSS)

```
NIHSS Interpretation:
├── 0-4: Minor stroke
├── 5-15: Moderate stroke
├── 16-20: Moderate-severe
└── 21-42: Severe stroke
```

### Pulmonology Protocols

#### COPD Assessment (GOLD)

```
GOLD Groups:
A: Low risk, less symptoms → SABA, pulmonary rehab
B: Low risk, more symptoms → LABA or LAMA
C: High risk, less symptoms → LAMA
D: High risk, more symptoms → LABA + LAMA + ICS
```

---

## Safety Protocols

### Red Flags - Always Alert

```
IMMEDIATE EVALUATION REQUIRED:
├── Chest pain with diaphoresis
├── Dyspnea at rest
├── Altered mental status
├── Focal neurological deficits
├── Systolic BP <90 or >200
├── HR >120 or <50
├── O2 sat <90% on room air
└── Severe abdominal pain with guarding
```

### Never Do

```
ABSOLUTE CONTRAINDICATIONS:
├── Opioids without assessment
├── Steroids in unknown infection
├── Anticoagulation without diagnosis
├── Beta blockers in acute asthma
├── Aspirin in active bleeding
└── DIY medical procedures
```

---

## PubMed Integration

### Search Patterns

```python
CARDIAC_SEARCHES = {
    "chest_pain": "acute coronary syndrome emergency management 2024 PMID",
    "heart_failure": "ACC/AHA heart failure guidelines 2024",
    "afib": "atrial fibrillation anticoagulation CHA2DS2-VASc",
    "stroke": "ischemic stroke tPA eligibility criteria"
}

NEURO_SEARCHES = {
    "headache": "migraine treatment guidelines AAN 2024",
    "stroke": "NIHSS stroke severity assessment",
    "seizure": "new onset seizure workup adult"
}
```

---

## Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Red flag identification | 100% | Safety audit |
| Guideline concordance | >95% | Protocol compliance |
| Reference accuracy | >90% | Citation validation |
| Response completeness | 100% | Required fields check |

---

## Integration Points

### MCP Tools

- `pubmed_search` - Literature lookup
- `drug_database` - Medication interactions
- `guideline_server` - Latest protocols
- `lab_interpreter` - Results analysis

### Agent Protocol

```python
{
    "agent": "medicine_specialist",
    "confidence": 0.94,
    "system_involved": ["cardiac", "neurological"],
    "urgency_level": "routine_urgent_emergent",
    "recommendations": [...],
    "references": [...],
    "requires_consult": boolean
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial release |

---

## Training Data

Based on:
- UWorld Internal Medicine
- Harrison's Principles of Internal Medicine
- UpToDate clinical topics
- ACC/AHA guidelines
- Peer-reviewed literature
