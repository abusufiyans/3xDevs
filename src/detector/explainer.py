"""
Explainer module — generates human-readable explanations for detection verdicts.

Produces explanations in both English and Marathi based on which
detection signals fired and which keywords were flagged.
"""

from __future__ import annotations

from src.detector.model import DetectionResult, CATEGORY_LABELS_EN
from src.language.marathi import CATEGORY_LABELS_MR


def explain(result: DetectionResult, language: str = "en") -> str:
    """
    Build a human-readable explanation string from a DetectionResult.

    Parameters
    ----------
    result : DetectionResult
        Output from ``detect()``.
    language : str
        ``"en"`` or ``"mr"``.

    Returns
    -------
    str
        Plain-language explanation of the verdict.
    """
    if language == "mr":
        return _explain_marathi(result)
    return _explain_english(result)


def _explain_english(result: DetectionResult) -> str:
    if result.verdict == "real":
        return (
            "No significant misinformation signals were detected. "
            "The text appears to be credible based on our analysis."
        )

    parts: list[str] = []

    if result.matched_categories:
        category_names = [
            CATEGORY_LABELS_EN.get(cat, cat)
            for cat in result.matched_categories
        ]
        flagged_preview = result.flagged[:5]
        quoted = ", ".join(f"'{w}'" for w in flagged_preview)

        parts.append(
            f"This text contains {_join_list(category_names)}"
        )
        if quoted:
            parts.append(f"Flagged phrases include: {quoted}.")

    if result.verdict == "uncertain":
        parts.append(
            "While not definitively misleading, the text shows patterns "
            "commonly associated with misinformation."
        )
    else:
        parts.append(
            "These are patterns commonly found in misinformation and "
            "fake news content."
        )

    return " ".join(parts) if parts else "Analysis complete."


def _explain_marathi(result: DetectionResult) -> str:
    if result.verdict == "real":
        return (
            "या मजकुरात चुकीच्या माहितीचे कोणतेही महत्त्वपूर्ण संकेत "
            "आढळले नाहीत. मजकूर विश्वसनीय वाटतो."
        )

    parts: list[str] = []

    if result.matched_categories:
        category_names = [
            CATEGORY_LABELS_MR.get(cat, cat)
            for cat in result.matched_categories
        ]
        flagged_preview = result.flagged[:5]
        quoted = ", ".join(f"'{w}'" for w in flagged_preview)

        parts.append(
            f"या मजकुरात {_join_list_mr(category_names)} आढळली."
        )
        if quoted:
            parts.append(f"चिन्हांकित शब्द: {quoted}.")

    if result.verdict == "uncertain":
        parts.append(
            "मजकूर निश्चितपणे चुकीचा नसला तरी, चुकीच्या माहितीशी "
            "संबंधित नमुने दिसतात."
        )
    else:
        parts.append(
            "हे नमुने सामान्यतः खोट्या बातम्या आणि चुकीच्या "
            "माहितीमध्ये आढळतात."
        )

    return " ".join(parts) if parts else "विश्लेषण पूर्ण."


def _join_list(items: list[str]) -> str:
    """Join a list with commas and 'and'."""
    if len(items) == 0:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def _join_list_mr(items: list[str]) -> str:
    """Join a list with commas and 'आणि' (Marathi 'and')."""
    if len(items) == 0:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " आणि " + items[-1]
