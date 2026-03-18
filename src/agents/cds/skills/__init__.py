"""
CDS Skills Loader - Advanced Clinical Decision Support Skills

This module loads and manages skills for the CDS specialist agents.
Each skill is a comprehensive markdown file with metadata, guidelines, 
reasoning frameworks, and integration points.

Usage:
    from src.agents.cds.skills import skills_loader, get_all_skills
    
    # Get all skills at startup
    all_skills = get_all_skills()
    
    # Get specific skill
    obgyn = skills_loader.load_skill("obgyn")
    
    # Get system prompt for agent
    prompt = get_system_prompt("medicine")
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class SkillMetadata:
    """Parsed metadata from skill file"""
    skill_id: str
    name: str
    version: str
    domain: str
    specialty: str
    capabilities: List[str]
    safety_level: str
    requires_human_override: bool
    guidelines: List[str]
    last_updated: str
    # Optional specialty-specific fields
    acog_code: Optional[str] = None
    acr_code: Optional[str] = None
    # Additional specialty organization codes
    acs_code: Optional[str] = None  # American College of Surgeons
    aap_code: Optional[str] = None  # American Academy of Pediatrics
    apa_code: Optional[str] = None  # American Psychiatric Association
    uscap_code: Optional[str] = None  # USCAP (United States and Canadian Academy of Pathology)
    accp_code: Optional[str] = None  # American College of Clinical Pharmacology
    # Additional optional fields from skill files
    operator_required: Optional[bool] = None  # Surgery
    age_range: Optional[str] = None  # Pediatrics
    crisis_protocol: Optional[bool] = None  # Psychiatry
    subspecialties: Optional[List[str]] = None
    modalities: Optional[List[str]] = None


@dataclass
class ClinicalGuideline:
    """Clinical guideline entry"""
    title: str
    criteria: Dict[str, Any]
    recommendations: List[str]
    references: List[str]


class SkillsLoader:
    """
    Loads and manages CDS skills for specialist agents.
    
    Auto-loads all skills at initialization for fast access.
    
    Usage:
        loader = SkillsLoader()  # Auto-loads all skills
        obgyn_skill = loader.get_skill("obgyn")
        print(obgyn_skill.system_prompt)
    """
    
    SKILLS_DIR = Path(__file__).parent
    
    # Skill file mapping
    SKILL_FILES = {
        "obgyn": "obgyn_skill.md",
        "medicine": "medicine_skill.md",
        "surgery": "surgery_skill.md",
        "pediatrics": "pediatrics_skill.md",
        "radiology": "radiology_skill.md",
        "psychiatry": "psychiatry_skill.md",
        "pathology": "pathology_skill.md",
        "pharmacology": "pharmacology_skill.md"
    }
    
    def __init__(self, auto_load: bool = True):
        """
        Initialize skills loader.
        
        Args:
            auto_load: If True, loads all skills at initialization
        """
        self._skills_cache: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
        
        if auto_load:
            self.load_all_skills()
    
    def load_all_skills(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all skills from disk into cache.
        Called automatically at startup.
        
        Returns:
            Dictionary mapping specialty name to skill data
        """
        loaded_skills = {}
        
        for specialty, filename in self.SKILL_FILES.items():
            try:
                skill_path = self.SKILLS_DIR / filename
                if skill_path.exists():
                    skill_data = self._parse_skill_file(skill_path)
                    self._skills_cache[specialty] = skill_data
                    loaded_skills[specialty] = skill_data
                    print(f"Loaded skill: {specialty} v{skill_data.get('metadata').version if skill_data.get('metadata') else 'unknown'}")
                else:
                    print(f"Warning: Skill file not found: {skill_path}")
            except Exception as e:
                print(f"Error loading skill {specialty}: {e}")
        
        self._loaded = True
        return loaded_skills
    
    def reload_skills(self) -> Dict[str, Dict[str, Any]]:
        """
        Clear cache and reload all skills.
        
        Returns:
            Dictionary of reloaded skills
        """
        self._skills_cache.clear()
        self._loaded = False
        return self.load_all_skills()
    
    @property
    def is_loaded(self) -> bool:
        """Check if skills have been loaded"""
        return self._loaded and len(self._skills_cache) > 0
    
    @property
    def loaded_specialties(self) -> List[str]:
        """Get list of loaded specialty names"""
        return list(self._skills_cache.keys())
    
    def get_skill(self, specialty: str) -> Dict[str, Any]:
        """
        Get a skill by specialty name. Loads if not cached.
        
        Args:
            specialty: One of obgyn, medicine, surgery, pediatrics, radiology, psychiatry, pathology, pharmacology
            
        Returns:
            Dictionary containing skill data
        """
        specialty = specialty.lower()
        
        if specialty in self._skills_cache:
            return self._skills_cache[specialty]
        
        # Load if not in cache
        skill_file = self.SKILL_FILES.get(specialty)
        if not skill_file:
            raise ValueError(f"Unknown specialty: {specialty}")
        
        skill_path = self.SKILLS_DIR / skill_file
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_path}")
        
        skill_data = self._parse_skill_file(skill_path)
        self._skills_cache[specialty] = skill_data
        
        return skill_data
    
    # Alias for get_skill
    load_skill = get_skill
    
    def _parse_skill_file(self, filepath: Path) -> Dict[str, Any]:
        """Parse a skill markdown file into structured data."""
        content = filepath.read_text(encoding='utf-8')
        
        # Extract metadata JSON block
        metadata = self._extract_metadata(content)
        
        # Extract 3-Phase Execution Protocol
        phase1 = self._extract_section(content, "Phase 1")
        phase2 = self._extract_section(content, "Phase 2")
        phase3 = self._extract_section(content, "Phase 3")
        
        # Extract system prompt
        system_prompt = self._extract_section(content, "System Prompt")
        
        # Extract clinical guidelines
        guidelines = self._extract_guidelines(content)
        
        # Extract reasoning framework
        reasoning = self._extract_section(content, "Reasoning Framework")
        
        # Extract knowledge base
        knowledge = self._extract_section(content, "Knowledge Base")
        
        # Extract safety protocols
        safety = self._extract_section(content, "Safety Protocols")
        
        # Extract PubMed search patterns
        search_patterns = self._extract_search_patterns(content)
        
        # Extract quality metrics
        metrics = self._extract_metrics(content)
        
        return {
            "metadata": metadata,
            "phase1_direct_response": phase1,
            "phase2_cds_framework": phase2,
            "phase3_evidence_grounding": phase3,
            "system_prompt": system_prompt,
            "guidelines": guidelines,
            "reasoning_framework": reasoning,
            "knowledge_base": knowledge,
            "safety_protocols": safety,
            "pubmed_searches": search_patterns,
            "quality_metrics": metrics,
            "raw_content": content
        }
    
    def _extract_metadata(self, content: str) -> Optional[SkillMetadata]:
        """Extract JSON metadata from skill file."""
        # Find JSON block in metadata section
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, content, re.DOTALL)
        
        if match:
            data = json.loads(match.group(1))
            return SkillMetadata(**data)
        
        return None
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """Extract a section by title."""
        # Match section header
        pattern = rf'##\s+{re.escape(section_name)}\s*\n(.*?)(?=##\s+|$)'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _extract_guidelines(self, content: str) -> List[Dict[str, Any]]:
        """Extract clinical guidelines tables."""
        guidelines = []
        
        # Look for markdown tables
        table_pattern = r'\|(.+?)\|\s*\n\|[-:\s|]+\|\s*\n((?:\|.+\|\s*\n)+)'
        matches = re.finditer(table_pattern, content)
        
        for match in matches:
            headers = [h.strip() for h in match.group(1).split('|') if h.strip()]
            rows = []
            for row in match.group(2).split('\n'):
                if row.strip():
                    cells = [c.strip() for c in row.split('|') if c.strip()]
                    if cells:
                        rows.append(cells)
            
            if headers and rows:
                guidelines.append({
                    "headers": headers,
                    "rows": rows
                })
        
        return guidelines
    
    def _extract_search_patterns(self, content: str) -> Dict[str, str]:
        """Extract PubMed search patterns."""
        # Find Python code blocks with SEARCH_ patterns
        pattern = r'```python\s*.*?SEARCHES\s*=\s*\{(.*?)\}\s*```'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            try:
                # Simple parse of dict-like string
                dict_str = '{' + match.group(1) + '}'
                return eval(dict_str)
            except:
                pass
        
        return {}
    
    def _extract_metrics(self, content: str) -> Dict[str, Any]:
        """Extract quality metrics table."""
        metrics = {}
        
        # Look for metrics table
        table_pattern = r'\|\s*Metric\s*\|\s*Target\s*\|\s*Measurement\s*\|\s*\n\|[-:\s|]+\|\s*\n((?:\|.+\|\s*\n)+)'
        match = re.search(table_pattern, content)
        
        if match:
            for row in match.group(1).split('\n'):
                if '|' in row:
                    cells = [c.strip() for c in row.split('|') if c.strip()]
                    if len(cells) >= 3:
                        metrics[cells[0]] = {
                            "target": cells[1],
                            "measurement": cells[2]
                        }
        
        return metrics
    
    def get_system_prompt(self, specialty: str) -> str:
        """Get the system prompt for a specialty."""
        skill = self.get_skill(specialty)
        return skill.get("system_prompt", "")
    
    def get_safety_protocols(self, specialty: str) -> str:
        """Get safety protocols for a specialty."""
        skill = self.get_skill(specialty)
        return skill.get("safety_protocols", "")
    
    def get_pubmed_searches(self, specialty: str) -> Dict[str, str]:
        """Get PubMed search patterns for a specialty."""
        skill = self.get_skill(specialty)
        return skill.get("pubmed_searches", {})
    
    def get_capabilities(self, specialty: str) -> List[str]:
        """Get capabilities for a specialty."""
        skill = self.get_skill(specialty)
        metadata = skill.get("metadata")
        if metadata:
            return metadata.capabilities
        return []
    
    def requires_human_override(self, specialty: str) -> bool:
        """Check if specialty requires human override."""
        skill = self.get_skill(specialty)
        metadata = skill.get("metadata")
        if metadata:
            return metadata.requires_human_override
        return True
    
    def get_3_phase_protocol(self, specialty: str) -> Dict[str, str]:
        """
        Get the 3-Phase Execution Protocol for a specialty.
        
        Returns:
            Dict with keys: phase1, phase2, phase3
        """
        skill = self.get_skill(specialty)
        return {
            "phase1": skill.get("phase1_direct_response", ""),
            "phase2": skill.get("phase2_cds_framework", ""),
            "phase3": skill.get("phase3_evidence_grounding", "")
        }


