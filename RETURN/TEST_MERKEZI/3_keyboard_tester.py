import sys
import io

# Windows konsol encoding sorununu çöz
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')


"""
Klavye Test Uygulaması - Flask Backend (Otomatik Tema + Temiz Kontrol Menüsü)
"""

from flask import Flask, render_template_string, jsonify, request, Response
from datetime import datetime
import uuid
import json
import time

app = Flask(__name__)
app.secret_key = 'klavye-test-secret-key-2024'

# Oturum verileri (Basit bellek içi depolama)
sessions_data = {}

HTML_TEMPLATE_V2 = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-TR" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Online Keyboard Tester | Test Your Keyboard</title>
    <meta
      name="description"
      content="Test your keyboard and troubleshoot issues with this interactive tool. Explore keyboard layouts and functionality."
    />
    <style>
/* ------------------ general.css --- */
:root {
  --def-fs: 62.5%;
  --ff: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;

  /* --- VARSAYILAN AÇIK TEMA RENKLERİ --- */
  --c-page-bg: #f0f2f5;
  --c-text: #343a40;
  --c-text-secondary: #6c757d;
  
  /* İYİLEŞTİRME: Açık tema istatistik çubuğu renkleri */
  --c-stats-bg: #ffffff; /* Açık modda beyaz */
  --c-stats-value: #343a40; /* Açık modda koyu metin */
  --c-stats-label: #6c757d; /* Açık modda etiketler */
  --c-stats-shadow: 0 4px 10px rgba(0,0,0,0.08); /* Açık modda hafif gölge */
  
  --c-select-bg: white;
  --c-select-border: #ddd;

  /* keycaps (Aydınlık Klavye - Inverted Retro) */
  --color-keycaps-legends: #343a40; 
  --color-keycaps-bg: #ced4da; 
  --color-keycaps-shadow: #adb5bd;
  --color-keycaps-legends-accent: #343a40;
  --color-keycaps-bg-accent: #e9ecef; 
  --color-keycaps-shadow-accent: #adb5bd;
  --color-keycaps-legends-pressed: #f8f9fa; 
  --color-keycaps-bg-pressed: #343a40; 
  --color-keycaps-shadow-pressed: #484e53;
  --color-keyboard: #f8f9fa; 
  --color-keyboard-border: #e2e3e6;

  --color-bg-title: linear-gradient(
    45deg,
    #14181c,
    #506070,
    #2e3235,
    #506070,
    #2e3235,
    #506070,
    #14181c
  );
}

/* --- SİSTEM KARANLIK MOD AYARLARI (KOYU TEMA) --- */
@media (prefers-color-scheme: dark) {
    :root {
        --c-page-bg: #1c1d1f;
        --c-text: #e4e6eb;
        --c-text-secondary: #b0b3b8;
        
        /* İYİLEŞTİRME: Koyu tema istatistik çubuğu renkleri */
        --c-stats-bg: #2a2a2e; /* Koyu modda daha açık gri */
        --c-stats-value: #f8f9fa; /* Koyu modda beyaz metin */
        --c-stats-label: #b0b3b8; /* Koyu modda etiketler */
        --c-stats-shadow: 0 4px 10px rgba(0,0,0,0.4); /* Koyu modda gölge */
        
        --c-select-bg: #3a3b3c;
        --c-select-border: #3e4042;
        
        /* keycaps (Koyu Klavye - Retro) */
        --color-keycaps-legends: #555;
        --color-keycaps-bg: #f8f9fa;
        --color-keycaps-shadow: #adb5bd;
        --color-keycaps-legends-accent: #555;
        --color-keycaps-bg-accent: #e2e3e6;
        --color-keycaps-shadow-accent: #adb5bd;
        --color-keycaps-legends-pressed: #2f3674;
        --color-keycaps-bg-pressed: #a4a9b0;
        --color-keycaps-shadow-pressed: #7f8489;
        --color-keyboard: #3c3e4a;
        --color-keyboard-border: #303642;
    }
}
/* ------------------------------------- */

* {
  padding: 0;
  margin: 0;
  box-sizing: border-box;
}

html {
  font-size: var(--def-fs);
  overflow-x: hidden;
}

body {
  font-family: var(--ff);
  line-height: 1;
  font-weight: 400;
  background-color: var(--c-page-bg); 
  color: var(--c-text); 
  transition: background-color 0.3s, color 0.3s;
}

.heading-primary {
  font-size: 5.2rem;
  font-weight: 700;
  letter-spacing: 0.1rem;
  margin-bottom: 1.6rem;
  color: var(--c-text);
}

.description-text {
  font-size: 2rem;
  color: var(--c-text-secondary);
  line-height: 1.6;
}

