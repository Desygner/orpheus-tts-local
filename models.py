from pydantic import BaseModel, Field, validator
from typing import Optional, List
from enum import Enum

class VoiceType(str, Enum):
    """Available voice types for TTS synthesis."""
    TARA = "tara"
    LEAH = "leah" 
    JESS = "jess"
    LEO = "leo"
    DAN = "dan"
    MIA = "mia"
    ZAC = "zac"
    ZOE = "zoe"

class SynthesizeRequest(BaseModel):
    """Request model for TTS synthesis."""
    text: str = Field(..., min_length=1, max_length=5000, description="Text to convert to speech")
    voice: VoiceType = Field(default=VoiceType.TARA, description="Voice to use for synthesis")
    temperature: float = Field(default=0.6, ge=0.1, le=2.0, description="Temperature for generation (0.1-2.0)")
    top_p: float = Field(default=0.9, ge=0.1, le=1.0, description="Top-p sampling parameter (0.1-1.0)")
    repetition_penalty: float = Field(default=1.1, ge=1.0, le=2.0, description="Repetition penalty (1.0-2.0)")
    max_tokens: int = Field(default=1200, ge=100, le=5000, description="Maximum tokens to generate")

    @validator('text')
    def validate_text(cls, v):
        """Validate text input."""
        if not v.strip():
            raise ValueError('Text cannot be empty or only whitespace')
        return v.strip()

class VoiceInfo(BaseModel):
    """Information about a voice."""
    name: str = Field(..., description="Voice name")
    is_default: bool = Field(..., description="Whether this is the default voice")
    description: str = Field(..., description="Voice description")

class VoicesResponse(BaseModel):
    """Response model for available voices."""
    voices: List[VoiceInfo] = Field(..., description="List of available voices")
    emotion_tags: List[str] = Field(..., description="Available emotion tags")

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    lm_studio_connected: bool = Field(..., description="LM Studio connection status")
    version: str = Field(..., description="API version")

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    error_code: str = Field(..., description="Error code")

class SynthesizeResponse(BaseModel):
    """Response model for successful synthesis."""
    message: str = Field(..., description="Success message")
    duration_seconds: float = Field(..., description="Generated audio duration in seconds")
    voice_used: str = Field(..., description="Voice that was used for synthesis")
    filename: str = Field(..., description="Generated filename")