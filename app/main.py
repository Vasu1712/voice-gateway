#app/main.py
import asyncio
import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from app.services import vad_service, stt_service, llm_service, tts_service

app = FastAPI(title="Full-Duplex Voice Agent")

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    with open("app/static/index.html") as f:
        return HTMLResponse(content=f.read())

@app.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    
    state = {
        "is_speaking": False,
        "interrupt_signal": asyncio.Event(),
        "audio_buffer": bytearray()
    }

    async def receive_loop():
        try:
            while True:
                data = await websocket.receive_bytes()
                audio_chunk = np.frombuffer(data, dtype=np.float32)

                if vad_service.is_speech(audio_chunk):
                    # Barge-in detection
                    if state["is_speaking"] and not state["interrupt_signal"].is_set():
                        print("🛑 BARGE-IN DETECTED")
                        state["interrupt_signal"].set()
                        try:
                            await websocket.send_json({"type": "interrupt"})
                        except:
                            pass
                    
                    state["audio_buffer"].extend(data)
                else:
                    # Silence → process utterance
                    if len(state["audio_buffer"]) > 32000:  # ~0.5 s
                        audio_to_process = np.frombuffer(state["audio_buffer"], dtype=np.float32)
                        state["audio_buffer"] = bytearray()
                        asyncio.create_task(process_and_respond(audio_to_process))

        except WebSocketDisconnect:
            print("Client disconnected")
        except Exception as e:
            print(f"receive_loop error: {e}")

    async def process_and_respond(audio_data):
        if state["is_speaking"]:
            return

        transcript = await stt_service.transcribe(audio_data)
        if not transcript or len(transcript.strip()) < 2:
            return

        print(f"User: {transcript}")
        state["is_speaking"] = True
        state["interrupt_signal"].clear()

        llm_generator = llm_service.generate_stream(transcript)
        sentence_buffer = ""

        async for text_chunk in llm_generator:
            if state["interrupt_signal"].is_set():
                break

            sentence_buffer += text_chunk

            # Send a phrase as soon as we have punctuation or ~120 chars
            if any(p in text_chunk for p in ".!?") or len(sentence_buffer) > 120:
                phrase = sentence_buffer.strip()
                if phrase:
                    audio_bytes = await tts_service.generate_bytes(phrase)
                    if audio_bytes:
                        try:
                            await websocket.send_bytes(audio_bytes)
                        except:
                            break
                sentence_buffer = ""

        # Flush last piece
        if sentence_buffer.strip() and not state["interrupt_signal"].is_set():
            audio_bytes = await tts_service.generate_bytes(sentence_buffer.strip())
            if audio_bytes:
                await websocket.send_bytes(audio_bytes)

        state["is_speaking"] = False
        print("✅ Turn finished")

    await receive_loop()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)