/* ------------------ REUSABLE BUTTONS ------------------ */

.btn {
  padding: 1rem 2.4rem;
  border: none;
  border-radius: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 1.6rem;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5568d3;
  transform: translateY(-0.2rem);
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.container {
  max-width: 140rem;
  margin: 0 auto;
  padding: 0 3.2rem;
}

/* ------------------ themes.css --- */
/* Klavye tuşlarının temel stilleri */
.theme--retro, .theme--inverted-retro {
  --key-border-radius: 0.6rem;
  --box-shadow-keycaps-value: inset 0 -0.2rem 0 0.3rem;
  --box-shadow-keycaps-hover-value: inset 0 -0.1rem 0 0.2rem;
  --box-shadow-keycaps: var(--box-shadow-keycaps-value) var(--color-keycaps-shadow);
  --box-shadow-keycaps-hover: var(--box-shadow-keycaps-hover-value) var(--color-keycaps-shadow);
  --box-shadow-keycaps-accent: var(--box-shadow-keycaps-value) var(--color-keycaps-shadow-accent);
  --box-shadow-keycaps-accent-hover: var(--box-shadow-keycaps-hover-value) var(--color-keycaps-shadow-accent);
  --box-shadow-keycaps-pressed: var(--box-shadow-keycaps-value) var(--color-keycaps-shadow-pressed);
  --box-shadow-keycaps-pressed-hover: var(--box-shadow-keycaps-hover-value) var(--color-keycaps-shadow-pressed);
}


/* Klavye Container ve Tuşları otomatik olarak tema değişkenlerini kullanacak */

/* ------------------ style.css (Klavye Düzeni Stilleri) --- */
.intro {
  max-width: 130rem;
  margin: 0 auto;
  padding: 4.8rem 3.2rem 0rem;
}

.title span {
  background-image: var(--color-bg-title);
  background-clip: text;
  -webkit-background-clip: text;
  -moz-background-clip: text;
  -webkit-text-fill-color: transparent;
  -moz-text-fill-color: transparent;
}

/* --- İSTATİSTİK KUTUSU DÜZENLEMESİ --- */
.stats-bar {
    display: flex;
    justify-content: center;
    gap: 3.2rem;
    margin: 2.4rem auto;
    padding: 1.6rem;
    background: var(--c-stats-bg); 
    border-radius: 1.2rem;
    max-width: 120rem;
    box-shadow: var(--c-stats-shadow); /* Temaya göre gölge */
    transition: background-color 0.3s, box-shadow 0.3s;
}

.stat-item {
    text-align: center;
}

.stat-value {
    font-size: 3.2rem;
    font-weight: 700;
    color: var(--c-stats-value); /* Temaya göre değer rengi */
    transition: color 0.3s;
}

.stat-label {
    font-size: 1.4rem;
    font-weight: 500;
    color: var(--c-stats-label); /* Temaya göre etiket rengi */
    transition: color 0.3s;
}
/* --- İSTATİSTİK KUTUSU SONU --- */

.theme-and-layout {
  display: flex;
  justify-content: center;
  gap: 2rem;
  max-width: 120rem;
  margin: 0 auto 3.2rem;
  transition: all 0.25s;
}

.control-group {
    display: flex;
    align-items: center;
    gap: 1.2rem;
}

.control-group label {
    font-size: 1.6rem;
    font-weight: 600;
    color: var(--c-text); /* OTOMATİK TEMA */
}

select {
    padding: 1rem 1.6rem;
    border: 2px solid var(--c-select-border); /* OTOMATİK TEMA */
    border-radius: 0.8rem;
    font-size: 1.6rem;
    cursor: pointer;
    background: var(--c-select-bg); /* OTOMATİK TEMA */
    color: var(--c-text); /* OTOMATİK TEMA */
    transition: background-color 0.3s, color 0.3s, border-color 0.3s;
}

/* Klavye container - DAHA KOMPAKT */
.keyboard-container {
  background: var(--color-keyboard);
  border-radius: 1.2rem;
  padding: 1.8rem 1.4rem;
  box-shadow: 0 0.8rem 0 0.6rem var(--color-keyboard-border), 0 1.2rem 3.2rem rgba(0, 0, 0, 0.2);
  max-width: 110rem;
  margin: 0 auto;
  transition: max-width 0.3s ease, background-color 0.3s;
}

/* Klavye grid - DAHA KÜÇÜK */
.keyboard {
  display: grid;
  grid-template-columns: 215fr 1.5fr 45fr 0.8fr 60fr;
  gap: 0.6rem;
  transition: grid-template-columns 0.3s ease;
}

/* Region padding - ÇOK KÜÇÜK */
.region {
  display: grid;
  gap: 0.35rem;
  padding: 0.4rem;
  transition: all 0.3s ease;
}

/* Function row - KOMPAKT */
.function {
  grid-template-columns: 2fr 1.5fr repeat(4, 2fr) 0.6fr repeat(4, 2fr) 0.6fr repeat(4, 2fr);
  transition: all 0.3s ease;
}

.system-control {
  grid-column: 3;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.35rem;
  transition: all 0.3s ease;
}

.typewriter {
  grid-row: 2;
}

/* Keyboard rows - ÇOK KÜÇÜK GAP */
.keyboard-row {
  display: grid;
  gap: 0.35rem;
  margin-bottom: 0.35rem;
}

/* Row templates - AYNI KAL */
.row-1 { 
  grid-template-columns: repeat(13, 1fr) 2fr; 
}

.row-2 { 
  grid-template-columns: 1.5fr repeat(12, 1fr) 1.5fr; 
}

.row-3 { 
  grid-template-columns: 1.75fr repeat(11, 1fr) 2.25fr; 
}

.row-4 { 
  grid-template-columns: 2.25fr repeat(10, 1fr) 2.75fr;
  transition: grid-template-columns 0.3s ease;
}

.row-5 { 
  grid-template-columns: 1.25fr 1.25fr 1.25fr 6.25fr 1.25fr 1.25fr 1.25fr 1.25fr;
  transition: grid-template-columns 0.3s ease;
}

.navigation {
  grid-column: 3;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(5, 1fr);
  gap: 0.35rem;
  transition: all 0.3s ease;
}

.numpad {
  grid-column: 5;
  grid-template-columns: repeat(4, 1fr);
  grid-template-rows: repeat(5, 1fr);
  gap: 0.35rem;
  transition: opacity 0.3s ease;
}

/* Tuş boyutları - DAHA KÜÇÜK */
.key {
  background: var(--color-keycaps-bg);
  color: var(--color-keycaps-legends);
  border: none;
  border-radius: var(--key-border-radius);
  font-size: 1.2rem;
  font-weight: 600;
  min-height: 4.4rem;
  height: 4.4rem;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--box-shadow-keycaps);
  transition: all 0.075s;
  user-select: none;
  position: relative;
  z-index: 1;
  padding: 0.3rem;
}

