(function() {
    const canvas = document.getElementById('waveformCanvas');
    if (!canvas) return; 
    
    const ctx = canvas.getContext('2d');
    let isActive = false;
    let animationFrame;
    let vizContext;
    let analyser;
    let dataArray;

    function resizeCanvas() {
        canvas.width = canvas.offsetWidth * window.devicePixelRatio;
        canvas.height = canvas.offsetHeight * window.devicePixelRatio;
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    }
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const waveCount = 4;
    const waves = [];

    for (let i = 0; i < waveCount; i++) {
        waves.push({
            amplitude: 15 + i * 4,
            frequency: 0.02 + i * 0.01,
            phase: i * Math.PI / 4,
            speed: 0.05 + i * 0.02,
            opacity: 1 - (i * 0.2)
        });
    }

    function drawWaveform(time, volumeMultiplier = 1) {
        const width = canvas.offsetWidth;
        const height = canvas.offsetHeight;
        const centerY = height / 2;

        ctx.clearRect(0, 0, width, height);

        waves.forEach((wave, index) => {
            ctx.beginPath();
            if (index === 0) {
                ctx.strokeStyle = `rgba(255, 255, 255, ${wave.opacity})`;
                ctx.lineWidth = 2;
            } else {
                ctx.strokeStyle = `rgba(59, 130, 246, ${wave.opacity * 0.6})`; 
                ctx.lineWidth = 1.5;
            }

            for (let x = 0; x < width; x++) {
                const angle = wave.frequency * x + wave.phase + time * wave.speed;
                const distanceToCenter = Math.abs(x - width/2);
                const taper = Math.max(0, 1 - (distanceToCenter / (width/2.2)));
                
                const y = centerY + Math.sin(angle) * wave.amplitude * volumeMultiplier * taper;
                
                if (x === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.stroke();
        });
    }

    function animate() {
        const time = Date.now() * 0.002;
        let volumeMultiplier = 1;
        
        if (isActive && analyser && dataArray) {
            analyser.getByteTimeDomainData(dataArray);
            let sum = 0;
            for (let i = 0; i < dataArray.length; i++) {
                const v = (dataArray[i] - 128) / 128;
                sum += v * v;
            }
            const rms = Math.sqrt(sum / dataArray.length);

            volumeMultiplier = 1 + Math.pow(rms * 10, 1.6);
        } else {
            volumeMultiplier = 0.2;
        }

        drawWaveform(time, volumeMultiplier);
        animationFrame = requestAnimationFrame(animate);
    }

    animate();

    window.startWaveizer = (stream) => {
        isActive = true;
        try {
            vizContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = vizContext.createAnalyser();
            analyser.fftSize = 256;
            
            const source = vizContext.createMediaStreamSource(stream);
            source.connect(analyser);
            dataArray = new Uint8Array(analyser.frequencyBinCount);
        } catch (err) {
            console.error("Visualizer init error:", err);
        }
    };

    window.stopWaveizer = () => {
        isActive = false;
        if (vizContext) {
            vizContext.close();
            vizContext = null;
        }
    };
})();