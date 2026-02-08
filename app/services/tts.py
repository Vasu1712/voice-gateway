import asyncio
import subprocess

class TTSService:
    def __init__(self, model_path="app/models/piper/en_US-lessac-medium.onnx"):
        self.model_path = model_path
        self.sample_rate = 22050
        print("✅ Piper CLI ready for streaming TTS")

    async def generate_stream(self, text: str):
        """Streams raw int16 PCM chunks (~20-100 ms each) using the piper CLI."""
        if not text.strip():
            return

        proc = await asyncio.create_subprocess_exec(
            "piper",
            "--model", self.model_path,
            "--output-raw",
            "--sentence-silence", "0.0",      # no artificial pauses
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Send text
        try:
            proc.stdin.write(text.encode("utf-8"))
            await proc.stdin.drain()
            proc.stdin.close()
        except Exception as e:
            print("Piper stdin error:", e)

        # Stream stdout in small chunks
        while True:
            chunk = await proc.stdout.read(2048)   # ~90 ms of audio
            if not chunk:
                break
            yield chunk
            await asyncio.sleep(0)   # allow interrupt check

        # Clean up
        await proc.wait()
        if proc.returncode != 0:
            err = (await proc.stderr.read()).decode(errors="ignore")
            print("Piper CLI error:", err)

tts_service = TTSService()