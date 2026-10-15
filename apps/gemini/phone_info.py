import sys
import io

# Windows konsol encoding sorununu çöz
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


# phone_info.py
import subprocess
import json
import shlex
import time
import re
from flask import Flask, jsonify

app = Flask(__name__)

# HTML/CSS/JavaScript şablonu
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📱 Telefon Detay Bilgileri</title>
    <style>
        /* ------------------------------------------------------------------- */
        /* TEMA DEĞİŞKENLERİ (AYDINLIK TEMA - Varsayılan) */
        /* ------------------------------------------------------------------- */
        :root {
            --bg-primary: #f3f3f3; /* Ana Arka Plan */
            --bg-secondary: #ffffff; /* Kart Arka Planı */
            --text-primary: #1e1e1e; /* Ana Yazı Rengi */
            --text-secondary: #605e5c; /* Açıklama Yazı Rengi */
            --accent-color: #0078d4; /* Vurgu Rengi (Windows Mavisi) */
            --accent-text: #ffffff;
            --border-color: #e0e0e0;
            --shadow-color: rgba(0,0,0,0.1);
            --status-good: #10b981;
            --status-warning: #f59e0b;
            --status-bad: #ef4444;
        }

        /* ------------------------------------------------------------------- */
        /* KARANLIK TEMA (Sistem Tercihine Göre Otomatik Uygulanır) */
        /* ------------------------------------------------------------------- */
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-primary: #202020;
                --bg-secondary: #2c2c2c;
                --text-primary: #ffffff;
                --text-secondary: #b3b3b3;
                --accent-color: #0078d4;
                --accent-text: #ffffff;
                --border-color: #444444;
                --shadow-color: rgba(0,0,0,0.5);
                --status-good: #34d399;
                --status-warning: #fbbf24;
                --status-bad: #f87171;
            }
        }

        /* ------------------------------------------------------------------- */
        /* GENEL STİL */
        /* ------------------------------------------------------------------- */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 40px 20px;
            transition: background-color 0.3s, color 0.3s; /* Yumuşak geçiş */
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
        }

        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            color: var(--text-primary);
            transition: color 0.3s;
        }

        .header p {
            color: var(--text-secondary);
            transition: color 0.3s;
        }

        /* Yenile Butonu (Yalnızca Bu Buton Kaldı) */
        .refresh-btn {
            background: var(--accent-color);
            color: var(--accent-text);
            border: none;
            padding: 15px 40px;
            border-radius: 50px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px var(--shadow-color);
            transition: all 0.3s;
        }

        .refresh-btn:hover {
            filter: brightness(1.1);
            transform: translateY(-2px);
            box-shadow: 0 6px 20px var(--shadow-color);
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }

        .card {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 8px 20px var(--shadow-color);
            transition: background-color 0.3s, transform 0.3s, box-shadow 0.3s;
            border: 1px solid var(--border-color);
        }

        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 25px var(--shadow-color);
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid var(--accent-color);
        }

        .card-icon {
            font-size: 40px;
        }

        .card-title {
            font-size: 24px;
            color: var(--accent-color);
            font-weight: 600;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid var(--border-color);
        }

        .info-row:last-child {
            border-bottom: none;
        }

        .info-label {
            color: var(--text-secondary);
            font-size: 15px;
            font-weight: 500;
        }

        .info-value {
            font-weight: 600;
            color: var(--text-primary);
            font-size: 15px;
        }

        /* Durum Sınıfları */
        .status-good { color: var(--status-good); }
        .status-warning { color: var(--status-warning); }
        .status-bad { color: var(--status-bad); }

        /* Loading ve Error stilleri */
        .loading {
            text-align: center;
            padding: 60px;
            background: var(--bg-secondary);
            border-radius: 12px;
            box-shadow: 0 10px 30px var(--shadow-color);
            color: var(--text-primary);
        }

        .spinner {
            border: 5px solid var(--border-color);
            border-top: 5px solid var(--accent-color);
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .error {
            background: var(--bg-secondary);
            color: var(--status-bad);
            padding: 20px;
            border-radius: 12px;
            border: 1px solid var(--status-bad);
            text-align: center;
            font-size: 18px;
            box-shadow: 0 4px 10px rgba(239, 68, 68, 0.2);
        }

        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }

            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body> <div class="container">
        <div class="header">
            <h1>📱 Telefon Detay Bilgileri</h1>
            <p style="font-size: 18px; margin: 15px 0;">Cihazınızın tüm teknik özelliklerini görüntüleyin</p>
            <button class="refresh-btn" onclick="loadPhoneInfo()">🔄 Bilgileri Yenile</button>
        </div>

        <div id="content">
            <div class="loading">
                <div class="spinner"></div>
                <p style="font-size: 18px; color: var(--accent-color);">Telefon bilgileri yükleniyor...</p>
            </div>
        </div>
    </div>

    <script>
        // Sadece veri çekme ve gösterme fonksiyonları kaldı, tema yönetimi JS'ten çıkarıldı.
        window.addEventListener('load', loadPhoneInfo);

        async function loadPhoneInfo() {
            const content = document.getElementById('content');
            content.innerHTML = `
                <div class="loading">
                    <div class="spinner"></div>
                    <p style="font-size: 18px; color: var(--accent-color);">⏳ Yükleniyor...</p>
                </div>
            `;

            try {
                const response = await fetch('/info');
                const data = await response.json();

                if (data.error) {
                    content.innerHTML = `<div class="error">❌ ${data.error}</div>`;
                    return;
                }

                displayPhoneInfo(data);
            } catch (error) {
                content.innerHTML = `<div class="error">❌ Bağlantı hatası! ADB bağlı mı?</div>`;
                console.error(error);
            }
        }

        function displayPhoneInfo(data) {
            let html = '<div class="grid">';

            html += `
                <div class="card">
                    <div class="card-header">
                        <div class="card-icon">📱</div>
                        <div class="card-title">Cihaz Bilgileri</div>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Marka</span>
                        <span class="info-value">${data.device.brand}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Model</span>
                        <span class="info-value">${data.device.model}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Seri Numarası</span>
                        <span class="info-value">${data.device.serial}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">Android Sürümü</span>
                        <span class="info-value">${data.device.android_version}</span>
                    </div>
                </div>
            `;

            if (data.imei && Object.keys(data.imei).length > 0) {
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">📡</div>
                            <div class="card-title">IMEI Numarası</div>
                        </div>
                        ${Object.entries(data.imei).map(([key, value]) => `
                            <div class="info-row">
                                <span class="info-label">${key.toUpperCase()}</span>
                                <span class="info-value">${value}</span>
                            </div>
                        `).join('')}
                    </div>
                `;
            }

            if (data.battery && Object.keys(data.battery).length > 0) {
                const healthClass = data.battery.health === 'İyi' ? 'status-good' : 'status-warning';
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">🔋</div>
                            <div class="card-title">Batarya Durumu</div>
                        </div>
                        ${data.battery.level ? `
                            <div class="info-row">
                                <span class="info-label">Şarj Seviyesi</span>
                                <span class="info-value">${data.battery.level}%</span>
                            </div>
                        ` : ''}
                        ${data.battery.health ? `
                            <div class="info-row">
                                <span class="info-label">Sağlık Durumu</span>
                                <span class="info-value ${healthClass}">${data.battery.health}</span>
                            </div>
                        ` : ''}
                        ${data.battery.cycle_count ? `
                            <div class="info-row">
                                <span class="info-label">Döngü Sayısı</span>
                                <span class="info-value">${data.battery.cycle_count}</span>
                            </div>
                        ` : ''}
                        ${data.battery.temperature ? `
                            <div class="info-row">
                                <span class="info-label">Sıcaklık</span>
                            <span class="info-value">${data.battery.temperature}</span>
                            </div>
                        ` : ''}
                        ${data.battery.voltage ? `
                            <div class="info-row">
                                <span class="info-label">Voltaj</span>
                                <span class="info-value">${data.battery.voltage}</span>
                            </div>
                        ` : ''}
                    </div>
                `;
            }

            if (data.screen && Object.keys(data.screen).length > 0) {
                const screenClass = data.screen.status === 'Açık' ? 'status-good' : 'status-warning';
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">🖥️</div>
                            <div class="card-title">Ekran Bilgileri</div>
                        </div>
                        ${data.screen.resolution ? `
                            <div class="info-row">
                                <span class="info-label">Çözünürlük</span>
                                <span class="info-value">${data.screen.resolution}</span>
                            </div>
                        ` : ''}
                        ${data.screen.status ? `
                            <div class="info-row">
                                <span class="info-label">Durum</span>
                                <span class="info-value ${screenClass}">${data.screen.status}</span>
                            </div>
                        ` : ''}
                        ${data.screen.brightness ? `
                            <div class="info-row">
                                <span class="info-label">Parlaklık</span>
                                <span class="info-value">${data.screen.brightness}</span>
                            </div>
                        ` : ''}
                    </div>
                `;
            }

            if (data.ram && Object.keys(data.ram).length > 0) {
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">💾</div>
                            <div class="card-title">RAM Bellek</div>
                        </div>
                        ${data.ram.total ? `
                            <div class="info-row">
                                <span class="info-label">Toplam RAM</span>
                                <span class="info-value">${data.ram.total}</span>
                            </div>
                        ` : ''}
                        ${data.ram.available ? `
                            <div class="info-row">
                                <span class="info-label">Kullanılabilir</span>
                                <span class="info-value">${data.ram.available}</span>
                            </div>
                        ` : ''}
                        ${data.ram.free ? `
                            <div class="info-row">
                                <span class="info-label">Boş Alan</span>
                                <span class="info-value">${data.ram.free}</span>
                            </div>
                        ` : ''}
                    </div>
                `;
            }

            if (data.storage && Object.keys(data.storage).length > 0) {
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">💿</div>
                            <div class="card-title">Depolama Alanı</div>
                        </div>
                        ${data.storage.total ? `
                            <div class="info-row">
                                <span class="info-label">Toplam Alan</span>
                                <span class="info-value">${data.storage.total}</span>
                            </div>
                        ` : ''}
                        ${data.storage.used ? `
                            <div class="info-row">
                                <span class="info-label">Kullanılan</span>
                                <span class="info-value">${data.storage.used}</span>
                            </div>
                        ` : ''}
                        ${data.storage.free ? `
                            <div class="info-row">
                                <span class="info-label">Boş Alan</span>
                                <span class="info-value">${data.storage.free}</span>
                            </div>
                        ` : ''}
                        ${data.storage.usage_percent ? `
                            <div class="info-row">
                                <span class="info-label">Kullanım Oranı</span>
                                <span class="info-value">${data.storage.usage_percent}</span>
                            </div>
                        ` : ''}
                    </div>
                `;
            }

            if (data.camera && Object.keys(data.camera).length > 0) {
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">📷</div>
                            <div class="card-title">Kamera</div>
                        </div>
                        ${data.camera.status ? `
                            <div class="info-row">
                                <span class="info-label">Durum</span>
                                <span class="info-value">${data.camera.status}</span>
                            </div>
                        ` : ''}
                        ${data.camera.camera_count ? `
                            <div class="info-row">
                                <span class="info-label">Kamera Sayısı</span>
                                <span class="info-value">${data.camera.camera_count}</span>
                            </div>
                        ` : ''}
                    </div>
                `;
            }

            if (data.microphone && Object.keys(data.microphone).length > 0) {
                html += `
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">🎤</div>
                            <div class="card-title">Mikrofon</div>
                        </div>
                        <div class="info-row">
                            <span class="info-label">Durum</span>
                            <span class="info-value">${data.microphone.status}</span>
                        </div>
                    </div>
                `;
            }

            html += '</div>';
            document.getElementById('content').innerHTML = html;
        }
    </script>