.key:hover {
  background: var(--color-keycaps-bg-hover);
  box-shadow: var(--box-shadow-keycaps-hover);
}

.key.accent {
  background: var(--color-keycaps-bg-accent);
  color: var(--color-keycaps-legends-accent);
  box-shadow: var(--box-shadow-keycaps-accent);
}

.key.pressing {
  transform: scale(0.98);
  background: var(--color-keycaps-bg-pressed);
  color: var(--color-keycaps-legends-pressed);
  box-shadow: var(--box-shadow-keycaps-pressed-hover);
}

.key.tested {
  background: var(--color-keycaps-bg-pressed);
  color: var(--color-keycaps-legends-pressed);
  box-shadow: var(--box-shadow-keycaps-pressed);
}

.key.tested:hover {
  background: var(--color-keycaps-bg-pressed-hover);
  box-shadow: var(--box-shadow-keycaps-pressed-hover);
}

/* Özel Tuş Düzenleri */
.arrow-up { grid-column: 2; grid-row: 4; }
.arrow-left { grid-row: 5; grid-column: 1; }
.arrow-down { grid-row: 5; grid-column: 2; }
.arrow-right { grid-row: 5; grid-column: 3; }
.numpad-add { grid-column: 4; grid-row: 2 / span 2; }
.numpad-enter { grid-column: 4; grid-row: 4 / span 2; }
.numpad-0 { grid-column: 1 / span 2; }

/* ------------------ LAYOUT TOGGLE STYLES ------------------ */

/* TKL Layout */
.keyboard.layout-tkl {
  grid-template-columns: 215fr 2fr 45fr 1fr 0fr;
}

.keyboard.layout-tkl .numpad {
  display: none;
}

/* 75% Layout */
.keyboard.layout-75 {
  
  grid-template-columns: 215fr 0fr 45fr 0fr 0fr;
}

.keyboard.layout-75 .numpad {
  display: none;
}

.keyboard.layout-75 .region {
  padding: 0.15rem;
}

.keyboard.layout-75 .function {
  grid-template-columns: 2fr 0 repeat(4, 2fr) 0 repeat(4, 2fr) 0 repeat(4, 2fr);
  width: 86.7%;
}

.keyboard.layout-75 .system-control {
  width: 90%;
  transform: translateX(-90%);
}

