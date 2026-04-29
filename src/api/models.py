"""Pydantic models for API request/response validation."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class AnalyzeRequest(BaseModel):
    """Request model for text analysis."""
    
    text: str = Field(..., min_length=1, max_length=1000, description="Sheng text to analyze")
    include_logistics: bool = Field(default=True, description="Include logistics intent detection")
    include_code_switches: bool = Field(default=True, description="Include code-switching analysis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Karao wako mabs, jam imetupa",
                "include_logistics": True,
                "include_code_switches": True
            }
        }


class LogisticsIntent(BaseModel):
    """Logistics intent information."""
    
    intent: Optional[str] = Field(None, description="Detected logistics intent")
    severity: Optional[str] = Field(None, description="Severity level: low, medium, high")
    description: Optional[str] = Field(None, description="Human-readable description")
    
    class Config:
        json_schema_extra = {
            "example": {
                "intent": "police_report",
                "severity": "medium",
                "description": "Police checkpoint or presence"
            }
        }


class AnalysisResponse(BaseModel):
    """Response model for text analysis."""
    
    original_text: str = Field(..., description="Original input text")
    normalized_text: str = Field(..., description="Normalized Sheng text")
    tokens: List[str] = Field(..., description="Tokenized words")
    slang_terms: List[str] = Field(..., description="Detected Sheng slang terms")
    code_switches: List[str] = Field(default=[], description="Detected code-switching patterns")
    sentiment_score: float = Field(..., description="Sentiment score from -1.0 to 1.0")
    sentiment_label: str = Field(..., description="Sentiment label: positive, negative, neutral")
    logistics_intent: Optional[LogisticsIntent] = Field(None, description="Logistics intent information")
    is_logistics: bool = Field(default=False, description="Whether text contains logistics intent")
    confidence: float = Field(default=0.0, description="Confidence score for logistics detection")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_text": "Karao wako mabs",
                "normalized_text": "karao wako mabs",
                "tokens": ["karao", "wako", "mabs"],
                "slang_terms": ["karao", "mabs"],
                "code_switches": [],
                "sentiment_score": -0.5,
                "sentiment_label": "negative",
                "logistics_intent": {
                    "intent": "police_report",
                    "severity": "medium",
                    "description": "Police checkpoint or presence"
                },
                "metadata": {
                    "token_count": 3,
                    "slang_count": 2,
                    "switch_count": 0,
                    "has_logistics_intent": True
                }
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(..., description="API status")
    version: str = Field(..., description="API version")
    model: str = Field(..., description="Dictionary version")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "0.3.0",
                "model": "Sheng-Native Dictionary v0.3"
            }
        }
