# speed_tester_flask_cli.py
# Flask + speedtest-cli tabanlı web hız testi (SSE ile canlı sonuç ve Otomatik Tema)

from flask import Flask, render_template_string, Response, stream_with_context
import socket
import json

# speedtest-cli modülünü doğru şekilde import et
try:
    import speedtest
except ImportError:
    print("HATA: speedtest-cli modülü bulunamadı!")
    print("Lütfen şu komutu çalıştırın: pip install speedtest-cli")
    exit(1)

app = Flask(__name__)

# --- Yerel IP Bulma Fonksiyonu ---
def get_local_ip():
    s = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except socket.error:
        try:
            return socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            return "127.0.0.1"
    finally:
        if s:
            s.close()

# --- HTML Arayüz ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ağ Hızı Testi (speedtest-cli)</title>
    <style>
        /* --- OTOMATİK TEMA DEĞİŞKENLERİ --- */
        :root {
            /* Varsayılan: Aydınlık Tema */
            --c-bg: #f0f2f5;
            --c-text: #333;
            --c-text-secondary: #666;
            --c-container-bg: #fff;
            --c-shadow: 0 10px 40px rgba(0,0,0,.1);
            --c-primary: #667eea;
            --c-accent: #764ba2;
            --c-result-box-bg: #f8f9ff;
            --c-result-box-border: #e0e7ff;
            --c-progress-track: #e0e7ff;
            --c-ip-info-bg: #e0e7ff;
            --c-ip-info-text: #4f46e5;
            --c-ip-info-border: #c7d2fe;
            --c-ip-error-bg: #fee2e2;
            --c-ip-error-text: #ef4444;
            --c-ip-error-border: #fecaca;
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
                --c-result-box-bg: #2c2c31;
                --c-result-box-border: #444;
                --c-progress-track: #444;
                --c-ip-info-bg: #2c2c31;
                --c-ip-info-text: #c7d2fe;
                --c-ip-info-border: #444;
                --c-ip-error-bg: #452323;
                --c-ip-error-text: #f87171;
                --c-ip-error-border: #7f1d1d;
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
            transition: background-color 0.3s, color 0.3s;
        }
        .container {
            background: var(--c-container-bg);
            padding: 40px;
            border-radius: 20px;
            box-shadow: var(--c-shadow);
            text-align: center;
            width: 100%;
            max-width: 700px;
            transition: background-color 0.3s;
        }
        h1 { color: var(--c-primary); margin-bottom: 10px; }
        p { color: var(--c-text-secondary); margin-bottom: 20px; }
        #startBtn {
            background: linear-gradient(135deg, var(--c-primary), var(--c-accent));
            color: white;
            border: none;
            border-radius: 50px;
            padding: 20px 60px;
            font-size: 22px;
            cursor: pointer;
            margin-top: 20px;
            transition: 0.3s;
        }
        #startBtn:hover:not(:disabled) { transform: scale(1.05); }
        #startBtn:disabled {
            opacity: 0.8;
            cursor: not-allowed;
            background: var(--c-btn-disabled-bg);
        }

        #status { margin-top: 25px; color: var(--c-accent); font-weight: bold; min-height: 24px; }
        #status.error { color: var(--c-ip-error-text); }

        .results {
            display: grid;
            grid-template-columns: repeat(auto-fit,minmax(150px,1fr));
            gap: 20px;
            margin-top: 40px;
        }
        .result-box {
            background: var(--c-result-box-bg);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid var(--c-result-box-border);
            transition: background-color 0.3s, border-color 0.3s;
        }
        .label { color: var(--c-accent); font-weight: bold; margin-bottom: 10px; font-size: 14px; }
        .value { font-size: 2.5em; color: var(--c-primary); font-weight: bold; }
        .unit { font-size: 0.5em; color: var(--c-text-secondary); }

        #progressBarContainer {
            height: 10px; background-color: var(--c-progress-track); border-radius: 5px;
            margin-top: 20px; overflow: hidden; display: none;
            transition: background-color 0.3s;
        }
        #progressBar {
            height: 100%; width: 0%; background-color: var(--c-primary);
            transition: width 0.3s ease-out, background-color 0.3s;
        }

        .ip-info {
            margin-top: 30px;
            background: var(--c-ip-info-bg);
            padding: 15px;
            border-radius: 10px;
            color: var(--c-ip-info-text);
            border: 1px solid var(--c-ip-info-border);
            font-size: 14px;
            transition: background-color 0.3s, color 0.3s, border-color 0.3s;
        }
        .ip-info.error {
            background: var(--c-ip-error-bg);
            color: var(--c-ip-error-text);
            border-color: var(--c-ip-error-border);
        }
    </style>
</head>
<body>
<div class="container">
    <h1>⚡ Ağ Hızı Testi</h1>
    <p>İnternet bağlantınızın indirme, yükleme hızını ve gecikmesini ölçün.</p>

    <button id="startBtn">Testi Başlat</button>
    <div id="status"></div>
    <div id="progressBarContainer"><div id="progressBar"></div></div>

    <div class="results">
        <div class="result-box">
            <div class="label">Ping</div>
            <div><span id="pingValue" class="value">-</span><span class="unit"> ms</span></div>
        </div>
        <div class="result-box">
            <div class="label">Download</div>
            <div><span id="downloadValue" class="value">-</span><span class="unit"> Mbps</span></div>
        </div>
        <div class="result-box">
            <div class="label">Upload</div>
            <div><span id="uploadValue" class="value">-</span><span class="unit"> Mbps</span></div>
        </div>
    </div>

    <div id="ipInfo" class="ip-info">IP bilgileri yükleniyor...</div>
