"""
Heuristic-based misinformation detection model.

Scores text across multiple signals (keyword presence, structural
patterns, forwarding phrases) and produces a verdict with confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.detector.preprocess import preprocess, extract_raw_features
from src.language.marathi import find_marathi_keywords, is_marathi

# ---------------------------------------------------------------------------
# English keyword sets
# ---------------------------------------------------------------------------

ENGLISH_KEYWORDS: dict[str, list[str]] = {
    "sensationalist": [
        "miracle", "shocking", "unbelievable", "secret", "banned",
        "terrifying", "horrifying", "exposed", "conspiracy", "hoax",
        "bombshell", "jaw-dropping", "mind-blowing",
    ],
    "urgency": [
        "act now", "last chance", "breaking", "urgent", "hurry",
        "immediately", "before it's too late", "limited time",
        "don't miss", "now or never",
    ],
    "forwarding": [
        "forward this", "share this", "send to everyone",
        "viral", "spread the word", "pass it on",
        "send to 10 people", "whatsapp", "forward to",
    ],
    "health_misinfo": [
        "cure", "home remedy", "doctors don't want",
        "big pharma", "vaccine danger", "natural cure",
        "they don't want you to know", "government hiding",
        "corona cure", "immunity booster",
    ],
}

CATEGORY_LABELS_EN: dict[str, str] = {
    "sensationalist": "sensationalist language",
    "urgency": "urgency-inducing phrases",
    "forwarding": "forwarding / chain-message patterns",
    "health_misinfo": "health-related misinformation patterns",
}

WEIGHTS = {
    "keyword_score": 0.45,
    "exclamation_score": 0.15,
    "caps_score": 0.15,
    "forwarding_score": 0.25,
}


@dataclass
class DetectionResult:
    """Container for the detection output."""
    verdict: str
    confidence: int
    flagged: list[str] = field(default_factory=list)
    matched_categories: dict[str, list[str]] = field(default_factory=dict)
    raw_score: float = 0.0


def detect(text: str, language: str = "en") -> DetectionResult:
    """Analyze *text* and return a DetectionResult."""
    if language == "en" and is_marathi(text):
        language = "mr"

    raw_features = extract_raw_features(text)
    cleaned = preprocess(text, language)

    if language == "mr":
        matched_categories = find_marathi_keywords(cleaned)
    else:
        matched_categories = _find_english_keywords(cleaned)

    all_flagged = [kw for kws in matched_categories.values() for kw in kws]

    keyword_score = _keyword_score(matched_categories)
    exclamation_score = _exclamation_score(raw_features)
    caps_score = _caps_score(raw_features, language)
    forwarding_score = _forwarding_score(matched_categories)

    weighted = (
        WEIGHTS["keyword_score"] * keyword_score
        + WEIGHTS["exclamation_score"] * exclamation_score
        + WEIGHTS["caps_score"] * caps_score
        + WEIGHTS["forwarding_score"] * forwarding_score
    )

    confidence = int(min(max(weighted * 100, 0), 100))

    if confidence >= 60:
        verdict = "fake"
    elif confidence >= 35:
        verdict = "uncertain"
    else:
        verdict = "real"
        confidence = 100 - confidence

    return DetectionResult(
        verdict=verdict,
        confidence=confidence,
        flagged=all_flagged,
        matched_categories=matched_categories,
        raw_score=weighted,
    )


def _find_english_keywords(text: str) -> dict[str, list[str]]:
    matches: dict[str, list[str]] = {}
    for category, keywords in ENGLISH_KEYWORDS.items():
        found = [kw for kw in keywords if kw in text]
        if found:
            matches[category] = found
    return matches


def _keyword_score(matched: dict[str, list[str]]) -> float:
    if not matched:
        return 0.0
    total_matches = sum(len(v) for v in matched.values())
    category_count = len(matched)
    return min((category_count * 0.25) + (total_matches * 0.1), 1.0)


def _exclamation_score(features: dict) -> float:
    count = features.get("exclamation_count", 0)
    word_count = features.get("word_count", 1) or 1
    ratio = count / word_count
    if ratio > 0.3:
        return 1.0
    elif ratio > 0.15:
        return 0.7
    elif ratio > 0.05:
        return 0.3
    return 0.0


def _caps_score(features: dict, language: str) -> float:
    if language == "mr":
        return 0.0
    ratio = features.get("caps_ratio", 0.0)
    if ratio > 0.6:
        return 1.0
    elif ratio > 0.4:
        return 0.6
    elif ratio > 0.25:
        return 0.3
    return 0.0


def _forwarding_score(matched: dict[str, list[str]]) -> float:
    forwarding = matched.get("forwarding", [])
    if len(forwarding) >= 2:
        return 1.0
    elif len(forwarding) == 1:
        return 0.7
    return 0.0
