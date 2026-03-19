#!/usr/bin/env python3
"""
Clinical MCP Server for dr_ikechukwu_pa
========================================
A custom MCP server providing clinical decision support tools.

Tools:
- search_medical_literature: Search medical journals and guidelines
- check_drug_interactions: Check for drug-drug interactions
- lookup_clinical_guidelines: Look up clinical practice guidelines
- calculate_bmi: Calculate BMI from weight/height
- assess_fall_risk: Assess patient fall risk

Usage:
    pip install fastmcp
    python clinical_mcp_server.py

Environment:
    Export MEDLINE_API_KEY for production use
"""

import os
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("Clinical Tools")

# Sample clinical guidelines database (in production, connect to real APIs)
CLINICAL_GUIDELINES = {
    "diabetes": {
        "title": "ADA Standards of Care in Diabetes",
        "recommendations": [
            "HbA1c target < 7% for most adults",
            "Screen for retinopathy annually",
            "Statin therapy for cardiovascular risk",
            "Blood pressure target < 130/80 mmHg"
        ]
    },
    "hypertension": {
        "title": "JNC 8 Hypertension Guidelines",
        "recommendations": [
            "BP target < 140/90 for general population",
            "BP target < 130/80 for high-risk patients",
            "First-line: ACEI, ARB, CCB, or thiazide",
            "Lifestyle modifications: diet, exercise, sodium reduction"
        ]
    },
    "asthma": {
        "title": "GINA Asthma Guidelines",
        "recommendations": [
            "ICS-formoterol as preferred reliever",
            "Step-up/step-down based on control",
            "Assess inhaler technique regularly",
            "Action plan for exacerbations"
        ]
    },
    "chest_pain": {
        "title": "ACC/AHA Chest Pain Guidelines",
        "recommendations": [
            "Risk stratify using HEART or TIMI score",
            "Serial ECGs and troponins",
            "Consider CTA for intermediate risk",
            "Early invasive strategy for high-risk ACS"
        ]
    }
}

# Drug interaction database (simplified)
DRUG_INTERACTIONS = {
    ("warfarin", "aspirin"): "Increased bleeding risk - Monitor INR closely",
    ("warfarin", "ibuprofen"): "Increased bleeding risk - Avoid combination",
    ("metformin", "contrast"): "Risk of lactic acidosis - Hold metformin",
    ("lisinopril", "potassium"): "Risk of hyperkalemia - Monitor potassium",
    ("simvastatin", "erythromycin"): "Increased myopathy risk - Reduce statin dose",
}


@mcp.tool()
def search_medical_literature(query: str, max_results: int = 5) -> str:
    """Search medical literature and clinical guidelines.
    
    Args:
        query: Medical condition or search term
        max_results: Maximum number of results (default 5)
        
    Returns:
        Formatted search results with citations
    """
    # In production, connect to PubMed/Medline API
    # For now, return structured placeholder
    
    results = [
        {
            "title": f"Clinical review: {query}",
            "source": "NEJM",
            "year": 2024,
            "summary": f"Current evidence-based review of {query} management"
        },
        {
            "title": f"Guidelines for {query}",
            "source": "UpToDate",
            "year": 2024,
            "summary": f"Evidence-based recommendations for {query}"
        }
    ]
    
    output = f"Medical Literature Search: {query}\n"
    output += "=" * 50 + "\n\n"
    
    for i, r in enumerate(results[:max_results], 1):
        output += f"{i}. {r['title']}\n"
        output += f"   Source: {r['source']} ({r['year']})\n"
        output += f"   Summary: {r['summary']}\n\n"
    
    output += "\nNote: Connect to MEDLINE API for live search"
    return output


@mcp.tool()
def check_drug_interactions(drugs: List[str]) -> str:
    """Check for potential drug-drug interactions.
    
    Args:
        drugs: List of medication names to check
        
    Returns:
        Report of any identified interactions
    """
    drugs_lower = [d.lower().strip() for d in drugs]
    interactions_found = []
    
    for i, drug1 in enumerate(drugs_lower):
        for drug2 in drugs_lower[i+1:]:
            pair = (drug1, drug2)
            reverse_pair = (drug2, drug1)
            
            if pair in DRUG_INTERACTIONS:
                interactions_found.append({
                    "drugs": f"{drug1} + {drug2}",
                    "warning": DRUG_INTERACTIONS[pair]
                })
            elif reverse_pair in DRUG_INTERACTIONS:
                interactions_found.append({
                    "drugs": f"{drug2} + {drug1}",
                    "warning": DRUG_INTERACTIONS[reverse_pair]
                })
    
    if not interactions_found:
        return "No known interactions found in database.\n\nNote: Always verify with full drug interaction checker."
    
    output = "Drug Interaction Report\n"
    output += "=" * 50 + "\n\n"
    
    for interaction in interactions_found:
        output += f"⚠️ {interaction['drugs']}\n"
        output += f"   {interaction['warning']}\n\n"
    
    return output


