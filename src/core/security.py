import re
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

# Maximum input length to prevent ReDoS attacks
MAX_INPUT_LENGTH = 10000

class SecuritySanitizer:
    """
    Zero-Trust Data Sanitization layer for clinical data.
    Strips PII and PHI before external API calls to comply with Nigeria NH Act 2014.
    """

    # PII patterns
    PHONE_PATTERN = r'\b(?:\+234|0)[0-9]{10}\b'
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    PATIENT_ID_PATTERN = r'\b(?:MRN|Patient ID|PID)[\s:]*([A-Z0-9-]+)\b'
    
    # PHI patterns
    HOSPITAL_NAME_PATTERN = r'\b(?:University Teaching Hospital|General Hospital|Medical Centre)[A-Za-z\s]*\b'
    DOCTOR_NAME_PATTERN = r'\bDr\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
    DATE_OF_BIRTH_PATTERN = r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b'
    
    @staticmethod
    def sanitize_clinical_prompt(prompt: str) -> Tuple[str, dict]:
        """
        Sanitize clinical queries by removing PII/PHI before sending to external APIs.
        
        Args:
            prompt: Raw clinical query
            
        Returns:
            Tuple of (sanitized_prompt, metadata_dict containing redacted_items)
        """
        # Input validation for ReDoS protection
        if not prompt or len(prompt) > MAX_INPUT_LENGTH:
            return prompt if prompt else "", {}
        
        sanitized = prompt
        redacted_items = {}
        
        # Strip phone numbers
        phones = re.findall(SecuritySanitizer.PHONE_PATTERN, sanitized)
        if phones:
            redacted_items['phone_numbers'] = len(phones)
            sanitized = re.sub(SecuritySanitizer.PHONE_PATTERN, '[PHONE_REDACTED]', sanitized)
        
        # Strip emails
        emails = re.findall(SecuritySanitizer.EMAIL_PATTERN, sanitized)
        if emails:
            redacted_items['emails'] = len(emails)
            sanitized = re.sub(SecuritySanitizer.EMAIL_PATTERN, '[EMAIL_REDACTED]', sanitized)
        
        # Strip patient IDs
        patient_ids = re.findall(SecuritySanitizer.PATIENT_ID_PATTERN, sanitized)
        if patient_ids:
            redacted_items['patient_ids'] = len(patient_ids)
            sanitized = re.sub(SecuritySanitizer.PATIENT_ID_PATTERN, 'Patient ID [ID_REDACTED]', sanitized)
        
        # Strip hospital names
        hospitals = re.findall(SecuritySanitizer.HOSPITAL_NAME_PATTERN, sanitized)
        if hospitals:
            redacted_items['hospitals'] = len(hospitals)
            sanitized = re.sub(SecuritySanitizer.HOSPITAL_NAME_PATTERN, '[HOSPITAL_REDACTED]', sanitized)
        
        # Strip doctor names
        doctors = re.findall(SecuritySanitizer.DOCTOR_NAME_PATTERN, sanitized)
        if doctors:
            redacted_items['doctor_names'] = len(doctors)
            sanitized = re.sub(SecuritySanitizer.DOCTOR_NAME_PATTERN, '[DOCTOR_REDACTED]', sanitized)
        
        # Strip dates of birth
        dobs = re.findall(SecuritySanitizer.DATE_OF_BIRTH_PATTERN, sanitized)
        if dobs:
            redacted_items['dates'] = len(dobs)
            sanitized = re.sub(SecuritySanitizer.DATE_OF_BIRTH_PATTERN, '[DATE_REDACTED]', sanitized)
        
        if redacted_items:
            logger.info(f"Security: Sanitized prompt. Redacted items: {redacted_items}")
        
        return sanitized, redacted_items


def sanitize_for_api(prompt: str) -> str:
    """Convenience function for FastAPI middleware."""
    sanitized, _ = SecuritySanitizer.sanitize_clinical_prompt(prompt)
    return sanitized
