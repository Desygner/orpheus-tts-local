#!/bin/bash

# Orpheus TTS Local Environment Setup
echo "Activating Orpheus TTS Local environment..."

# Activate virtual environment
source .venv/bin/activate

# Set environment variables
export ORPHEUS_TTS_LOCAL=1

echo "Environment activated!"
echo "To use the TTS system, ensure LM Studio is running with the Orpheus model loaded."
echo ""
echo "Example usage:"
echo "  python gguf_orpheus.py --text 'Hello world' --voice tara"
echo ""
echo "Available voices: tara, leah, jess, leo, dan, mia, zac, zoe"