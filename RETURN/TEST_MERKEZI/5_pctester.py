import os
import psutil
import cpuinfo
import wmi
from flask import Flask, jsonify, render_template_string
import logging

# Flask'in varsayılan loglarını kapatarak terminali temiz tut
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# --- 1. Kütüphane ve Donanım Kurulumu ---
try:
    import clr
    # Gerekli DLL dosyalarının yollarını belirle
    script_dir = os.path.dirname(os.path.abspath(__file__))
    lhm_dll_path = os.path.join(script_dir, "LibreHardwareMonitorLib.dll")
    hid_dll_path = os.path.join(script_dir, "HidSharp.dll")
    
    if os.path.exists(lhm_dll_path) and os.path.exists(hid_dll_path):
        clr.AddReference(lhm_dll_path)
        from LibreHardwareMonitor.Hardware import Computer
        LHM_COMPUTER = Computer()
        LHM_COMPUTER.IsCpuEnabled = True
        LHM_COMPUTER.IsGpuEnabled = True
        LHM_COMPUTER.IsMotherboardEnabled = True
        LHM_COMPUTER.IsControllerEnabled = True
        LHM_COMPUTER.Open()
        print("[BİLGİ] LibreHardwareMonitor sensörleri başarıyla başlatıldı.")
    else:
        LHM_COMPUTER = None
        print("[UYARI] Gerekli DLL dosyaları (LibreHardwareMonitorLib.dll, HidSharp.dll) bulunamadı. Sıcaklık/Fan verileri gösterilmeyecek.")
except Exception as e:
    LHM_COMPUTER = None
    print(f"[HATA] 'pythonnet' veya LibreHardwareMonitor yüklenemedi. Sıcaklık/Fan verileri gösterilmeyecek. Detay: {e}")


# --- 2. Flask Uygulamasının Tanımlanması ---
app = Flask(__name__)


# --- 3. Donanım Verilerini Toplayan API Uç Noktası ---
@app.route("/api/data")
def get_hardware_data():
    """Tüm donanım verilerini toplayıp JSON formatında sunar."""
    
    # Sensör Verileri (Sıcaklık, Yük, Fan)
    temps, loads, fans = {}, {}, {}
    if LHM_COMPUTER:
        for hw in LHM_COMPUTER.Hardware:
            hw.Update()
            all_components = [hw] + list(hw.SubHardware)
            for component in all_components:
                component.Update()
                for sensor in component.Sensors:
                    if sensor.Value is not None:
                        key = f"{component.Name} - {sensor.Name}"
                        sensor_type = str(sensor.SensorType)
                        if "Temperature" in sensor_type: temps[key] = round(sensor.Value, 1)
                        elif "Load" in sensor_type: loads[key] = round(sensor.Value, 1)
                        elif "Fan" in sensor_type: fans[key] = int(sensor.Value)

    # CPU Bilgileri
    cpu_info = {
        "brand": cpuinfo.get_cpu_info().get("brand_raw", "N/A"),
        "usage": psutil.cpu_percent(interval=0.5)
    }
    
    # RAM Bilgileri
    ram_info = { "total_gb": round(psutil.virtual_memory().total / (1024**3), 2), "percent": psutil.virtual_memory().percent }

    # Disk Bilgileri
    disk_info = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disk_info.append({ "device": part.device, "total_gb": round(usage.total / (1024**3), 2), "percent": usage.percent })
        except PermissionError: continue
        
    # GPU Bilgileri
    gpu_info = []
    try:
        w = wmi.WMI()
        for gpu in w.Win32_VideoController():
            gpu_name = gpu.Name
            gpu_entry = {"name": gpu_name, "load": "N/A", "temp": "N/A"}
            for key, val in loads.items():
                if ("GPU" in key.upper()) and ("CORE" in key.upper()): gpu_entry["load"] = f"{val}%"
            for key, val in temps.items():
                if ("GPU" in key.upper()) and ("CORE" in key.upper() or "HOT SPOT" in key.upper()): gpu_entry["temp"] = f"{val}°C"
            gpu_info.append(gpu_entry)
    except Exception:
        gpu_info.append({"name": "GPU bilgisi alınamadı"})

    return jsonify({ "cpu": cpu_info, "ram": ram_info, "disks": disk_info, "gpus": gpu_info, "temps": temps, "fans": fans })


