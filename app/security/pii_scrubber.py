import re

PII_PATTERNS = {
    "CREDIT_CARD": re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
    "PAN_CARD": re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', re.IGNORECASE),
    "AADHAAR": re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}\b'),
    "EMAIL": re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.IGNORECASE),
    "PHONE": re.compile(r'\b(?:\+91[\-\s]?)?[6-9]\d{9}\b'),
}

ACCOUNT_PATTERN = re.compile(r'\b(\d+)\b')

def mask_pii(text: str) -> str:
    """Scrubs heavy PII tokens and applies partial masking to account numbers."""
    if not text:
        return text
        
    masked_text = text
    
    for pii_type, pattern in PII_PATTERNS.items():
        masked_text = pattern.sub(f"[{pii_type}_REDACTED]", masked_text)
        
    def account_replacer(match):
        digits = match.group(1)
        if 6 <= len(digits) <= 12:
            visible_count = 4
            if len(digits) <= 4:
                return "X" * len(digits)
            return "X" * (len(digits) - visible_count) + digits[-visible_count:]
        return digits

    masked_text = ACCOUNT_PATTERN.sub(account_replacer, masked_text)
    return masked_text