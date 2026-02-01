// app/static/client.js

class VoiceGateway {
  constructor() {
    this.ws = new WebSocket(`wss://${location.host}/ws/voice`);
    this.audioContext = new AudioContext({ sampleRate: 16000 });
    this.startCapture();
  }

  async startCapture() {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: { sampleRate: 16000, channelCount: 1, echoCancellation: true }
    });
    
    const processor = this.audioContext.createScriptProcessor(4096, 1, 1);
    const source = this.audioContext.createMediaStreamSource(stream);
    
    processor.onaudioprocess = (e) => {
      const input = e.inputBuffer.getChannelData(0);
      this.ws.send(input);  // Full-duplex: Send while listening
    };
    
    source.connect(processor);
    processor.connect(this.audioContext.destination);
    
    // Play bot responses
    this.ws.binaryType = 'arraybuffer';
    this.ws.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        const audio = this.audioContext.createBuffer(1, event.data.byteLength / 4, 16000);
        const channel = audio.getChannelData(0);
        const input = new Float32Array(event.data);
        channel.set(input);
        
        const source = this.audioContext.createBufferSource();
        source.buffer = audio;
        source.connect(this.audioContext.destination);
        source.start();
      }
    };
  }
}

new VoiceGateway();  // Auto-start