</body>
</html>
"""

def run_adb(command, timeout=10):
    """Güvenli bir şekilde bir ADB komutu çalıştırır ve çıktısını döndürür."""
    try:
        full_command = f"adb {command}"
        proc = subprocess.run(
            full_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        return proc.stdout.strip(), proc.stderr.strip(), proc.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 124
    except Exception as e:
        return "", str(e), 1

def adb_available():
    out, err, rc = run_adb("devices", timeout=3)
    return rc == 0 and "List of devices attached" in out

def get_connected_device_serial():
    out, err, rc = run_adb("devices", timeout=3)
    if rc != 0:
        return None
    lines = [l.strip() for l in out.splitlines() if l.strip()]
    devices = []
    for line in lines[1:]:
        if line:
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "device":
                devices.append(parts[0])
    return devices[0] if devices else None

def get_imei():
    """IMEI bilgisini alır"""
    out, err, rc = run_adb("shell service call iphonesubinfo 1 s16 com.android.shell", timeout=5)

    if rc != 0 or not out:
        return {}

    imei_digits = []
    hex_pattern = re.findall(r'\b([0-9a-f]{8})\b', out.lower())

    for hex_val in hex_pattern:
        if hex_val in ['00000000', '0000000f', 'fffffffe']:
            continue

        part1 = hex_val[0:4]
        part2 = hex_val[4:8]

        try:
            if part1 != '0000':
                char = chr(int(part1, 16))
                if char.isdigit():
                    imei_digits.append(char)

            if part2 != '0000':
                char = chr(int(part2, 16))
                if char.isdigit():
                    imei_digits.append(char)
        except:
            pass

    imei = ''.join(imei_digits)

    if len(imei) >= 15 and imei.isdigit():
        return {"imei1": imei[:15]}

    return {}

def get_battery_info():
    """Batarya bilgilerini alır"""
    out, _, rc = run_adb("shell dumpsys battery", timeout=5)

    if rc != 0:
        return {}

    battery_data = {}
    for line in out.splitlines():
        if line.strip().startswith("level:"):
            battery_data["level"] = line.split(":")[-1].strip()
        elif line.strip().startswith("health:"):
            health_code = line.split(":")[-1].strip()
            health_map = {"2": "İyi", "3": "Aşırı Isınmış", "4": "Ölü", "5": "Aşırı Voltaj", "6": "Hata"}
            battery_data["health"] = health_map.get(health_code, "Bilinmiyor")
        elif line.strip().startswith("temperature:"):
            temp = int(line.split(":")[-1].strip()) / 10
            battery_data["temperature"] = f"{temp}°C"
        elif line.strip().startswith("voltage:"):
            voltage = int(line.split(":")[-1].strip()) / 1000
            battery_data["voltage"] = f"{voltage}V"

    cycle_count_found = False

    out_prop, _, rc_prop = run_adb("shell dumpsys batteryproperties", timeout=5)
    if rc_prop == 0:
        for line in out_prop.splitlines():
            if "cycle_count" in line:
                try:
                    count = line.split(":")[-1].strip()
                    if count.isdigit():
                        battery_data["cycle_count"] = count
                        cycle_count_found = True
                        break
                except:
                    pass

    if not cycle_count_found and "mSavedBatteryUsage:" in out:
        for line in out.splitlines():
            if "mSavedBatteryUsage:" in line:
                try:
                    usage = line.split("[")[-1].split("]")[0]
                    battery_data["cycle_count"] = usage
                    cycle_count_found = True
                    break
                except:
                    pass

    if not cycle_count_found:
        battery_data["cycle_count"] = "Desteklenmiyor"

    return battery_data

def get_camera_status():
    """Kamera durumunu kontrol eder"""
    out, _, rc = run_adb("shell dumpsys media.camera", timeout=5)

    if rc != 0:
        return {"status": "Bilinmiyor"}

    camera_data = {}

    if "Number of camera devices:" in out:
        for line in out.splitlines():
            if "Number of camera devices:" in line:
                camera_data["camera_count"] = line.split(":")[-1].strip()
                break

    if "Camera" in out and ("open" in out.lower() or "active" in out.lower()):
        camera_data["status"] = "Çalışıyor"
    else:
        camera_data["status"] = "Hazır"

    return camera_data

def get_microphone_status():
    """Mikrofon durumunu kontrol eder"""
    out, _, rc = run_adb("shell dumpsys audio", timeout=5)

    if rc != 0:
        return {"status": "Bilinmiyor"}

    mic_data = {}

    if "active" in out.lower() and "record" in out.lower():
        mic_data["status"] = "Aktif"
    else:
        mic_data["status"] = "Hazır"

    return mic_data

def get_screen_info():
    """Ekran bilgilerini alır"""
    out, _, rc = run_adb("shell dumpsys display", timeout=5)

    if rc != 0:
        return {}

    screen_data = {}

    resolution_match = re.search(r'(\d{3,4})\s*x\s*(\d{3,4})', out)
    if resolution_match:
        screen_data["resolution"] = f"{resolution_match.group(1)}x{resolution_match.group(2)}"

    if "mScreenState=ON" in out or "state=ON" in out:
        screen_data["status"] = "Açık"
    elif "mScreenState=OFF" in out or "state=OFF" in out:
        screen_data["status"] = "Kapalı"
    else:
        screen_data["status"] = "Bilinmiyor"

    brightness_out, _, brightness_rc = run_adb("shell settings get system screen_brightness", timeout=3)
    if brightness_rc == 0 and brightness_out.strip().isdigit():
        screen_data["brightness"] = brightness_out.strip()
    else:
        brightness_match = re.search(r'mBrightness[=:](\d+)', out)
        if brightness_match:
            screen_data["brightness"] = f"{brightness_match.group(1)}"
        else:
            screen_data["brightness"] = "Bilinmiyor"

    return screen_data

def get_storage_info():
    """Depolama bilgilerini alır"""
    out, _, rc = run_adb("shell df -h /data", timeout=5)

    if rc != 0:
        return {}

    storage_data = {}
    lines = out.splitlines()

    if len(lines) >= 2:
        parts = lines[1].split()
        if len(parts) >= 6:
            storage_data["total"] = parts[1]
            storage_data["used"] = parts[2]
            storage_data["free"] = parts[3]
            storage_data["usage_percent"] = parts[4]

    return storage_data

def get_ram_info():
    """RAM bilgilerini alır"""
    out, _, rc = run_adb("shell cat /proc/meminfo", timeout=5)

    if rc != 0:
        return {}

    ram_data = {}

    for line in out.splitlines():
        if "MemTotal:" in line:
            total_kb = int(line.split()[1])
            ram_data["total"] = f"{total_kb / 1024 / 1024:.2f} GB"
        elif "MemAvailable:" in line:
            available_kb = int(line.split()[1])
            ram_data["available"] = f"{available_kb / 1024 / 1024:.2f} GB"
        elif "MemFree:" in line:
            free_kb = int(line.split()[1])
            ram_data["free"] = f"{free_kb / 1024 / 1024:.2f} GB"

    return ram_data

def parse_getprop(keys=None):
    """getprop bilgilerini parse eder"""
    result = {}
    if keys:
        for k in keys:
            out, err, rc = run_adb(f"shell getprop {shlex.quote(k)}", timeout=3)
            result[k] = out if rc == 0 else None
    else:
        out, err, rc = run_adb("shell getprop", timeout=6)
        if rc == 0:
            for line in out.splitlines():
                if "]:" in line:
                    try:
                        left, right = line.split("]:", 1)
                        key = left.strip().lstrip("[").rstrip("]")
                        val = right.strip().lstrip("[").rstrip("]")
                        result[key] = val
                    except:
                        pass
    return result

@app.route("/")
def index():
    """Ana sayfa - HTML şablonunu döndür"""
    return HTML_TEMPLATE

@app.route("/info", methods=["GET"])
def info():
    """Telefon bilgilerini JSON olarak döndür"""
    if not adb_available():
        return jsonify({"error": "ADB bulunamadı veya çalışmıyor."}), 500

    device = get_connected_device_serial()
    if not device:
        return jsonify({"error": "Bağlı cihaz bulunamadı."}), 404

    props = parse_getprop([
        "ro.product.brand", "ro.product.model", "ro.serialno",
        "ro.build.version.release", "ro.build.version.sdk"
    ])

    battery_info = get_battery_info()
    camera_info = get_camera_status()
    mic_info = get_microphone_status()
    screen_info = get_screen_info()
    storage_info = get_storage_info()
    ram_info = get_ram_info()
    imei_info = get_imei()

    result = {
        "device": {
            "serial": device,
            "brand": props.get("ro.product.brand", "Bilinmiyor"),
            "model": props.get("ro.product.model", "Bilinmiyor"),
            "android_version": props.get("ro.build.version.release", "Bilinmiyor")
        },
        "imei": imei_info,
        "battery": battery_info,
        "camera": camera_info,
        "microphone": mic_info,
        "screen": screen_info,
        "storage": storage_info,
        "ram": ram_info
    }

    return jsonify(result)

if __name__ == "__main__":
    print("📱 Telefon bilgi sistemi başlatılıyor...")
    print("🌐 Tarayıcıdan http://127.0.0.1:5002 adresine git")
    app.run(debug=True, host="127.0.0.1", port=5002, use_reloader=False)
