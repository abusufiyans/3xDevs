"""
FastAPI application — serves the frontend and exposes the /detect API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.detector.model import detect
from src.detector.explainer import explain

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SatyaCheck API",
    description="Misinformation detection in regional Indian languages",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class DetectRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: str = Field(default="en", pattern="^(en|mr)$")


class DetectResponse(BaseModel):
    verdict: str
    confidence: int
    explanation: str
    flagged: list[str]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def serve_frontend():
    """Serve the main frontend page."""
    return FileResponse("frontend/index.html")


@app.post("/detect", response_model=DetectResponse)
def detect_misinformation(req: DetectRequest):
    """
    Analyze text for misinformation and return a verdict.

    - **text**: The content to analyze (1–5000 characters).
    - **language**: ``en`` (English) or ``mr`` (Marathi).
    """
    from src.detector.llm_verifier import check_authenticity_with_llm

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # Try LLM first
    llm_result = check_authenticity_with_llm(req.text, req.language)
    
    # If LLM verification is unavailable, fallback to heuristic model
    if "LLM verification is currently unavailable" in llm_result["explanation"] or "An error occurred" in llm_result["explanation"]:
        result = detect(req.text, req.language)
        explanation_text = explain(result, req.language)
        return DetectResponse(
            verdict=result.verdict,
            confidence=result.confidence,
            explanation=explanation_text,
            flagged=result.flagged,
        )

    return DetectResponse(
        verdict=llm_result["verdict"],
        confidence=llm_result["confidence"],
        explanation=llm_result["explanation"],
        flagged=llm_result["flagged"],
    )


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}