# --- 4. HTML Arayüz Şablonu ---
HTML_TEMPLATE = """
<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Donanım Paneli</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    .progress { height: 25px; font-size: 1rem; }
    /* Koyul tema kart ayarı */
    [data-bs-theme="dark"] .card { 
        backdrop-filter: blur(5px); 
        background-color: rgba(40, 40, 40, 0.5); 
    }
    /* Açık temada kart arkaplanını ayarla */
    [data-bs-theme="light"] .card { 
        backdrop-filter: blur(5px); 
        background-color: rgba(255, 255, 255, 0.6); 
        border: 1px solid rgba(0,0,0,0.1);
    }
    .sensor-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }
  </style>
</head>
<body>
  <div class="container py-4">
    <header class="text-center mb-4"><h1>💻 Donanım Durum Paneli</h1></header>
    <main id="dashboard-content"><div class="text-center p-5"><div class="spinner-border text-primary" style="width: 3rem; height: 3rem;" role="status"></div><p class="mt-2">Veriler yükleniyor...</p></div></main>
    <footer class="text-center text-secondary mt-4"><p>Veriler 3 saniyede bir otomatik olarak yenilenir.</p></footer>
  </div>
  <script>
    // --- YENİ: SİSTEM TEMASINI OTOMATİK ALGILAYAN KOD ---
    document.addEventListener('DOMContentLoaded', () => {
        const doc = document.documentElement;
        const body = document.body;

        // Sistemi dinleyecek medya sorgusu
        const lightSchemeMediaQuery = window.matchMedia('(prefers-color-scheme: light)');

        function applyTheme(isLight) {
            if (isLight) {
                doc.setAttribute('data-bs-theme', 'light');
                body.classList.remove('bg-dark', 'text-light');
            } else {
                doc.setAttribute('data-bs-theme', 'dark');
                body.classList.add('bg-dark', 'text-light');
            }
        }

        // 1. Sayfa ilk yüklendiğinde temayı uygula
        applyTheme(lightSchemeMediaQuery.matches);

        // 2. Sistem teması değiştiğinde temayı otomatik güncelle
        lightSchemeMediaQuery.addEventListener('change', (e) => {
            applyTheme(e.matches);
        });
    });
    // --- SCRIPT SONU ---

    const content = document.getElementById('dashboard-content');
    function renderComponent(icon, title, body) { return `<div class="col-md-6 mb-4"><div class="card"><div class="card-header fs-5">${icon} ${title}</div><div class="card-body">${body}</div></div></div>`; }
    function renderFullWidthComponent(icon, title, body) { return `<div class="col-12 mb-4"><div class="card"><div class="card-header fs-5">${icon} ${title}</div><div class="card-body">${body}</div></div></div>`; }
    function renderSensors(title, data, unit) {
        if (Object.keys(data).length === 0) return '<p class="text-secondary">Okunabilir sensör bulunamadı.</p>';
        let items = '';
        for (const [key, value] of Object.entries(data)) { items += `<div class="d-flex justify-content-between p-2 bg-secondary bg-opacity-10 rounded"><span>${key}</span><strong>${value} ${unit}</strong></div>`; }
        return `<div class="sensor-grid">${items}</div>`;
    }
    async function updateDashboard() {
        try {
            const response = await fetch('/api/data');
            const data = await response.json();
            let html = '<div class="row">';
            
            let cpuBody = `<h5 class="card-title">${data.cpu.brand}</h5>
                             <h6 class="mt-3">Kullanım Oranı</h6>
                             <div class="progress" role="progressbar">
                               <div class="progress-bar progress-bar-striped progress-bar-animated bg-info" style="width: ${data.cpu.usage}%">${data.cpu.usage.toFixed(1)}%</div>
                             </div>`;
            html += renderComponent('🧠', 'İşlemci (CPU)', cpuBody);
            
            let ramBody = `<h5 class="card-title">${data.ram.total_gb} GB Toplam Bellek</h5>
                             <h6>Kullanım Oranı</h6>
                             <div class="progress" role="progressbar">
                               <div class="progress-bar progress-bar-striped progress-bar-animated bg-success" style="width: ${data.ram.percent}%">${data.ram.percent}%</div>
                             </div>`;
            html += renderComponent('💾', 'Bellek (RAM)', ramBody);
            let gpuBody = '';
            data.gpus.forEach(gpu => { gpuBody += `<div class="p-2 rounded bg-secondary bg-opacity-10 mb-2"><strong>${gpu.name}</strong> | Yük: ${gpu.load} | Sıcaklık: ${gpu.temp}</div>`; });
            html += renderFullWidthComponent('🎮', 'Ekran Kartı (GPU)', gpuBody);
            let diskBody = '';
            data.disks.forEach(d => { diskBody += `<h6 class="mt-2">${d.device} - ${d.total_gb} GB</h6><div class="progress" role="progressbar"><div class="progress-bar bg-warning text-dark" style="width: ${d.percent}%">${d.percent.toFixed(1)}% Dolu</div></div>`; });
            html += renderFullWidthComponent('💽', 'Diskler', diskBody);
            let sensorBody = '<h6>Sıcaklıklar</h6>' + renderSensors('Sıcaklıklar', data.temps, '°C');
            sensorBody += '<h6 class="mt-3">Fan Hızları</h6>' + renderSensors('Fan Hızları', data.fans, 'RPM');
            html += renderFullWidthComponent('🌡️', 'Diğer Sensörler', sensorBody);
            html += '</div>';
            content.innerHTML = html;
        } catch (error) {
            content.innerHTML = '<div class="alert alert-danger">Veri sunucusuna bağlanılamadı. Python betiğinin yönetici olarak çalıştığından emin misiniz?</div>';
            console.error("Hata:", error);
        }
    }
    setInterval(updateDashboard, 3000);
    window.onload = updateDashboard;
  </script>
</body>
</html>
"""

# --- 5. Sunucuyu Başlatan Ana Rota ve Çalıştırma Bloğu ---
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == "__main__":
    print("\n" + "="*50)
    print("Donanım Paneli Sunucusu Başlatıldı!")
    print("Arayüze erişmek için web tarayıcınızı açın ve")
    print("şu adrese gidin: http://127.0.0.1:5005")
    print("="*50 + "\n")
    app.run(host='127.0.0.1', port=5005)