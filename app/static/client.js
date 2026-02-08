(function() {
    const startBtn = document.getElementById('startBtn');
    const status = document.getElementById('status');
    const voiceCard = document.querySelector('.voice-card');
    let ws, audioContext, workletNode, inputStream;
    let audioQueue = [];
    let isPlaying = false;
    let currentSource = null;
    let playbackTime = 0;

    startBtn.onclick = async () => {
        updateStatus('connecting');
        
        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 22050 });
        await audioContext.resume();

        ws = new WebSocket(`ws://${location.host}/ws/voice`);
        ws.binaryType = 'arraybuffer';

        ws.onopen = async () => {
            updateStatus('connected');
            startBtn.disabled = true;
            startBtn.style.transform = "scale(0.95)";
            
            await initMicrophone();
            playbackTime = audioContext.currentTime;
        };

        ws.onmessage = (event) => {
            if (typeof event.data === 'string') {
                try {
                    const msg = JSON.parse(event.data);
                    if (msg.type === "interrupt") stopPlayback();
                } catch (e) {}
            } else {
                enqueuePCM(event.data);
            }
        };

        ws.onclose = () => {
            updateStatus('disconnected');
            startBtn.disabled = false;
            startBtn.style.transform = "scale(1)";
            stopAudio();
        };
    };

    async function initMicrophone() {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 16000,
                echoCancellation: true,
                noiseSuppression: true
            }
        });
        inputStream = stream;

        if (window.startWaveizer) {
            window.startWaveizer(stream);
        }

        await audioContext.audioWorklet.addModule('/static/voice-processor.js');

        const source = audioContext.createMediaStreamSource(stream);
        workletNode = new AudioWorkletNode(audioContext, 'voice-processor');

        workletNode.port.onmessage = (e) => {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(e.data.buffer);
            }
        };

        source.connect(workletNode);
        workletNode.connect(audioContext.destination);
    }

    function enqueuePCM(arrayBuffer) {
        const int16 = new Int16Array(arrayBuffer);
        const float32 = new Float32Array(int16.length);
        for (let i = 0; i < int16.length; i++) {
            float32[i] = int16[i] / 32768.0;
        }
        audioQueue.push(float32);
        if (!isPlaying) playNextChunk();
    }

    function playNextChunk() {
        if (audioQueue.length === 0) {
            isPlaying = false;
            return;
        }
        isPlaying = true;
        const pcmData = audioQueue.shift();

        const buffer = audioContext.createBuffer(1, pcmData.length, audioContext.sampleRate);
        buffer.getChannelData(0).set(pcmData);

        const source = audioContext.createBufferSource();
        source.buffer = buffer;
        source.connect(audioContext.destination);

        currentSource = source;
        source.onended = () => {
            currentSource = null;
            playNextChunk();
        };

        if (playbackTime < audioContext.currentTime) playbackTime = audioContext.currentTime;
        source.start(playbackTime);
        playbackTime += buffer.duration;
    }

    function stopPlayback() {
        audioQueue = [];
        if (currentSource) {
            try { currentSource.stop(); } catch (e) {}
            currentSource = null;
        }
        playbackTime = audioContext.currentTime;
        isPlaying = false;
    }

    function stopAudio() {
        stopPlayback();
        
        if (window.stopWaveizer) {
            window.stopWaveizer();
        }

        if (workletNode) workletNode.disconnect();
        if (inputStream) inputStream.getTracks().forEach(t => t.stop());
    }

    function updateStatus(state) {
        status.classList.add('visible');
        voiceCard.classList.remove('connected', 'disconnected');
        
        if (state === 'connecting') {
            status.innerHTML = '<span class="status-dot" style="color: yellow">●</span> Connecting...';
        } else if (state === 'connected') {
            voiceCard.classList.add('connected');
            status.innerHTML = '<span class="status-dot" style="color: #4ade80">●</span> Online - Speak now';
        } else if (state === 'disconnected') {
            voiceCard.classList.add('disconnected');
            status.innerHTML = '<span class="status-dot" style="color: #ef4444">●</span> Disconnected';
        }
    }
})();