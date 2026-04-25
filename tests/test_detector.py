"""
Tests for the SatyaCheck misinformation detection system.

Covers: preprocessing, Marathi utilities, detection model,
explainer, and API integration.
"""

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Unit tests — Preprocessing
# ---------------------------------------------------------------------------

from src.detector.preprocess import preprocess, extract_raw_features


class TestPreprocess:
    """Tests for text preprocessing pipeline."""

    def test_empty_string(self):
        assert preprocess("") == ""

    def test_whitespace_collapse(self):
        assert preprocess("  hello   world  ") == "hello world"

    def test_url_removal(self):
        text = "Check this https://fake-news.com for details"
        result = preprocess(text)
        assert "https://" not in result
        assert "fake-news" not in result

    def test_lowercase_english(self):
        assert preprocess("HELLO WORLD", "en") == "hello world"

    def test_no_lowercase_marathi(self):
        text = "हे एक चाचणी आहे"
        result = preprocess(text, "mr")
        assert result == text

    def test_emoji_removal(self):
        text = "Breaking news! 🔥🔥🔥 Share now!"
        result = preprocess(text)
        assert "🔥" not in result


class TestExtractRawFeatures:
    """Tests for raw feature extraction."""

    def test_empty_string(self):
        features = extract_raw_features("")
        assert features["exclamation_count"] == 0
        assert features["caps_ratio"] == 0.0

    def test_exclamation_count(self):
        features = extract_raw_features("Wow!!! Amazing!!!")
        assert features["exclamation_count"] == 6

    def test_caps_ratio(self):
        features = extract_raw_features("HELLO world")
        # 5 upper out of 10 alpha = 0.5
        assert features["caps_ratio"] == 0.5

    def test_url_count(self):
        text = "Visit https://a.com and https://b.com"
        features = extract_raw_features(text)
        assert features["url_count"] == 2

    def test_word_count(self):
        features = extract_raw_features("one two three")
        assert features["word_count"] == 3


# ---------------------------------------------------------------------------
# Unit tests — Marathi utilities
# ---------------------------------------------------------------------------

from src.language.marathi import (
    normalize_marathi,
    is_marathi,
    find_marathi_keywords,
)


class TestMarathiUtils:
    """Tests for Marathi language utilities."""

    def test_normalize_whitespace(self):
        text = "  हे   एक   चाचणी  "
        assert normalize_marathi(text) == "हे एक चाचणी"

    def test_is_marathi_true(self):
        assert is_marathi("हे एक चाचणी आहे") is True

    def test_is_marathi_false(self):
        assert is_marathi("This is an English sentence") is False

    def test_is_marathi_empty(self):
        assert is_marathi("") is False

    def test_find_keywords_sensationalist(self):
        text = "हे खरोखरच चमत्कार आहे!"
        matches = find_marathi_keywords(text)
        assert "sensationalist" in matches
        assert "चमत्कार" in matches["sensationalist"]

    def test_find_keywords_forwarding(self):
        text = "हे सर्वांना पसरवा आणि शेअर करा"
        matches = find_marathi_keywords(text)
        assert "forwarding" in matches

    def test_find_keywords_none(self):
        text = "आज हवामान चांगले आहे"
        matches = find_marathi_keywords(text)
        assert len(matches) == 0


# ---------------------------------------------------------------------------
# Unit tests — Detection model
# ---------------------------------------------------------------------------

from src.detector.model import detect


