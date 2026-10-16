import sys
import io

# Windows konsol encoding sorununu çöz
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')



from flask import Flask, render_template_string, jsonify
import threading
import time
import pygame
import os

# Önce inputs kütüphanesini dene (XInput için)
try:
    from inputs import get_gamepad, devices
    USE_INPUTS = True
    print("✅ 'inputs' kütüphanesi yüklendi (XInput modu mevcut)")
except ImportError:
    USE_INPUTS = False
    print("⚠️  'inputs' kütüphanesi bulunamadı (Sadece PyGame/DirectInput modu kullanılacak)")

# PyGame her durumda yüklensin (DirectInput için)
# Çevresel değişkenler, Pygame'in DirectInput ve arkaplan olaylarını daha iyi işlemesine yardımcı olur.
os.environ['SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS'] = '1'
os.environ['SDL_XINPUT_ENABLED'] = '1' # SDL'in XInput desteğini zorla
pygame.init()
pygame.joystick.init()

app = Flask(__name__)

# Kontrolcü durumunu tutan global değişken
gamepad_state = {
    "connected": False,
    "name": "",
    "buttons": {},
    "axes": {},
    "hats": {},
    "controller_info": {}
}

running = True
joystick = None
current_mode = None  # "xinput" veya "directinput"

# inputs kütüphanesi için Xbox button mapping
INPUTS_BUTTON_MAP = {
    'BTN_SOUTH': 0, 'BTN_EAST': 1, 'BTN_WEST': 2, 'BTN_NORTH': 3,
    'BTN_TL': 4, 'BTN_TR': 5,
    'BTN_SELECT': 6, 'BTN_START': 7,
    'BTN_THUMBL': 8, 'BTN_THUMBR': 9,
    'BTN_MODE': 10,
    # Bazı DirectInput/Generic kodları (inputs kütüphanesini kullanırken nadiren görülür)
    'BTN_TRIGGER': 0, 'BTN_THUMB': 1, 'BTN_THUMB2': 2,
    'BTN_TOP': 3, 'BTN_TOP2': 4, 'BTN_PINKIE': 5,
    'BTN_BASE': 6, 'BTN_BASE2': 7, 'BTN_BASE3': 8,
    'BTN_BASE4': 9, 'BTN_BASE5': 10, 'BTN_BASE6': 11
}

