# touch_tester.py (Düzeltilmiş IP Hatası)

from flask import Flask, render_template_string
import os
import math 
import socket

app = Flask(__name__)

# --- Otomatik Yerel IP Bulma Fonksiyonu (DÜZELTİLDİ) ---
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
            # HATA BURADAYDI: 1227 -> 127 olarak düzeltildi.
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Dokunmatik Ekran Testi (Otomatik Tema)</title>
    <style>
        /* --- OTOMATİK TEMA DEĞİŞKENLERİ --- */
        :root {
            /* Varsayılan: Aydınlık Tema */
            --c-bg: #f0f2f5;
            --c-text: #333;
            --c-text-secondary: #777;
            --c-content-box-bg: white;
            --c-shadow: 0 10px 40px rgba(0,0,0,.1);
            --c-primary: #667eea;
            --c-accent: #764ba2;
            --c-test-area-bg: #f0f2f5; /* Test alanı arkaplanı (Aydınlık) */
            --c-grid-line: #ccc;      /* Grid çizgileri (Aydınlık) */
        }

        @media (prefers-color-scheme: dark) {
            :root {
                /* Karanlık Tema */
                --c-bg: #121212;
                --c-text: #e0e0e0;
                --c-text-secondary: #aaa;
                --c-content-box-bg: #1e1e1e;
                --c-shadow: 0 10px 40px rgba(0,0,0,.5);
                --c-primary: #818cf8;
                --c-accent: #a78bfa;
                --c-test-area-bg: #333; /* Test alanı arkaplanı (Karanlık) */
                --c-grid-line: #555;      /* Grid çizgileri (Karanlık) */
            }
        }
        /* --- TEMA DEĞİŞKENLERİ SONU --- */

        body, html {
            font-family: 'Segoe UI', sans-serif;
            background: var(--c-bg);
            color: var(--c-text);
            margin: 0; padding: 0; width: 100%; height: 100%; overflow: hidden;
            touch-action: none;
            -webkit-tap-highlight-color: transparent;
            transition: background-color 0.3s, color 0.3s;
        }
        .container {
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            min-height: 100vh; padding: 20px; box-sizing: border-box; text-align: center;
            background: var(--c-bg);
            color: var(--c-text);
        }
        .content-box {
            background: var(--c-content-box-bg);
            border-radius: 20px;
            box-shadow: var(--c-shadow);
            padding: 50px;
            transition: background-color 0.3s;
        }
        h1 { color: var(--c-primary); margin-top: 0; }
        p { font-size: 1.1em; line-height: 1.6; }
        #startTestButton {
            background: linear-gradient(135deg, var(--c-primary), var(--c-accent));
            color: white; border: none; border-radius: 12px;
            font-size: 22px; font-weight: bold; padding: 25px 50px; cursor: pointer; transition: all 0.3s;
            margin-top: 30px; box-shadow: 0 5px 20px rgba(102,126,234,.4);
        }
        #startTestButton:hover { transform: scale(1.05); box-shadow: 0 8px 30px rgba(102,126,234,.6); }
        
        #touchArea {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            background-color: var(--c-test-area-bg);
            display: none; z-index: 100; cursor: crosshair;
        }
        #touchCanvas { display: block; width: 100%; height: 100%; }
        
        .instruction-overlay {
            position: fixed; left: 50%; transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.7); color: #FFF; padding: 15px 25px; border-radius: 10px;
            font-weight: bold; z-index: 101; pointer-events: none;
            border: 2px solid rgba(255, 255, 255, 0.8);
            text-align: center; display: none; white-space: nowrap;
        }
        #fullscreenInstruction { top: 30px; }
        #progressIndicator { top: 30px; }
    </style>
