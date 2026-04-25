# SatyaCheck — Architecture Document

> **Misinformation Detection in Regional Languages**
> Team 3xDevs · BFB'26 · MIT, Chhatrapati Sambhajinagar

---

## 1. System Overview

SatyaCheck is a web-based misinformation detection system designed to analyze textual content in **English** and **Marathi**, classify it as credible or misleading, and provide a human-readable explanation for the verdict. The system uses a rule-based heuristic engine backed by keyword scoring, structural analysis, and Marathi-specific NLP utilities — requiring no external API keys or GPU resources.

### 1.1 Design Goals

| Goal | Description |
|------|-------------|
| **Regional language support** | First-class support for Marathi (Devanagari script) alongside English |
| **Explainability** | Every verdict includes a plain-language explanation and flagged phrases |
| **Zero external dependencies** | No paid APIs, no cloud ML endpoints — runs fully offline |
| **Lightweight** | Sub-second response on commodity hardware |
| **Extensible** | New languages can be added by creating a new module in `src/language/` |

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                     │
│  ┌───────────┐  ┌────────────┐  ┌────────────────────────┐  │
│  │ index.html│  │ style.css  │  │       main.js          │  │
│  │ (layout)  │  │ (design)   │  │ (API calls, DOM logic) │  │
│  └───────────┘  └────────────┘  └────────────────────────┘  │
│                        │  POST /detect                      │
└────────────────────────┼────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Application                       │
│                   src/api/app.py                             │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │  POST /detect│──▶│  Preprocessor│──▶│  Detection     │  │
│  │  (endpoint)  │   │  (clean text)│   │  Model         │  │
│  └──────────────┘   └──────────────┘   └───────┬────────┘  │
│                                                 │           │
│                     ┌──────────────┐            │           │
│                     │  Explainer   │◀───────────┘           │
│                     │  (reasoning) │                        │
│                     └──────────────┘                        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Language Modules                         │   │
│  │  src/language/marathi.py  (transliteration, keywords) │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Component Architecture

### 3.1 Frontend (`frontend/`)

| File | Responsibility |
|------|----------------|
| `index.html` | Semantic page structure — input form, result card, how-it-works section |
| `static/css/style.css` | Design system — typography, color tokens, layout, animations |
| `static/js/main.js` | Language toggle, API integration, result rendering, character count |

**Key interactions:**

1. User selects language (English / Marathi) via toggle buttons.
2. User pastes or types text into the textarea.
3. On clicking **Analyze Text**, `main.js` sends a `POST /detect` request.
4. The response (verdict, confidence, explanation, flagged phrases) is rendered in the result card.

### 3.2 API Layer (`src/api/app.py`)

- **Framework:** FastAPI
- **Responsibilities:**
  - Serve the frontend as static files.
  - Expose `POST /detect` endpoint.
  - Validate request payload (`text`, `language`).
  - Orchestrate the detection pipeline: preprocess → detect → explain.
  - Return structured JSON response.

**Request schema:**
```json
{
  "text": "string",
  "language": "en | mr"
}
```

**Response schema:**
```json
{
  "verdict": "fake | real | uncertain",
  "confidence": 0-100,
  "explanation": "string",
  "flagged": ["phrase1", "phrase2"]
}
```

### 3.3 Preprocessing (`src/detector/preprocess.py`)

| Step | Description |
|------|-------------|
| Normalize whitespace | Collapse multiple spaces, strip leading/trailing |
| Lowercase (English) | Convert to lowercase for keyword matching |
| URL removal | Strip hyperlinks that add noise |
| Emoji removal | Remove emojis that don't carry semantic weight |
| Devanagari normalization | Normalize Marathi Unicode combining characters |

### 3.4 Detection Model (`src/detector/model.py`)

The detection model uses a **multi-signal heuristic scoring** approach:

| Signal | Weight | Description |
|--------|--------|-------------|
| Keyword match | High | Sensationalist / clickbait vocabulary (per-language) |
| Exclamation density | Medium | Excessive use of `!` or `।` |
| Caps ratio (English) | Medium | ALL-CAPS shouting patterns |
| URL presence | Low | Unsourced claims often lack or abuse URLs |
| Forward-chain phrases | High | "Share this", "Forward to 10 people" |
| Urgency patterns | Medium | "Act now", "Last chance", "Breaking" |

