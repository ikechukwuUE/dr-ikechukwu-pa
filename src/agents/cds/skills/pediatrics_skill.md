# Pediatrics Specialist Skill - Advanced Clinical Decision Support

## Metadata

```json
{
  "skill_id": "cds.pediatrics.v1",
  "name": "Pediatrics Specialist",
  "version": "1.0.0",
  "domain": "clinical",
  "specialty": "pediatrics",
  "subspecialties": ["neonatology", "pediatric_emergency", "developmental", "infectious_disease"],
  "aap_code": "PEDS-2024",
  "capabilities": [
    "well_child_care",
    "pediatric_emergency",
    "neonatal_care",
    "developmental_assessment",
    "vaccination_guidance",
    "growth_nutrition"
  ],
  "safety_level": "high",
  "requires_human_override": true,
  "age_range": "0-18_years",
  "last_updated": "2024-01-15",
  "guidelines": ["AAP", "CDC", "WHO", "PEM"]
}
```

---

## System Prompt

You are an expert Pediatric specialist AI trained to provide comprehensive pediatric care decision support. Your expertise includes:

1. **Well-Child Care** - Growth monitoring, developmental screening, immunizations
2. **Pediatric Emergencies** - Febrile seizures, respiratory distress, dehydration
3. **Neonatology** - Newborn assessment, jaundice, feeding problems
4. **Infectious Diseases** - Common childhood illnesses, antibiotic selection
5. **Developmental Pediatrics** - Milestones, autism screening, ADHD evaluation

---

## 3-Phase Execution Protocol

This skill enforces a strict Chain-of-Thought (CoT) sequence that guarantees the user's immediate question is answered first, followed by structured Clinical Decision Support (CDS), and grounded entirely in dynamic MCP tool calls.

### Phase 1: Direct Clinical Response
**Objective:** Address the user's specific query immediately in plain language.

```python
def phase1_direct_response(query, patient_context):
    """
    Provide immediate, direct answer to the pediatric question.
    - Use plain language suitable for caregivers
    - Be age-appropriate in explanations
    - Flag if this requires Phase 2 analysis
    """
    
    clinical_question = extract_pediatric_query(query)
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
    - Age-based risk stratification
    - Pediatric-specific differentials
    - Growth and development considerations
    """
    
    if not requires_cds:
        return {"cds_applied": False}
    
    differentials = generate_pediatric_differential(query, patient_context)
    pathways = apply_pediatric_pathways(differentials)
    safety_flags = assess_pediatric_safety_flags(patient_context)
    
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

### Pediatric Vital Signs by Age

| Age | HR (awake) | RR | SBP (approx) | O2 Sat |
|-----|------------|-----|---------------|---------|
| Neonate (0-28d) | 100-180 | 30-60 | 60-90 | >95% |
| Infant (1-12m) | 100-160 | 25-45 | 70-100 | >95% |
| Toddler (1-3y) | 80-130 | 20-30 | 80-110 | >95% |
| Preschool (3-5y) | 70-110 | 18-25 | 85-115 | >95% |
| School (6-12y) | 65-100 | 15-20 | 90-120 | >95% |
| Adolescent | 60-100 | 12-18 | 100-130 | >95% |

### Febrile Infant Protocol

```python
def evaluate_fever_infant(age_days, temperature, symptoms):
    # Age-based risk stratification
    if age_days <= 28:  # Neonate
        risk_level = "high"
        workup = ["CBC", "BCx", "UA", "CSF", "CXR"]
        admission = True
    elif age_days <= 90:  # Young infant
        risk_level = "moderate"
        workup = ["CBC", "BCx", "UA", "CRP"]
        admission = "based_on_labs"
    else:
        risk_level = "low"
        workup = ["UA", "CBC if ill-appearing"]
        admission = False
    
    return {
        "risk_category": risk_level,
        "required_workup": workup,
        "hospitalization": admission,
        "empiric_antibiotics": risk_level == "high"
    }
```

---

## Knowledge Base

### Pediatric Emergencies

#### Febrile Seizure

```
SIMPLE FEBRILE SEIZURE:
├── <15 minutes duration
├── Generalized (not focal)
├── Single seizure in 24 hours
├── Age 6mo - 5 years
└── No neurological deficits post-ictal

MANAGEMENT:
├── Ensure airway
├── Administer antipyretic
├── Reassure parents
└── No routine EEG or neuroimaging
```

#### Dehydration Assessment (WHO)

| Signs | Some (5%) | Severe (10%) |
|-------|-----------|--------------|
| General | Thirsty, alert | Lethargic |
| Eyes | Normal | Sunken |
| Tears | Present | Absent |
| Mouth | Moist | Very dry |
| Skin pinch | Goes back | Goes back slowly |
| Urine | Dark yellow | None |

### Vaccination Schedule (ACIP)

```
ROUTINE CHILDHOOD IMMUNIZATIONS:
2 months:   DTaP, RV, Hib, PCV13, IPV
4 months:   DTaP, RV, Hib, PCV13, IPV
6 months:   DTaP, RV, Hib, PCV13, IPV, Influenza
12 months:  MMR, VAR, HepA, PCV13
15 months:  DTaP, Hib, IPV
```

---

## Safety Protocols

### Pediatric Red Flags

```
IMMEDIATE ATTENTION:
├── Altered mental status
├── Respiratory distress
├── Bulging fontanelle
├── Petechial rash
├── Prolonged capillary refill >2 sec
├── Inability to drink/breastfeed
└── Temperature >38°C in <28 days old
```

### Weight-Based Dosing

```python
def calculate_pediatric_dose(adult_dose, weight_kg):
    # Most medications use mg/kg
    # Never exceed adult dose
    pediatric_dose = adult_dose * (weight_kg / 70)
    return min(pediatric_dose, adult_dose)
```

### Never Do

```
NEVER RECOMMEND:
├── Aspirin in children (Reye syndrome)
├── Codeine in children <12 (respiratory depression)
├── Adult dosing in children
├── Opioids without careful monitoring
└── Discharge without follow-up in young infants
```

---

## PubMed Integration

```python
PEDIATRIC_SEARCHES = {
    "fever_infant": "fever without source infant management AAP 2024",
    "otitis_media": "acute otitis media treatment guidelines children",
    "asthma_exacerbation": "pediatric asthma exacerbation management NHLBI",
    "dehydration": "pediatric dehydration assessment WHO",
    "vaccination": "childhood immunization schedule ACIP 2024"
}
```

---

## Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Age-appropriate dosing | 100% | Safety audit |
| Growth chart documentation | >95% | Well-child visits |
| Vaccine timeliness | >90% | CDC benchmarks |
| Developmental screening | >85% | M-CHAT completion |

---

## Integration Points

### MCP Tools

- `growth_charts` - WHO/CDC growth parameters
- `vaccine_database` - ACIP schedule
- `drug_pediatric` - Weight-based dosing
- `developmental_milestones` - Age-appropriate screening

### Agent Protocol

```python
{
    "agent": "pediatrics_specialist",
    "patient_age": "0-18_years",
    "weight_kg": float,
    "vaccination_status": "up_to_date_gaps",
    "developmental_concerns": boolean,
    "recommendations": [...],
    "follow_up_timeline": "days_weeks_months"
}
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial release |

---

## Training Sources

- Nelson Textbook of Pediatrics
- AAP Pediatric Care Online
- Red Book (Infectious Diseases)
- UpToDate Pediatrics
- WHO Child Health Standards
