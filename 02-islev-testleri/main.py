# -*- coding: utf-8 -*-
import sys
import os

# Windows emoji hatası çözümü (GÜNCELLENMİŞ VERSİYON)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    os.system('chcp 65001 > nul 2>&1')

# Diğer importlar
import subprocess
import time
from flask import Flask, render_template_string, jsonify
import socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Test uygulamaları ve yerel portları
sunucular = {
    os.path.join(BASE_DIR, "price_estimator.py"): 5001,
    os.path.join(BASE_DIR, "phone_info.py"): 5002,
    os.path.join(BASE_DIR, "keyboard_tester.py"): 5003,
    os.path.join(BASE_DIR, "gamepad_tester.py"): 5004,
    os.path.join(BASE_DIR, "pc_tester.py"): 5005,
    os.path.join(BASE_DIR, "headphone_tester.py"): 5006,
    os.path.join(BASE_DIR, "dead_pixel_tester.py"): 5007,
    os.path.join(BASE_DIR, "mouse_tester.py"): 5008,
    os.path.join(BASE_DIR, "touch_tester.py"): 5009,
    os.path.join(BASE_DIR, "speed_tester.py"): 5010,
    os.path.join(BASE_DIR, "typing_tester.py"): 5011,
    os.path.join(BASE_DIR, "webcam_tester.py"): 5012
}

prosesler = []
log_dosyalari = {}
sunucu_durumu = {}