.keyboard.layout-75 .system-control .key:nth-child(2) {
    display: none; /* Scrlk tuşunu gizle */
}



/* 75% Layout - TEMEL YAPI */

.keyboard.layout-75 {
    grid-template-columns: 215fr 0fr 45fr 0fr 0fr;
}


.keyboard.layout-75 .numpad {
    display: none;
}

.keyboard.layout-75 .region {
    padding: 0.15rem;
}

.keyboard.layout-75 .function {
    grid-template-columns: 2fr 0 repeat(4, 2fr) 0 repeat(4, 2fr) 0 repeat(4, 2fr);
    width: 86.7%;
}

/* SYSTEM CONTROL BÖLGESİ (PrtSc, Pause) */
.keyboard.layout-75 .system-control {
    width: 95%;
    transform: translateX(-77%);
}
.keyboard.layout-75 .system-control .key:nth-child(2) {
    display: none; /* Scrlk tuşunu gizler */
}

/* ---------------------------------------------------- */
/* NAVİGASYON BÖLGESİ (DEL/HOME/END/PGUP/PGDN) */
/* ---------------------------------------------------- */

/* ADIM 1: TÜM NAVİGASYON BLOĞUNU YUKARI TAŞIYARAK PG DOWN İÇİN YER AÇ */
/* ADIM 1: TÜM NAVİGASYON BLOĞUNU YUKARI TAŞIYARAK PG DOWN İÇİN YER AÇ */
/* Bu kural, Delete/Home/End/PgUp/PgDn tuşlarını yukarı taşır */
.keyboard.layout-75 .navigation {
    /* Yatay pozisyonunuzu koruyun */
    /* Dikey yığını bir tuş sırası kadar yukarı taşır */
    transform: translateX(-72%) translateY(-20.3%); 
}

/* ... Dikey Sıralama Kuralları (grid-row: 1'den 5'e kadar) AYNEN KALIR ve DOĞRUDUR ... */

/* ---------------------------------------------------------------------------------- */
/* ADIM 2: OK TUŞLARINI GERİ AŞAĞI KAYDIRARAK KAYMAYI TELAFİ ET (Ok tuşlarının kaymasını önler) */
/* ---------------------------------------------------------------------------------- */

.keyboard.layout-75 .navigation div:nth-child(7), /* Boş div */
.keyboard.layout-75 .navigation .key:nth-child(8), /* ↑ ArrowUp */
.keyboard.layout-75 .navigation div:nth-child(9), /* İkinci Boş div */
.keyboard.layout-75 .navigation .key:nth-child(10), /* ← ArrowLeft */
.keyboard.layout-75 .navigation .key:nth-child(11), /* ↓ ArrowDown */
.keyboard.layout-75 .navigation .key:nth-child(12) /* → ArrowRight */
{ 
    /* Kapsayıcının kaydığı miktarın (translateY(-100%)) tersi yönde kaydırılır */
    transform: translateY(120%); 
}

/* Insert (Ins) - Gizlenir */
.keyboard.layout-75 .navigation .key:nth-child(1) {
    display: none; 
}

/* Dikey Sıralama (Delete, Home, End, PgUp, PgDn) */

/* 1. DELETE (Del) - grid-row: 1 */
.keyboard.layout-75 .navigation .key:nth-child(4) {
    grid-column: 3;
    grid-row: 1; 
}

/* 2. HOME - grid-row: 2 */
.keyboard.layout-75 .navigation .key:nth-child(2) {
    grid-column: 3;
    grid-row: 2;
}

/* 3. END - grid-row: 3 */
.keyboard.layout-75 .navigation .key:nth-child(5) {
    grid-column: 3;
    grid-row: 3;
}

/* 4. PAGE UP (PgUp) - grid-row: 4 */
.keyboard.layout-75 .navigation .key:nth-child(3) {
    grid-column: 3;
    grid-row: 4;
}

/* 5. PAGE DOWN (PgDn) - grid-row: 5 (Artık Ok Tuşları ile çakışmayacak ve görünür olacak) */
.keyboard.layout-75 .navigation .key:nth-child(6) {
    grid-column: 3;
    grid-row: 5;
}




/* ---------------------------------------------------- */
/* ROW DÜZENLERİ */
/* ---------------------------------------------------- */

.keyboard.layout-75 .row-4 {
    grid-template-columns: 2.25fr 1fr 1fr 1fr 1fr 1fr 1fr 1fr 1fr 1fr 1fr 1.75fr 1.04fr;
}

.keyboard.layout-75 .row-5 {
    grid-template-columns: 1.25fr 1.25fr 1.25fr 6.25fr 1.25fr 1.25fr 1fr 2.00fr;
}

