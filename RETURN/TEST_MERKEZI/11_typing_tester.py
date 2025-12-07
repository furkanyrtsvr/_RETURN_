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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>10 Parmak Yazı Testi</title>
    <style>
        /* --- Tema Renk Değişkenleri --- */
        :root {
            /* Varsayılan: Aydınlık Tema */
            --body-bg: #f0f2f5;
            --text-color: #333; /* İsteğiniz üzerine siyah/koyu gri yapıldı */
            --container-bg: white;
            --container-shadow: 0 10px 40px rgba(0,0,0,.1);
            --history-bg: #f8f9ff;
            --history-item-bg: white;
            --history-item-border: #e0e7ff;
            --history-header-color: #764ba2;
            --controls-bg: #f8f9ff;
            --word-display-bg: #eee;
            --word-display-border: #ddd;
            --input-bg: white;
            --input-border: #ccc;
            --input-focus-border: #667eea;
            --input-error-bg: #fee2e2;
            --input-error-border: #fecaca;
            --header-color: #667eea;
            --accent-color-1: #667eea;
            --accent-color-2: #764ba2;
            --button-bg: #e0e7ff;
            --button-text: #4f46e5;
            --button-active-bg: #667eea;
            --button-active-text: white;
            --correct-color: #10b981;
            --incorrect-color: #ef4444;
            --favorite-star-color: #ccc;
            --favorite-star-active-color: #f59e0b;
            --results-overlay-bg: rgba(255, 255, 255, 0.8);
            --unit-color: #666;
        }

        /* YENİ: Otomatik Karanlık Tema Algılama */
        @media (prefers-color-scheme: dark) {
            :root {
                --body-bg: #121212;
                --text-color: #e0e0e0;
                --container-bg: #1e1e1e;
                --container-shadow: 0 10px 40px rgba(0,0,0,.5);
                --history-bg: #2a2a2e;
                --history-item-bg: #2c2c31;
                --history-item-border: #444;
                --history-header-color: #a78bfa;
                --controls-bg: #2c2c31;
                --word-display-bg: #2c2c31;
                --word-display-border: #444;
                --input-bg: #2c2c31;
                --input-border: #555;
                --input-focus-border: #818cf8;
                --input-error-bg: #452323;
                --input-error-border: #7f1d1d;
                --header-color: #818cf8;
                --accent-color-1: #818cf8;
                --accent-color-2: #a78bfa;
                --button-bg: #374151;
                --button-text: #e5e7eb;
                --button-active-bg: #818cf8;
                --button-active-text: #1e1e1e;
                --correct-color: #34d399;
                --incorrect-color: #f87171;
                --favorite-star-color: #555;
                --favorite-star-active-color: #f59e0b;
                --results-overlay-bg: rgba(30, 30, 30, 0.9);
                --unit-color: #aaa;
            }
        }
        /* --- Tema Değişkenleri Sonu --- */

        body {
            font-family: 'Segoe UI', sans-serif;
            background: var(--body-bg);
            color: var(--text-color);
            margin: 0;
            display: flex; justify-content: center; align-items: flex-start;
            min-height: 100vh; padding: 0;
            box-sizing: border-box; user-select: none;
            overflow-x: hidden;
            position: relative;
            transition: background 0.3s, color 0.3s;
        }

        .main-wrapper {
            display: flex;
            justify-content: center;
            width: 100%;
            max-width: 900px;
            padding: 20px;
            box-sizing: border-box;
        }
        .test-container {
            width: 100%;
            background: var(--container-bg);
            border-radius: 20px;
            box-shadow: var(--container-shadow);
            padding: 30px 40px; text-align: center;
            flex-shrink: 0;
            transition: background 0.3s;
        }

        .history-container {
            position: fixed;
            top: 0;
            right: -350px;
            width: 300px;
            height: 100vh;
            background: var(--history-bg);
            box-shadow: -5px 0 15px rgba(0,0,0,0.1);
            padding: 25px;
            box-sizing: border-box;
            overflow-y: auto;
            z-index: 1000;
            transition: right 0.3s ease-in-out, background 0.3s;
        }
        .history-container.is-open { right: 0; }
        .history-container h2 {
            color: var(--history-header-color);
            margin-top: 0; text-align: center; border-bottom: 2px solid var(--input-border); padding-bottom: 10px;
        }
        .history-list { list-style: none; padding: 0; margin: 0; }
        .history-item {
            background: var(--history-item-bg);
            border-radius: 10px; padding: 15px; margin-bottom: 10px;
            border: 1px solid var(--history-item-border);
            display: flex; justify-content: space-between; align-items: center;
            font-size: 0.9em;
        }
        .history-details span { display: block; margin-bottom: 3px; color: var(--text-color); }
        .history-details strong { color: var(--accent-color-1); }
        .favorite-star {
            font-size: 1.5em; cursor: pointer; color: var(--favorite-star-color);
            margin-left: 15px; transition: color 0.2s, transform 0.2s;
        }
        .favorite-star.is-favorite { color: var(--favorite-star-active-color); }
        .favorite-star:hover { transform: scale(1.2); }

        h1 { color: var(--header-color); margin-top: 0; font-size: 2em; }
        .controls {
            display: flex; justify-content: space-between; align-items: center;
            margin-bottom: 25px; padding: 15px; background: var(--controls-bg); border-radius: 10px;
        }

        .language-buttons button {
            background: var(--button-bg); color: var(--button-text); border: none; padding: 10px 15px; margin-left: 10px;
            border-radius: 8px; font-weight: bold; cursor: pointer; transition: background 0.3s, color 0.3s;
        }
        .language-buttons button.active { background: var(--button-active-bg); color: var(--button-active-text); }
        .timer { font-size: 2em; font-weight: bold; color: var(--accent-color-2); }

        .word-display {
            font-size: 1.8em; line-height: 1.6; letter-spacing: 1px;
            background: var(--word-display-bg); border-radius: 10px; padding: 20px; height: 110px;
            overflow: hidden; margin-bottom: 20px; text-align: left;
            border: 2px solid var(--word-display-border);
        }
        .word-display span.current { background-color: var(--button-bg); padding: 2px 5px; border-radius: 5px;}
        .word-display span.correct { color: var(--correct-color); }
        .word-display span.incorrect { color: var(--incorrect-color); text-decoration: underline wavy var(--incorrect-color);}

        #typingInput {
            width: calc(100% - 40px); padding: 15px 20px; font-size: 1.5em; border-radius: 10px;
            border: 2px solid var(--input-border); outline: none; transition: border-color 0.3s, background-color 0.1s;
            margin-bottom: 30px;
            background-color: var(--input-bg);
            color: var(--text-color);
        }
        #typingInput:focus { border-color: var(--input-focus-border); }
        #typingInput.error { background-color: var(--input-error-bg); border-color: var(--input-error-border);}

        .results-overlay {
            display: none;
            background: var(--results-overlay-bg);
            border-radius: 15px; padding: 30px; margin-top: -50px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            z-index: 10;
        }
        .result-box { background: var(--controls-bg); border-radius: 10px; padding: 20px 15px; }
        .result-box .label { font-size: 0.9em; color: var(--accent-color-2); font-weight: bold; margin-bottom: 8px; text-transform: uppercase;}
        .result-box .value { font-size: 1.8em; font-weight: bold; color: var(--accent-color-1); line-height: 1.1; }
        .result-box .unit { font-size: 0.8em; color: var(--unit-color);}

        .menu-toggle {
            background: var(--button-active-bg);
             position: fixed; top: 20px; right: 20px; width: 40px; height: 40px;
             border-radius: 8px; display: flex; flex-direction: column; justify-content: space-around;
             align-items: center; padding: 8px 0; cursor: pointer; z-index: 1001;
             box-shadow: 0 4px 10px rgba(0,0,0,0.1); transition: background 0.3s;
        }
        .menu-toggle:hover { background: var(--accent-color-1); opacity: 0.9; }
        .menu-toggle span {
            background: var(--button-active-text);
            display: block; width: 70%; height: 3px; border-radius: 2px;
            transition: all 0.3s ease-in-out;
        }
        .menu-toggle.active span:nth-child(1) { transform: translateY(8px) rotate(45deg); }
        .menu-toggle.active span:nth-child(2) { opacity: 0; }
        .menu-toggle.active span:nth-child(3) { transform: translateY(-8px) rotate(-45deg); }
        #restartBtn {
            background: #f59e0b; color: white; border: none; padding: 10px 20px;
            border-radius: 8px; font-weight: bold; cursor: pointer; transition: background 0.3s;
            display: none; font-size: 1em;
        }
        #restartBtn:hover { background: #d97706; }
        .results-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
            gap: 15px; text-align: center;
        }

        @media (max-width: 900px) {
             .main-wrapper { padding: 10px; }
             .test-container { padding: 20px 25px; }
             .menu-toggle { top: 10px; right: 10px; width: 35px; height: 35px; padding: 6px 0; }
             .history-container { width: 90%; max-width: 300px; right: -100%; }
             .history-container.is-open { right: 0; }
        }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="test-container">
            <h1>⌨️ 10 Parmak Yazı Testi</h1>
            <div class="controls">
                <div class="language-buttons">
                    <button id="langTr" class="active">Türkçe</button>
                    <button id="langEn">English</button>
                </div>
                <div id="timerDisplay" class="timer">1:00</div>
                <button id="restartBtn">Yeniden Başlat</button>
            </div>
            <div id="wordDisplay" class="word-display"></div>
            <input type="text" id="typingInput" placeholder="Yazmaya başlayın..." autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">
            <div id="resultsOverlay" class="results-overlay">
                <h2>Test Sonuçları</h2>
                <div class="results-grid">
                      <div class="result-box"><div class="label">Hız (WPM)</div><div class="value" id="resultWpm">-</div><div class="unit">kelime/dk</div></div>
                      <div class="result-box"><div class="label">Doğruluk</div><div class="value" id="resultAcc">-</div><div class="unit">%</div></div>
                      <div class="result-box"><div class="label">Doğru Kelime</div><div class="value" id="resultCorrectWords">-</div></div>
                      <div class="result-box"><div class="label">Yanlış Kelime</div><div class="value" id="resultIncorrectWords">-</div></div>
                      <div class="result-box"><div class="label">Toplam Vuruş</div><div class="value" id="resultTotalKeys">-</div></div>
                      <div class="result-box"><div class="label">Doğru Vuruş</div><div class="value" id="resultCorrectKeys">-</div></div>
                </div>
            </div>
        </div>
    </div>
    <div class="menu-toggle" id="menuToggle">
        <span></span>
        <span></span>
        <span></span>
    </div>
    <div class="history-container" id="historyContainer">
        <h2>📊 Skor Geçmişi</h2>
        <ul class="history-list" id="historyList">
            <p class="no-history">Henüz kaydedilmiş skor yok.</p>
        </ul>
    </div>

    <script>
        // --- localStorage Anahtarları ---
        const HISTORY_STORAGE_KEY = 'typingTestHistory_v2';
        const MAX_HISTORY_ITEMS = 20;

        // --- DOM Elementleri ---
        const langTrBtn = document.getElementById('langTr');
        const langEnBtn = document.getElementById('langEn');
        const timerDisplay = document.getElementById('timerDisplay');
        const restartBtn = document.getElementById('restartBtn');
        const wordDisplay = document.getElementById('wordDisplay');
        const typingInput = document.getElementById('typingInput');
        const resultsOverlay = document.getElementById('resultsOverlay');
        const resultWpm = document.getElementById('resultWpm');
        const resultAcc = document.getElementById('resultAcc');
        const resultCorrectWords = document.getElementById('resultCorrectWords');
        const resultIncorrectWords = document.getElementById('resultIncorrectWords');
        const resultTotalKeys = document.getElementById('resultTotalKeys');
        const resultCorrectKeys = document.getElementById('resultCorrectKeys');
        const historyList = document.getElementById('historyList');
        const menuToggle = document.getElementById('menuToggle');
        const historyContainer = document.getElementById('historyContainer');

        const wordsTr = ["ve", "bir", "bu", "da", "için", "ama", "çok", "ben", "o", "ne", "var", "mi", "ile", "de", "olduğunu", "olarak", "daha", "şey", "sonra", "gibi", "kadar", "onu", "her", "zaman", "dedi", "yok", "bunu", "şimdi", "kendi", "geldi", "sadece", "bile", "önce", "yeni", "büyük", "iyi", "başka", "artık", "lazım", "küçük", "ilk", "diye", "iş", "yer", "el", "gün", "insan", "çocuk", "hayat", "kez", "kadın", "adam", "ev", "yıl", "ses", "yüz", "su", "para", "hava", "gece", "sabah", "akşam", "hafta", "ay", "saat", "dakika", "saniye", "bugün", "yarın", "dün", "kitap", "okul", "sınıf", "öğrenci", "öğretmen", "arkadaş", "aile", "anne", "baba", "kardeş", "kapı", "pencere", "masa", "sandalye", "yemek", "içmek", "uyumak", "gitmek", "gelmek", "konuşmak", "yazmak", "okumak", "sevmek", "istemek", "bilmek", "yapmak", "vermek", "almak", "bakmak", "görmek", "duymak", "anlamak", "düşünmek", "sormak", "cevaplamak", "çalışmak", "oynamak", "güzel", "zor", "kolay", "hızlı", "yavaş", "eski", "mutlu", "üzgün", "sıcak", "soğuk", "uzun", "kısa", "renk", "beyaz", "siyah", "kırmızı", "mavi", "yeşil", "sarı", "açık", "koyu"];
        const wordsEn = ["the", "be", "to", "of", "and", "a", "in", "that", "have", "I", "it", "for", "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which", "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know", "take", "people", "into", "year", "your", "good", "some", "could", "them", "see", "other", "than", "then", "now", "look", "only", "come", "its", "over", "think", "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way", "even", "new", "want", "because", "any", "these", "give", "day", "most", "us"];

        let selectedLanguage = 'tr';
        let words = [];
        let wordSpans = [];
        let currentWordIndex = 0;
        let isTestActive = false;
        let timeLeft = 60;
        let timerInterval = null;
        let totalTypedEntries = 0;
        let correctChars = 0;
        let totalCharsIntended = 0;
        let correctWordsCount = 0;
        let incorrectWordsCount = 0;
        let testStartTime = null;

        // TEMA İLE İLGİLİ TÜM JAVASCRIPT KODLARI KALDIRILDI
        // CSS, @media (prefers-color-scheme: dark) ile temayı otomatik olarak hallediyor.

        function loadHistory() {
            const historyData = localStorage.getItem(HISTORY_STORAGE_KEY);
            return historyData ? JSON.parse(historyData) : [];
        }
        function saveHistory(history) {
            localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history));
        }
        function addScoreToHistory(score) {
            let history = loadHistory();
            history.unshift(score);
            if (history.length > MAX_HISTORY_ITEMS) {
                for (let i = history.length - 1; i >= 0 && history.length > MAX_HISTORY_ITEMS; i--) {
                    if (!history[i].isFavorite) { history.splice(i, 1); }
                }
                while (history.length > MAX_HISTORY_ITEMS) { history.pop(); }
            }
            saveHistory(history);
            displayHistory();
        }
        function displayHistory() {
            const history = loadHistory();
            historyList.innerHTML = '';
            if (history.length === 0) {
                historyList.innerHTML = '<p class="no-history">Henüz kaydedilmiş skor yok.</p>';
                return;
            }
            history.sort((a, b) => {
                if (a.isFavorite && !b.isFavorite) return -1;
                if (!a.isFavorite && b.isFavorite) return 1;
                return new Date(b.date) - new Date(a.date);
            });
            history.forEach(score => {
                const li = document.createElement('li');
                li.classList.add('history-item');
                const date = new Date(score.date);
                const formattedDate = date.toLocaleString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
                li.innerHTML = `
                    <div class="history-details">
                        <span><strong>${score.wpm}</strong> WPM / <strong>${score.acc}%</strong> Doğruluk</span>
                        <span>Dil: ${score.lang === 'tr' ? 'Türkçe' : 'English'}</span>
                        <span class="history-date">${formattedDate}</span>
                    </div>
                    <span class="favorite-star ${score.isFavorite ? 'is-favorite' : ''}" data-id="${score.id}" title="Favorilere ekle/kaldır">★</span>
                `;
                historyList.appendChild(li);
            });
        }
        function toggleFavorite(scoreId) {
             let history = loadHistory();
             const scoreIndex = history.findIndex(score => score.id == scoreId);
             if (scoreIndex !== -1) {
                   history[scoreIndex].isFavorite = !history[scoreIndex].isFavorite;
                   saveHistory(history);
                   displayHistory();
             }
        }
        historyList.addEventListener('click', (event) => {
            if (event.target.classList.contains('favorite-star')) {
                const scoreId = event.target.getAttribute('data-id');
                toggleFavorite(scoreId);
            }
        });

        menuToggle.addEventListener('click', () => {
            historyContainer.classList.toggle('is-open');
            menuToggle.classList.toggle('active');
        });

        function initTest() {
            clearInterval(timerInterval);
            timerInterval = null;
            isTestActive = false;
            timeLeft = 60;
            timerDisplay.textContent = "1:00";
            currentWordIndex = 0;
            totalTypedEntries = 0;
            correctChars = 0;
            totalCharsIntended = 0;
            correctWordsCount = 0;
            incorrectWordsCount = 0;
            testStartTime = null;
            words = selectedLanguage === 'tr' ? [...wordsTr] : [...wordsEn];
            shuffleArray(words);
            words = words.slice(0, 150);
            loadWordsToDisplay();
            typingInput.value = '';
            typingInput.disabled = false;
            typingInput.classList.remove('error');
            typingInput.placeholder = 'Yazmaya başlayın...';
            typingInput.focus();
            resultsOverlay.style.display = 'none';
            restartBtn.style.display = 'none';
            wordDisplay.scrollTop = 0;
        }

        function loadWordsToDisplay() {
            wordDisplay.innerHTML = '';
            wordSpans = [];
            if (words.length === 0) {
                wordDisplay.textContent = 'Kelime listesi boş!'; return;
            }
            words.forEach((word) => {
                const span = document.createElement('span');
                span.textContent = word;
                wordDisplay.appendChild(span);
                wordDisplay.appendChild(document.createTextNode(' '));
                wordSpans.push(span);
            });
            wordSpans[0]?.classList.add('current');
        }

        function shuffleArray(array) {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
        }

        function startTestTimer() {
            if (isTestActive || timeLeft !== 60) return;
            isTestActive = true;
            testStartTime = performance.now();
            typingInput.placeholder = '';
            timerInterval = setInterval(updateTimer, 1000);
            updateTimer();
        }

        function updateTimer() {
            if (timeLeft <= 0) { endTest(); return; }
            timeLeft--;
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            timerDisplay.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
            if (timeLeft <= 0) { endTest(); }
        }

        typingInput.addEventListener('input', () => {
            if (!isTestActive && timeLeft === 60 && typingInput.value.trim().length > 0) { startTestTimer(); }
            if (!isTestActive) return;
            const currentWordSpan = wordSpans[currentWordIndex];
            if (!currentWordSpan) return;
            const targetWord = currentWordSpan.textContent;
            const typedValue = typingInput.value;
            if (targetWord.startsWith(typedValue)) { typingInput.classList.remove('error'); }
            else { typingInput.classList.add('error'); }
        });

        typingInput.addEventListener('keydown', (e) => {
            if (isTestActive) {
                if (e.key.length === 1 || e.key === 'Backspace') { totalTypedEntries++; }
                if (e.key === ' ' ) {
                    e.preventDefault();
                    const typedValue = typingInput.value;
                    if (typedValue.length > 0) {
                        const currentWordSpan = wordSpans[currentWordIndex];
                        if (currentWordSpan) {
                            const targetWord = currentWordSpan.textContent;
                            processWord(typedValue, targetWord, currentWordSpan);
                        }
                    }
                }
            } else if (timeLeft === 60 && e.key === ' ') { e.preventDefault(); }
        });

        function processWord(typedWord, targetWord, wordSpan) {
            if (!isTestActive) return;
            totalCharsIntended += targetWord.length + 1;
            wordSpan.classList.remove('current');
            if (typedWord === targetWord) {
                correctWordsCount++;
                correctChars += targetWord.length + 1;
                wordSpan.classList.add('correct');
            } else {
                incorrectWordsCount++;
                wordSpan.classList.add('incorrect');
            }
            currentWordIndex++;
            if (currentWordIndex >= wordSpans.length) { endTest(); return; }
            const nextWordSpan = wordSpans[currentWordIndex];
            if (nextWordSpan) {
                nextWordSpan.classList.add('current');
                scrollToCurrentWord(nextWordSpan);
            }
            typingInput.value = '';
            typingInput.classList.remove('error');
        }

        function scrollToCurrentWord(currentSpan) {
            const displayRect = wordDisplay.getBoundingClientRect();
            const wordRect = currentSpan.getBoundingClientRect();
            const isOutOfView = wordRect.top < displayRect.top || wordRect.bottom > displayRect.bottom;
            if (isOutOfView) {
                const scrollTopOffset = wordRect.top - displayRect.top - (displayRect.height / 2) + (wordRect.height / 2);
                wordDisplay.scrollTop += scrollTopOffset;
            }
        }

        function endTest() {
            if (!isTestActive) return;
            clearInterval(timerInterval);
            timerInterval = null;
            isTestActive = false;
            typingInput.disabled = true;
            typingInput.placeholder = 'Test tamamlandı!';
            const endTime = performance.now();
            const elapsedTimeSeconds = testStartTime ? (endTime - testStartTime) / 1000 : 60;
            const elapsedTimeMinutes = elapsedTimeSeconds / 60;
            let netWpm = 0;
            let accuracy = 0;
            if (elapsedTimeMinutes > 0) {
                netWpm = Math.max(0, Math.round((correctChars / 5) / elapsedTimeMinutes));
                accuracy = totalCharsIntended > 0 ? Math.max(0, Math.min(100, Math.round((correctChars / totalCharsIntended) * 100))) : 0;
            }
            resultWpm.textContent = netWpm;
            resultAcc.textContent = accuracy;
            resultCorrectWords.textContent = correctWordsCount;
            resultIncorrectWords.textContent = incorrectWordsCount;
            resultTotalKeys.textContent = totalTypedEntries;
            resultCorrectKeys.textContent = correctChars;
            const newScore = {
                id: Date.now(), wpm: netWpm, acc: accuracy,
                lang: selectedLanguage, date: new Date().toISOString(), isFavorite: false
            };
            addScoreToHistory(newScore);
            resultsOverlay.style.display = 'block';
            restartBtn.style.display = 'inline-block';
        }

        langTrBtn.addEventListener('click', () => {
            if (isTestActive) return;
            selectedLanguage = 'tr';
            langTrBtn.classList.add('active');
            langEnBtn.classList.remove('active');
            initTest();
        });
        langEnBtn.addEventListener('click', () => {
            if (isTestActive) return;
            selectedLanguage = 'en';
            langEnBtn.classList.add('active');
            langTrBtn.classList.remove('active');
            initTest();
        });
        restartBtn.addEventListener('click', initTest);

        document.addEventListener('DOMContentLoaded', () => {
            initTest();
            displayHistory();
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
    port = 5011

    print("="*60)
    print("⌨️  10 Parmak Yazı Testi (Otomatik Temalı) başlatılıyor...")
    print(f"   -> Bilgisayardan erişim: http://localhost:{port}")
    if local_ip != "127.0.0.1":
        print(f"   -> Ağdaki diğer cihazlardan erişim: http://{local_ip}:{port}")
    else:
        print("   -> Yerel IP adresi bulunamadı, ağdan erişim için 'ipconfig' kullanın.")
    print("Tema, işletim sisteminizin aydınlık/karanlık moduna göre otomatik ayarlanır.")
    print("="*60)

    app.run(debug=True, host='0.0.0.0', port=port)