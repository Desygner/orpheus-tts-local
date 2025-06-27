import os
import logging
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from models import (
    SynthesizeRequest, SynthesizeResponse, VoicesResponse, 
    HealthResponse, ErrorResponse, VoiceInfo
)
from tts_service import TTSService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global TTS service instance
tts_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global tts_service
    
    # Startup
    logger.info("Starting Orpheus TTS API...")
    api_url = os.getenv("LM_STUDIO_API_URL", "http://192.168.68.95:1234/v1/completions")
    tts_service = TTSService(api_url=api_url)
    logger.info(f"TTS Service initialized with LM Studio URL: {api_url}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Orpheus TTS API...")

# Create FastAPI app
app = FastAPI(
    title="Orpheus TTS API",
    description="RESTful API for Orpheus Text-to-Speech synthesis using LM Studio",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint to verify service status."""
    try:
        lm_studio_connected = tts_service.check_lm_studio_connection() if tts_service else False
        
        return HealthResponse(
            status="healthy" if lm_studio_connected else "degraded",
            lm_studio_connected=lm_studio_connected,
            version="1.0.0"
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Health check failed",
                detail=str(e),
                error_code="HEALTH_CHECK_ERROR"
            ).dict()
        )

@app.get("/voices", response_model=VoicesResponse, tags=["Voices"])
async def get_voices():
    """Get list of available voices and emotion tags."""
    try:
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS service not initialized")
        
        voices = tts_service.get_available_voices()
        emotion_tags = tts_service.get_emotion_tags()
        
        return VoicesResponse(
            voices=voices,
            emotion_tags=emotion_tags
        )
    except Exception as e:
        logger.error(f"Failed to get voices: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Failed to retrieve voices",
                detail=str(e),
                error_code="VOICES_ERROR"
            ).dict()
        )

@app.post("/synthesize", tags=["TTS"])
async def synthesize_speech(request: SynthesizeRequest):
    """
    Synthesize speech from text and return audio file.
    
    Returns the generated WAV audio file as a streaming response.
    """
    try:
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS service not initialized")
        
        logger.info(f"Starting synthesis for text: '{request.text[:50]}...' with voice: {request.voice}")
        
        # Generate speech
        audio_segments, duration, output_file = tts_service.generate_speech(
            prompt=request.text,
            voice=request.voice.value,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            repetition_penalty=request.repetition_penalty
        )
        
        logger.info(f"Synthesis completed. Duration: {duration:.2f}s, File: {output_file}")
        
        # Prepare file response
        if not os.path.exists(output_file):
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse(
                    error="Audio file generation failed",
                    detail="Generated audio file not found",
                    error_code="FILE_NOT_FOUND"
                ).dict()
            )
        
        # Return file as streaming response
        def iterfile():
            try:
                with open(output_file, "rb") as file_like:
                    yield from file_like
            finally:
                # Clean up the temporary file after streaming
                if os.path.exists(output_file):
                    try:
                        os.remove(output_file)
                        logger.info(f"Cleaned up temporary file: {output_file}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to cleanup file {output_file}: {cleanup_error}")
        
        # Get file size for Content-Length header
        file_size = os.path.getsize(output_file)
        filename = os.path.basename(output_file)
        
        headers = {
            "Content-Disposition": f"attachment; filename={filename}",
            "Content-Length": str(file_size),
            "X-Duration-Seconds": str(duration),
            "X-Voice-Used": request.voice.value,
            "X-Generated-Segments": str(len(audio_segments))
        }
        
        return StreamingResponse(
            iterfile(),
            media_type="audio/wav",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synthesis failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Speech synthesis failed",
                detail=str(e),
                error_code="SYNTHESIS_ERROR"
            ).dict()
        )

@app.post("/synthesize-info", response_model=SynthesizeResponse, tags=["TTS"])
async def synthesize_speech_info(request: SynthesizeRequest):
    """
    Synthesize speech from text and return metadata without the audio file.
    
    Useful for testing and getting synthesis information without downloading audio.
    """
    try:
        if not tts_service:
            raise HTTPException(status_code=503, detail="TTS service not initialized")
        
        logger.info(f"Starting synthesis info for text: '{request.text[:50]}...' with voice: {request.voice}")
        
        # Generate speech
        audio_segments, duration, output_file = tts_service.generate_speech(
            prompt=request.text,
            voice=request.voice.value,
            temperature=request.temperature,
            top_p=request.top_p,
            max_tokens=request.max_tokens,
            repetition_penalty=request.repetition_penalty
        )
        
        # Clean up the file since we're only returning metadata
        if os.path.exists(output_file):
            try:
                os.remove(output_file)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup file {output_file}: {cleanup_error}")
        
        return SynthesizeResponse(
            message="Speech synthesis completed successfully",
            duration_seconds=duration,
            voice_used=request.voice.value,
            filename=os.path.basename(output_file)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Synthesis info failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="Speech synthesis failed",
                detail=str(e),
                error_code="SYNTHESIS_ERROR"
            ).dict()
        )

# Custom exception handler for better error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return Response(
        content=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        status_code=exc.status_code,
        media_type="application/json"
    )

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )