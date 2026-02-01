# app/services/vad.py
import numpy as np

class VADService:
    def is_speech(self, audio_chunk, threshold=0.01):
        """
        Simple energy based VAD.
        Returns True if audio energy is above threshold.
        """
        if len(audio_chunk) == 0: return False
        return np.mean(np.abs(audio_chunk)) > threshold

vad_service = VADService()