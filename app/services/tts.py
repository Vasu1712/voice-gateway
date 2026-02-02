# app/services/tts.py
import pyttsx3
import asyncio
import os
import uuid

class TTSService:
    def __init__(self):
        pass

    async def generate_bytes(self, text):
        """Generates WAV audio bytes from text."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._generate_sync, text)

    def _generate_sync(self, text):
        engine = pyttsx3.init()
        filename = f"temp_{uuid.uuid4()}.wav"
        
        engine.save_to_file(text, filename)
        engine.runAndWait()
        
        with open(filename, "rb") as f:
            data = f.read()
            
        os.remove(filename)
        return data

tts_service = TTSService()