# Global singleton instance - auto-loads all skills at import
skills_loader = SkillsLoader(auto_load=True)


def get_all_skills() -> Dict[str, Dict[str, Any]]:
    """
    Get all loaded skills.
    
    Returns:
        Dictionary mapping specialty to skill data
    """
    return {specialty: skills_loader.get_skill(specialty) 
            for specialty in skills_loader.loaded_specialties}


def get_skill(specialty: str) -> Dict[str, Any]:
    """Convenience function to get a skill."""
    return skills_loader.get_skill(specialty)


def get_system_prompt(specialty: str) -> str:
    """Convenience function to get system prompt."""
    return skills_loader.get_system_prompt(specialty)


def get_safety_protocols(specialty: str) -> str:
    """Convenience function to get safety protocols."""
    return skills_loader.get_safety_protocols(specialty)


def get_pubmed_searches(specialty: str) -> Dict[str, str]:
    """Convenience function to get PubMed searches."""
    return skills_loader.get_pubmed_searches(specialty)


def get_3_phase_protocol(specialty: str) -> Dict[str, str]:
    """Convenience function to get 3-Phase Execution Protocol."""
    return skills_loader.get_3_phase_protocol(specialty)


def reload_all_skills() -> Dict[str, Dict[str, Any]]:
    """Reload all skills from disk."""
    return skills_loader.reload_skills()
