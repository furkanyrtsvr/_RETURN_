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
    <title>Fare (Mouse) Testi</title>
    <style>
        /* --- OTOMATİK TEMA DEĞİŞKENLERİ --- */
        :root {
            /* Varsayılan: Aydınlık Tema */
            --c-bg: #f0f2f5;
            --c-text: #333;
            --c-text-light: #666;
            --c-container-bg: white;
            --c-shadow: 0 10px 40px rgba(0,0,0,.1);
            --c-primary: #667eea;
            --c-secondary-bg: #f8f9fa;
            --c-mouse-fill: #fff;
            --c-mouse-stroke: #000;
            --c-mouse-text: #444;
            --c-active: #f59e0b;
            --c-active-text: #fff;
            --c-button-hz-bg: #667eea;
            --c-button-cps-bg: #059669;
            --c-button-stop-bg: #ef4444;
            --c-button-text: white;
            --c-chart-grid: #e5e7eb;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                /* Karanlık Tema */
                --c-bg: #121212;
                --c-text: #e0e0e0;
                --c-text-light: #aaa;
                --c-container-bg: #1e1e1e;
                --c-shadow: 0 10px 40px rgba(0,0,0,.5);
                --c-primary: #818cf8;
                --c-secondary-bg: #2c2c31;
                --c-mouse-fill: #2c2c31;
                --c-mouse-stroke: #555;
                --c-mouse-text: #bbb;
                --c-chart-grid: #444;
            }
        }
        /* --- TEMA DEĞİŞKENLERİ SONU --- */
        
        body {
            font-family: 'Segoe UI', sans-serif;
            background: var(--c-bg);
            color: var(--c-text);
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            user-select: none;
            transition: background-color 0.3s, color 0.3s;
        }
        .container {
            background: var(--c-container-bg);
            border-radius: 20px;
            box-shadow: var(--c-shadow);
            padding: 40px 60px;
            text-align: center;
            transition: background-color 0.3s;
        }
        h1 { 
            color: var(--c-primary); 
            margin-top: 0;
        }
        p { 
            font-size: 1.1em; 
            margin-bottom: 30px;
            color: var(--c-text-light);
        }
        .mouse-container {
            position: relative;
            width: 300px;
            height: 400px;
            margin: 40px auto;
            transform: scale(1.1);
        }
        .mouse-svg {
            width: 100%;
            height: 100%;
            filter: drop-shadow(0px 10px 20px rgba(0,0,0,0.2));
        }
        .st0 {
            fill: var(--c-mouse-fill);
            stroke: var(--c-mouse-stroke);
            stroke-miterlimit: 10;
            stroke-width: 20px;
            transition: fill 0.15s ease, stroke 0.15s ease;
            cursor: pointer;
        }
        .st0.active {
            fill: var(--c-active);
            stroke: var(--c-active);
        }
        .button-text {
            font-family: 'Segoe UI', sans-serif;
            font-size: 180px;
            font-weight: bold;
            fill: var(--c-mouse-text);
            text-anchor: middle;
            pointer-events: none;
            opacity: 0.8;
            transition: fill 0.15s ease, opacity 0.15s ease;
        }
        .button-text.active {
            fill: var(--c-active-text);
            opacity: 1;
        }
        .side-text {
            font-size: 100px;
        }
        .test-section {
            margin-top: 20px;
            padding: 20px;
            background: var(--c-secondary-bg);
            border-radius: 10px;
            transition: background-color 0.3s;
        }
        .test-button {
            color: var(--c-button-text);
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            font-weight: bold;
            transition: background-color 0.3s;
        }
        #hzTestBtn { background: var(--c-button-hz-bg); }
        #cpsTestBtn { background: var(--c-button-cps-bg); width: 100%;}
        .test-result {
            margin-top: 20px;
            font-size: 18px;
            font-weight: bold;
            color: var(--c-text);
            min-height: 60px;
        }
        .test-result .info {
            color: var(--c-text-light);
            font-size: 14px;
            margin-top: 10px;
        }
        #hzChart {
            margin-top: 20px;
            background: var(--c-container-bg);
            border-radius: 8px;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖱️ Fare (Mouse) Testi</h1>
        <p>Farenizin tuşlarına basın veya tekerleği çevirin.<br>Algılanan tuş turuncu renkte yanacaktır.</p>

        <div class="mouse-container">
            <svg id="mouseSvg" class="mouse-svg" viewBox="0 0 4000 4000">
                <rect class="st0" x="1065.22" y="500" width="1869.57" height="3000" rx="934.78" ry="934.78"/>
                <line class="st0" x1="1065.22" y1="1659.42" x2="2934.78" y2="1659.42"/>
                <line class="st0" x1="2000" y1="500" x2="2000" y2="1659.42"/>
                <rect class="st0" id="scrollWheel" x="1862.77" y="774.46" width="274.46" height="668.48" rx="137.23" ry="137.23"/>
                <text x="2000" y="980" class="button-text" id="scrollTextUp">▲</text>
                <text x="2000" y="1320" class="button-text" id="scrollTextDown">▼</text>
                <path class="st0" id="svgBtnFwd" d="M1065.22,1996.06v116.18c0,16.38,13.28,29.65,29.65,29.65h31.64c16.38,0,29.65-13.28,29.65-29.65v-183.22c0-16.38-13.28-29.65-29.65-29.65h-31.64c-16.38,0-29.65,13.28-29.65,29.65v67.04Z"/>
                <text x="920" y="2070" class="button-text side-text">↑</text>
                <path class="st0" id="svgBtnBack" d="M1065.22,2294.73v116.18c0,16.38,13.28,29.65,29.65,29.65h31.64c16.38,0,29.65-13.28,29.65-29.65v-183.22c0-16.38-13.28-29.65-29.65-29.65h-31.64c-16.38,0-29.65,13.28-29.65,29.65v67.04Z"/>
                <text x="920" y="2370" class="button-text side-text">↓</text>
                <path id="svgBtnLeft" class="st0" style="fill: transparent; stroke: none;" d="M1065.22,500v1159.42h934.78V500h-434.78c-245.97,0-500,189.24-500,434.78Z"/>
                <text x="1532" y="1100" class="button-text" id="textLeft">L</text>
                <path id="svgBtnRight" class="st0" style="fill: transparent; stroke: none;" d="M2000,500h500c235.97,0,434.78,189.24,434.78,434.78v724.64h-934.78V500Z"/>
                <text x="2467" y="1100" class="button-text" id="textRight">R</text>
            </svg>
        </div>

        <div class="test-section">
            <button id="hzTestBtn" class="test-button">Hz Testi Başlat</button>
            <div id="hzResult" class="test-result">
                <div class="info">Fareyi hareket ettirin, Hz değeri anlık olarak ölçülecek!</div>
            </div>
            <canvas id="hzChart" width="600" height="200"></canvas>
        </div>

        <div class="test-section">
            <button id="cpsTestBtn" class="test-button">Click Testi Başlat (30sn)</button>
            <div id="cpsResult" class="test-result">
                <div class="info">Başlat'a tıklayın ve 30 saniye boyunca olabildiğince hızlı tıklayın!</div>
            </div>
        </div>
    </div>

    <script>
        const svgBtnLeft = document.getElementById('svgBtnLeft');
        const svgBtnRight = document.getElementById('svgBtnRight');
        const scrollWheel = document.getElementById('scrollWheel');
        const svgBtnFwd = document.getElementById('svgBtnFwd');
        const svgBtnBack = document.getElementById('svgBtnBack');
        const textLeft = document.getElementById('textLeft');
        const textRight = document.getElementById('textRight');
        const scrollTextUp = document.getElementById('scrollTextUp');
        const scrollTextDown = document.getElementById('scrollTextDown');
        const textFwd = svgBtnFwd.nextElementSibling;
        const textBack = svgBtnBack.nextElementSibling;

        const buttons = {
            0: { el: svgBtnLeft, text: textLeft },
            1: { el: scrollWheel, text: null },
            2: { el: svgBtnRight, text: textRight },
            3: { el: svgBtnBack, text: textBack },
            4: { el: svgBtnFwd, text: textFwd }
        };

        document.addEventListener('mousedown', (e) => {
            const button = buttons[e.button];
            if (button) {
                button.el.classList.add('active');
                if (button.text) button.text.classList.add('active');
            }
            if (hzTestActive) { mouseEvents.push(e.timeStamp); }
            if (cpsTestActive && e.button === 0 && e.target !== cpsTestBtn) {
                incrementClick();
            }
        });

        document.addEventListener('mouseup', (e) => {
            const button = buttons[e.button];
            if (button) {
                setTimeout(() => {
                    button.el.classList.remove('active');
                    if (button.text) button.text.classList.remove('active');
                }, 150);
            }
            if (hzTestActive) { mouseEvents.push(e.timeStamp); }
        });

        document.addEventListener('wheel', (e) => {
            scrollWheel.classList.add('active');
            const targetText = e.deltaY < 0 ? scrollTextUp : scrollTextDown;
            targetText.classList.add('active');
            setTimeout(() => {
                targetText.classList.remove('active');
                scrollWheel.classList.remove('active');
            }, 150);
            e.preventDefault();
            if (hzTestActive) { mouseEvents.push(e.timeStamp); }
        });

        document.addEventListener('contextmenu', e => e.preventDefault());

        let hzTestActive = false;
        let mouseEvents = [];
        let lastUpdateTime = 0;
        let lastHistoryPushTime = 0;
        let hzHistory = [];
        const maxHistoryLength = 30;
        let smoothedHz = 0;
        const SMOOTH_ALPHA = 0.25;
        const hzTestBtn = document.getElementById('hzTestBtn');
        const hzResult = document.getElementById('hzResult');
        const hzChart = document.getElementById('hzChart');
        const ctx = hzChart.getContext('2d');

        function drawChart() {
            ctx.clearRect(0, 0, hzChart.width, hzChart.height);
            if (hzHistory.length === 0) return;
            const maxHz = Math.max(...hzHistory, 1000);
            const padding = 40;
            const chartWidth = hzChart.width - padding * 2;
            const chartHeight = hzChart.height - padding * 2;
            const pointSpacing = chartWidth / (maxHistoryLength - 1);
            
            const gridColor = getComputedStyle(document.documentElement).getPropertyValue('--c-chart-grid').trim();
            const textColor = getComputedStyle(document.documentElement).getPropertyValue('--c-text-light').trim();
            const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--c-primary').trim();

            ctx.strokeStyle = gridColor;
            ctx.lineWidth = 1;
            for (let i = 0; i <= 5; i++) {
                const y = padding + (chartHeight / 5) * i;
                ctx.beginPath();
                ctx.moveTo(padding, y);
                ctx.lineTo(hzChart.width - padding, y);
                ctx.stroke();
                ctx.fillStyle = textColor;
                ctx.font = '12px Segoe UI';
                ctx.textAlign = 'right';
                ctx.fillText(Math.round(maxHz - (maxHz / 5) * i) + ' Hz', padding - 5, y + 4);
            }

            ctx.strokeStyle = primaryColor;
            ctx.lineWidth = 3;
            ctx.beginPath();
            hzHistory.forEach((hz, i) => {
                const x = padding + i * pointSpacing;
                const y = padding + chartHeight - (hz / maxHz) * chartHeight;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            });
            ctx.stroke();

            ctx.fillStyle = primaryColor;
            hzHistory.forEach((hz, i) => {
                const x = padding + i * pointSpacing;
                const y = padding + chartHeight - (hz / maxHz) * chartHeight;
                ctx.beginPath();
                ctx.arc(x, y, 4, 0, Math.PI * 2);
                ctx.fill();
            });
        }

        function calculateHz() {
            const now = performance.now();
            mouseEvents = mouseEvents.filter(t => now - t < 1000);
            if (mouseEvents.length < 10) return 0;
            const timeSpan = mouseEvents[mouseEvents.length - 1] - mouseEvents[0];
            if (timeSpan < 100) return 0;
            const hz = Math.round((mouseEvents.length - 1) / timeSpan * 1000);
            return Math.min(Math.max(hz, 0), 4000);
        }

        function updateDisplay() {
            if (!hzTestActive) return;
            const now = performance.now();
            if (now - lastUpdateTime >= 25) {
                const hz = calculateHz();
                smoothedHz = Math.round(SMOOTH_ALPHA * hz + (1 - SMOOTH_ALPHA) * smoothedHz);
                const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--c-primary').trim();
                hzResult.innerHTML = `<div style="color: ${primaryColor}; font-size: 32px;">⚡ ${smoothedHz} Hz</div>`;

                if (now - lastHistoryPushTime >= 100) {
                    hzHistory.push(smoothedHz);
                    if (hzHistory.length > maxHistoryLength) hzHistory.shift();
                    drawChart();
                    lastHistoryPushTime = now;
                }
                lastUpdateTime = now;
            }
            requestAnimationFrame(updateDisplay);
        }

        hzTestBtn.addEventListener('click', () => {
            hzTestActive = !hzTestActive;
            const stopColor = getComputedStyle(document.documentElement).getPropertyValue('--c-button-stop-bg').trim();
            const startColor = getComputedStyle(document.documentElement).getPropertyValue('--c-button-hz-bg').trim();
            const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--c-primary').trim();
            
            if (hzTestActive) {
                hzTestBtn.textContent = 'Hz Testi Durdur';
                hzTestBtn.style.backgroundColor = stopColor;
                hzChart.style.display = 'block';
                hzHistory = [];
                mouseEvents = [];
                smoothedHz = 0;
                updateDisplay();
            } else {
                hzTestBtn.textContent = 'Hz Testi Başlat';
                hzTestBtn.style.backgroundColor = startColor;
                hzChart.style.display = 'none';
                const avg = hzHistory.length ? Math.round(hzHistory.reduce((a, b) => a + b, 0) / hzHistory.length) : 0;
                const max = hzHistory.length ? Math.max(...hzHistory) : 0;
                const min = hzHistory.length ? Math.min(...hzHistory) : 0;
                hzResult.innerHTML = `
                    <div style="color: ${primaryColor}; font-size: 24px;">📊 Test Tamamlandı</div>
                    <div class="info">Ortalama: ${avg} Hz | Max: ${max} Hz | Min: ${min} Hz</div>`;
            }
        });

        document.addEventListener('pointermove', e => {
            if (hzTestActive) {
                if (typeof e.getCoalescedEvents === 'function') {
                    e.getCoalescedEvents().forEach(event => mouseEvents.push(event.timeStamp));
                } else {
                    mouseEvents.push(e.timeStamp);
                }
            }
        });

        const cpsTestBtn = document.getElementById('cpsTestBtn');
        const cpsResult = document.getElementById('cpsResult');
        let cpsTestActive = false;
        let clickCount = 0;
        let cpsTimerInterval;
        let timeRemaining = 30;

        function startCpsTest() {
            if (cpsTestActive) return;
            cpsTestActive = true;
            clickCount = 0;
            timeRemaining = 30;
            cpsTestBtn.textContent = `Tıkla! (Süre: ${timeRemaining}s)`;
            cpsTestBtn.style.backgroundColor = getComputedStyle(document.documentElement).getPropertyValue('--c-active').trim();
            cpsResult.innerHTML = `<div style="font-size: 32px;">Tıklama: 0</div><div class="info">Test başladı!</div>`;

            cpsTimerInterval = setInterval(() => {
                timeRemaining--;
                if (cpsTestActive) {
                    cpsTestBtn.textContent = `Tıkla! (Süre: ${timeRemaining}s)`;
                }
                if (timeRemaining <= 0) {
                    clearInterval(cpsTimerInterval);
                    cpsTestActive = false;
                    const cps = (clickCount / 30).toFixed(2);
                    const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--c-primary').trim();
                    cpsResult.innerHTML = `
                        <div style="color: ${primaryColor}; font-size: 24px;">📊 Test Tamamlandı</div>
                        <div style="font-size: 32px; margin-top: 8px;">${cps} CPS</div>
                        <div class="info">(30 saniyede ${clickCount} tıklama)</div>`;
                    cpsTestBtn.textContent = 'Click Testi Başlat (30sn)';
                    cpsTestBtn.style.backgroundColor = getComputedStyle(document.documentElement).getPropertyValue('--c-button-cps-bg').trim();
                }
            }, 1000);
        }

        function incrementClick() {
            if (!cpsTestActive) return;
            clickCount++;
            cpsResult.innerHTML = `<div style="font-size: 32px;">Tıklama: ${clickCount}</div><div class="info">Devam!</div>`;
        }

        cpsTestBtn.addEventListener('click', () => {
            if (!cpsTestActive) {
                startCpsTest();
                incrementClick();
            } else {
                incrementClick();
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
    port = 5006
    print("="*60)
    print("🖱️ Fare Testi (Otomatik Temalı) başlatılıyor...")
    print(f"   -> Bilgisayardan erişim: http://localhost:{port}")
    if local_ip != "127.0.0.1":
        print(f"   -> Ağdaki diğer cihazlardan erişim: http://{local_ip}:{port}")
    print("Tema, işletim sisteminizin aydınlık/karanlık moduna göre ayarlanır.")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=port)