</head>
<body>
    <div class="container" id="mainControls">
        <div class="content-box">
            <h1>👆 Dokunmatik Ekran Testi</h1>
            <p>
                Dokunmatik ekranınızın her noktasının çalışıp çalışmadığını kontrol edin.<br>
                Testi başlattığınızda sayfa tam ekran olacaktır.<br>
                <b>Dokunduğunuz kareler yeşile dönecek.</b> Ekranın %98'ini boyadığınızda test bitecek.
            </p>
            <p style="font-size: 0.9em; color: var(--c-text-secondary);">
                (Manuel tam ekran için klavyenizden <b>F11</b> tuşuna basabilirsiniz.)
            </p>
            <button id="startTestButton">Dokunmatik Testi Başlat</button>
        </div>
    </div>
    
    <div id="touchArea">
        <canvas id="touchCanvas"></canvas>
    </div>

    <div class="instruction-overlay" id="fullscreenInstruction">Lütfen tam ekran moduna geçin...</div>
    <div class="instruction-overlay" id="progressIndicator">%0 Tamamlandı</div>

    <script>
        const mainControls = document.getElementById('mainControls');
        const startTestButton = document.getElementById('startTestButton');
        const touchArea = document.getElementById('touchArea');
        const touchCanvas = document.getElementById('touchCanvas');
        const ctx = touchCanvas.getContext('2d');
        const fullscreenInstruction = document.getElementById('fullscreenInstruction');
        const progressIndicator = document.getElementById('progressIndicator');

        let isTestRunning = false;
        const CELL_SIZE = 20;
        const COMPLETION_THRESHOLD = 0.98;
        
        let gridState = [];
        let numCols, numRows, totalCells, paintedCells;

        function setupCanvasAndGrid() {
            touchCanvas.width = window.innerWidth;
            touchCanvas.height = window.innerHeight;
            
            numCols = Math.ceil(touchCanvas.width / CELL_SIZE);
            numRows = Math.ceil(touchCanvas.height / CELL_SIZE);
            totalCells = numCols * numRows;
            paintedCells = 0;

            gridState = new Array(numRows).fill(null).map(() => new Array(numCols).fill(false));

            drawGridLines();
            updateProgressIndicator();
        }

        function drawGridLines() {
            const gridBgColor = getComputedStyle(document.documentElement).getPropertyValue('--c-test-area-bg').trim();
            const gridLineColor = getComputedStyle(document.documentElement).getPropertyValue('--c-grid-line').trim();
            
            ctx.clearRect(0, 0, touchCanvas.width, touchCanvas.height);
            ctx.fillStyle = gridBgColor;
            ctx.fillRect(0, 0, touchCanvas.width, touchCanvas.height);
            
            ctx.strokeStyle = gridLineColor;
            ctx.lineWidth = 1;

            for (let x = 0; x <= touchCanvas.width; x += CELL_SIZE) {
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, touchCanvas.height); ctx.stroke();
            }
            for (let y = 0; y <= touchCanvas.height; y += CELL_SIZE) {
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(touchCanvas.width, y); ctx.stroke();
            }
        }

        function startTest() {
            if (isTestRunning) return;
            isTestRunning = true;
            mainControls.style.display = 'none';
            fullscreenInstruction.style.display = 'block';

            document.documentElement.requestFullscreen()
                .then(() => {
                    fullscreenInstruction.style.display = 'none';
                    touchArea.style.display = 'block';
                    progressIndicator.style.display = 'block';
                    
                    setupCanvasAndGrid();
                    
                    touchArea.addEventListener('touchstart', handleTouch);
                    touchArea.addEventListener('touchmove', handleTouch);
                })
                .catch((err) => {
                    console.error(`Tam ekran moduna geçilemedi: ${err.message}`);
                    fullscreenInstruction.textContent = 'Hata: Tam ekrana geçilemedi. Test başlatılamıyor.';
                    setTimeout(stopTest, 3000);
                });
        }

        function stopTest(success = false) {
            if (!isTestRunning) return;
            isTestRunning = false;

            if (success) {
                progressIndicator.textContent = "✅ Test Başarılı!";
                ctx.fillStyle = '#00FF00'; // Başarı rengi
                ctx.fillRect(0, 0, touchCanvas.width, touchCanvas.height);
                setTimeout(() => {
                    if (document.fullscreenElement) document.exitFullscreen();
                    resetUI();
                }, 1000);
            } else {
                if (document.fullscreenElement) document.exitFullscreen();
                resetUI();
            }
        }
        
        function resetUI() {
            touchArea.removeEventListener('touchstart', handleTouch);
            touchArea.removeEventListener('touchmove', handleTouch);
            touchArea.style.display = 'none';
            fullscreenInstruction.style.display = 'none';
            progressIndicator.style.display = 'none';
            mainControls.style.display = 'flex';
            fullscreenInstruction.textContent = 'Lütfen tam ekran moduna geçin...';
        }

        function handleTouch(e) {
            e.preventDefault();
            const touches = e.touches;
            let needsUpdate = false;

            ctx.fillStyle = '#00FF00'; // Boyama rengi

            for (let i = 0; i < touches.length; i++) {
                const touch = touches[i];
                const col = Math.floor(touch.clientX / CELL_SIZE);
                const row = Math.floor(touch.clientY / CELL_SIZE);

                if (row >= 0 && row < numRows && col >= 0 && col < numCols && !gridState[row][col]) {
                    gridState[row][col] = true;
                    paintedCells++;
                    needsUpdate = true;
                    ctx.fillRect(col * CELL_SIZE + 1, row * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2);
                }
            }

            if (needsUpdate) {
                updateProgressIndicator();
                const completionRatio = paintedCells / totalCells;
                if (completionRatio >= COMPLETION_THRESHOLD) {
                    stopTest(true);
                }
            }
        }
        
        function updateProgressIndicator() {
            const percentage = totalCells > 0 ? Math.floor((paintedCells / totalCells) * 100) : 0;
            progressIndicator.textContent = `%${percentage} Tamamlandı`;
        }

        startTestButton.onclick = startTest;

        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement && isTestRunning) {
                stopTest(false);
            }
            if (isTestRunning) {
                setTimeout(setupCanvasAndGrid, 100);
            }
        });
        
        window.addEventListener('resize', () => {
            if (isTestRunning && document.fullscreenElement) {
                setupCanvasAndGrid();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

if __name__ == '__main__':
    local_ip = get_local_ip()
    port = 5009
    print("="*60)
    print("👆 Dokunmatik Ekran Testi (Otomatik Temalı) HTTP üzerinden başlatılıyor...")
    print(f"   -> Bilgisayardan erişim: http://localhost:{port}")
    if local_ip != "127.0.0.1":
        print(f"   -> Ağdaki diğer cihazlardan erişim: http://{local_ip}:{port}")
    print("Tema, işletim sisteminizin aydınlık/karanlık moduna göre otomatik ayarlanır.")
    print("="*60)
    
    app.run(debug=True, host='0.0.0.0', port=port)