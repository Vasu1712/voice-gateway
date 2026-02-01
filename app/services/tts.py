# app/services/tts.py
import pyttsx3
import asyncio
import os
import uuid

class TTSService:
    def __init__(self):
        pass

    CHUNK_SIZE = 320  # 20ms @ 16kHz

    async def stream_tts(text_stream, ws, interrupt_event):
        for text_chunk in text_stream:
            if interrupt_event.is_set():
                break

            audio = tts_model.generate(text_chunk)
            audio = audio.astype("float32")

            for i in range(0, len(audio), CHUNK_SIZE):
                if interrupt_event.is_set():
                    return

                chunk = audio[i:i+CHUNK_SIZE]
                await ws.send_bytes(chunk.tobytes())

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