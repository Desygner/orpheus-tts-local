import os
import requests
import json
import time
import wave
import uuid
import tempfile
from typing import Generator, Optional, Tuple
import threading
import queue
import asyncio
from models import VoiceType, VoiceInfo

class TTSService:
    """Service class for Text-to-Speech functionality using Orpheus model."""
    
    def __init__(self, api_url: str = "http://192.168.68.66:1234/v1/completions"):
        self.api_url = api_url
        self.headers = {"Content-Type": "application/json"}
        self.sample_rate = 24000
        self.available_voices = ["tara", "leah", "jess", "leo", "dan", "mia", "zac", "zoe"]
        self.default_voice = "tara"
        self.custom_token_prefix = "<custom_token_"
        
    def get_available_voices(self) -> list[VoiceInfo]:
        """Get list of available voices with metadata."""
        voices = []
        for voice in self.available_voices:
            voices.append(VoiceInfo(
                name=voice,
                is_default=(voice == self.default_voice),
                description=f"Orpheus TTS voice: {voice.title()}"
            ))
        return voices
    
    def get_emotion_tags(self) -> list[str]:
        """Get list of available emotion tags."""
        return ["laugh", "chuckle", "sigh", "cough", "sniffle", "groan", "yawn", "gasp"]
    
    def format_prompt(self, prompt: str, voice: str = "tara") -> str:
        """Format prompt for Orpheus model with voice prefix and special tokens."""
        if voice not in self.available_voices:
            voice = self.default_voice
            
        formatted_prompt = f"{voice}: {prompt}"
        special_start = "<|audio|>"
        special_end = "<|eot_id|>"
        
        return f"{special_start}{formatted_prompt}{special_end}"
    
    def check_lm_studio_connection(self) -> bool:
        """Check if LM Studio is accessible."""
        try:
            response = requests.get(self.api_url.replace('/v1/completions', '/v1/models'), timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def generate_tokens_from_api(self, prompt: str, voice: str = "tara", 
                               temperature: float = 0.6, top_p: float = 0.9, 
                               max_tokens: int = 1200, repetition_penalty: float = 1.1) -> Generator[str, None, None]:
        """Generate tokens from text using LM Studio API."""
        formatted_prompt = self.format_prompt(prompt, voice)
        
        payload = {
            "model": "orpheus-3b-0.1-ft-q4_k_m",
            "prompt": formatted_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "repeat_penalty": repetition_penalty,
            "stream": True
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=payload, stream=True, timeout=30)
            
            if response.status_code != 200:
                raise Exception(f"LM Studio API error: {response.status_code} - {response.text}")
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                            
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and len(data['choices']) > 0:
                                token_text = data['choices'][0].get('text', '')
                                if token_text:
                                    yield token_text
                        except json.JSONDecodeError:
                            continue
                            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to LM Studio: {str(e)}")
    
    def turn_token_into_id(self, token_string: str, index: int) -> Optional[int]:
        """Convert token string to numeric ID for audio processing."""
        token_string = token_string.strip()
        last_token_start = token_string.rfind(self.custom_token_prefix)
        
        if last_token_start == -1:
            return None
        
        last_token = token_string[last_token_start:]
        
        if last_token.startswith(self.custom_token_prefix) and last_token.endswith(">"):
            try:
                number_str = last_token[14:-1]
                token_id = int(number_str) - 10 - ((index % 7) * 4096)
                return token_id
            except ValueError:
                return None
        return None
    
    def convert_to_audio(self, multiframe: list, count: int) -> Optional[bytes]:
        """Convert token frames to audio using decoder."""
        from decoder import convert_to_audio as orpheus_convert_to_audio
        return orpheus_convert_to_audio(multiframe, count)
    
    async def tokens_decoder(self, token_gen) -> Generator[bytes, None, None]:
        """Asynchronous token decoder that converts token stream to audio stream."""
        buffer = []
        count = 0
        async for token_text in token_gen:
            token = self.turn_token_into_id(token_text, count)
            if token is not None and token > 0:
                buffer.append(token)
                count += 1
                
                if count % 7 == 0 and count > 27:
                    buffer_to_proc = buffer[-28:]
                    audio_samples = self.convert_to_audio(buffer_to_proc, count)
                    if audio_samples is not None:
                        yield audio_samples
    
    def tokens_decoder_sync(self, syn_token_gen, output_file: Optional[str] = None) -> Tuple[list, float]:
        """Synchronous wrapper for the asynchronous token decoder."""
        audio_queue = queue.Queue()
        audio_segments = []
        
        wav_file = None
        if output_file:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            wav_file = wave.open(output_file, "wb")
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
        
        async def async_token_gen():
            for token in syn_token_gen:
                yield token

        async def async_producer():
            async for audio_chunk in self.tokens_decoder(async_token_gen()):
                audio_queue.put(audio_chunk)
            audio_queue.put(None)

        def run_async():
            asyncio.run(async_producer())

        thread = threading.Thread(target=run_async)
        thread.start()

        while True:
            audio = audio_queue.get()
            if audio is None:
                break
            
            audio_segments.append(audio)
            
            if wav_file:
                wav_file.writeframes(audio)
        
        if wav_file:
            wav_file.close()
        
        thread.join()
        
        duration = sum([len(segment) // (2 * 1) for segment in audio_segments]) / self.sample_rate
        return audio_segments, duration
    
    def generate_speech(self, prompt: str, voice: str = "tara", 
                       temperature: float = 0.6, top_p: float = 0.9, 
                       max_tokens: int = 1200, repetition_penalty: float = 1.1,
                       output_file: Optional[str] = None) -> Tuple[list, float, str]:
        """Generate speech from text and return audio segments, duration, and filename."""
        
        if not self.check_lm_studio_connection():
            raise Exception("Cannot connect to LM Studio. Please ensure it's running and accessible.")
        
        if voice not in self.available_voices:
            voice = self.default_voice
        
        if output_file is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            output_file = f"outputs/{voice}_{timestamp}_{unique_id}.wav"
        
        os.makedirs("outputs", exist_ok=True)
        
        try:
            audio_segments, duration = self.tokens_decoder_sync(
                self.generate_tokens_from_api(
                    prompt=prompt,
                    voice=voice,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    repetition_penalty=repetition_penalty
                ),
                output_file=output_file
            )
            
            return audio_segments, duration, output_file
            
        except Exception as e:
            if os.path.exists(output_file):
                os.remove(output_file)
            raise e