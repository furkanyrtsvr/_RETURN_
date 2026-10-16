# dead_pixel_tester.py (Otomatik Temalı)

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
    <title>Ölü Piksel Testi</title>
    <style>
        /* --- OTOMATİK TEMA DEĞİŞKENLERİ --- */
        :root {
            /* Varsayılan: Aydınlık Tema */
            --c-bg: #f0f2f5;
            --c-text: #333;
            --c-text-secondary: #777;
            --c-container-bg: white;
            --c-shadow: 0 10px 40px rgba(0,0,0,.1);
            --c-primary: #667eea;
            --c-accent: #764ba2;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                /* Karanlık Tema */
                --c-bg: #121212;
                --c-text: #e0e0e0;
                --c-text-secondary: #aaa;
                --c-container-bg: #1e1e1e;
                --c-shadow: 0 10px 40px rgba(0,0,0,.5);
                --c-primary: #818cf8;
                --c-accent: #a78bfa;
            }
        }
        /* --- TEMA DEĞİŞKENLERİ SONU --- */

        body, html {
            font-family: 'Segoe UI', sans-serif;
            background: var(--c-bg);
            color: var(--c-text);
            margin: 0; padding: 0; width: 100%; height: 100%;
            transition: background-color 0.3s, color 0.3s;
        }
        .container {
            display: flex; flex-direction: column; justify-content: center; align-items: center;
            min-height: 100vh; padding: 20px; box-sizing: border-box; text-align: center;
        }
        .content-box {
            background: var(--c-container-bg);
            border-radius: 20px;
            box-shadow: var(--c-shadow);
            padding: 50px;
            transition: background-color 0.3s;
        }
        h1 { color: var(--c-primary); margin-top: 0; }
        p { font-size: 1.1em; line-height: 1.6; }
        .info-text {
             font-size: 0.9em;
             color: var(--c-text-secondary);
        }

        #startTestButton {
            background: linear-gradient(135deg, var(--c-primary), var(--c-accent));
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 22px;
            font-weight: bold;
            padding: 25px 50px;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 30px;
            box-shadow: 0 5px 20px rgba(102,126,234,.4);
        }
        #startTestButton:hover { transform: scale(1.05); box-shadow: 0 8px 30px rgba(102,126,234,.6); }

        #testScreen {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
            display: none; z-index: 100; cursor: pointer;
        }

        .exit-instruction {
            display: none; position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.5); color: #FFF; padding: 10px 20px; border-radius: 50px;
            font-weight: bold; z-index: 101; pointer-events: none;
            border: 2px solid rgba(255, 255, 255, 0.8);
        }
    </style>
</head>
<body>
    <div class="container" id="mainControls">
        <div class="content-box">
            <h1>🖥️ Ölü Piksel Testi</h1>
            <p>
                Ekranınızda ölü veya sıkışmış piksel olup olmadığını kontrol etmek için testi başlatın.<br>
                Test tam ekran olarak başlayacaktır.
            </p>
            <p class="info-text">
                (Tam ekran için klavyenizden <b>F11</b> tuşunu da kullanabilirsiniz.)
            </p>
            <button id="startTestButton">Piksel Testini Başlat</button>
        </div>
    </div>

    <div id="testScreen"></div>

    <div class="exit-instruction" id="exitInstruction">Sonraki renk için <b>tıklayın</b> | Çıkmak için <b>ESC</b> tuşuna basın</div>

    <script>
        const mainControls = document.getElementById('mainControls');
        const exitInstruction = document.getElementById('exitInstruction');
        const testScreen = document.getElementById('testScreen');
        const startTestButton = document.getElementById('startTestButton');

        const TEST_COLORS = ['#FF0000', '#00FF00', '#0000FF', '#000000', '#FFFFFF'];
        let colorIndex = 0;
        let isTestRunning = false;

        function startTest() {
            colorIndex = 0;
            isTestRunning = true;
            mainControls.style.display = 'none';

            testScreen.style.backgroundColor = TEST_COLORS[colorIndex];
            testScreen.style.display = 'block';
            exitInstruction.style.display = 'block';

            document.documentElement.requestFullscreen().catch((err) => {
                console.error(`Tam ekran moduna geçilemedi: ${err.message}`);
            });
        }

        function stopTest() {
            if (!isTestRunning) return;
            isTestRunning = false;

            if (document.fullscreenElement) {
                document.exitFullscreen();
            }

            testScreen.style.display = 'none';
            mainControls.style.display = 'flex';
            exitInstruction.style.display = 'none';
        }

        startTestButton.onclick = startTest;

        testScreen.onclick = () => {
            if (!isTestRunning) return;
            colorIndex++;
            if (colorIndex < TEST_COLORS.length) {
                testScreen.style.backgroundColor = TEST_COLORS[colorIndex];
            } else {
                stopTest();
            }
        };

        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement && isTestRunning) {
                stopTest();
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
    port = 5007
    print("="*60)
    print("🖥️ Ölü Piksel Testi (Otomatik Temalı) başlatılıyor...")
    print(f"   -> Bilgisayardan erişim: http://localhost:{port}")
    if local_ip != "127.0.0.1":
        print(f"   -> Ağdaki diğer cihazlardan erişim: http://{local_ip}:{port}")
    print("Tema, işletim sisteminizin aydınlık/karanlık moduna göre otomatik ayarlanır.")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=port)
