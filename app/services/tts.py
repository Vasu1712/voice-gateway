import subprocess
import os
import uuid
import asyncio

class TTSService:
    async def generate_bytes(self, text):
        """Generates audio using macOS native 'say' command."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._generate_sync, text)

    def _generate_sync(self, text):
        filename = f"temp_{uuid.uuid4()}.wav"
        
        # macOS 'say' command: 
        # --data-format=LEI16@16000 forces 16kHz Mono WAV (Standard for browser playback)
        try:
            subprocess.run(
                ["say", "-o", filename, "--data-format=LEI16@16000", text], 
                check=True
            )
            
            with open(filename, "rb") as f:
                data = f.read()
                
            os.remove(filename)
            return data
        except Exception as e:
            print(f"TTS Error: {e}")
            return b""

tts_service = TTSService()