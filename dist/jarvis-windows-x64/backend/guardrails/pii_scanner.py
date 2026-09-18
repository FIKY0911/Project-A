import re
from typing import Optional, Tuple

# Patterns from SRD Section 6.1
EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")
CREDENTIALS_REGEX = re.compile(r"(?i)(password|passwd|secret|api[_-]?key|bearer|token)\s*[:=]\s*\S+")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")

class PIIScanner:
    """
    Validates text against PII patterns before executing OS typing or storing sensitive values.
    """
    @classmethod
    def scan(cls, text: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Returns (is_violation, violation_code, matched_content)
        """
        if not text:
            return False, None, None

        # Check credentials
        cred_match = CREDENTIALS_REGEX.search(text)
        if cred_match:
            return True, "PII_PASSWORD", cred_match.group(0)

        # Check email
        email_match = EMAIL_REGEX.search(text)
        if email_match:
            return True, "PII_EMAIL", email_match.group(0)

        # Check credit card
        cc_match = CREDIT_CARD_REGEX.search(text)
        if cc_match:
            return True, "PII_CREDIT_CARD", cc_match.group(0)

        # Check phone
        phone_match = PHONE_REGEX.search(text)
        if phone_match:
            return True, "PII_PHONE", phone_match.group(0)

        return False, None, None
