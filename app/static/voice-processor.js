// app/static/voice-processor.js
class VoiceProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
    }

    process(inputs) {
        // inputs[0][0] = first input, first (mono) channel
        const input = inputs[0][0];
        if (input && input.length > 0) {
            // Send a copy to the main thread (safe practice)
            this.port.postMessage(new Float32Array(input));
        }
        return true; // keep the processor alive
    }
}

registerProcessor('voice-processor', VoiceProcessor);