.keyboard.layout-75 .row-5 .key:nth-child(7) {
    display: none;
}
/* ------------------ queries.css --- */
@media (max-width: 1200px) {
  .keyboard-container {
    max-width: 95rem;
  }
  .keyboard, .keyboard.layout-tkl, .keyboard.layout-75 {
    grid-template-columns: 1fr;
    gap: 0;
  }
  .system-control, .navigation, .numpad {
    display: none;
  }
  .typewriter {
    grid-row: auto;
  }
}

/* --- Toast Notification --- */
.toast {
    position: fixed;
    top: 20px;
    right: 20px;
    background: white;
    padding: 16px 24px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    display: none;
    z-index: 1000;
    font-size: 1.6rem;
    font-weight: 600;
}

.toast.show {
    display: block;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from { transform: translateX(400px); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
}

    </style>
  </head>
  <body class="theme--retro">
    <div class="container">
      <header class="intro">
        <h1 class="heading-primary title">
          <span>ONLINE KLAVYE TESTİ</span>
        </h1>
        <p class="description-text">
          Fiziksel klavyenizdeki sorunları tespit edin veya düzenini keşfedin
        </p>
      </header>

      <div class="stats-bar">
          <div class="stat-item">
              <div class="stat-value" id="testedCount">0</div>
              <div class="stat-label">Test Edilen Tuş</div>
          </div>
          <div class="stat-item">
              <div class="stat-value" id="totalPresses">0</div>
              <div class="stat-label">Toplam Basım</div>
          </div>
          <div class="stat-item">
              <div class="stat-value" id="sessionTime">0s</div>
              <div class="stat-label">Oturum Süresi</div>
          </div>
      </div>

      <div class="theme-and-layout">
        <div class="control-group">
          </div>
        <div class="control-group">
          <label for="layoutSelect">Düzen:</label>
          <select id="layoutSelect">
            <option value="full" selected>Full Size</option>
            <option value="tkl">TKL</option>
            <option value="75">75%</option>
            </select>
        </div>
        <button class="btn btn-secondary" onclick="resetTest()">Sıfırla</button>
        <button class="btn btn-primary" onclick="downloadReport()">Rapor İndir</button>
        <button class="btn btn-danger" onclick="endSession()">Oturumu Bitir</button>
      </div>

      <main class="keyboard-container">
        <div class="keyboard" id="keyboard">
          <div class="region function">
            <button class="key accent" data-key="Escape">ESC</button>
            <div></div>
            <button class="key" data-key="F1">F1</button>
            <button class="key" data-key="F2">F2</button>
            <button class="key" data-key="F3">F3</button>
            <button class="key" data-key="F4">F4</button>
            <div></div>
            <button class="key" data-key="F5">F5</button>
            <button class="key" data-key="F6">F6</button>
            <button class="key" data-key="F7">F7</button>
            <button class="key" data-key="F8">F8</button>
            <div></div>
            <button class="key" data-key="F9">F9</button>
            <button class="key" data-key="F10">F10</button>
            <button class="key" data-key="F11">F11</button>
            <button class="key" data-key="F12">F12</button>
          </div>

          <div class="region system-control">
            <button class="key accent" data-key="PrintScreen">Prt Sc</button>
            <button class="key accent" data-key="ScrollLock">Scr Lk</button>
            <button class="key accent" data-key="Pause">Pause</button>
          </div>

          <div class="region typewriter">
            <div class="keyboard-row row-1">
              <button class="key accent" data-key="Backquote">~ `</button>
              <button class="key" data-key="Digit1">! 1</button>
              <button class="key" data-key="Digit2">@ 2</button>
              <button class="key" data-key="Digit3"># 3</button>
              <button class="key" data-key="Digit4">$ 4</button>
              <button class="key" data-key="Digit5">% 5</button>
              <button class="key" data-key="Digit6">^ 6</button>
              <button class="key" data-key="Digit7">& 7</button>
              <button class="key" data-key="Digit8">* 8</button>
              <button class="key" data-key="Digit9">( 9</button>
              <button class="key" data-key="Digit0">) 0</button>
              <button class="key" data-key="Minus">_ -</button>
              <button class="key" data-key="Equal">+ =</button>
              <button class="key accent" data-key="Backspace">⌫</button>
            </div>
            <div class="keyboard-row row-2">
              <button class="key accent" data-key="Tab">Tab</button>
              <button class="key" data-key="KeyQ">Q</button>
              <button class="key" data-key="KeyW">W</button>
              <button class="key" data-key="KeyE">E</button>
              <button class="key" data-key="KeyR">R</button>
              <button class="key" data-key="KeyT">T</button>
              <button class="key" data-key="KeyY">Y</button>
              <button class="key" data-key="KeyU">U</button>
              <button class="key" data-key="KeyI">I</button>
              <button class="key" data-key="KeyO">O</button>
              <button class="key" data-key="KeyP">P</button>
              <button class="key" data-key="BracketLeft">{ [</button>
              <button class="key" data-key="BracketRight">} ]</button>
              <button class="key accent" data-key="Backslash">| \\</button>
            </div>
            <div class="keyboard-row row-3">
              <button class="key accent" data-key="CapsLock">Caps</button>
              <button class="key" data-key="KeyA">A</button>
              <button class="key" data-key="KeyS">S</button>
              <button class="key" data-key="KeyD">D</button>
              <button class="key" data-key="KeyF">F</button>
              <button class="key" data-key="KeyG">G</button>
              <button class="key" data-key="KeyH">H</button>
              <button class="key" data-key="KeyJ">J</button>
              <button class="key" data-key="KeyK">K</button>
              <button class="key" data-key="KeyL">L</button>
              <button class="key" data-key="Semicolon">: ;</button>
              <button class="key" data-key="Quote">" '</button>
              <button class="key accent" data-key="Enter">↵</button>
            </div>
            <div class="keyboard-row row-4">
              <button class="key accent" data-key="ShiftLeft">Shift</button>
              <button class="key" data-key="KeyZ">Z</button>
              <button class="key" data-key="KeyX">X</button>
              <button class="key" data-key="KeyC">C</button>
              <button class="key" data-key="KeyV">V</button>
              <button class="key" data-key="KeyB">B</button>
              <button class="key" data-key="KeyN">N</button>
              <button class="key" data-key="KeyM">M</button>
              <button class="key" data-key="Comma">< ,</button>
              <button class="key" data-key="Period">> .</button>
              <button class="key" data-key="Slash">? /</button>
              <button class="key accent" data-key="ShiftRight">Shift</button>
            </div>
            <div class="keyboard-row row-5">
              <button class="key accent" data-key="ControlLeft">Ctrl</button>
              <button class="key accent" data-key="MetaLeft">Win</button>
              <button class="key accent" data-key="AltLeft">Alt</button>
              <button class="key accent" data-key="Space">Space</button>
              <button class="key accent" data-key="AltRight">Alt</button>
              <button class="key accent" data-key="MetaRight">Win</button>
              <button class="key accent" data-key="ContextMenu">Menu</button>
              <button class="key accent" data-key="ControlRight">Ctrl</button>
            </div>
          </div>

          <div class="region navigation">
            <button class="key accent" data-key="Insert">Ins</button>
            <button class="key accent" data-key="Home">Home</button>
            <button class="key accent" data-key="PageUp">PgUp</button>
            <button class="key accent" data-key="Delete">Del</button>
            <button class="key accent" data-key="End">End</button>
            <button class="key accent" data-key="PageDown">PgDn</button>
            <div></div>
            <button class="key arrow-up" data-key="ArrowUp">↑</button>
            <div></div>
            <button class="key arrow-left" data-key="ArrowLeft">←</button>
            <button class="key arrow-down" data-key="ArrowDown">↓</button>
            <button class="key arrow-right" data-key="ArrowRight">→</button>
          </div>

          <div class="region numpad" id="numpad">
            <button class="key accent" data-key="NumLock">Num</button>
            <button class="key" data-key="NumpadDivide">/</button>
            <button class="key" data-key="NumpadMultiply">*</button>
            <button class="key" data-key="NumpadSubtract">-</button>
            <button class="key" data-key="Numpad7">7</button>
            <button class="key" data-key="Numpad8">8</button>
            <button class="key" data-key="Numpad9">9</button>
            <button class="key numpad-add" data-key="NumpadAdd">+</button>
            <button class="key" data-key="Numpad4">4</button>
            <button class="key" data-key="Numpad5">5</button>
            <button class="key" data-key="Numpad6">6</button>
            <button class="key" data-key="Numpad1">1</button>
            <button class="key" data-key="Numpad2">2</button>
            <button class="key" data-key="Numpad3">3</button>
            <button class="key numpad-enter" data-key
-key="NumpadEnter">↵</button>
            <button class="key numpad-0" data-key="Numpad0">0</button>
            <button class="key" data-key="NumpadDecimal">.</button>
          </div>
        </div>
        <p class="info-text" style="text-align: center; margin-top: 1.6rem; font-size: 1.4rem; color: var(--c-text-secondary);">
            Klavyenizdeki tuşlara basarak test edin • Python Backend ile çalışıyor
        </p>
      </main>
    </div>

    <div class="toast" id="toast"></div>

    <script>
        // Sayfa yüklendiğinde otomatik temayı uygula
        document.addEventListener('DOMContentLoaded', () => {
            // Sistem temasını algıla ve body'e uygun sınıfı ekle
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            if (prefersDark) {
                // Koyu tema varsayılan olduğu için özel bir sınıf eklemeye gerek yok
                // Zaten body elementinin sınıfı `theme--retro` olarak tanımlı
                // Eğer farklı bir retro koyu tema olsaydı buraya eklenebilirdi.
            } else {
                // Açık tema için body'e sınıf ekleyelim
                document.body.classList.add('theme--inverted-retro');
            }

            // Sistem teması değiştiğinde de otomatik olarak temayı güncelle
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', event => {
                if (event.matches) {
                    document.body.classList.remove('theme--inverted-retro');
                    // Koyu temaya geçişte retro varsayılan olduğu için ek sınıf gerekmiyor
                } else {
                    document.body.classList.add('theme--inverted-retro');
                }
            });
        });


        let sessionId = '{{ session_id }}';
        let sessionStartTime = Date.now();
        const TOTAL_FULL_SIZE_KEYS = 104;
        let isFullTestComplete = false;

        const keyboard = document.getElementById('keyboard');
        const layoutSelect = document.getElementById('layoutSelect');
        const body = document.querySelector('body');
        const container = document.querySelector('.keyboard-container');
        
        // Düzen Değiştirme
        layoutSelect.addEventListener('change', (e) => {
            keyboard.classList.remove('layout-tkl', 'layout-75');
            
            if (e.target.value === 'tkl') {
                keyboard.classList.add('layout-tkl');
                container.style.maxWidth = '90rem';
            } else if (e.target.value === '75') {
                keyboard.classList.add('layout-75');
                container.style.maxWidth = '78rem';
            } else {
                container.style.maxWidth = '110rem';
            }
        });

        // Tuş basma olayını yakala
        document.addEventListener('keydown', async (e) => {
            e.preventDefault(); 
            const keyElement = document.querySelector(`[data-key="${e.code}"]`);
            
            if (keyElement && !keyElement.classList.contains('pressing')) {
                keyElement.classList.add('pressing');
                keyElement.classList.add('tested');

                await fetch('/api/key-press', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        key_code: e.code,
                        key: e.key,
                        timestamp: Date.now()
                    })
                });
                updateStats();
            }
        });

        document.addEventListener('keyup', (e) => {
            const keyElement = document.querySelector(`[data-key="${e.code}"]`);
            if (keyElement) {
                keyElement.classList.remove('pressing');
            }
        });

        // Toast bildirimi
        function showToast(message, type = 'info') {
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.className = 'toast show';

            if (type === 'success') {
                toast.style.backgroundColor = '#28a745';
                toast.style.color = 'white';
            } else {
                // Tema uyumluluğu için renkler
                const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
                if(isDark) {
                    toast.style.backgroundColor = '#3a3b3c';
                    toast.style.color = '#e4e6eb';
                    toast.style.boxShadow = '0 4px 12px rgba(255, 255, 255, 0.1)';
                } else {
                    toast.style.backgroundColor = 'white';
                    toast.style.color = 'var(--color-primary)';
                    toast.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
                }
            }
            
            setTimeout(() => {
                toast.classList.remove('show');
                toast.style.backgroundColor = '';
                toast.style.color = '';
                toast.style.boxShadow = '';
            }, 3000);
        }

        // İstatistikleri güncelle
        async function updateStats() {
            const response = await fetch(`/api/stats/${sessionId}`);
            if (response.status === 404) return;
            const stats = await response.json();
            
            document.getElementById('testedCount').textContent = stats.tested_keys;
            document.getElementById('totalPresses').textContent = stats.total_presses;

            if (stats.tested_keys >= TOTAL_FULL_SIZE_KEYS && !isFullTestComplete) {
                showToast('🎉 Klavyenizin tüm tuşları çalışmaktadır!', 'success');
                isFullTestComplete = true;
            }
        }

        // Oturum süresini güncelle
        setInterval(() => {
            const seconds = Math.floor((Date.now() - sessionStartTime) / 1000);
            document.getElementById('sessionTime').textContent = seconds + 's';
        }, 1000);

        // Sıfırla
        async function resetTest() {
            if (confirm('Tüm test verilerini sıfırlamak istediğinizden emin misiniz?')) {
                await fetch(`/api/reset/${sessionId}`, { method: 'POST' });
                document.querySelectorAll('.key.tested').forEach(key => {
                    key.classList.remove('tested');
                });
                sessionStartTime = Date.now();
                isFullTestComplete = false;
                updateStats();
                showToast('Test verileri sıfırlandı');
            }
        }

        // Rapor indir
        async function downloadReport() {
            window.location.href = `/api/report/${sessionId}`;
            showToast('Rapor indiriliyor...');
        }

        // Oturumu bitir
        async function endSession() {
            if (confirm('Oturumu bitirmek istediğinizden emin misiniz?')) {
                await fetch(`/api/end-session/${sessionId}`, { method: 'POST' });
                showToast('Oturum sonlandırıldı');
                setTimeout(() => location.reload(), 1500);
            }
        }

        updateStats();
    </script>
  </body>
</html>
"""

# ----------------------------------------------------
# FLASK ENDPOINTS
# ----------------------------------------------------

@app.route('/')
def index():
    """Ana sayfa. Her istekte yeni bir oturum başlatır."""
    session_id = str(uuid.uuid4())
    sessions_data[session_id] = {
        'start_time': datetime.now().timestamp(),
        'tested_keys': set(),
        'key_presses': {},
        'total_presses': 0
    }
    
    # Body'e varsayılan olarak `theme--retro` sınıfı ekleniyor.
    # Bu sınıf, `prefers-color-scheme` media query'si ile birlikte çalışarak
    # otomatik tema geçişini sağlayacak.
    return render_template_string(HTML_TEMPLATE_V2, session_id=session_id)


@app.route('/api/key-press', methods=['POST'])
def key_press():
    """Tuş basma olayını kaydeder."""
    data = request.json
    session_id = data.get('session_id')
    key_code = data.get('key_code')
    
    if session_id in sessions_data:
        session_data = sessions_data[session_id]
        session_data['tested_keys'].add(key_code)
        session_data['key_presses'][key_code] = session_data['key_presses'].get(key_code, 0) + 1
        session_data['total_presses'] += 1
        
        return jsonify({'status': 'success'})
    
    return jsonify({'status': 'error', 'message': 'Session not found'}), 404


@app.route('/api/stats/<session_id>')
def get_stats(session_id):
    """İstatistikleri getirir."""
    if session_id in sessions_data:
        session_data = sessions_data[session_id]
        duration_seconds = int(time.time() - session_data['start_time'])
        
        return jsonify({
            'tested_keys': len(session_data['tested_keys']),
            'total_presses': session_data['total_presses'],
            'session_duration': duration_seconds
        })
    
    return jsonify({'error': 'Session not found'}), 404


@app.route('/api/reset/<session_id>', methods=['POST'])
def reset_session(session_id):
    """Test verilerini sıfırlar."""
    if session_id in sessions_data:
        sessions_data[session_id]['tested_keys'] = set()
        sessions_data[session_id]['key_presses'] = {}
        sessions_data[session_id]['total_presses'] = 0
        sessions_data[session_id]['start_time'] = datetime.now().timestamp()
        
        return jsonify({'status': 'success'})
    
    return jsonify({'error': 'Session not found'}), 404


@app.route('/api/report/<session_id>')
def download_report(session_id):
    """Rapor oluşturur ve indirir."""
    if session_id in sessions_data:
        session_data = sessions_data[session_id]
        start_time_iso = datetime.fromtimestamp(session_data['start_time']).isoformat()
        
        report = f"""
KLAVYE TEST RAPORU
==================

Oturum ID: {session_id}
Başlangıç: {start_time_iso}
Bitiş: {datetime.now().isoformat()}

İSTATİSTİKLER
-------------
Test Edilen Tuşlar: {len(session_data['tested_keys'])}
Toplam Basım: {session_data['total_presses']}

DETAYLAR
--------
"""
        for key, count in sorted(session_data['key_presses'].items(), key=lambda x: x[1], reverse=True):
            report += f"{key}: {count} basım\n"
        
        return Response(
            report,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment;filename=keyboard_test_{session_id[:8]}.txt'}
        )
    
    return jsonify({'error': 'Session not found'}), 404


@app.route('/api/end-session/<session_id>', methods=['POST'])
def end_session_route(session_id):
    """Oturumu sonlandırır ve verileri bellekten siler."""
    if session_id in sessions_data:
        del sessions_data[session_id]
        return jsonify({'status': 'success'})
    
    return jsonify({'error': 'Session not found'}), 404


if __name__ == '__main__':
    print("🚀 Klavye Test Uygulaması Başlatılıyor...")
    print("📍 http://127.0.0.1:5003")
    print("⌨️ Tarayıcınızda açın ve test etmeye başlayın!")
    app.run(debug=True, host='0.0.0.0', port=5003)