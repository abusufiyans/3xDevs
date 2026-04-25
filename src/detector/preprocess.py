"""
Text preprocessing pipeline for misinformation detection.

Cleans and normalizes user input before it enters the detection model.
Handles both English and Marathi (Devanagari) text.
"""

import re
import unicodedata

# ---------------------------------------------------------------------------
# Regex patterns compiled once at module load
# ---------------------------------------------------------------------------

_URL_PATTERN = re.compile(
    r"https?://\S+|www\.\S+", re.IGNORECASE
)

# Matches most emoji / symbol / pictograph Unicode blocks
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

_MULTI_SPACE = re.compile(r"\s+")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def preprocess(text: str, language: str = "en") -> str:
    """
    Run the full preprocessing pipeline on *text*.

    Steps:
        1. Unicode NFC normalization
        2. Strip URLs
        3. Strip emojis
        4. Collapse whitespace
        5. Strip leading/trailing whitespace
        6. Lowercase (English only — Devanagari has no case)

    Parameters
    ----------
    text : str
        Raw user input.
    language : str
        ISO 639-1 code, ``"en"`` or ``"mr"``.

    Returns
    -------
    str
        Cleaned text ready for detection.
    """
    if not text:
        return ""

    # Step 1 — Unicode normalization
    text = unicodedata.normalize("NFC", text)

    # Step 2 — Remove URLs
    text = _URL_PATTERN.sub("", text)

    # Step 3 — Remove emojis
    text = _EMOJI_PATTERN.sub("", text)

    # Step 4 — Collapse whitespace
    text = _MULTI_SPACE.sub(" ", text)

    # Step 5 — Strip
    text = text.strip()

    # Step 6 — Lowercase for English
    if language == "en":
        text = text.lower()

    return text


def extract_raw_features(text: str) -> dict:
    """
    Extract structural features from the *raw* (un-preprocessed) text.

    These features are used by the detection model alongside keyword
    matches.  Extracting from raw text preserves casing and punctuation
    information.

    Returns
    -------
    dict
        ``exclamation_count``, ``caps_ratio``, ``url_count``,
        ``char_count``, ``word_count``.
    """
    if not text:
        return {
            "exclamation_count": 0,
            "caps_ratio": 0.0,
            "url_count": 0,
            "char_count": 0,
            "word_count": 0,
        }

    alpha_chars = [ch for ch in text if ch.isalpha()]
    upper_count = sum(1 for ch in alpha_chars if ch.isupper())

    return {
        "exclamation_count": text.count("!") + text.count("।"),
        "caps_ratio": (upper_count / len(alpha_chars)) if alpha_chars else 0.0,
        "url_count": len(_URL_PATTERN.findall(text)),
        "char_count": len(text),
        "word_count": len(text.split()),
    }
