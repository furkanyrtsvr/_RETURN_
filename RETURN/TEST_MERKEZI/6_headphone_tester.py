from flask import Flask, render_template_string
import os
import socket

app = Flask(__name__)

# --- Otomatik Yerel IP Bulma Fonksiyonu ---
def get_local_ip():
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        return ip_address
    except socket.error:
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return "127.0.0.1"
    finally:
        if s:
            s.close()
# --- IP Bulma Fonksiyonu Sonu ---

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Kulaklık & Mikrofon Testi</title>
    <style>
        /* --- OTOMATİK TEMA DEĞİŞKENLERİ --- */
        :root {
            /* Varsayılan: Aydınlık Tema */
            --c-bg: #f0f2f5;
            --c-text: #333;
            --c-container-bg: white;
            --c-shadow: 0 10px 40px rgba(0,0,0,.1);
            --c-primary: #667eea;
            --c-accent: #764ba2;
            --c-divider: #eee;
            --c-secondary-bg: #f8f9ff;
            --c-mic-viz-bg: #2c2c3e;
            --c-btn-disabled-bg: #ccc;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                /* Karanlık Tema */
                --c-bg: #121212;
                --c-text: #e0e0e0;
                --c-container-bg: #1e1e1e;
                --c-shadow: 0 10px 40px rgba(0,0,0,.5);
                --c-primary: #818cf8;
                --c-accent: #a78bfa;
                --c-divider: #444;
                --c-secondary-bg: #2c2c31;
                --c-mic-viz-bg: #1e1e1e; /* Konteynır ile aynı renk daha iyi durur */
                --c-btn-disabled-bg: #555;
            }
        }
        /* --- TEMA DEĞİŞKENLERİ SONU --- */

        body {
            font-family: 'Segoe UI', sans-serif;
            background: var(--c-bg);
            color: var(--c-text);
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
            transition: background-color 0.3s, color 0.3s;
        }
        .container {
            background: var(--c-container-bg);
            border-radius: 20px;
            box-shadow: var(--c-shadow);
            width: 100%;
            max-width: 600px;
            overflow: hidden;
            transition: background-color 0.3s;
        }
        h1 {
            text-align: center;
            color: var(--c-primary);
            padding: 30px 20px 0 20px;
            margin: 0;
            transition: color 0.3s;
        }
        .test-section {
            padding: 30px;
            border-bottom: 1px solid var(--c-divider);
            transition: border-color 0.3s;
        }
        .test-section:last-child {
            border-bottom: none;
        }
        h2 {
            margin-top: 0;
            border-bottom: 2px solid var(--c-primary);
            padding-bottom: 10px;
            color: var(--c-text);
            transition: border-color 0.3s, color 0.3s;
        }
        
        #micVisualizer {
            width: 100%;
            height: 100px;
            background: var(--c-mic-viz-bg);
            border-radius: 10px;
            border: 2px solid var(--c-primary);
            margin-bottom: 15px;
            transition: background-color 0.3s, border-color 0.3s;
        }
        #micStatus {
            text-align: center;
            margin-top: 15px;
            font-weight: bold;
            color: var(--c-accent);
            transition: color 0.3s;
        }
        
        .playback-control {
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 15px 0;
            padding: 10px;
            background: var(--c-secondary-bg);
            border-radius: 8px;
            transition: background-color 0.3s;
        }
        .playback-control input {
            margin-right: 10px;
            width: 18px;
            height: 18px;
        }
        .playback-control label {
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            user-select: none;
            color: var(--c-text);
        }
        
        .controls {
            display: flex;
            justify-content: space-around;
            align-items: center;
            margin-top: 20px;
        }
        button {
            background: linear-gradient(135deg, var(--c-primary), var(--c-accent));
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
            padding: 15px 30px;
            cursor: pointer;
            transition: all 0.3s;
        }
        button:hover {
            transform: scale(1.05);
            box-shadow: 0 5px 15px rgba(102,126,234,.5);
        }
        button:active {
            transform: scale(0.98);
        }
        button:disabled {
            background: var(--c-btn-disabled-bg);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .volume-control {
            display: flex;
            align-items: center;
            margin-top: 25px;
        }
        .volume-control span {
            font-size: 24px;
            margin: 0 10px;
        }
        #volumeSlider {
            width: 100%;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎙️ Kulaklık & Mikrofon Testi 🎧</h1>
        
        <div class="test-section">
            <h2>1. Kademe: Mikrofon Testi</h2>
            <p>Aşağıdaki butona tıklayın ve tarayıcının mikrofonunuza erişmesine izin verin. Konuştuğunuzda aşağıdaki görselleştiricide hareket görmelisiniz.</p>
            <button id="startMicTest" style="width: 100%; margin-bottom: 15px;">Mikrofon Testini Başlat</button>
            <canvas id="micVisualizer" width="540" height="100"></canvas>
            
            <div class="playback-control">
                <input type="checkbox" id="micPlaybackCheckbox" disabled>
                <label for="micPlaybackCheckbox">Kendi sesimi 0.3sn gecikmeyle duy</label>
            </div>
            
            <p id="micStatus">Mikrofon bekleniyor...</p>
        </div>
        
        <div class="test-section">
            <h2>2. Kademe: Kulaklık (Stereo) Testi</h2>
            <p>Kulaklığınızı takın. Aşağıdaki butonlara basarak sol ve sağ kanalları ayrı ayrı test edebilirsiniz. Test sesinin yüksekliğini alttaki çubuktan ayarlayın.</p>
            
            <div class="controls">
                <button id="playLeft">Sadece SOL Kanal  L</button>
                <button id="playRight">R Sadece SAĞ Kanal</button>
            </div>
            
            <div class="volume-control">
                <span>🔈</span>
                <input type="range" id="volumeSlider" min="0" max="1" step="0.01" value="0.5">
                <span>🔊</span>
            </div>
        </div>
    </div>

    <script>
        const startMicTestBtn = document.getElementById('startMicTest');
        const micStatus = document.getElementById('micStatus');
        const canvas = document.getElementById('micVisualizer');
        const canvasCtx = canvas.getContext('2d');
        const micPlaybackCheckbox = document.getElementById('micPlaybackCheckbox');
        
        let audioContext;
        let analyser;
        let dataArray;
        let bufferLength;
        let drawVisual;
        let sidetoneGain;

        startMicTestBtn.onclick = async () => {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                micStatus.textContent = "✅ Mikrofon algılandı! Görselleştirici aktif.";
                startMicTestBtn.disabled = true;
                micPlaybackCheckbox.disabled = false;

                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const source = audioContext.createMediaStreamSource(stream);

                analyser = audioContext.createAnalyser();
                source.connect(analyser);

                const delayNode = audioContext.createDelay(1.0);
                delayNode.delayTime.value = 0.3;

                sidetoneGain = audioContext.createGain();
                sidetoneGain.gain.value = 0;

                source.connect(delayNode).connect(sidetoneGain).connect(audioContext.destination);

                analyser.fftSize = 2048;
                bufferLength = analyser.frequencyBinCount;
                dataArray = new Uint8Array(bufferLength);
                draw();

            } catch (err) {
                micStatus.textContent = "❌ Hata: Mikofona erişilemedi. " + err.message;
            }
        };

        micPlaybackCheckbox.onchange = () => {
            if (!audioContext) return;
            const targetGain = micPlaybackCheckbox.checked ? 1.0 : 0.0;
            sidetoneGain.gain.linearRampToValueAtTime(targetGain, audioContext.currentTime + 0.01);
            micStatus.textContent = `✅ Mikrofon algılandı! (Geri-dinleme ${micPlaybackCheckbox.checked ? 'AÇIK' : 'KAPALI'})`;
        };

        function draw() {
            drawVisual = requestAnimationFrame(draw);
            analyser.getByteTimeDomainData(dataArray);

            const vizBgColor = getComputedStyle(document.documentElement).getPropertyValue('--c-mic-viz-bg').trim();
            const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--c-primary').trim();

            canvasCtx.fillStyle = vizBgColor;
            canvasCtx.fillRect(0, 0, canvas.width, canvas.height);
            canvasCtx.lineWidth = 3;
            canvasCtx.strokeStyle = primaryColor;
            canvasCtx.beginPath();

            const sliceWidth = canvas.width * 1.0 / bufferLength;
            let x = 0;

            for (let i = 0; i < bufferLength; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * canvas.height / 2;
                if (i === 0) {
                    canvasCtx.moveTo(x, y);
                } else {
                    canvasCtx.lineTo(x, y);
                }
                x += sliceWidth;
            }
            canvasCtx.lineTo(canvas.width, canvas.height / 2);
            canvasCtx.stroke();
        }

        const playLeftBtn = document.getElementById('playLeft');
        const playRightBtn = document.getElementById('playRight');
        const volumeSlider = document.getElementById('volumeSlider');

        playLeftBtn.onclick = () => playStereoTest('left');
        playRightBtn.onclick = () => playStereoTest('right');

        function playStereoTest(channel) {
            const stereoContext = new (window.AudioContext || window.webkitAudioContext)();
            const oscillator = stereoContext.createOscillator();
            oscillator.type = 'sine';
            oscillator.frequency.setValueAtTime(440, stereoContext.currentTime);

            const panner = stereoContext.createStereoPanner();
            panner.pan.setValueAtTime(channel === 'left' ? -1 : 1, stereoContext.currentTime);

            const gainNode = stereoContext.createGain();
            gainNode.gain.setValueAtTime(volumeSlider.value, stereoContext.currentTime);

            oscillator.connect(panner).connect(gainNode).connect(stereoContext.destination);
            oscillator.start();
            oscillator.stop(stereoContext.currentTime + 1);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

if __name__ == '__main__':
    local_ip = get_local_ip()
    port = 5006
    print("="*60)
    print("🎙️ Kulaklık & Mikrofon Testi (Otomatik Temalı) başlatılıyor...")
    print(f"   -> Bilgisayardan erişim: http://localhost:{port}")
    if local_ip != "127.0.0.1":
        print(f"   -> Ağdaki diğer cihazlardan erişim: http://{local_ip}:{port}")
    print("UYARI: Güvenli olmayan (http) bağlantı nedeniyle mikrofon testi")
    print("         sadece Firefox gibi tarayıcılarda çalışabilir.")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=port)