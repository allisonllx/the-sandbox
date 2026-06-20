"""
Compiled regex patterns for deterministic PII detection and masking.

All patterns use named groups so callers can identify the PII type from a match.
Patterns are ordered from most-specific to least-specific within each category
to avoid partial-match shadowing.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PIIPattern:
    name: str
    pattern: re.Pattern[str]
    placeholder: str


# --- Tokens / Secrets ---

_JWT = PIIPattern(
    name="jwt",
    pattern=re.compile(
        r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*",
        re.ASCII,
    ),
    placeholder="[JWT_REDACTED]",
)

_AWS_ACCESS_KEY = PIIPattern(
    name="aws_access_key",
    pattern=re.compile(r"(?<![A-Z0-9])(AKIA|ASIA|AROA|AIDA)[A-Z0-9]{16}(?![A-Z0-9])"),
    placeholder="[AWS_KEY_REDACTED]",
)

_GENERIC_API_KEY = PIIPattern(
    name="api_key",
    pattern=re.compile(
        r"""(?ix)
        (?:api[_\-\s]?key|apikey|api[_\-\s]?token|access[_\-\s]?token|
           secret[_\-\s]?key|auth[_\-\s]?token|bearer)
        [\s:='"]+
        ([A-Za-z0-9/+_\-]{20,})
        """,
    ),
    placeholder="[API_KEY_REDACTED]",
)

_SDK_KEY = PIIPattern(
    name="api_key",
    # Matches common SDK key prefixes: Stripe sk_live_, pk_test_, etc.
    pattern=re.compile(r"(?:sk|pk|rk)_(?:live|test)_[A-Za-z0-9]{10,}"),
    placeholder="[API_KEY_REDACTED]",
)

_BEARER_HEADER = PIIPattern(
    name="bearer_token",
    pattern=re.compile(r"Bearer\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
    placeholder="[BEARER_REDACTED]",
)

_PRIVATE_KEY_BLOCK = PIIPattern(
    name="private_key_block",
    pattern=re.compile(
        r"-----BEGIN\s+(?:RSA\s+|EC\s+|OPENSSH\s+)?PRIVATE KEY-----.*?-----END[^-]+-----",
        re.DOTALL,
    ),
    placeholder="[PRIVATE_KEY_REDACTED]",
)

# --- Contact / Identity ---

_EMAIL = PIIPattern(
    name="email",
    pattern=re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    ),
    placeholder="[EMAIL_REDACTED]",
)

# E.164 and common North-American formats; intentionally conservative to avoid
# false-positives on version strings like "1.2.3.4".
_PHONE = PIIPattern(
    name="phone",
    pattern=re.compile(
        r"""(?x)
        (?<!\d)
        (?:\+?1[\s\-.]?)?          # optional country code
        \(?(\d{3})\)?              # area code
        [\s\-.]
        (\d{3})                    # exchange
        [\s\-.]
        (\d{4})                    # subscriber
        (?!\d)
        """,
    ),
    placeholder="[PHONE_REDACTED]",
)

_SSN = PIIPattern(
    name="ssn",
    pattern=re.compile(r"(?<!\d)\d{3}-\d{2}-\d{4}(?!\d)"),
    placeholder="[SSN_REDACTED]",
)

_CREDIT_CARD = PIIPattern(
    name="credit_card",
    # Luhn-valid ranges; we don't run Luhn here — structural match is enough.
    pattern=re.compile(
        r"(?<!\d)"
        r"(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6(?:011|5\d{2}))"
        r"[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}"
        r"(?!\d)"
    ),
    placeholder="[CC_REDACTED]",
)

_IPV4 = PIIPattern(
    name="ipv4",
    pattern=re.compile(
        r"(?<!\d)"
        r"(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|[01]?\d\d?)"
        r"(?!\d)"
    ),
    placeholder="[IP_REDACTED]",
)

# Ordered: most-specific first so JWT beats generic API key, AWS key beats generic, etc.
ALL_PATTERNS: list[PIIPattern] = [
    _PRIVATE_KEY_BLOCK,
    _JWT,
    _AWS_ACCESS_KEY,
    _SDK_KEY,
    _BEARER_HEADER,
    _GENERIC_API_KEY,
    _EMAIL,
    _PHONE,
    _SSN,
    _CREDIT_CARD,
    _IPV4,
]


def scrub(text: str) -> tuple[str, dict[str, int]]:
    """
    Replace all PII occurrences in *text* with their respective placeholders.

    Returns:
        scrubbed_text: the text with PII replaced
        detections:    mapping of pii_type -> count of replacements made
    """
    detections: dict[str, int] = {}
    for p in ALL_PATTERNS:
        scrubbed, n = p.pattern.subn(p.placeholder, text)
        if n:
            detections[p.name] = detections.get(p.name, 0) + n
            text = scrubbed
    return text, detections