</div>

<script>
const startBtn = document.getElementById('startBtn');
const statusDiv = document.getElementById('status');
const pingDiv = document.getElementById('pingValue');
const downDiv = document.getElementById('downloadValue');
const upDiv = document.getElementById('uploadValue');
const progressBarContainer = document.getElementById('progressBarContainer');
const progressBar = document.getElementById('progressBar');
let eventSource = null;

async function fetchIpInfo() {
    const ipInfo = document.getElementById('ipInfo');
    try {
        const ipData = await fetch('https://api.ipify.org?format=json').then(r=>r.json());
        const geo = await fetch(`https://ipapi.co/${ipData.ip}/json/`).then(r=>r.json());
        if(geo.error) throw new Error(geo.reason || 'IP bilgisi alınamadı');
        ipInfo.innerHTML = `<b>IP:</b> ${ipData.ip}<br><b>Sağlayıcı:</b> ${geo.org || 'Bilinmiyor'}<br><b>Konum:</b> ${geo.city || 'Bilinmiyor'}, ${geo.country_name || 'Bilinmiyor'}`;
        ipInfo.classList.remove('error');
    } catch(e) {
        ipInfo.textContent = "IP bilgisi alınamadı: " + e.message;
        ipInfo.classList.add("error");
    }
}

function resetUI() {
    pingDiv.textContent = downDiv.textContent = upDiv.textContent = '-';
    statusDiv.textContent = '';
    statusDiv.classList.remove('error');
    progressBar.style.width = '0%';
    progressBarContainer.style.display = 'none';
}

function runSpeedTest() {
    if(eventSource) eventSource.close();
    
    resetUI();
    startBtn.disabled = true;
    startBtn.textContent = "Test yapılıyor...";
    progressBarContainer.style.display = 'block';
    
    eventSource = new EventSource('/stream');
    
    eventSource.onmessage = (event)=>{
        const data = JSON.parse(event.data);
        
        if(data.type==="status"){ 
            statusDiv.textContent = data.message; 
        }
        else if(data.type==="ping"){ 
            pingDiv.textContent = data.value.toFixed(0);
            progressBar.style.width = '25%';
        }
        else if(data.type==="download"){ 
            downDiv.textContent = data.value.toFixed(2);
            progressBar.style.width = '50%';
        }
        else if(data.type==="upload"){ 
            upDiv.textContent = data.value.toFixed(2);
            progressBar.style.width = '75%';
        }
        else if(data.type==="final"){
            statusDiv.textContent = "✅ Test tamamlandı!";
            progressBar.style.width = '100%';
            eventSource.close();
            startBtn.disabled = false;
            startBtn.textContent = "Testi Tekrar Başlat";
        }
        else if(data.type==="error"){
            statusDiv.textContent = "❌ Hata: " + data.message;
            statusDiv.classList.add('error');
            progressBar.style.width = '0%';
            eventSource.close();
            startBtn.disabled = false;
            startBtn.textContent = "Tekrar Dene";
        }
    };
    
    eventSource.onerror = ()=>{
        statusDiv.textContent = "❌ Bağlantı hatası!";
        statusDiv.classList.add('error');
        progressBar.style.width = '0%';
        eventSource.close();
        startBtn.disabled = false;
        startBtn.textContent = "Tekrar Dene";
    };
}

startBtn.addEventListener('click', runSpeedTest);
document.addEventListener('DOMContentLoaded', fetchIpInfo);
</script>
</body>
</html>
"""

# --- Hız Testi İşlemi (Backend) ---
def generate_speed_test_updates():
    try:
        # --- HATA DÜZELTMESİ: Tüm '\\n\\n' ifadeleri '\n\n' olarak değiştirildi ---
        yield f"data: {json.dumps({'type':'status','message':'Hız testi başlatılıyor...'})}\n\n"
        
        st = speedtest.Speedtest()

        yield f"data: {json.dumps({'type':'status','message':'En iyi sunucu bulunuyor...'})}\n\n"
        best = st.get_best_server()
        sponsor = f"{best['sponsor']} ({best['name']}, {best['country']})"
        yield f"data: {json.dumps({'type':'status','message':f'Sunucu: {sponsor}'})}\n\n"

        ping = st.results.ping
        yield f"data: {json.dumps({'type':'ping','value':ping})}\n\n"

        yield f"data: {json.dumps({'type':'status','message':'Download testi yapılıyor...'})}\n\n"
        down = st.download() / 1_000_000
        yield f"data: {json.dumps({'type':'download','value':down})}\n\n"

        yield f"data: {json.dumps({'type':'status','message':'Upload testi yapılıyor...'})}\n\n"
        up = st.upload() / 1_000_000
        yield f"data: {json.dumps({'type':'upload','value':up})}\n\n"

        yield f"data: {json.dumps({'type':'final','ping':ping,'download':down,'upload':up})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"

@app.route('/stream')
def stream():
    return Response(
        stream_with_context(generate_speed_test_updates()),
        mimetype='text/event-stream',
        headers={'Cache-Control':'no-cache','X-Accel-Buffering':'no'}
    )

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

if __name__ == '__main__':
    local_ip = get_local_ip()
    port = 5010
    print("="*60)
    print("⚡ Ağ Hızı Testi (Otomatik Temalı) başlatılıyor...")
    print(f"   -> Tarayıcıdan aç: http://localhost:{port}")
    if local_ip != "127.0.0.1":
        print(f"   -> Aynı ağdaki diğer cihazlardan: http://{local_ip}:{port}")
    print("Tema, işletim sisteminizin aydınlık/karanlık moduna göre otomatik ayarlanır.")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)