#!/usr/bin/env python3
"""
Startup script for Orpheus TTS FastAPI server.

This script provides a convenient way to start the API server with
configurable options and proper logging.
"""

import os
import sys
import argparse
import uvicorn
import logging
from pathlib import Path

def setup_logging(log_level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("orpheus_tts_api.log")
        ]
    )

def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import fastapi
        import uvicorn
        import torch
        import snac
        print("✓ All dependencies are available")
        return True
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Please install dependencies with: pip install -r requirements.txt")
        return False

def check_lm_studio():
    """Check if LM Studio is accessible."""
    import requests
    
    api_url = os.getenv("LM_STUDIO_API_URL", "http://192.168.68.95:1234")
    
    try:
        response = requests.get(f"{api_url}/v1/models", timeout=5)
        if response.status_code == 200:
            print(f"✓ LM Studio is accessible at {api_url}")
            return True
        else:
            print(f"✗ LM Studio returned status code {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Cannot connect to LM Studio at {api_url}: {e}")
        print("Please ensure LM Studio is running and the Orpheus model is loaded.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Start Orpheus TTS API Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       help="Log level (default: INFO)")
    parser.add_argument("--lm-studio-url", help="LM Studio API URL (default: http://192.168.68.95:1234)")
    parser.add_argument("--skip-checks", action="store_true", help="Skip dependency and LM Studio checks")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes (default: 1)")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    print("🎤 Starting Orpheus TTS API Server...")
    print(f"   Host: {args.host}")
    print(f"   Port: {args.port}")
    print(f"   Log Level: {args.log_level}")
    
    # Set LM Studio URL if provided
    if args.lm_studio_url:
        os.environ["LM_STUDIO_API_URL"] = f"{args.lm_studio_url}/v1/completions"
        print(f"   LM Studio URL: {args.lm_studio_url}")
    
    # Run checks unless skipped
    if not args.skip_checks:
        print("\n🔍 Running pre-flight checks...")
        
        if not check_dependencies():
            sys.exit(1)
        
        if not check_lm_studio():
            print("\n⚠️  Warning: LM Studio check failed. The API will start but TTS requests may fail.")
            response = input("Continue anyway? (y/N): ").strip().lower()
            if response != 'y':
                sys.exit(1)
    
    print("\n🚀 Starting server...\n")
    
    # Ensure outputs directory exists
    Path("outputs").mkdir(exist_ok=True)
    
    try:
        # Start the server
        uvicorn.run(
            "api:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level=args.log_level.lower(),
            workers=args.workers if not args.reload else 1,
            access_log=True
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()