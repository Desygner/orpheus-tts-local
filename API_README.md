# Orpheus TTS FastAPI Server

A RESTful API service for Orpheus Text-to-Speech synthesis using LM Studio.

## Quick Start

1. **Install dependencies:**

   ```bash
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Start LM Studio** with the Orpheus model loaded

3. **Start the API server:**

   ```bash
   python run_api.py
   ```

4. **Test the API:**
   ```bash
   python test_api.py
   ```

## API Endpoints

### Health Check

```http
GET /health
```

Returns server status and LM Studio connection status.

### Available Voices

```http
GET /voices
```

Returns list of available voices and emotion tags.

### Synthesize Speech (Audio File)

```http
POST /synthesize
Content-Type: application/json

{
  "text": "Hello, this is a test",
  "voice": "tara",
  "temperature": 0.6,
  "top_p": 0.9,
  "repetition_penalty": 1.1,
  "max_tokens": 1200
}
```

Returns audio file as streaming response.

### Synthesize Speech (Metadata Only)

```http
POST /synthesize-info
Content-Type: application/json

{
  "text": "Hello, this is a test",
  "voice": "tara"
}
```

Returns synthesis metadata without audio file.

## Voice Options

- `tara` (default) - Best overall voice for general use
- `leah`, `jess`, `leo`, `dan`, `mia`, `zac`, `zoe`

## Emotion Tags

Add emotion to speech with XML tags:

- `<laugh>`, `<chuckle>`, `<sigh>`, `<cough>`
- `<sniffle>`, `<groan>`, `<yawn>`, `<gasp>`

Example: `"Hello <laugh> this is funny <laugh> text"`

## Configuration

Environment variables:

- `LM_STUDIO_API_URL` - LM Studio API URL (default: http://192.168.68.95:1234)
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)

## Command Line Usage

```bash
# Start with custom settings
python run_api.py --host 127.0.0.1 --port 8080 --lm-studio-url http://localhost:1234

# Development mode with auto-reload
python run_api.py --reload

# Skip pre-flight checks
python run_api.py --skip-checks
```

## Testing

```bash
# Run all tests
python test_api.py

# Test specific endpoint
python test_api.py --test health
python test_api.py --test voices
python test_api.py --test info
python test_api.py --test audio

# Custom text and voice
python test_api.py --text "Custom message" --voice leo --output my_audio.wav
```

## API Documentation

Once the server is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Example Usage with curl

```bash
# Health check
curl http://localhost:8000/health

# Get voices
curl http://localhost:8000/voices

# Synthesize audio
curl -X POST http://localhost:8000/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "tara"}' \
  --output hello.wav

# Get synthesis info
curl -X POST http://localhost:8000/synthesize-info \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "voice": "tara"}'
```

## Example Usage with Python

```python
import requests

# Health check
response = requests.get("http://localhost:8000/health")
print(response.json())

# Synthesize speech
payload = {
    "text": "Hello, this is a test",
    "voice": "tara",
    "temperature": 0.6
}

response = requests.post("http://localhost:8000/synthesize", json=payload)
with open("output.wav", "wb") as f:
    f.write(response.content)
```

## Troubleshooting

1. **Connection refused errors:**

   - Ensure LM Studio is running
   - Check the API URL configuration
   - Verify the Orpheus model is loaded in LM Studio

2. **Missing dependencies:**

   - Run `pip install -r requirements.txt`
   - Ensure virtual environment is activated

3. **Audio generation fails:**
   - Check LM Studio logs
   - Verify model is properly loaded
   - Try reducing max_tokens parameter

## Architecture

- **api.py** - Main FastAPI application
- **models.py** - Pydantic request/response models
- **tts_service.py** - TTS logic and LM Studio integration
- **run_api.py** - Server startup script
- **test_api.py** - API testing utilities
