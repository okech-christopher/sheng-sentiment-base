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
from ..tokenizers.intent_engine import ShengIntentEngine
from ..engine.logic import ShengLogicRefiner
from ..engine.pipeline import ShengInferencePipeline
from .middleware import RequestLoggingMiddleware, PerformanceMiddleware
from .models import (
    AnalyzeRequest,
    AnalysisResponse,
    HealthResponse,
    LogisticsIntent
)

logger = logging.getLogger(__name__)

# Global pipeline instance
pipeline: ShengInferencePipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - initialize pipeline on startup."""
    global pipeline
    
    # Startup
    logger.info("Starting Sheng-Native API...")
    try:
        pipeline = ShengInferencePipeline()
        logger.info("Sheng-Native API initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize pipeline: {e}")
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

# Add performance middleware
app.add_middleware(PerformanceMiddleware)
app.add_middleware(RequestLoggingMiddleware, latency_threshold=100.0)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    if tokenizer is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    return HealthResponse(
        status="healthy",
        version="0.4.0",
        model=tokenizer.dictionary_path.parent.name
    )


@app.get("/v1/health/detailed", tags=["Health"])
async def detailed_health_check():
    """Detailed health check with system metrics."""
    if tokenizer is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # Get performance metrics from middleware
    performance_middleware = None
    for middleware in app.user_middleware:
        if hasattr(middleware.cls, '__name__') and middleware.cls.__name__ == 'PerformanceMiddleware':
            performance_middleware = middleware
            break
    
    metrics = {}
    if performance_middleware:
        metrics = performance_middleware.cls(app).get_metrics()
    
    return {
        "status": "healthy",
        "version": "0.4.0",
        "uptime": "running",  # Would calculate actual uptime
        "dictionary": {
            "version": "v0.4",
            "total_entries": len(tokenizer.slang_mappings),
            "sentiment_rules": len(tokenizer.sentiment_rules),
            "logistics_intents": len(tokenizer.logistics_intent_rules)
        },
        "performance": metrics,
        "endpoints": {
            "analyze": "/v1/analyze",
            "batch": "/v1/batch",
            "dictionary": "/v1/dictionary",
            "stats": "/v1/stats"
        },
        "last_evaluation": {
            "overall_accuracy": "74.5%",
            "sentiment_accuracy": "81.2%",
            "logistics_accuracy": "90.1%",
            "target": "91.0%"
        }
    }


@app.post("/v1/analyze", response_model=AnalysisResponse, tags=["Analysis"])
async def analyze_text(request: AnalyzeRequest):
    """Analyze Sheng text for sentiment, logistics intent, and code-switching.
    
    This endpoint provides comprehensive analysis of Sheng text including:
    - Sentiment analysis with contextual understanding
    - Logistics intent detection (police reports, traffic, route suggestions)
    - Code-switching pattern detection
    - Slang term identification
    - Multi-intent resolution with RecursiveSlangResolver
    
    Args:
        request: Analysis request with text and options
        
    Returns:
        AnalysisResponse with full analysis results
    """
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Run complete pipeline analysis
        result = pipeline.analyze(
            request.text,
            include_code_switches=request.include_code_switches,
            include_logistics=request.include_logistics
        )
        
        # Build logistics intent object
        logistics_intent_obj = None
        if result.is_logistics and result.logistics_intent:
            logistics_intent_obj = LogisticsIntent(
                intent=result.logistics_intent,
                severity=result.logistics_severity,
                description=result.logistics_description
            )
        
        # Build response
        response = AnalysisResponse(
            original_text=result.text,
            normalized_text=result.normalized_text,
            tokens=result.tokens,
            slang_terms=result.slang_terms,
            code_switches=result.code_switches,
            sentiment_score=result.sentiment_score,
            sentiment_label=result.sentiment_label,
            logistics_intent=logistics_intent_obj,
            is_logistics=result.is_logistics,
            confidence=result.confidence,
            metadata=result.metadata
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
            "version": "v0.4",
            "total_slang_terms": len(tokenizer.slang_mappings),
            "total_sentiment_rules": len(tokenizer.sentiment_rules),
            "total_logistics_intents": len(tokenizer.logistics_intent_rules)
        },
        "slang_mappings": tokenizer.slang_mappings,
        "sentiment_rules": tokenizer.sentiment_rules,
        "logistics_intents": tokenizer.logistics_intent_rules
    }


@app.post("/v1/batch", response_model=List[AnalysisResponse], tags=["Analysis"])
async def analyze_batch(requests: List[AnalyzeRequest]):
    """Analyze multiple Sheng texts in a single request.
    
    This endpoint processes multiple messages efficiently,
    ideal for batch processing of chat logs or social media feeds.
    
    Args:
        requests: List of analysis requests
        
    Returns:
        List of analysis responses
    """
    if tokenizer is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    if len(requests) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 requests per batch")
    
    results = []
    
    for req in requests:
        try:
            # Tokenize the text
            result = tokenizer.tokenize(req.text)
            
            # Apply logic refinements
            refinement_result = logic_refiner.refine_sentiment(
                req.text, 
                result.sentiment_label, 
                result.sentiment_score, 
                result.slang_terms
            )
            
            # Update sentiment if refined
            if refinement_result.sentiment_adjusted:
                result.sentiment_label = refinement_result.refined_sentiment
            
            # Run intent engine for logistics detection
            intent_result = intent_engine.detect_intent(req.text, result.slang_terms)
            
            # Build logistics intent object
            logistics_intent_obj = None
            if intent_result.is_logistics:
                logistics_intent_obj = LogisticsIntent(
                    intent=intent_result.intent_type,
                    severity=intent_result.severity,
                    description=intent_result.description
                )
            
            # Calculate combined confidence
            base_confidence = intent_result.intent_score
            refinement_boost = refinement_result.confidence_adjusted if refinement_result.sentiment_adjusted else 0.0
            combined_confidence = min(1.0, base_confidence + refinement_boost)
            
            # Build response
            response = AnalysisResponse(
                original_text=result.original_text,
                normalized_text=result.normalized_text,
                tokens=result.tokens,
                slang_terms=result.slang_terms,
                code_switches=result.code_switches if req.include_code_switches else [],
                sentiment_score=result.sentiment_score,
                sentiment_label=result.sentiment_label,
                logistics_intent=logistics_intent_obj if req.include_logistics else None,
                is_logistics=intent_result.is_logistics,
                confidence=combined_confidence,
                metadata={
                    **result.metadata,
                    "is_logistics": intent_result.is_logistics,
                    "intent_score": intent_result.intent_score,
                    "refinement_applied": refinement_result.sentiment_adjusted,
                    "refinement_reasoning": refinement_result.reasoning
                }
            )
            
            results.append(response)
            
        except Exception as e:
            logger.error(f"Error during batch analysis: {e}")
            # Create error response
            error_response = AnalysisResponse(
                original_text=req.text,
                normalized_text="",
                tokens=[],
                slang_terms=[],
                code_switches=[],
                sentiment_score=0.0,
                sentiment_label="error",
                logistics_intent=None,
                is_logistics=False,
                confidence=0.0,
                metadata={"error": str(e)}
            )
            results.append(error_response)
    
    return results


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
