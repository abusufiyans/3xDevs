"""
Marathi language utilities for misinformation detection.

Provides keyword dictionaries, forward-chain phrase patterns,
Unicode normalization, and Devanagari script detection.
"""

import re
import unicodedata

# ---------------------------------------------------------------------------
# Marathi misinformation keyword sets
# ---------------------------------------------------------------------------

MARATHI_KEYWORDS: dict[str, list[str]] = {
    "sensationalist": [
        "चमत्कार",       # miracle
        "धक्कादायक",     # shocking
        "भयंकर",         # terrible / horrifying
        "अविश्वसनीय",    # unbelievable
        "गुप्त",          # secret
        "खळबळजनक",      # sensational
        "बंदी",           # banned
        "धोकादायक",      # dangerous
        "भयानक",         # horrific
        "अफवा",          # rumor
    ],
    "urgency": [
        "लगेच",           # immediately
        "आत्ताच",         # right now
        "शेवटची संधी",    # last chance
        "वेळ नाही",       # no time
        "ताबडतोब",       # at once
        "आजच",           # today itself
    ],
    "forwarding": [
        "पसरवा",          # spread
        "पुढे पाठवा",     # forward this
        "शेअर करा",       # share this
        "सर्वांना पाठवा",  # send to everyone
        "१० लोकांना पाठवा", # send to 10 people
        "व्हायरल",        # viral
        "ग्रुपमध्ये पाठवा", # send in group
    ],
    "health_misinfo": [
        "घरगुती उपाय",    # home remedy
        "औषध सापडले",     # cure found
        "डॉक्टरांनी लपवले", # doctors hid this
        "लस घातक",       # vaccine dangerous
        "कोरोना इलाज",    # corona cure
        "रामबाण उपाय",    # miracle cure
    ],
}

# Flattened keyword list for quick matching
ALL_MARATHI_KEYWORDS: list[str] = [
    kw for group in MARATHI_KEYWORDS.values() for kw in group
]

# Category labels in Marathi for explanation generation
CATEGORY_LABELS_MR: dict[str, str] = {
    "sensationalist": "खळबळजनक भाषा",
    "urgency": "तातडीचे शब्द",
    "forwarding": "फॉरवर्ड करण्याचे आवाहन",
    "health_misinfo": "आरोग्यविषयक चुकीची माहिती",
}


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

def normalize_marathi(text: str) -> str:
    """
    Normalize Marathi (Devanagari) text for consistent matching.

    - Apply Unicode NFC normalization (compose combining characters).
    - Collapse multiple whitespace characters into a single space.
    - Strip leading / trailing whitespace.
    """
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Script detection
# ---------------------------------------------------------------------------

_DEVANAGARI_RANGE = re.compile(r"[\u0900-\u097F]")


def is_marathi(text: str) -> bool:
    """
    Heuristic check: returns True if >40% of alphabetic characters
    in the text are Devanagari.
    """
    if not text:
        return False

    devanagari_count = len(_DEVANAGARI_RANGE.findall(text))
    alpha_count = sum(1 for ch in text if ch.isalpha())

    if alpha_count == 0:
        return False

    return (devanagari_count / alpha_count) > 0.4


# ---------------------------------------------------------------------------
# Keyword matching
# ---------------------------------------------------------------------------

def find_marathi_keywords(text: str) -> dict[str, list[str]]:
    """
    Scan *text* for known Marathi misinformation keywords.

    Returns a dict mapping category names to lists of matched keywords.
    Only categories with at least one match are included.
    """
    normalized = normalize_marathi(text)
    matches: dict[str, list[str]] = {}

    for category, keywords in MARATHI_KEYWORDS.items():
        found = [kw for kw in keywords if kw in normalized]
        if found:
            matches[category] = found

    return matches