class TestDetectionModel:
    """Tests for the heuristic detection model."""

    def test_clearly_fake_english(self):
        text = (
            "SHOCKING! This miracle cure is banned by the government! "
            "Forward this to everyone NOW!"
        )
        result = detect(text, "en")
        assert result.verdict == "fake"
        assert result.confidence >= 60
        assert len(result.flagged) > 0

    def test_clearly_real_english(self):
        text = (
            "The quarterly earnings report from the company showed a "
            "5% increase in revenue over the previous quarter."
        )
        result = detect(text, "en")
        assert result.verdict == "real"

    def test_uncertain_english(self):
        text = "Shocking urgent news: share this viral message now!"
        result = detect(text, "en")
        assert result.verdict in ("uncertain", "fake")

    def test_marathi_fake(self):
        text = "हा चमत्कार आहे! सर्वांना पसरवा! लगेच शेअर करा!"
        result = detect(text, "mr")
        assert result.verdict == "fake"
        assert len(result.flagged) > 0

    def test_marathi_real(self):
        text = "आज पुण्यात हवामान चांगले आहे. तापमान ३२ अंश आहे."
        result = detect(text, "mr")
        assert result.verdict == "real"

    def test_auto_detect_marathi(self):
        """Language auto-detection should switch to Marathi."""
        text = "हा चमत्कार आहे! सर्वांना पसरवा!"
        result = detect(text, "en")  # Pass "en" but text is Marathi
        assert result.verdict == "fake"

    def test_confidence_range(self):
        text = "Some random normal text about weather."
        result = detect(text, "en")
        assert 0 <= result.confidence <= 100

    def test_flagged_list_type(self):
        result = detect("hello world", "en")
        assert isinstance(result.flagged, list)


# ---------------------------------------------------------------------------
# Unit tests — Explainer
# ---------------------------------------------------------------------------

from src.detector.explainer import explain


class TestExplainer:
    """Tests for the explanation generator."""

    def test_real_english_explanation(self):
        result = detect("Normal weather report today.", "en")
        explanation = explain(result, "en")
        assert "credible" in explanation.lower() or "no" in explanation.lower()

    def test_fake_english_explanation(self):
        text = "SHOCKING miracle cure! Forward this to everyone!"
        result = detect(text, "en")
        explanation = explain(result, "en")
        assert len(explanation) > 20

    def test_marathi_explanation(self):
        text = "हा चमत्कार आहे! सर्वांना पसरवा!"
        result = detect(text, "mr")
        explanation = explain(result, "mr")
        # Should contain Marathi text
        assert any(
            "\u0900" <= ch <= "\u097F" for ch in explanation
        )

    def test_explanation_not_empty(self):
        result = detect("test", "en")
        explanation = explain(result, "en")
        assert len(explanation) > 0


# ---------------------------------------------------------------------------
# Integration tests — API
# ---------------------------------------------------------------------------

from src.api.app import app

client = TestClient(app)


class TestAPI:
    """Integration tests for the FastAPI endpoints."""

    def test_health_check(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_detect_english_fake(self):
        resp = client.post("/detect", json={
            "text": "SHOCKING miracle cure banned! Forward this to all!",
            "language": "en",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["verdict"] == "fake"
        assert "explanation" in data
        assert isinstance(data["flagged"], list)

    def test_detect_english_real(self):
        resp = client.post("/detect", json={
            "text": "The weather forecast for tomorrow predicts rain.",
            "language": "en",
        })
        assert resp.status_code == 200
        assert resp.json()["verdict"] == "real"

    def test_detect_marathi(self):
        resp = client.post("/detect", json={
            "text": "हा चमत्कार आहे! सर्वांना पसरवा!",
            "language": "mr",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["verdict"] == "fake"

    def test_detect_empty_text(self):
        resp = client.post("/detect", json={
            "text": "",
            "language": "en",
        })
        assert resp.status_code == 422  # Validation error

    def test_detect_invalid_language(self):
        resp = client.post("/detect", json={
            "text": "Some text",
            "language": "xyz",
        })
        assert resp.status_code == 422

    def test_detect_response_shape(self):
        resp = client.post("/detect", json={
            "text": "Normal text here.",
            "language": "en",
        })
        data = resp.json()
        assert "verdict" in data
        assert "confidence" in data
        assert "explanation" in data
        assert "flagged" in data
        assert isinstance(data["confidence"], int)
