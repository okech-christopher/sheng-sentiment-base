"""FastAPI service for Sheng-Native NLP API.

This service provides REST endpoints for Sheng text analysis including
sentiment detection, logistics intent classification, and code-switching analysis.
"""

import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ..tokenizers.sheng_tokenizer import ShengTokenizer
from .models import (
    AnalyzeRequest,
    AnalysisResponse,
    HealthResponse,
    LogisticsIntent
)

logger = logging.getLogger(__name__)

# Global tokenizer instance
tokenizer: ShengTokenizer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - initialize tokenizer on startup."""
    global tokenizer
    
    # Startup
    logger.info("Starting Sheng-Native API...")
    try:
        tokenizer = ShengTokenizer()
        logger.info("Sheng-Native API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize tokenizer: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down Sheng-Native API...")


# Initialize FastAPI app
app = FastAPI(
    title="Sheng-Native API",
    description="Contextual sentiment analysis and logistics intent detection for Kenyan Sheng",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    if tokenizer is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return HealthResponse(
        status="healthy",
        version="0.3.0",
        model=tokenizer.dictionary_path.parent.name
    )


@app.post("/v1/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_text(request: AnalyzeRequest):
    """Analyze Sheng text for sentiment, logistics intent, and code-switching.
    
    This endpoint provides comprehensive analysis of Sheng text including:
    - Sentiment analysis with contextual understanding
    - Logistics intent detection (police reports, traffic, route suggestions)
    - Code-switching pattern detection
    - Slang term identification
    
    Args:
        request: Analysis request with text and options
        
    Returns:
        AnalysisResponse with full analysis results
    """
    if tokenizer is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Tokenize the text
        result = tokenizer.tokenize(request.text)
        
        # Build logistics intent object
        logistics_intent_obj = None
        if result.logistics_intent:
            logistics_intent_obj = LogisticsIntent(
                intent=result.logistics_intent,
                severity=result.logistics_severity,
                description=result.logistics_description
            )
        
        # Build response
        response = AnalysisResponse(
            original_text=result.original_text,
            normalized_text=result.normalized_text,
            tokens=result.tokens,
            slang_terms=result.slang_terms,
            code_switches=result.code_switches if request.include_code_switches else [],
            sentiment_score=result.sentiment_score,
            sentiment_label=result.sentiment_label,
            logistics_intent=logistics_intent_obj if request.include_logistics else None,
            is_logistics=intent_result.is_logistics,
            confidence=intent_result.intent_score,
            metadata={
                **result.metadata,
                "is_logistics": intent_result.is_logistics,
                "intent_score": intent_result.intent_score
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/v1/stats", tags=["System"])
async def get_stats():
    """Get system statistics and model information."""
    if tokenizer is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "slang_terms_count": len(tokenizer.slang_mappings),
        "sentiment_rules_count": len(tokenizer.sentiment_rules),
        "logistics_intent_count": len(tokenizer.logistics_intent_rules),
        "dictionary_version": "v0.3",
        "model_status": "loaded"
    }


@app.get("/v1/dictionary", tags=["System"])
async def get_dictionary():
    """Get the current Sheng dictionary entries."""
    if tokenizer is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return {
        "metadata": {
            "version": "v0.3",
            "total_slang_terms": len(tokenizer.slang_mappings),
            "total_sentiment_rules": len(tokenizer.sentiment_rules),
            "total_logistics_intents": len(tokenizer.logistics_intent_rules)
        },
        "slang_mappings": tokenizer.slang_mappings,
        "sentiment_rules": tokenizer.sentiment_rules,
        "logistics_intents": tokenizer.logistics_intent_rules
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Sheng-Native API",
        "version": "0.3.0",
        "description": "Contextual sentiment analysis and logistics intent detection for Kenyan Sheng",
        "endpoints": {
            "health": "/health",
            "analyze": "/v1/analyze",
            "stats": "/v1/stats",
            "docs": "/docs"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
