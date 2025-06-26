#!/usr/bin/env python3
"""
Test script for Orpheus TTS API endpoints.

This script tests the main API functionality to ensure everything is working correctly.
"""

import requests
import json
import time
import os
from typing import Dict, Any

class TTSAPITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_health(self) -> Dict[str, Any]:
        """Test the health endpoint."""
        print("🔍 Testing health endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Health check passed: {data['status']}")
                print(f"  LM Studio connected: {data['lm_studio_connected']}")
                print(f"  Version: {data['version']}")
                return data
            else:
                print(f"✗ Health check failed with status {response.status_code}")
                return {"error": response.text}
        except Exception as e:
            print(f"✗ Health check error: {e}")
            return {"error": str(e)}
    
    def test_voices(self) -> Dict[str, Any]:
        """Test the voices endpoint."""
        print("\n🎤 Testing voices endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/voices")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Found {len(data['voices'])} voices:")
                for voice in data['voices']:
                    marker = "★" if voice['is_default'] else " "
                    print(f"  {marker} {voice['name']}: {voice['description']}")
                print(f"  Emotion tags: {', '.join(data['emotion_tags'])}")
                return data
            else:
                print(f"✗ Voices request failed with status {response.status_code}")
                return {"error": response.text}
        except Exception as e:
            print(f"✗ Voices request error: {e}")
            return {"error": str(e)}
    
    def test_synthesize_info(self, text: str = "Hello, this is a test", voice: str = "tara") -> Dict[str, Any]:
        """Test the synthesize-info endpoint."""
        print(f"\n🔊 Testing synthesis info for: '{text}' with voice '{voice}'...")
        try:
            payload = {
                "text": text,
                "voice": voice,
                "temperature": 0.6,
                "top_p": 0.9,
                "repetition_penalty": 1.1
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/synthesize-info", json=payload)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Synthesis completed in {end_time - start_time:.2f}s")
                print(f"  Duration: {data['duration_seconds']:.2f}s")
                print(f"  Voice used: {data['voice_used']}")
                print(f"  Filename: {data['filename']}")
                return data
            else:
                print(f"✗ Synthesis failed with status {response.status_code}")
                print(f"  Error: {response.text}")
                return {"error": response.text}
        except Exception as e:
            print(f"✗ Synthesis error: {e}")
            return {"error": str(e)}
    
    def test_synthesize_audio(self, text: str = "Hello, this is a test", voice: str = "tara", 
                            save_file: str = "test_output.wav") -> Dict[str, Any]:
        """Test the synthesize endpoint and save audio file."""
        print(f"\n🎵 Testing audio synthesis for: '{text}' with voice '{voice}'...")
        try:
            payload = {
                "text": text,
                "voice": voice,
                "temperature": 0.6,
                "top_p": 0.9,
                "repetition_penalty": 1.1
            }
            
            start_time = time.time()
            response = self.session.post(f"{self.base_url}/synthesize", json=payload, stream=True)
            end_time = time.time()
            
            if response.status_code == 200:
                # Save the audio file
                with open(save_file, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                file_size = os.path.getsize(save_file)
                duration = response.headers.get('X-Duration-Seconds', 'Unknown')
                voice_used = response.headers.get('X-Voice-Used', 'Unknown')
                
                print(f"✓ Audio synthesis completed in {end_time - start_time:.2f}s")
                print(f"  File saved: {save_file} ({file_size} bytes)")
                print(f"  Duration: {duration}s")
                print(f"  Voice used: {voice_used}")
                print(f"  Content-Type: {response.headers.get('content-type')}")
                
                return {
                    "success": True,
                    "file_size": file_size,
                    "duration": duration,
                    "voice_used": voice_used
                }
            else:
                print(f"✗ Audio synthesis failed with status {response.status_code}")
                print(f"  Error: {response.text}")
                return {"error": response.text}
        except Exception as e:
            print(f"✗ Audio synthesis error: {e}")
            return {"error": str(e)}
    
    def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting Orpheus TTS API Tests\n")
        
        results = {}
        
        # Test health
        results['health'] = self.test_health()
        
        # Test voices
        results['voices'] = self.test_voices()
        
        # Test synthesis info
        results['synthesis_info'] = self.test_synthesize_info()
        
        # Test audio synthesis (only if previous tests passed)
        if 'error' not in results['health'] and 'error' not in results['synthesis_info']:
            results['audio_synthesis'] = self.test_synthesize_audio()
        else:
            print("\n⚠️  Skipping audio synthesis test due to previous failures")
        
        # Summary
        print(f"\n📊 Test Summary:")
        for test_name, result in results.items():
            status = "✓ PASS" if 'error' not in result else "✗ FAIL"
            print(f"  {test_name}: {status}")
        
        return results

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Orpheus TTS API")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--text", default="Hello, this is a test of the Orpheus TTS API", help="Text to synthesize")
    parser.add_argument("--voice", default="tara", help="Voice to use")
    parser.add_argument("--output", default="test_output.wav", help="Output audio file")
    parser.add_argument("--test", choices=["health", "voices", "info", "audio", "all"], 
                       default="all", help="Which test to run")
    
    args = parser.parse_args()
    
    tester = TTSAPITester(args.url)
    
    if args.test == "health":
        tester.test_health()
    elif args.test == "voices":
        tester.test_voices()
    elif args.test == "info":
        tester.test_synthesize_info(args.text, args.voice)
    elif args.test == "audio":
        tester.test_synthesize_audio(args.text, args.voice, args.output)
    else:
        tester.run_all_tests()

if __name__ == "__main__":
    main()