@mcp.tool()
def lookup_clinical_guidelines(condition: str) -> str:
    """Look up clinical practice guidelines for a medical condition.
    
    Args:
        condition: Medical condition name
        
    Returns:
        Relevant clinical guidelines and recommendations
    """
    condition_lower = condition.lower().strip()
    
    # Find matching guidelines
    matched = None
    for key in CLINICAL_GUIDELINES:
        if key in condition_lower or condition_lower in key:
            matched = CLINICAL_GUIDELINES[key]
            break
    
    if not matched:
        # Search for partial match
        for key, guidelines in CLINICAL_GUIDELINES.items():
            if any(word in condition_lower for word in key.split("_")):
                matched = guidelines
                break
    
    if not matched:
        return f"Guidelines for '{condition}' not found in database.\n\n"
    
    output = f"Clinical Guidelines: {matched['title']}\n"
    output += "=" * 50 + "\n\n"
    output += "Recommendations:\n"
    
    for i, rec in enumerate(matched['recommendations'], 1):
        output += f"{i}. {rec}\n"
    
    output += "\nNote: Verify with latest guidelines - may have updates"
    return output


@mcp.tool()
def calculate_bmi(weight_kg: float, height_cm: float) -> str:
    """Calculate Body Mass Index (BMI) from weight and height.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        
    Returns:
        BMI value with category interpretation
    """
    if weight_kg <= 0 or height_cm <= 0:
        return "Error: Weight and height must be positive values"
    
    height_m = height_cm / 100
    bmi = weight_kg / (height_m ** 2)
    
    # BMI Categories
    if bmi < 18.5:
        category = "Underweight"
        action = "Consider nutritional counseling"
    elif bmi < 25:
        category = "Normal weight"
        action = "Maintain healthy lifestyle"
    elif bmi < 30:
        category = "Overweight"
        action = "Consider lifestyle modifications"
    else:
        category = "Obese"
        action = "Comprehensive weight management recommended"
    
    output = f"BMI Calculation Results\n"
    output += "=" * 50 + "\n\n"
    output += f"Weight: {weight_kg} kg\n"
    output += f"Height: {height_cm} cm\n"
    output += f"BMI: {bmi:.1f}\n\n"
    output += f"Category: {category}\n"
    output += f"Recommendation: {action}\n"
    
    return output


@mcp.tool()
def assess_fall_risk(age: int, medications: List[str], history: List[str], 
                     vision_problems: bool = False, mobility_issues: bool = False) -> str:
    """Assess patient fall risk based on multiple factors.
    
    Args:
        age: Patient age in years
        medications: List of current medications
        history: List of relevant medical history
        vision_problems: Whether patient has vision problems
        mobility_issues: Whether patient has mobility issues
        
    Returns:
        Fall risk assessment with recommendations
    """
    risk_score = 0
    risk_factors = []
    
    # Age-based risk
    if age >= 65:
        risk_score += 1
        risk_factors.append(f"Age >= 65 (age: {age})")
    
    if age >= 80:
        risk_score += 1
        risk_factors.append("Age >= 80 - high risk")
    
    # Medication-based risk
    high_risk_meds = ["warfarin", "sedative", "antihypertensive", "diuretic", "opioid"]
    med_count = sum(1 for med in medications if any(r in med.lower() for r in high_risk_meds))
    
    if med_count >= 5:
        risk_score += 2
        risk_factors.append(f"Polypharmacy ({med_count} high-risk medications)")
    elif med_count >= 3:
        risk_score += 1
        risk_factors.append(f"Multiple medications ({med_count} high-risk)")
    
    # History-based risk
    fall_keywords = ["fall", "fracture", "stroke", "parkinson"]
    if any(any(kw in h.lower() for kw in fall_keywords) for h in history):
        risk_score += 2
        risk_factors.append("Previous fall history")
    
    # Physical factors
    if vision_problems:
        risk_score += 1
        risk_factors.append("Vision problems")
    
    if mobility_issues:
        risk_score += 2
        risk_factors.append("Mobility issues/balance problems")
    
    # Determine risk level
    if risk_score >= 5:
        risk_level = "HIGH"
        recommendations = [
            "Comprehensive fall prevention program",
            "Home safety assessment",
            "Physical therapy referral",
            "Medication review",
            "Assistive devices evaluation"
        ]
    elif risk_score >= 3:
        risk_level = "MODERATE"
        recommendations = [
            "Home safety modifications",
            "Balance exercises",
            "Regular vision checks",
            "Review medications"
        ]
    else:
        risk_level = "LOW"
        recommendations = [
            "Maintain physical activity",
            "Regular vision screening",
            "Home safety awareness"
        ]
    
    output = f"Fall Risk Assessment\n"
    output += "=" * 50 + "\n\n"
    output += f"Risk Score: {risk_score}/10\n"
    output += f"Risk Level: {risk_level}\n\n"
    output += "Risk Factors Identified:\n"
    for factor in risk_factors:
        output += f"  • {factor}\n"
    
    output += "\nRecommendations:\n"
    for rec in recommendations:
        output += f"  • {rec}\n"
    
    return output


if __name__ == "__main__":
    # Run the MCP server
    print("Starting Clinical MCP Server...")
    print("Tools available: search_medical_literature, check_drug_interactions, ")
    print("                 lookup_clinical_guidelines, calculate_bmi, assess_fall_risk")
    mcp.run(transport="stdio")
