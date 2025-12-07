from flask import Flask, render_template_string
import os
import socket

app = Flask(__name__)

# --- Otomatik Yerel IP Bulma Fonksiyonu ---
def get_local_ip():
    """Bilgisayarın yerel ağ IP adresini bulmaya çalışır."""
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)) # Bağlantı aslında kurulmaz
        ip_address = s.getsockname()[0]
        return ip_address
    except socket.error:
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return "1227.0.0.1" # Son çare localhost
    finally:
        if s:
            s.close() # Soketi kapat
# --- IP Bulma Fonksiyonu Sonu ---

# --- SERTİFİKA AYARLARI ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SSL_CERT = os.path.join(BASE_DIR, 'localhost.pem')
SSL_KEY = os.path.join(BASE_DIR, 'localhost-key.pem')
# --- AYARLAR SONU ---


HTML_CONTENT = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Web Kamerası Testi</title>
    <style>
        /* --- OTOMATİK TEMA DEĞİŞKENLERİ --- */
        :root {
            /* Varsayılan: Aydınlık Tema */
            --c-bg: #f0f2f5;
            --c-text: #333;
            --c-text-secondary: #666;
            --c-container-bg: white;
            --c-shadow: 0 10px 40px rgba(0,0,0,.1);
            --c-primary: #667eea;
            --c-accent: #764ba2;
            --c-error: #ef4444;
            --c-btn-text: white;
            --c-grad-start-bg: linear-gradient(135deg, #667eea, #764ba2);
            --c-grad-mirror-bg: linear-gradient(135deg, #a276ba, #764ba2);
            --c-grad-start-shadow: 0 5px 20px rgba(102,126,234,.4);
            --c-grad-mirror-shadow: 0 5px 20px rgba(162,118,186,.6);
            --c-btn-disabled-bg: #ccc;
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
                --c-error: #f87171;
                --c-grad-start-shadow: 0 5px 20px rgba(129, 140, 248, .3);
                --c-grad-mirror-shadow: 0 5px 20px rgba(192, 132, 252, .3);
                --c-btn-disabled-bg: #555;
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
            padding: 20px;
            box-sizing: border-box;
            transition: background-color 0.3s, color 0.3s;
        }
        .container {
            background: var(--c-container-bg);
            border-radius: 20px;
            box-shadow: var(--c-shadow);
            padding: 40px;
            text-align: center;
            max-width: 700px;
            width: 100%;
            transition: background-color 0.3s;
        }
        h1 {
            color: var(--c-primary);
            margin-top: 0;
            font-size: 2em;
        }
        p {
            font-size: 1.1em;
            margin-bottom: 30px;
            color: var(--c-text-secondary);
        }

        #startBtn, #mirrorBtn {
            background: var(--c-grad-start-bg);
            color: var(--c-btn-text);
            border: none;
            border-radius: 50px;
            font-size: 20px;
            font-weight: bold;
            padding: 18px 50px;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 10px;
            box-shadow: var(--c-grad-start-shadow);
        }
        #startBtn:hover:not(:disabled), #mirrorBtn:hover:not(:disabled) {
            transform: scale(1.05);
            box-shadow: 0 8px 30px rgba(102,126,234,.6); /* Bu gölge hover'da sabit kalabilir veya ayarlanabilir */
        }
        #startBtn:disabled, #mirrorBtn:disabled {
            background: var(--c-btn-disabled-bg);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
            opacity: 0.7;
        }
        #mirrorBtn {
            font-size: 16px;
            padding: 10px 25px;
            margin-left: 10px;
            background: var(--c-grad-mirror-bg);
        }
        #mirrorBtn:hover:not(:disabled) {
            box-shadow: var(--c-grad-mirror-shadow);
        }
        #webcamVideo {
            display: none;
            width: 100%;
            max-width: 600px;
            height: auto;
            margin: 30px auto 0 auto;
            border-radius: 15px;
            background-color: #000;
            border: 3px solid var(--c-primary);
            transform: scaleX(-1);
            -webkit-transform: scaleX(-1);
            transition: transform 0.2s ease-in-out, border-color 0.3s;
        }
        #status {
            margin-top: 25px;
            font-weight: bold;
            color: var(--c-accent);
            min-height: 25px;
            font-size: 1.1em;
        }
        #status.error {
            color: var(--c-error);
        }
        #resolutionInfo {
            font-size: 0.9em;
            color: var(--c-text-secondary);
            margin-top: 10px;
            min-height: 20px;
        }
        .console-info {
            font-size: 0.8em;
            color: #888;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📷 Web Kamerası Testi</h1>
        <p>Kameranızın çalışıp çalışmadığını kontrol etmek için testi başlatın.<br>Tarayıcınızın kameranıza erişmesine izin vermeniz istenecektir.</p>
        <button id="startBtn">Kamera Testini Başlat</button>
        <button id="mirrorBtn" disabled>↔️ Aynala / Çevir</button>
        <div id="status">Kamera bekleniyor...</div>
        <video id="webcamVideo" autoplay playsinline></video>
        <div id="resolutionInfo"></div>
        <div class="console-info">Sorun yaşarsanız (örn: siyah ekran), tarayıcı konsolunu (F12) kontrol edin. Algılanan ve kullanılan kameralar listelenecektir.</div>
    </div>
    <script>
        const startBtn = document.getElementById('startBtn');
        const mirrorBtn = document.getElementById('mirrorBtn');
        const statusDiv = document.getElementById('status');
        const videoElement = document.getElementById('webcamVideo');
        const resolutionInfoDiv = document.getElementById('resolutionInfo');
        let currentStream = null;
        let isMirrored = true;

        async function listCameras() {
            statusDiv.textContent = 'Kameralar listeleniyor...';
            statusDiv.classList.remove('error');
            try {
                await navigator.mediaDevices.getUserMedia({ video: true });
                const devices = await navigator.mediaDevices.enumerateDevices();
                const videoDevices = devices.filter(device => device.kind === 'videoinput');

                console.log("--- Algılanan Kameralar ---");
                if (videoDevices.length > 0) {
                    videoDevices.forEach((device, index) => {
                        console.log(` Kamera ${index + 1}: Etiket='${device.label}', ID='${device.deviceId}'`);
                    });
                } else {
                    console.log(" Hiçbir video giriş cihazı bulunamadı.");
                }
                console.log("--------------------------");

                if (videoDevices.length > 1) {
                    statusDiv.textContent = `Birden fazla kamera algılandı (${videoDevices.length} adet). Varsayılan kullanılacak. Ayrıntılar için Konsolu (F12) kontrol edin.`;
                } else if (videoDevices.length === 0) {
                    statusDiv.textContent = '❌ Hata: Hiçbir kamera algılanmadı.';
                    statusDiv.classList.add('error');
                    return null;
                }
                return videoDevices;
            } catch (err) {
                console.error("Kamera listesi alınamadı veya ilk izin reddedildi:", err);
                statusDiv.textContent = '❌ Hata: Kamera listesi alınamadı veya izin reddedildi.';
                statusDiv.classList.add('error');
                return null;
            }
        }

        async function startWebcamTest() {
            startBtn.disabled = true; startBtn.textContent = 'Kamera Başlatılıyor...';
            mirrorBtn.disabled = true;
            statusDiv.textContent = 'Kameralar listeleniyor...'; statusDiv.classList.remove('error');
            videoElement.style.display = 'none'; resolutionInfoDiv.textContent = '';
            stopWebcamStream();

            const videoDevices = await listCameras();
            if (!videoDevices || videoDevices.length === 0) {
                resetUI();
                return;
            }
            statusDiv.textContent = 'Kamera izni isteniyor...';

            try {
                let firstCameraId = videoDevices[0].deviceId;
                console.log(`İlk kameranın ID'si (${firstCameraId}) kullanılmaya çalışılacak.`);

                const constraints = {
                    video: {
                        deviceId: firstCameraId ? { exact: firstCameraId } : undefined,
                        facingMode: "user"
                    },
                    audio: false
                };

                const stream = await navigator.mediaDevices.getUserMedia(constraints);

                if (stream.getVideoTracks().length > 0) {
                    const currentTrack = stream.getVideoTracks()[0];
                    console.log("Kullanılan Kamera Akışı:", currentTrack.label || `(etiket yok) - ID: ${currentTrack.id}`);
                    statusDiv.textContent = `Kullanılan Kamera: ${currentTrack.label || '(isim alınamadı)'}. Yükleniyor...`;
                } else {
                    console.warn("Alınan akışta video izi bulunamadı.");
                    throw new Error("Kamera akışı video izi içermiyor.");
                }

                currentStream = stream;
                videoElement.srcObject = stream;

                videoElement.onloadedmetadata = () => {
                    console.log("Video metadata yüklendi. Oynatma deneniyor...");
                    videoElement.style.display = 'block';
                    videoElement.play().then(() => {
                        console.log("Video oynatılıyor.");
                        statusDiv.textContent = '✅ Kamera aktif!';
                        startBtn.textContent = 'Testi Durdur';
                        startBtn.disabled = false;
                        mirrorBtn.disabled = false;
                        try {
                            const track = stream.getVideoTracks()[0];
                            const settings = track.getSettings();
                            console.log("Kamera Ayarları:", settings);
                            if (settings.width && settings.height) {
                                resolutionInfoDiv.textContent = `Algılanan Çözünürlük: ${settings.width} x ${settings.height}`;
                            } else { resolutionInfoDiv.textContent = 'Çözünürlük bilgisi alınamadı.'; }
                        } catch (settingsError) {
                            console.error("Kamera ayarları alınamadı:", settingsError);
                            resolutionInfoDiv.textContent = 'Çözünürlük bilgisi alınamadı.';
                        }
                    }).catch(playError => {
                        console.error("!!! Video oynatma hatası:", playError);
                        statusDiv.textContent = `❌ Hata: Video akışı oynatılamadı. Konsolu kontrol edin. (${playError.name})`;
                        statusDiv.classList.add('error');
                        resetUI();
                    });
                };
                videoElement.onerror = (e) => {
                    console.error("!!! Video elementi hatası:", e, videoElement.error);
                    statusDiv.textContent = `❌ Hata: Video yüklenirken sorun oluştu. Konsolu kontrol edin. (Kod: ${videoElement.error?.code})`;
                    statusDiv.classList.add('error');
                    resetUI();
                };
                videoElement.onplaying = () => { console.log("Video 'playing' olayı tetiklendi."); };
                videoElement.onstalled = () => { console.warn("Video 'stalled' (durakladı) olayı tetiklendi."); };

            } catch (error) {
                console.error("!!! getUserMedia veya sonrası hata:", error);
                statusDiv.classList.add('error');
                if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                    statusDiv.textContent = '❌ Hata: Kamera erişim izni reddedildi.';
                } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                    statusDiv.textContent = '❌ Hata: İstenen kamera bulunamadı veya kullanılamıyor.';
                } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
                    statusDiv.textContent = '❌ Hata: Kamera başka bir uygulama tarafından kullanılıyor veya donanım hatası var.';
                } else if (error.name === 'OverconstrainedError' || error.name === 'ConstraintNotSatisfiedError') {
                    statusDiv.textContent = `❌ Hata: İstenen kamera ayarları desteklenmiyor.`;
                    console.warn("Constraint hatası alındı.");
                } else {
                    statusDiv.textContent = `❌ Hata: Kamera başlatılamadı (${error.name || error.message})`;
                }
                resetUI();
            }
        }

        function stopWebcamStream() {
            if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
                videoElement.srcObject = null;
                videoElement.style.display = 'none';
                videoElement.onloadedmetadata = null;
                videoElement.onerror = null;
                videoElement.onplaying = null;
                videoElement.onstalled = null;
            }
        }
        function resetUI() {
            stopWebcamStream();
            statusDiv.textContent = 'Kamera bekleniyor...'; statusDiv.classList.remove('error');
            resolutionInfoDiv.textContent = '';
            startBtn.disabled = false; startBtn.textContent = 'Kamera Testini Başlat';
            mirrorBtn.disabled = true;
        }

        startBtn.addEventListener('click', () => {
            if (currentStream) resetUI(); else startWebcamTest();
        });

        mirrorBtn.addEventListener('click', () => {
            if (videoElement.style.transform === 'scaleX(-1)') {
                videoElement.style.transform = 'scaleX(1)';
                isMirrored = false;
                console.log("Video aynalama kapalı.");
            } else {
                videoElement.style.transform = 'scaleX(-1)';
                isMirrored = true;
                console.log("Video aynalama açık.");
            }
        });

        window.addEventListener('beforeunload', stopWebcamStream);

    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

if __name__ == '__main__':
    local_ip = get_local_ip()
    port = 5012

    if not (os.path.exists(SSL_CERT) and os.path.exists(SSL_KEY)):
        print("="*60)
        print("❌ HATA: 'localhost.pem' ve 'localhost-key.pem' dosyaları bulunamadı!")
        print(f"Aranan konum: {BASE_DIR}")
        print("Webcam testi HTTPS gerektirir. Lütfen 'mkcert' komutlarını doğru klasörde çalıştırdığınızdan emin olun.")
        print("Program şimdi çıkacak.")
        print("="*60)
        exit()

    print("="*60)
    print("📷 Web Kamerası Testi (Otomatik Temalı HTTPS) başlatılıyor...")
    print(f"   -> Bilgisayardan erişim: https://localhost:{port}")
    if local_ip != "127.0.0.1":
        print(f"   -> Ağdaki diğer cihazlardan erişim: https://{local_ip}:{port}")
    else:
        print("   -> Yerel IP adresi bulunamadı.")
    print("Tema, işletim sisteminizin aydınlık/karanlık moduna göre otomatik ayarlanır.")
    print("="*60)

    context = (SSL_CERT, SSL_KEY)
    app.run(debug=True, host='0.0.0.0', port=port, ssl_context=context)