# HTML/CSS/JavaScript şablonu
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🎮 Universal Controller Tester</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }

    /* KOYU TEMA (VARSAYILAN) */
    [data-bs-theme="dark"] body { font-family: "Segoe UI", sans-serif; background: #0e1621; color: #e0e0e0; padding: 20px; }
    [data-bs-theme="dark"] .header h1 { color: #107c10; text-shadow: 0 0 20px rgba(16, 124, 16, 0.5); }
    [data-bs-theme="dark"] .gamepad-name { color: #4cc2ff; }
    [data-bs-theme="dark"] .device-info { background: #1a1f2e; border: 2px solid #2a3f5f; }
    [data-bs-theme="dark"] .device-info-title { color: #4cc2ff; }
    [data-bs-theme="dark"] .device-info-row { border-bottom: 1px solid #2a3f5f; }
    [data-bs-theme="dark"] .device-info-label { color: #9ca3af; }
    [data-bs-theme="dark"] .device-info-value { color: #4cc2ff; }
    [data-bs-theme="dark"] .panel { background: #1a1f2e; border: 2px solid #2a3f5f; }
    [data-bs-theme="dark"] .panel-title { color: #4cc2ff; border-bottom: 2px solid #107c10; }
    [data-bs-theme="dark"] .stick { border: 4px solid #2a3f5f; background: radial-gradient(circle, #0e1621, #1a1f2e); box-shadow: inset 0 0 40px rgba(0,0,0,0.5); }
    [data-bs-theme="dark"] .stick-label { color: #4cc2ff; }
    [data-bs-theme="dark"] .stick-btn { background: #252d3d; border: 2px solid #2a3f5f; }
    [data-bs-theme="dark"] h3 { color:#4cc2ff; }
    [data-bs-theme="dark"] .dpad-btn { background: #252d3d; border: 3px solid #2a3f5f; color: #4cc2ff; }
    [data-bs-theme="dark"] .bumper { background: #252d3d; border: 3px solid #2a3f5f; color: #4cc2ff; }
    [data-bs-theme="dark"] .trigger-label { color: #4cc2ff; }
    [data-bs-theme="dark"] .trigger-bar { background: #0e1621; border: 3px solid #2a3f5f; }
    [data-bs-theme="dark"] .center-btns .center-btn { background: #252d3d; border: 3px solid #2a3f5f; }
    [data-bs-theme="dark"] .center-btn-label { color: #4cc2ff; }

    /* AÇIK TEMA AYARLARI */
    [data-bs-theme="light"] body { font-family: "Segoe UI", sans-serif; background: #f0f2f5; color: #212529; padding: 20px; }
    [data-bs-theme="light"] .header h1 { color: #107c10; text-shadow: none; }
    [data-bs-theme="light"] .panel, [data-bs-theme="light"] .device-info { background: #ffffff; border-color: #ced4da; }
    [data-bs-theme="light"] .panel-title,
    [data-bs-theme="light"] .gamepad-name,
    [data-bs-theme="light"] .device-info-title,
    [data-bs-theme="light"] .device-info-value,
    [data-bs-theme="light"] .stick-label,
    [data-bs-theme="light"] .trigger-label,
    [data-bs-theme="light"] .center-btn-label,
    [data-bs-theme="light"] h3 { color: #005a9e; }
    [data-bs-theme="light"] .device-info-row { border-bottom-color: #dee2e6; }
    [data-bs-theme="light"] .device-info-label { color: #6c757d; }
    [data-bs-theme="light"] .stick { border-color: #ced4da; background: radial-gradient(circle, #f8f9fa, #e9ecef); box-shadow: inset 0 0 10px rgba(0,0,0,0.1); }
    [data-bs-theme="light"] .dpad-btn,
    [data-bs-theme="light"] .bumper,
    [data-bs-theme="light"] .center-btn,
    [data-bs-theme="light"] .stick-btn { background: #e9ecef; border-color: #adb5bd; color: #495057; }
    [data-bs-theme="light"] .trigger-bar { background: #e9ecef; border-color: #adb5bd; }

    /* Ortak Yapısal Stiller */
    .container { max-width: 1400px; margin: 0 auto; }
    .header { text-align: center; margin-bottom: 30px; }
    .header h1 { font-size: 2.5em; margin-bottom: 15px; }
    .status { padding: 12px 30px; border-radius: 25px; font-weight: bold; font-size: 1.2em; display: inline-block; margin-bottom: 10px; }
    .status.connected { background: linear-gradient(135deg, #107c10, #0e6b0e); color: white; box-shadow: 0 0 20px rgba(16, 124, 16, 0.5); }
    .status.disconnected { background: linear-gradient(135deg, #c42b1c, #a62818); color: white; }
    .gamepad-name { font-weight: bold; font-size: 1.2em; }
    .device-info { padding: 15px; border-radius: 10px; margin: 15px auto; max-width: 600px; }
    .device-info-title { font-size: 1.1em; font-weight: bold; margin-bottom: 10px; text-align: center; }
    .device-info-row:last-child { border-bottom: none; }
    .device-info-row { display: flex; justify-content: space-between; padding: 5px 0; }
    .device-info-label { font-weight: bold; }
    .device-info-value { font-family: monospace; }
    .layout { display: grid; grid-template-columns: 1fr 1fr; gap: 30px; margin-top: 30px; }
    .panel { padding: 25px; border-radius: 16px; }
    .panel-title { font-size: 1.4em; margin-bottom: 20px; padding-bottom: 10px; text-align: center; }
    .sticks { display: flex; justify-content: space-around; gap: 30px; margin-bottom: 30px; }
    .stick-box { text-align: center; }
    .stick { width: 200px; height: 200px; border-radius: 50%; position: relative; margin: 0 auto; }
    .stick-dot { position: absolute; width: 55px; height: 55px; background: radial-gradient(circle, #107c10, #0e6b0e); border-radius: 50%; top: 50%; left: 50%; transform: translate(-50%, -50%); transition: all 0.03s linear; border: 4px solid #4cc2ff; box-shadow: 0 0 20px rgba(16, 124, 16, 0.9); }
    .stick-label { margin-top: 15px; font-weight: bold; font-size: 1.1em; }
    .stick-btn { margin-top: 10px; padding: 8px 20px; border-radius: 8px; font-size: 0.9em; transition: all 0.1s; }
    .stick-btn.active { background: #107c10; border-color: #0e6b0e; transform: scale(0.95); }
    .face-buttons { position: relative; width: 220px; height: 220px; margin: 30px auto; }
    .face-btn { position: absolute; width: 70px; height: 70px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.8em; font-weight: bold; border: 4px solid; transition: all 0.1s; cursor: pointer; }
    .face-btn.active { transform: scale(0.9); box-shadow: 0 0 30px; }
    .btn-a { bottom: 0; left: 50%; transform: translateX(-50%); background: #0e6b0e; border-color: #107c10; color: white; }
    .btn-a.active { box-shadow: 0 0 30px #107c10; }
    .btn-b { right: 0; top: 50%; transform: translateY(-50%); background: #c42b1c; border-color: #d83b2d; color: white; }
    .btn-b.active { box-shadow: 0 0 30px #c42b1c; }
    .btn-x { left: 0; top: 50%; transform: translateY(-50%); background: #0078d4; border-color: #4cc2ff; color: white; }
    .btn-x.active { box-shadow: 0 0 30px #0078d4; }
    .btn-y { top: 0; left: 50%; transform: translateX(-50%); background: #faa61a; border-color: #ffb900; color: white; }
    .btn-y.active { box-shadow: 0 0 30px #faa61a; }
    .shoulders { display: flex; justify-content: space-around; margin: 25px 0; }
    .shoulder { text-align: center; }
    .bumper { padding: 15px 35px; border-radius: 12px; font-weight: bold; font-size: 1.2em; transition: all 0.1s; }
    .bumper.active { background: #107c10; border-color: #0e6b0e; color: white; transform: scale(0.95); box-shadow: 0 0 25px #107c10; }
    .trigger-label { font-weight: bold; margin: 15px 0 8px; }
    .trigger-bar { width: 200px; height: 35px; border-radius: 18px; overflow: hidden; }
    .trigger-fill { height: 100%; background: linear-gradient(90deg, #107c10, #0e6b0e); transition: width 0.05s linear; border-radius: 15px; box-shadow: 0 0 15px rgba(16, 124, 16, 0.7); }
    .dpad { display: grid; grid-template-columns: repeat(3, 75px); grid-template-rows: repeat(3, 75px); gap: 8px; margin: 30px auto; width: fit-content; }
    .dpad-btn { display: flex; justify-content: center; align-items: center; border-radius: 12px; transition: all 0.1s; font-size: 2.2em; }
    .dpad-btn.active { background: #107c10; border-color: #0e6b0e; color: white; transform: scale(0.9); box-shadow: 0 0 25px #107c10; }
    .center-btns { display: flex; justify-content: center; gap: 50px; margin: 30px 0; }
    .center-btn { width: 90px; height: 90px; border-radius: 50%; display: flex; flex-direction: column; justify-content: center; align-items: center; transition: all 0.1s; }
    .center-btn.active { background: #107c10; border-color: #0e6b0e; transform: scale(0.95); box-shadow: 0 0 25px #107c10; }
    .center-btn-icon { font-size: 2em; }
    .center-btn-label { font-size: 0.75em; margin-top: 5px; font-weight: bold; }

    @media (max-width: 1000px) {
      .layout { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🎮 UNIVERSAL CONTROLLER TESTER</h1>
      <div id="status" class="status disconnected">Yükleniyor...</div><br>
      <div id="gamepadName" class="gamepad-name"></div>

      <div class="device-info" id="deviceInfo" style="display: none;">
        <div class="device-info-title">📋 Kontrolcü Bilgileri</div>
        <div class="device-info-row">
          <span class="device-info-label">Mod:</span>
          <span class="device-info-value" id="info-mode">-</span>
        </div>
        <div class="device-info-row">
          <span class="device-info-label">Cihaz Adı:</span>
          <span class="device-info-value" id="info-name">-</span>
        </div>
        <div class="device-info-row">
          <span class="device-info-label">Vendor ID:</span>
          <span class="device-info-value" id="info-vendor">-</span>
        </div>
        <div class="device-info-row">
          <span class="device-info-label">Product ID:</span>
          <span class="device-info-value" id="info-product">-</span>
        </div>
        <div class="device-info-row">
          <span class="device-info-label">Buton/Eksen:</span>
          <span class="device-info-value" id="info-counts">-</span>
        </div>
      </div>
    </div>

    <div class="layout">
      <div class="panel">
        <h2 class="panel-title">⬅️ SOL KONTROLLER</h2>

        <div class="sticks">
          <div class="stick-box">
            <div class="stick">
              <div class="stick-dot" id="leftStick"></div>
            </div>
            <div class="stick-label">Sol Analog</div>
            <div class="stick-btn" id="btn-l3">L3</div>
          </div>
        </div>

        <h3 style="text-align:center; margin:20px 0;">🎯 D-Pad</h3>
        <div class="dpad">
          <div></div>
          <div class="dpad-btn" id="dpad-up">▲</div>
          <div></div>
          <div class="dpad-btn" id="dpad-left">◀</div>
          <div style="background:transparent;border:none;"></div>
          <div class="dpad-btn" id="dpad-right">▶</div>
          <div></div>
          <div class="dpad-btn" id="dpad-down">▼</div>
          <div></div>
        </div>

        <div class="shoulders">
          <div class="shoulder">
            <div class="bumper" id="btn-lb">LB</div>
            <div class="trigger-label">LT</div>
            <div class="trigger-bar">
              <div class="trigger-fill" id="lt-fill"></div>
            </div>
          </div>
        </div>
      </div>

      <div class="panel">
        <h2 class="panel-title">➡️ SAĞ KONTROLLER</h2>

        <div class="sticks">
          <div class="stick-box">
            <div class="stick">
              <div class="stick-dot" id="rightStick"></div>
            </div>
            <div class="stick-label">Sağ Analog</div>
            <div class="stick-btn" id="btn-r3">R3</div>
          </div>
        </div>

        <h3 style="text-align:center; margin:20px 0;">🔘 Aksiyon Butonları</h3>
        <div class="face-buttons">
          <div class="face-btn btn-a" id="btn-a">A</div>
          <div class="face-btn btn-b" id="btn-b">B</div>
          <div class="face-btn btn-x" id="btn-x">X</div>
          <div class="face-btn btn-y" id="btn-y">Y</div>
        </div>

        <div class="shoulders">
          <div class="shoulder">
            <div class="bumper" id="btn-rb">RB</div>
            <div class="trigger-label">RT</div>
            <div class="trigger-bar">
              <div class="trigger-fill" id="rt-fill"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="center-btns">
      <div class="center-btn" id="btn-back">
        <div class="center-btn-icon">⊞</div>
        <div class="center-btn-label">VIEW</div>
      </div>
      <div class="center-btn" id="btn-start">
        <div class="center-btn-icon">☰</div>
        <div class="center-btn-label">MENU</div>
      </div>
      <div class="center-btn" id="btn-xbox">
        <div class="center-btn-icon">Ⓧ</div>
        <div class="center-btn-label">XBOX</div>
      </div>
    </div>
  </div>

  <script>
    // --- YENİ: SİSTEM TEMASINI OTOMATİK ALGILAYAN KOD ---
    document.addEventListener('DOMContentLoaded', () => {
        const doc = document.documentElement;
        const lightSchemeMediaQuery = window.matchMedia('(prefers-color-scheme: light)');

        function applyTheme(isLight) {
            // HTML etiketine tema özniteliğini ata
            doc.setAttribute('data-bs-theme', isLight ? 'light' : 'dark');
        }

        // 1. Sayfa ilk yüklendiğinde temayı uygula
        applyTheme(lightSchemeMediaQuery.matches);

        // 2. Sistem teması değiştiğinde temayı otomatik güncelle
        lightSchemeMediaQuery.addEventListener('change', (e) => applyTheme(e.matches));
    });
    // --- SCRIPT SONU ---

    // Xbox layout'una göre düğme indeks haritası
    const BUTTON_MAP = {
      0: 'btn-a', 1: 'btn-b', 2: 'btn-x', 3: 'btn-y',
      4: 'btn-lb', 5: 'btn-rb',
      6: 'btn-back', 7: 'btn-start',
      8: 'btn-l3', 9: 'btn-r3',
      10: 'btn-xbox'
    };

    function updateGamepad(data) {
      const status = document.getElementById('status');
      const nameEl = document.getElementById('gamepadName');
      const deviceInfo = document.getElementById('deviceInfo');

      if (!data.connected) {
        status.textContent = "🎮 Kontrolcü Bulunamadı";
        status.className = "status disconnected";
        nameEl.textContent = "";
        deviceInfo.style.display = "none";
        return;
      }

      status.textContent = "✅ Kontrolcü Aktif";
      status.className = "status connected";
      nameEl.textContent = data.name;

      // Cihaz bilgilerini göster
      if (data.controller_info && Object.keys(data.controller_info).length > 0) {
        deviceInfo.style.display = "block";
        document.getElementById('info-mode').textContent = data.controller_info.mode || '-';
        document.getElementById('info-name').textContent = data.controller_info.name || '-';
        document.getElementById('info-vendor').textContent = data.controller_info.vendor_id || '-';
        document.getElementById('info-product').textContent = data.controller_info.product_id || '-';
        document.getElementById('info-counts').textContent = data.controller_info.counts || '-';
      }

      // Butonları güncelle
      Object.entries(data.buttons).forEach(([idx, pressed]) => {
        const btnId = BUTTON_MAP[parseInt(idx)];
        if (btnId) {
          const el = document.getElementById(btnId);
          if (el) el.classList.toggle('active', pressed);
        }
      });

      // Analog çubuklar (Merkeze göre 72px max hareket)
      if (data.axes[0] !== undefined && data.axes[1] !== undefined) {
        const x = parseFloat(data.axes[0]) * 72;
        const y = parseFloat(data.axes[1]) * 72;
        document.getElementById('leftStick').style.transform =
          `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`;
      }

      if (data.axes[2] !== undefined && data.axes[3] !== undefined) {
        const x = parseFloat(data.axes[2]) * 72;
        const y = parseFloat(data.axes[3]) * 72;
        document.getElementById('rightStick').style.transform =
          `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))`;
      }

      // Tetikler (Tetik değerleri -1.0 ile 1.0 arasından %0-100'e dönüştürülür)
      if (data.axes[4] !== undefined) {
        const ltVal = ((parseFloat(data.axes[4]) + 1) / 2) * 100;
        document.getElementById('lt-fill').style.width = `${ltVal}%`;
      }

      if (data.axes[5] !== undefined) {
        const rtVal = ((parseFloat(data.axes[5]) + 1) / 2) * 100;
        document.getElementById('rt-fill').style.width = `${rtVal}%`;
      }

      // D-Pad (Hatlar)
      if (data.hats && data.hats['0']) {
        const [x, y] = data.hats['0'];
        document.getElementById('dpad-up').classList.toggle('active', y === 1);
        document.getElementById('dpad-down').classList.toggle('active', y === -1);
        document.getElementById('dpad-left').classList.toggle('active', x === -1);
        document.getElementById('dpad-right').classList.toggle('active', x === 1);
      }
    }

    function pollGamepad() {
      fetch('/api/gamepad')
        .then(r => r.json())
        .then(updateGamepad)
        .catch(err => {
          document.getElementById('status').textContent = "❌ Bağlantı Hatası";
          document.getElementById('status').className = "status disconnected";
        });
    }

    // 33 milisaniyede bir (yaklaşık 30 FPS) güncelle
    setInterval(pollGamepad, 33);
    pollGamepad();
  </script>
</body>
</html>
"""

def detect_input_system():
    """XInput veya DirectInput cihazı tespit eder"""

    # XInput kontrol (inputs kütüphanesi)
    if USE_INPUTS:
        try:
            if devices.gamepads:
                names = [g.name for g in devices.gamepads]
                return "xinput"
        except Exception:
             # inputs.get_gamepad() çağrılmazsa, bu blok yalnızca bir tahmin yürütür.
             pass

    # DirectInput kontrol (PyGame)
    if pygame.joystick.get_count() > 0:
        names = [pygame.joystick.Joystick(i).get_name() for i in range(pygame.joystick.get_count())]
        return "directinput"

    return None

def gamepad_loop_inputs():
    """XInput cihazları için (inputs kütüphanesi)"""
    global running, gamepad_state, current_mode

    print("🎮 XInput modu başlatıldı")
    controller_info = {}

    # inputs kütüphanesinde sürekli olarak olayları dinler
    while running:
        try:
            events = get_gamepad()

            # Eğer kontrolcü takılı değilse veya olay yoksa bekler
            if not events:
                time.sleep(0.01)
                continue

            buttons = gamepad_state["buttons"].copy()
            axes = gamepad_state["axes"].copy()
            dpad = gamepad_state["hats"].get("0", [0, 0])

            # İlk event'te cihaz bilgilerini al
            if not controller_info:
                try:
                    device = events[0].device
                    # XInput cihazları için genellikle VID/PID almak zor olabilir
                    controller_info = {
                        "mode": "XInput",
                        "name": getattr(device, 'name', 'Xbox Controller'),
                        "vendor_id": hex(getattr(device, 'vendor', 0)),
                        "product_id": hex(getattr(device, 'product', 0)),
                        "counts": "N/A (XInput)"
                    }
                except:
                    controller_info = {"mode": "XInput", "name": "Xbox Controller", "vendor_id": "N/A", "product_id": "N/A", "counts": "N/A (XInput)"}

            for event in events:
                # Button events
                if event.ev_type == 'Key':
                    btn_idx = INPUTS_BUTTON_MAP.get(event.code)
                    if btn_idx is not None:
                        buttons[btn_idx] = (event.state == 1)

                # Axis events (32768/255'e göre normalize edilir)
                elif event.ev_type == 'Absolute':
                    if event.code == 'ABS_X':
                        axes[0] = round(event.state / 32768.0, 3)
                    elif event.code == 'ABS_Y':
                        # Y eksenini ters çevir (-32768 üst, +32767 alt)
                        axes[1] = -round(event.state / 32768.0, 3)
                    elif event.code == 'ABS_RX':
                        axes[2] = round(event.state / 32768.0, 3)
                    elif event.code == 'ABS_RY':
                        # Y eksenini ters çevir
                        axes[3] = -round(event.state / 32768.0, 3)
                    elif event.code == 'ABS_Z':
                        # Sol Tetik (0-255 -> -1.0 - 1.0)
                        axes[4] = round((event.state / 255.0) * 2 - 1, 3)
                    elif event.code == 'ABS_RZ':
                        # Sağ Tetik (0-255 -> -1.0 - 1.0)
                        axes[5] = round((event.state / 255.0) * 2 - 1, 3)
                    elif event.code == 'ABS_HAT0X':
                        dpad[0] = event.state
                    elif event.code == 'ABS_HAT0Y':
                        # inputs, Y'yi normalden ters verir: Yukarı +1, Aşağı -1
                        dpad[1] = -event.state # Web arayüzü PyGame/HTML standartlarına uysun diye tekrar ters çeviriyoruz

            gamepad_state = {
                "connected": True,
                "name": controller_info.get("name", "Xbox Controller"),
                "buttons": buttons,
                "axes": axes,
                "hats": {"0": dpad},
                "controller_info": controller_info
            }

        except Exception as e:
            # Kontrolcü bağlantısı kesildi veya hata oluştu
            gamepad_state["connected"] = False
            controller_info = {}
            time.sleep(1)

def gamepad_loop_pygame():
    """DirectInput cihazları için (PyGame)"""
    global joystick, running, gamepad_state, current_mode

    print("🎮 DirectInput modu başlatıldı")
    controller_info = {}

    while running:
        try:
            # 1. Pygame olay kuyruğunu güncelle
            pygame.event.pump()

            # Kontrolcü bağlantı kontrolü
            joystick_count = pygame.joystick.get_count()

            if joystick_count == 0:
                # Bağlantı yok durumu
                if joystick is not None:
                    joystick.quit()
                    joystick = None
                    controller_info = {}

                gamepad_state["connected"] = False

                # ÖNEMLİ DÜZELTME: Joystick sistemini kapatıp tekrar açarak
                # yeni cihazları veya tekrar bağlanan cihazları bulmasını sağla.
                pygame.joystick.quit()
                pygame.joystick.init()

                time.sleep(0.5)
                continue

            # Kontrolcüyü başlat/yeniden başlat
            if joystick is None or not joystick.get_init():
                # İlk kontrolcüyü (indeks 0) al
                joystick = pygame.joystick.Joystick(0)
                joystick.init()

                # Cihaz bilgilerini al (Aynı kaldı)
                try:
                    guid = joystick.get_guid()
                    vendor_id = guid[0:4] if len(guid) >= 4 else "0000"
                    product_id = guid[4:8] if len(guid) >= 8 else "0000"

                    controller_info = {
                        "mode": "DirectInput",
                        "name": joystick.get_name(),
                        "vendor_id": f"0x{vendor_id}",
                        "product_id": f"0x{product_id}",
                        "counts": f"{joystick.get_numbuttons()}B / {joystick.get_numaxes()}A / {joystick.get_numhats()}H"
                    }
                except:
                    controller_info = {
                        "mode": "DirectInput",
                        "name": joystick.get_name(),
                        "vendor_id": "N/A",
                        "product_id": "N/A",
                        "counts": "N/A"
                    }

                print(f"\n{'='*60}")
                print(f"✅ DirectInput Cihazı Başlatıldı: {joystick.get_name()}")
                print(f"{'='*60}\n")

            # Eksenleri, Butonları ve Hatları Oku (Aynı kaldı)
            axes = {}
            for i in range(joystick.get_numaxes()):
                value = joystick.get_axis(i)
                if i in [1, 3]:
                    axes[i] = -round(value, 3)
                else:
                    axes[i] = round(value, 3)

            buttons = {i: bool(joystick.get_button(i)) for i in range(joystick.get_numbuttons())}

            hats = {}
            for i in range(joystick.get_numhats()):
                hats[str(i)] = list(joystick.get_hat(i))

            gamepad_state = {
                "connected": True,
                "name": controller_info.get("name", joystick.get_name()),
                "axes": axes,
                "buttons": buttons,
                "hats": hats,
                "controller_info": controller_info
            }

            time.sleep(0.016)

        except pygame.error:
             # Eğer pygame bir hata döndürürse (örneğin cihaz aniden sökülürse)
            if joystick is not None:
                joystick.quit()
                joystick = None
            gamepad_state["connected"] = False

            # Hata durumunda da yeniden başlatmayı zorla
            pygame.joystick.quit()
            pygame.joystick.init()

            time.sleep(1)
        except Exception:
            time.sleep(1)
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/gamepad')
def get_gamepad_data():
    return jsonify(gamepad_state)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎮 UNIVERSAL CONTROLLER TESTER")
    print("="*60)

    # Cihaz tipini tespit et
    system = detect_input_system()
    current_mode = system

    # Hangi döngüyü kullanacağımıza karar ver
    if system == "xinput" and USE_INPUTS:
        print("📍 Mod: XInput (inputs kütüphanesi)")
        gamepad_thread = threading.Thread(target=gamepad_loop_inputs, daemon=True)
    # inputs kütüphanesi yoksa veya DirectInput cihazı tespit edildiyse PyGame kullan
    elif system == "directinput" or not USE_INPUTS:
        print("📍 Mod: DirectInput (PyGame kütüphanesi)")
        gamepad_thread = threading.Thread(target=gamepad_loop_pygame, daemon=True)
    else:
        # Başlangıçta kontrolcü bulunamazsa yine de PyGame ile izle
        print("📍 Mod: İzleme (kontrolcü bekleniyor)")
        gamepad_thread = threading.Thread(target=gamepad_loop_pygame, daemon=True)

    # Gamepad okuma döngüsünü başlat
    gamepad_thread.start()

    # Flask uygulamasını çalıştır
    try:
        print("📍 Tarayıcıda açın: http://localhost:5004")
        # use_reloader=False, threading ile çakışmayı engeller.
        app.run(host='0.0.0.0', port=5004, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        # Kullanıcı Ctrl+C yaptığında yakala
        pass
    finally:
        # Uygulama kapatılırken thread'i ve PyGame'i durdur
        running = False
        if 'gamepad_thread' in locals() and gamepad_thread.is_alive():
            gamepad_thread.join(timeout=2)
        if pygame.joystick.get_init():
            pygame.quit()
        print("\nKontrolcü Test Uygulaması Kapatıldı.")
