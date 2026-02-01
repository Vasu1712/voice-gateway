# app/services/stt.py
from faster_whisper import WhisperModel
import numpy as np
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Run heavy model in a separate thread to not block asyncio
executor = ThreadPoolExecutor(max_workers=1)

class STTService:
    def __init__(self):
        print("Loading Whisper model...")
        # 'tiny' is fast, 'base' or 'small' are better accuracy
        self.model = WhisperModel("tiny", device="cpu", compute_type="int8")
        print("Whisper loaded.")

    async def transcribe(self, audio_float32):
        """Transcribes raw float32 audio."""
        loop = asyncio.get_running_loop()
        # Whisper expects float32
        result = await loop.run_in_executor(
            executor, 
            self._transcribe_sync, 
            audio_float32
        )
        return result

    def _transcribe_sync(self, audio):
        segments, _ = self.model.transcribe(audio, beam_size=5, language="en")
        text = " ".join([segment.text for segment in segments])
        return text

stt_service = STTService()