The signals produce a weighted score normalized to a 0–100 confidence value. Thresholds:
- **score ≥ 60** → `fake`
- **score 35–59** → `uncertain`
- **score < 35** → `real`

### 3.5 Explainer (`src/detector/explainer.py`)

Generates a human-readable explanation string by describing which signals fired and why. Example outputs:

- *"This text contains sensationalist language ('miracle cure', 'shocking truth') and urges readers to forward it, which are common misinformation patterns."*
- *"या मजकुरात 'चमत्कार' आणि 'पसरवा' असे शब्द आहेत, जे सामान्यतः खोट्या बातम्यांमध्ये आढळतात."*

### 3.6 Language Module — Marathi (`src/language/marathi.py`)

| Utility | Purpose |
|---------|---------|
| `MARATHI_KEYWORDS` | Curated list of Marathi misinformation vocabulary |
| `MARATHI_FORWARD_PHRASES` | "पुढे पाठवा", "१० लोकांना पाठवा", etc. |
| `normalize_marathi()` | Unicode NFC normalization for Devanagari |
| `is_marathi()` | Detect if input text is predominantly Devanagari script |

---

## 4. Data Flow

```
User Input (text + language)
       │
       ▼
  ┌─────────┐
  │ Validate │──── empty text? → 400 error
  └────┬────┘
       ▼
  ┌──────────────┐
  │  Preprocess   │──── normalize, clean, strip noise
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  Detect       │──── score across all signals
  └──────┬───────┘
         ▼
  ┌──────────────┐
  │  Explain      │──── build reasoning string
  └──────┬───────┘
         ▼
  JSON Response { verdict, confidence, explanation, flagged }
```

---

## 5. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Frontend | HTML5, CSS3, Vanilla JS | No build step, maximum portability |
| Backend | Python 3.10+, FastAPI | Async, fast, auto-generated docs |
| Server | Uvicorn | ASGI server for FastAPI |
| Testing | pytest | Standard Python test framework |
| Styling | Vanilla CSS (Inter font) | Minimal, technical aesthetic |

---

## 6. Project Structure

```
3xDevs/
├── docs/
│   └── architecture.md          # This document
├── frontend/
│   ├── index.html               # Main HTML page
│   └── static/
│       ├── css/
│       │   └── style.css        # Design system
│       └── js/
│           └── main.js          # Client-side logic
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── app.py               # FastAPI application & routes
│   ├── detector/
│   │   ├── __init__.py
│   │   ├── preprocess.py        # Text cleaning & normalization
│   │   ├── model.py             # Heuristic scoring engine
│   │   └── explainer.py         # Human-readable explanation generator
│   └── language/
│       ├── __init__.py
│       └── marathi.py           # Marathi-specific NLP utilities
├── tests/
│   └── test_detector.py         # Unit & integration tests
├── requirements.txt             # Python dependencies
├── README.md
├── LICENSE
└── .gitignore
```

---

## 7. API Documentation

### `GET /`
Serves the frontend `index.html`.

### `POST /detect`

**Request:**
```json
{
  "text": "This miracle cure is banned by the government! Forward to everyone!",
  "language": "en"
}
```

**Response:**
```json
{
  "verdict": "fake",
  "confidence": 87,
  "explanation": "This text contains sensationalist language ('miracle', 'banned') and urges readers to forward the message — patterns commonly found in misinformation.",
  "flagged": ["miracle", "banned", "forward to everyone"]
}
```

### `GET /health`
Returns `{ "status": "ok" }` for uptime checks.

---

## 8. Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

The application will be available at `http://localhost:8000`.

### Production
- Deploy behind **Nginx** or **Caddy** as reverse proxy.
- Use `gunicorn` with `uvicorn` workers: `gunicorn src.api.app:app -w 4 -k uvicorn.workers.UvicornWorker`.
- No database required — stateless request/response model.

---

## 9. Future Scope

| Feature | Description |
|---------|-------------|
| **Hindi support** | Add `src/language/hindi.py` with Hindi keyword sets |
| **ML model** | Train a lightweight classifier (e.g., IndicBERT) on labeled fake news datasets |
| **Fact-check API** | Cross-reference claims against fact-checking databases |
| **Browser extension** | Flag misinformation directly on WhatsApp Web / social media |
| **Feedback loop** | Allow users to report false positives/negatives for model improvement |

---

*Document version: 1.0 · Last updated: April 2026*
