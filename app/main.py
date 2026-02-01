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
    
    # Shared state for this connection
    state = {
        "is_speaking": False,
        "interrupt_signal": asyncio.Event(),
        "audio_buffer": bytearray()
    }

    async def receive_loop():
        """Continuously listen for user audio and handle barge-in."""
        try:
            while True:
                data = await websocket.receive_bytes()
                audio_chunk = np.frombuffer(data, dtype=np.float32)

                # 1. VAD Check
                if vad_service.is_speech(audio_chunk):
                    # If agent is speaking, this is an interruption
                    if state["is_speaking"] and not state["interrupt_signal"].is_set():
                        print("🛑 BARGE-IN DETECTED: Stopping TTS")
                        state["interrupt_signal"].set() # Signal speaker to stop
                    
                    # Accumulate audio for STT
                    state["audio_buffer"].extend(data)
                else:
                    # Silence detected: if we have enough audio, process it
                    if len(state["audio_buffer"]) > 32000: # ~0.5s of audio min
                        # Copy and clear buffer to process
                        audio_to_process = np.frombuffer(state["audio_buffer"], dtype=np.float32)
                        state["audio_buffer"] = bytearray()
                        
                        # Trigger response in background
                        asyncio.create_task(process_and_respond(audio_to_process))

        except WebSocketDisconnect:
            print("Client disconnected")
        except Exception as e:
            print(f"Error in receive_loop: {e}")

    async def process_and_respond(audio_data):
        """Pipeline: STT -> LLM -> TTS"""
        if state["is_speaking"]: return # Don't process if already processing another turn

        # 2. STT
        transcript = await stt_service.transcribe(audio_data)
        if not transcript or len(transcript.strip()) < 2: return
        
        print(f"User: {transcript}")
        state["is_speaking"] = True
        state["interrupt_signal"].clear()

        # 3. LLM (Stream text)
        llm_generator = llm_service.generate_stream(transcript)
        
        # 4. TTS & Streaming Response
        # We accumulate sentence by sentence to keep TTS natural but low latency
        sentence_buffer = ""
        async for text_chunk in llm_generator:
            if state["interrupt_signal"].is_set():
                break # Stop generating if interrupted
            
            sentence_buffer += text_chunk
            if any(punct in text_chunk for punct in ".!?"):
                # Generate audio for the sentence
                audio_bytes = await tts_service.generate_bytes(sentence_buffer)
                if state["interrupt_signal"].is_set(): break
                
                # Send Audio
                try:
                    await websocket.send_bytes(audio_bytes)
                except: break
                
                sentence_buffer = ""
        
        # Process remaining buffer
        if sentence_buffer and not state["interrupt_signal"].is_set():
            audio_bytes = await tts_service.generate_bytes(sentence_buffer)
            if not state["interrupt_signal"].is_set():
                await websocket.send_bytes(audio_bytes)

        state["is_speaking"] = False
        print("✅ Finished speaking")

    await receive_loop()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)