def port_kullaniliyor_mu(port):
    """Port'un kullanımda olup olmadığını kontrol eder"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def sunucu_kontrol_et(dosya_adi, port):
    """Sunucu başlamadan önce gerekli kontrolleri yapar"""
    if not os.path.exists(dosya_adi):
        return False, f"Dosya bulunamadi"
    if port_kullaniliyor_mu(port):
        return False, f"Port {port} zaten kulanimda"
    return True, "OK"

print("="*60)
print("CIHAZ ANALIZ - ISLEV TESTLERI BASLATILIYOR...")
print("="*60)

for dosya_adi, port in sunucular.items():
    dosya_ismi = os.path.basename(dosya_adi)
    print(f"\n{dosya_ismi} kontrol ediliyor...")
    durum, mesaj = sunucu_kontrol_et(dosya_adi, port)

    if not durum:
        print(f"   HATA: {mesaj}")
        sunucu_durumu[dosya_ismi] = {"status": "offline", "port": port, "error": mesaj}
        continue

    log_dosyasi_adi = dosya_adi.replace('.py', '.log')
    try:
        log_dosyasi = open(log_dosyasi_adi, 'w', encoding='utf-8', buffering=1)
        log_dosyalari[dosya_adi] = log_dosyasi
        proses = subprocess.Popen(
            [sys.executable, dosya_adi],
            cwd=BASE_DIR,
            stdout=log_dosyasi,
            stderr=log_dosyasi,
            text=True,
            encoding='utf-8',
            env=os.environ.copy()
        )
        prosesler.append(proses)
        time.sleep(2)

        if proses.poll() is not None:
            print(f"   Sunucu hemen kapandi! Log: {log_dosyasi_adi}")
            sunucu_durumu[dosya_ismi] = {"status": "error", "port": port, "error": "Baslatilamadi"}
        else:
            print(f"   Basariyla baslatildi (Port: {port})")
            sunucu_durumu[dosya_ismi] = {"status": "online", "port": port}
    except Exception as e:
        print(f"   Baslatma hatasi: {e}")
        sunucu_durumu[dosya_ismi] = {"status": "error", "port": port, "error": str(e)}

print("\n" + "="*60)
print("ANA PANEL HAZIRLANIYOR...")
print("="*60)

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 İşlev Testleri - Ana Panel</title>
    <style>
        :root {
            /* Aydınlık Tema (Varsayılan) */
            --bg-main: #f8f9fa;
            --bg-sidebar: #fafafa;
            --bg-card: #ffffff;
            --bg-hover: #e9e9e9;
            --bg-toggle-btn: #ffffff;

            --text-primary: #212529;
            --text-secondary: #6c757d;
            --text-on-accent: #ffffff;

            --accent-color: #007bff;
            --accent-shadow: rgba(0, 123, 255, 0.3);

            --border-color: #ddd;
            --shadow-color: rgba(0,0,0,0.05);
            --shadow-color-hover: rgba(0,0,0,0.08);
            --shadow-toggle-btn: rgba(0,0,0,0.1);

            --spinner-track: #f3f3f3;

            --badge-online-bg: #d1fae5;
            --badge-online-text: #065f46;
            --badge-offline-bg: #fee2e2;
            --badge-offline-text: #991b1b;
            --badge-error-bg: #fef3c7;
            --badge-error-text: #92400e;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                /* Karanlık Tema (Otomatik) */
                --bg-main: #121212;
                --bg-sidebar: #1e1e1e;
                --bg-card: #2a2a2a;
                --bg-hover: #333333;
                --bg-toggle-btn: #2a2a2a;

                --text-primary: #f0f0f0;
                --text-secondary: #adb5bd;
                --text-on-accent: #ffffff;

                --accent-color: #0099ff; /* Daha parlak mavi */
                --accent-shadow: rgba(0, 153, 255, 0.3);

                --border-color: #444;
                --shadow-color: rgba(0,0,0,0.2);
                --shadow-color-hover: rgba(0,0,0,0.3);
                --shadow-toggle-btn: rgba(0,0,0,0.3);

                --spinner-track: #444;

                --badge-online-bg: #065f46;
                --badge-online-text: #d1fae5;
                --badge-offline-bg: #991b1b;
                --badge-offline-text: #fee2e2;
                --badge-error-bg: #92400e;
                --badge-error-text: #fef3c7;
            }
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg-main);
            color: var(--text-primary);
            min-height: 100vh;
        }

        .sidebar-toggle {
            position: fixed;
            top: 15px;
            left: 15px;
            font-size: 28px;
            background: var(--bg-toggle-btn);
            border: 1px solid var(--border-color);
            cursor: pointer;
            color: var(--accent-color);
            z-index: 2000;
            border-radius: 8px;
            padding: 5px 12px;
            box-shadow: 0 4px 10px var(--shadow-toggle-btn);
            transition: all 0.3s ease-in-out;
        }

        .sidebar-toggle:hover {
            background: var(--bg-hover);
            transform: scale(1.05);
        }

        body.fullscreen-mode .sidebar-toggle {
            opacity: 0.5;
        }
        body.fullscreen-mode .sidebar-toggle:hover {
            opacity: 1.0;
        }

        .sidebar {
            position: fixed;
            left: 0;
            top: 0;
            width: 280px;
            height: 100vh;
            background: var(--bg-sidebar);
            padding: 80px 20px 20px 20px;
            box-shadow: 5px 0 25px var(--shadow-color);
            z-index: 1000;
            overflow-y: auto;
            transition: transform 0.3s ease-in-out;
        }

        .logo {
            text-align: center;
            padding: 20px 0;
            border-bottom: 2px solid var(--accent-color);
            margin-bottom: 30px;
        }

        .logo h1 {
            color: var(--accent-color);
            font-size: 24px;
            margin-bottom: 5px;
        }

        .logo p {
            color: var(--text-secondary);
            font-size: 12px;
        }

        .nav-btn {
            width: 100%;
            padding: 15px 20px;
            margin: 10px 0;
            background: transparent;
            border: none;
            border-radius: 10px;
            color: var(--text-primary);
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 15px;
            text-align: left;
        }

        .nav-btn:hover {
            background: var(--bg-hover);
            transform: translateX(5px);
        }

        .nav-btn.active {
            background: var(--accent-color);
            color: var(--text-on-accent);
            box-shadow: 0 4px 15px var(--accent-shadow);
        }

        .nav-icon {
            font-size: 24px;
        }

        .main-content {
            position: relative;
            z-index: 1;
            margin-left: 280px;
            padding: 80px 40px 40px 40px;
            min-height: 100vh;
            transition: all 0.3s ease-in-out;
        }

        .header {
            background: var(--bg-card);
            padding: 20px 30px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px var(--shadow-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s ease-in-out;
        }

        .header h2 {
            color: var(--accent-color);
            font-size: 32px;
            margin-bottom: 10px;
        }

        .header p {
            color: var(--text-secondary);
            font-size: 16px;
        }

        /* GÜNCELLENDİ: Kartlar tekrar büyütüldü (küçük kareler iptal) */
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); /* Min genişlik büyüdü */
            gap: 25px; /* Boşluklar büyüdü */
        }

        .service-card {
            background: var(--bg-card);
            border-radius: 20px; /* Köşe yuvarlaklığı arttı */
            padding: 30px; /* İç dolgu arttı */
            box-shadow: 0 10px 30px var(--shadow-color); /* Gölge arttı */
            transition: transform 0.3s, box-shadow 0.3s;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            /* min-height kaldırıldı, içerik belirlesin */
        }

        .service-card:hover {
            transform: translateY(-5px); /* Hover efekti arttı */
            box-shadow: 0 15px 40px var(--shadow-color-hover); /* Hover gölge arttı */
        }

        .card-header {
            display: flex;
            align-items: center;
            gap: 15px; /* Boşluk arttı */
            margin-bottom: 20px; /* Boşluk arttı */
            padding-bottom: 15px; /* Boşluk arttı */
            border-bottom: 3px solid var(--accent-color); /* Çizgi kalınlığı arttı */
        }

        .card-icon {
            font-size: 40px; /* İkon boyutu arttı */
        }

        .card-title {
            font-size: 20px; /* Başlık boyutu arttı */
            color: var(--accent-color);
            font-weight: bold;
        }

        .card-desc {
            color: var(--text-secondary);
            margin-bottom: 20px; /* Boşluk arttı */
            font-size: 14px; /* Font boyutu arttı */
            line-height: 1.5;
            flex-grow: 1;
        }

        .info-row {
            display: flex;
            justify-content: space-between;
            padding: 12px 0; /* Boşluk arttı */
            border-bottom: 1px solid var(--border-color);
            font-size: 14px; /* Font boyutu arttı */
        }

        .info-row:last-child {
            border-bottom: none;
        }

        .info-label {
            color: var(--text-secondary);
            font-weight: 500;
        }

        .info-value {
            font-weight: bold;
            color: var(--text-primary);
        }

        .status-badge {
            display: inline-block;
            padding: 5px 12px; /* Boşluk arttı */
            border-radius: 15px; /* Yuvarlaklık arttı */
            font-size: 12px; /* Font boyutu arttı */
            font-weight: bold;
        }
        /* (badge renkleri değişmedi) */
        .badge-online { background: var(--badge-online-bg); color: var(--badge-online-text); }
        .badge-offline { background: var(--badge-offline-bg); color: var(--badge-offline-text); }
        .badge-error { background: var(--badge-error-bg); color: var(--badge-error-text); }

        .action-btn {
            width: 100%;
            padding: 12px; /* Boşluk arttı */
            background: var(--accent-color);
            color: var(--text-on-accent);
            border: none;
            border-radius: 10px; /* Yuvarlaklık arttı */
            font-size: 14px; /* Font boyutu arttı */
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            margin-top: 15px; /* Boşluk arttı */
        }

        .action-btn:hover:not(:disabled) {
            transform: translateY(-2px); /* Hover efekti arttı */
            box-shadow: 0 6px 20px var(--accent-shadow); /* Hover gölge arttı */
        }

        .action-btn:disabled { background: #ccc; cursor: not-allowed; opacity: 0.6; }

        .refresh-btn {
            background: var(--accent-color);
            color: var(--text-on-accent);
            border: none;
            padding: 12px 30px; /* Boşluklar büyüdü */
            border-radius: 10px; /* Yuvarlaklık büyüdü */
            font-size: 14px; /* Font büyüdü */
            font-weight: bold;
            cursor: pointer;
            box-shadow: 0 4px 15px var(--accent-shadow); /* Gölge büyüdü */
            transition: all 0.3s;
            white-space: nowrap;
        }

        .refresh-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px var(--accent-shadow);
        }

        .loading {
            text-align: center;
            padding: 60px; /* Boşluk arttı */
            background: var(--bg-card);
            border-radius: 20px; /* Yuvarlaklık arttı */
            box-shadow: 0 10px 30px var(--shadow-color);
        }

        .spinner {
            border: 5px solid var(--spinner-track); /* Kalınlık arttı */
            border-top: 5px solid var(--accent-color);
            width: 60px; /* Boyut arttı */
            height: 60px; /* Boyut arttı */
            animation: spin 1s linear infinite;
            margin: 0 auto 20px; /* Boşluk arttı */
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* GÜNCELLENDİ: Ana sayfa istatistik kartları için yeni stiller */
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }

        .stat-card {
            background: var(--bg-card);
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 8px 20px var(--shadow-color);
            transition: transform 0.3s, box-shadow 0.3s;
        }

        .stat-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 10px 25px var(--shadow-color-hover);
        }

        .stat-card-number {
            font-size: 40px;
            font-weight: bold;
            color: var(--accent-color);
            margin-bottom: 10px;
        }

        .stat-card-label {
            font-size: 14px;
            color: var(--text-secondary);
        }

        /* Sidebar Kapanma CSS'i */
        body.sidebar-collapsed .sidebar {
            transform: translateX(-280px);
        }

        body.sidebar-collapsed .main-content {
            margin-left: 0;
        }

        /* Fullscreen Iframe Modu CSS'i */
        body.fullscreen-mode .header {
            display: none;
        }

        body.fullscreen-mode .main-content {
            margin-left: 0;
            padding: 0;
            height: 100vh;
        }

        @media (max-width: 768px) {
            .sidebar { width: 70px; }
            .nav-btn span:last-child { display: none; }
            .main-content { margin-left: 70px; padding: 80px 20px 20px 20px; }
            .logo h1 { font-size: 16px; }
            .logo p { display: none; }
            .header h2 { font-size: 24px; }
            .services-grid { grid-template-columns: 1fr; }
            body.sidebar-collapsed .sidebar { transform: translateX(-70px); }
        }
    </style>
</head>
<body>
    <button class="sidebar-toggle" onclick="toggleSidebar()">☰</button>

    <div class="sidebar">
        <div class="logo">
            <h1>🎯 İŞLEV TESTLERİ</h1>
            <p>Ana Kontrol Paneli</p>
        </div>

        <button class="nav-btn active" onclick="loadPage('home', event)">
            <span class="nav-icon">🏠</span>
            <span>Ana Sayfa</span>
        </button>
        <button class="nav-btn" onclick="loadPage('services', event)">
            <span class="nav-icon">🔧</span>
            <span>Hizmetler</span>
        </button>
        <button class="nav-btn" onclick="loadPage('phone-defect', event)">
            <span class="nav-icon">📱</span>
            <span>Telefon Değerlendir</span>
        </button>
        <button class="nav-btn" onclick="loadPage('phone-info', event)">
            <span class="nav-icon">📊</span>
            <span>Telefon Bilgileri</span>
        </button>
        <button class="nav-btn" onclick="loadPage('keyboard', event)">
            <span class="nav-icon">⌨️</span>
            <span>Klavye Testi</span>
        </button>
        <button class="nav-btn" onclick="loadPage('gamepad', event)">
            <span class="nav-icon">🎮</span>
            <span>Gamepad Testi</span>
        </button>
        <button class="nav-btn" onclick="loadPage('hardware', event)">
            <span class="nav-icon">💻</span>
            <span>Donanım Paneli</span>
        </button>
        <button class="nav-btn" onclick="loadPage('headphone', event)">
            <span class="nav-icon">🎧</span>
            <span>Kulaklık/Ses Testi</span>
        </button>
        <button class="nav-btn" onclick="loadPage('dead-pixel', event)">
            <span class="nav-icon">⬛</span>
            <span>Ölü Piksel Testi</span>
        </button>
        <button class="nav-btn" onclick="loadPage('mouse', event)">
            <span class="nav-icon">🖱️</span>
            <span>Mouse Testi</span>
        </button>
        <button class="nav-btn" onclick="loadPage('touch', event)">
            <span class="nav-icon">👆</span>
            <span>Dokunmatik Testi</span>
        </button>
        <button class="nav-btn" onclick="loadPage('speed', event)">
            <span class="nav-icon">⚡</span>
            <span>Hız Testi</span>
        </button>
        <button class="nav-btn" onclick="loadPage('typing', event)">
            <span class="nav-icon">✍️</span>
            <span>Yazma Hızı Testi</span>
        </button>
        <button class="nav-btn" onclick="loadPage('webcam', event)">
            <span class="nav-icon">📸</span>
            <span>Webcam Testi</span>
        </button>
        <button class="nav-btn" onclick="loadPage('help', event)">
            <span class="nav-icon">❓</span>
            <span>Yardım</span>
        </button>
    </div>

    <div class="main-content">
        <div class="header">
            <div>
                <h2 id="pageTitle">İşlev Testleri</h2>
                <p id="pageDesc">Tüm test hizmetlerinizi yönetin</p>
            </div>
            <button class="refresh-btn" onclick="refreshPage()">🔄 Yenile</button>
        </div>

        <div id="pageContent"></div>
    </div>

    <script>
        const pages = {
            'home': { title: '🎯 İşlev Testleri', desc: 'Tüm test hizmetlerini tek yerden yönetin', render: renderHome },
            'services': { title: '🔧 Hizmetler', desc: 'Mevcut test hizmetlerini ve durumlarını görüntüleyin', render: renderServices },
            'phone-defect': { title: '📱 Telefon Değerlendirme', desc: 'Ekran kusurlarını tespit edin ve fiyat tahmini alın', url: 'http://localhost:5001', port: 5001 },
            'phone-info': { title: '📊 Telefon Bilgileri', desc: 'ADB ile bağlı cihazın teknik özelliklerini görün', url: 'http://localhost:5002', port: 5002 },
            'keyboard': { title: '⌨️ Klavye Testi', desc: 'Klavyenizdeki tüm tuşları test edin', url: 'http://localhost:5003', port: 5003 },
            'gamepad': { title: '🎮 Gamepad Testi', desc: 'Xbox/PlayStation kontrolcülerinizi test edin', url: 'http://localhost:5004', port: 5004 },
            'hardware': { title: '💻 Donanım Paneli', desc: 'Bilgisayarınızın donanım durumunu izleyin', url: 'http://localhost:5005', port: 5005 },
            'headphone': { title: '🎧 Kulaklık/Ses Testi', desc: 'Mikrofon ve hoparlör testleri (Not: HTTPS gerekebilir!)', url: 'http://localhost:5006', port: 5006 },
            'dead-pixel': { title: '⬛ Ölü Piksel Testi', desc: 'Ekranınızı ölü/sıkışmış pikseller için test edin', url: 'http://localhost:5007', port: 5007 },
            'mouse': { title: '🖱️ Mouse Testi', desc: 'Mouse butonlarını, tekerleği ve hızı test edin', url: 'http://localhost:5008', port: 5008 },
            'touch': { title: '👆 Dokunmatik Testi', desc: 'Dokunmatik ekran veya trackpad performansını test edin', url: 'http://localhost:5009', port: 5009 },
            'speed': { title: '⚡ Hız Testi', desc: 'İnternet bağlantı hızınızı test edin', url: 'http://localhost:5010', port: 5010 },
            'typing': { title: '✍️ Yazma Hızı Testi', desc: 'Dakikadaki kelime sayınızı (WPM) ölçün', url: 'http://localhost:5011', port: 5011 },
            'webcam': { title: '📸 Webcam Testi', desc: 'Kameranızın görüntü ve mikrofon kalitesini kontrol edin (Not: HTTPS gerekebilir!)', url: 'https://localhost:5012', port: 5012 },
            'help': { title: '❓ Yardım', desc: 'Sıkça sorulan sorular ve rehber', render: renderHelp }
        };

        let currentPage = 'home';

        function toggleSidebar() {
            document.body.classList.toggle('sidebar-collapsed');
        }

        function loadPage(pageId, event) {
            const page = pages[pageId];
            if (!page) return;

            currentPage = pageId;
            const body = document.body;

            if (!page.url) {
                document.getElementById('pageTitle').textContent = page.title;
                document.getElementById('pageDesc').textContent = page.desc;
            }

            document.querySelectorAll('.nav-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            if (event && event.target) {
                event.target.closest('.nav-btn').classList.add('active');
            } else {
                const homeButton = document.querySelector(`.nav-btn[onclick*="loadPage('${pageId}')"]`);
                if (homeButton) homeButton.classList.add('active');
            }

            const content = document.getElementById('pageContent');

            if (page.url) {
                body.classList.add('fullscreen-mode');
                body.classList.add('sidebar-collapsed');

                content.innerHTML = `
                    <div style="width: 100%; height: 100vh; overflow: hidden; background: #000;">
                        <iframe src="${page.url}"
                        allow="camera; microphone"
                        style="width: 100%; height: 100%; border: none;"></iframe>
                    </div>
                `;
            } else if (page.render) {
                body.classList.remove('fullscreen-mode');

                content.innerHTML = '<div class="loading"><div class="spinner"></div><p>Yükleniyor...</p></div>';

                setTimeout(() => {
                    if (pageId === 'services') {
                        content.innerHTML = `<div id="servicesGrid" class="services-grid"></div>`;
                        loadServices();
                    } else {
                        content.innerHTML = page.render();
                    }
                }, 300);
            }
        }

        function renderHome() {
            /* GÜNCELLENDİ: Ana sayfa istatistik kartları değiştirildi */
            return `
                <div style="background: var(--bg-card); padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 10px 30px var(--shadow-color);">
                    <div style="font-size: 80px; margin-bottom: 20px;">🎯</div>
                    <h2 style="color: var(--accent-color); margin-bottom: 15px; font-size: 28px;">İşlev Testlerine Hoş Geldiniz</h2>
                    <p style="color: var(--text-secondary); font-size: 16px; margin-bottom: 30px;">
                        Sol menüden istediğiniz sayfayı seçerek başlayın
                    </p>

                    <div class="stat-grid">
                        <div class="stat-card">
                            <div class="stat-card-number">12</div>
                            <div class="stat-card-label">Aktif Hizmet</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-card-number">∞</div>
                            <div class="stat-card-label">Test Kapasitesi</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-card-number">24/7</div>
                            <div class="stat-card-label">Hizmet Saati</div>
                        </div>
                    </div>
                </div>
            `;
        }

        function renderServices() {
            return `<div id="servicesGrid" class="services-grid">
                        <div class="loading"><div class="spinner"></div><p>Hizmet Durumları Yükleniyor...</p></div>
                    </div>`;
        }

        function renderHelp() {
            return `
                <div style="background: var(--bg-card); padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px var(--shadow-color);">
                    <h3 style="color: var(--accent-color); margin-bottom: 20px; font-size: 22px;">📖 Yardım & Rehber</h3>

                    <div style="margin-bottom: 30px;">
                        <h4 style="color: var(--text-primary); margin-bottom: 10px;">❓ İşlev Testlerini Nasıl Kullanırım?</h4>
                        <p style="color: var(--text-secondary); line-height: 1.6;">
                            Sol menüden test etmek istediğiniz hizmeti seçin. Her hizmet, ilgili sunucuya bağlanacak ve test aracını tam ekran olarak gösterecektir.<br>
                            Ana sayfaya dönmek veya başka bir testi seçmek için sol üstteki <strong>☰</strong> ikonuna basarak menüyü açabilirsiniz.
                        </p>
                    </div>

                    <div style="margin-bottom: 30px;">
                        <h4 style="color: var(--text-primary); margin-bottom: 10px;">📱 Mevcut Test Hizmetleri (Toplam 12)</h4>
                        <ul style="list-style: disc; color: var(--text-secondary); padding-left: 20px;">
                            <li style="padding: 5px 0;"><strong>📱 Telefon Değerlendirme:</strong> Ekran kusurlarını tespit edin</li>
                            <li style="padding: 5px 0;"><strong>📊 Telefon Bilgileri:</strong> Cihaz detaylarını görüntüleyin</li>
                            <li style="padding: 5px 0;"><strong>⌨️ Klavye Testi:</strong> Tüm tuşları test edin</li>
                            <li style="padding: 5px 0;"><strong>🎮 Gamepad Testi:</strong> Kontrolcü butonlarını test edin</li>
                            <li style="padding: 5px 0;"><strong>💻 Donanım Paneli:</strong> PC durumunu izleyin</li>
                            <li style="padding: 5px 0;"><strong>🎧 Kulaklık/Ses Testi:</strong> Mikrofon ve hoparlör testleri **(HTTPS)**</li>
                            <li style="padding: 5px 0;"><strong>⬛ Ölü Piksel Testi:</strong> Ekranınızı ölü/sıkışmış pikseller için test edin</li>
                            <li style="padding: 5px 0;"><strong>🖱️ Mouse Testi:</strong> Mouse butonlarını, tekerleği ve hızı test edin</li>
                            <li style="padding: 5px 0;"><strong>👆 Dokunmatik Testi:</strong> Dokunmatik ekran/trackpad performansını test edin</li>
                            <li style="padding: 5px 0;"><strong>⚡ Hız Testi:</strong> İnternet bağlantı hızınızı test edin</li>
                            <li style="padding: 5px 0;"><strong>✍️ Yazma Hızı Testi:</strong> Dakikadaki kelime sayınızı (WPM) ölçün</li>
                            <li style="padding: 5px 0;"><strong>📸 Webcam Testi:</strong> Kameranızın görüntü ve mikrofon kalitesini kontrol edin **(HTTPS)**</li>
                            </ul>
                    </div>

                    <div style="background: var(--bg-main); padding: 20px; border-radius: 10px; border-left: 4px solid var(--accent-color);">
                        <p style="color: var(--text-secondary); font-size: 14px;">
                            <strong>💡 İpucu:</strong> Kamera ve Mikrofon kullanan servisler (Kulaklık/Webcam) için tarayıcılar <strong>HTTPS</strong> bağlantısı gerektirebilir.
                        </p>
                    </div>
                </div>
            `;
        }

        async function loadServices() {
            const servicesGrid = document.getElementById('servicesGrid');
            if (!servicesGrid) return;

            servicesGrid.innerHTML = '<div class="loading"><div class="spinner"></div><p>Hizmet Durumları Alınıyor...</p></div>';

            try {
                const response = await fetch('/status');
                const data = await response.json();

                let html = '';

                const serviceInfo = {
                    'price_estimator.py': { icon: '📱', title: 'Telefon Değerlendirme', desc: 'Ekran kusurlarını tespit edin', pageId: 'phone-defect' },
                    'phone_info.py': { icon: '📊', title: 'Telefon Bilgileri', desc: 'Cihaz detaylarını görüntüleyin', pageId: 'phone-info' },
                    'keyboard_tester.py': { icon: '⌨️', title: 'Klavye Testi', desc: 'Tüm tuşları test edin', pageId: 'keyboard' },
                    'gamepad_tester.py': { icon: '🎮', title: 'Gamepad Testi', desc: 'Kontrolcü butonlarını test edin', pageId: 'gamepad' },
                    'pc_tester.py': { icon: '💻', title: 'Donanım Paneli', desc: 'Bilgisayarınızın donanım durumunu izleyin', pageId: 'hardware' },
                    'headphone_tester.py': { icon: '🎧', title: 'Kulaklık/Ses Testi', desc: 'Mikrofon ve hoparlör testleri (HTTPS gerekebilir)', pageId: 'headphone' },
                    'dead_pixel_tester.py': { icon: '⬛', title: 'Ölü Piksel Testi', desc: 'Ekranınızı ölü/sıkışmış pikseller için test edin', pageId: 'dead-pixel' },
                    'mouse_tester.py': { icon: '🖱️', title: 'Mouse Testi', desc: 'Mouse butonlarını, tekerleği ve hızı test edin', pageId: 'mouse' },
                    'touch_tester.py': { icon: '👆', title: 'Dokunmatik Testi', desc: 'Dokunmatik ekran veya trackpad performansını test edin', pageId: 'touch' },
                    'speed_tester.py': { icon: '⚡', title: 'Hız Testi', desc: 'İnternet bağlantı hızınızı test edin', pageId: 'speed' },
                    'typing_tester.py': { icon: '✍️', title: 'Yazma Hızı Testi', desc: 'Dakikadaki kelime sayınızı (WPM) ölçün', pageId: 'typing' },
                    'webcam_tester.py': { icon: '📸', title: 'Webcam Testi', desc: 'Kameranızın görüntü ve mikrofon kalitesini kontrol edin (HTTPS gerekebilir)', pageId: 'webcam' }
                };

                for (const [filename, status] of Object.entries(data)) {
                    const info = serviceInfo[filename] || { icon: '📦', title: filename, desc: 'Test servisi', pageId: null };
                    const isOnline = status.status === 'online';
                    const statusText = status.status === 'online' ? 'Çalışıyor' : (status.status === 'offline' ? 'Kapalı' : 'Hata');
                    const badgeClass = status.status === 'online' ? 'badge-online' : (status.status === 'offline' ? 'badge-offline' : 'badge-error');

                    const actionButton = isOnline
                        ? `<button class="action-btn" onclick="loadPage('${info.pageId}', event)">🚀 Testi Başlat</button>`
                        : `<button class="action-btn" disabled>❌ Offline</button>`;

                    html += `
                        <div class="service-card">
                            <div> <div class="card-header">
                                    <div class="card-icon">${info.icon}</div>
                                    <div class="card-title">${info.title}</div>
                                </div>
                                <p class="card-desc">${info.desc}</p>
                            </div>
                            <div> <div class="info-row">
                                    <span class="info-label">Durum</span>
                                    <span class="status-badge ${badgeClass}">${statusText}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Port</span>
                                    <span class="info-value">:${status.port}</span>
                                </div>
                                ${status.error ? `
                                    <div class="info-row">
                                        <span class="info-label">Hata</span>
                                        <span class="info-value" style="font-size: 11px; color: var(--badge-offline-text);">${status.error}</span>
                                    </div>
                                ` : ''}
                                ${actionButton}
                            </div>
                        </div>
                    `;
                }

                servicesGrid.innerHTML = html;
            } catch (error) {
                servicesGrid.innerHTML = `<p style="color: #ef4444; background: var(--bg-card); padding: 20px; border-radius: 10px; box-shadow: 0 5px 15px var(--shadow-color);">Hata: Hizmet durumları yüklenemedi: ${error.message}</p>`;
            }
        }

        function refreshPage() {
            if (currentPage === 'services') {
                loadServices();
            } else if (pages[currentPage] && pages[currentPage].render) {
                loadPage(currentPage);
            } else {
                loadPage(currentPage);
            }
        }

        window.addEventListener('load', () => {
            loadPage('home');
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/status')
def status():
    return_status = {}
    for dosya_yolu, durum in sunucu_durumu.items():
        dosya_adi = os.path.basename(dosya_yolu)
        current_status = durum.copy() # Kopyasını alarak çalış

        if current_status['status'] == 'online':
            if not port_kullaniliyor_mu(current_status['port']):
                current_status['status'] = 'offline'
                # Ana sözlükteki durumu da güncelle
                sunucu_durumu[dosya_yolu]['status'] = 'offline'

                for p in prosesler:
                    if os.path.basename(p.args[1]) == dosya_adi and p.poll() is None:
                        try:
                            p.terminate()
                            p.wait(timeout=1)
                        except:
                            p.kill()
                        break
        return_status[dosya_adi] = current_status

    return jsonify(return_status)

if __name__ == '__main__':
    try:
        print("\n" + "="*60)
        print("Ana panel baslatiliyor...")
        print("="*60)
        print("\nTarayicinizda su adresi acin:")
        print("   http://localhost:5000")
        print("\nKapatmak icin CTRL+C tuslayin")
        print("="*60 + "\n")

        app.run(port=5000, debug=False, host='127.0.0.1')

    except KeyboardInterrupt:
        print("\n\nKullanici tarafindan durduruldu...")
    except Exception as e:
        print(f"\nKRITIK HATA: {e}")
    finally:
        print("\nTum sunucular kapatiliyor...")
        for p in prosesler:
            try:
                p.terminate()
                p.wait(timeout=3)
            except:
                p.kill()

        for f in log_dosyalari.values():
            try:
                f.close()
            except:
                pass

        print("Kapatildi.")
