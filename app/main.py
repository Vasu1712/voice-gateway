# app/main.py
import multiprocessing
import warnings

multiprocessing.set_start_method('fork', force=True)
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message="resource_tracker: There appear to be"
)
import asyncio
import numpy as np
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.services import vad_service, stt_service, llm_service, tts_service, graph_rag_service

app = FastAPI(title="Full-Duplex Voice Agent")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

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
        "audio_buffer": bytearray(),
        "speech_counter": 0
    }

    async def receive_loop():
        """Continuously listen for user audio + detect barge-in"""
        try:
            while True:
                data = await websocket.receive_bytes()
                audio_chunk = np.frombuffer(data, dtype=np.float32)

                if vad_service.is_speech(audio_chunk, threshold=0.005):
                    state["speech_counter"] += 1

                    # Barge-in: require ~5 consecutive speech chunks (~40 ms)
                    if (state["is_speaking"] 
                        and state["speech_counter"] > 5 
                        and not state["interrupt_signal"].is_set()):
                        print("🛑 BARGE-IN DETECTED")
                        state["interrupt_signal"].set()
                        try:
                            await websocket.send_json({"type": "interrupt"})
                        except:
                            pass

                    state["audio_buffer"].extend(data)
                else:
                    state["speech_counter"] = 0
                    if len(state["audio_buffer"]) > 32000:
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
        state["speech_counter"] = 0

        llm_generator = graph_rag_service.generate_stream(transcript)
        sentence_buffer = ""

        async for text_chunk in llm_generator:
            if state["interrupt_signal"].is_set():
                break

            sentence_buffer += text_chunk

            if any(p in text_chunk for p in ".!?") or len(sentence_buffer) > 50:
                phrase = sentence_buffer.strip()
                if phrase:
                    async for pcm_chunk in tts_service.generate_stream(phrase):
                        if state["interrupt_signal"].is_set():
                            break
                        try:
                            await websocket.send_bytes(pcm_chunk)
                        except:
                            break
                sentence_buffer = ""

        # Flush last piece
        if sentence_buffer.strip() and not state["interrupt_signal"].is_set():
            async for pcm_chunk in tts_service.generate_stream(sentence_buffer.strip()):
                if state["interrupt_signal"].is_set():
                    break
                try:
                    await websocket.send_bytes(pcm_chunk)
                except:
                    break

        state["is_speaking"] = False
        print("✅ Turn finished")

    await receive_loop()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)