# -*- coding: utf-8 -*-
import base64
import io
import json
import os
import re
import time
import traceback

import google.genai as genai
import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template_string, request
from google.genai.errors import APIError
from PIL import Image
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from thefuzz import fuzz
from webdriver_manager.chrome import ChromeDriverManager

import subprocess
import sys

app = Flask(__name__)
TESTER_APP_MAP = {
    "telefon": ["Telefon", "http://localhost:5002"],
    "phone": ["Telefon", "http://localhost:5002"],
    "akıllı telefon": ["Telefon", "http://localhost:5002"],
    "oyun konsolu kolu": ["Gamepad", "http://localhost:5004"],
    "gamepad": ["Gamepad", "http://localhost:5004"],
    "oyun kolu": ["Gamepad", "http://localhost:5004"],
    "klavye": ["Klavye", "http://localhost:5003"],
    "keyboard": ["Klavye", "http://localhost:5003"],
    "kulaklık": ["Kulaklık", "http://localhost:5005"],
    "headphone": ["Kulaklık", "http://localhost:5005"],
    "fare": ["Fare", "http://localhost:5006"],
    "mouse": ["Fare", "http://localhost:5006"],
}



current_file_path = os.path.abspath(__file__)
base_dir = os.path.dirname(current_file_path)



# TESTER UYGULAMALARINI OTOMATIK BAŞLATMA

TESTER_PROCESSES = []  # Çalışan process'leri saklamak için

def start_tester_apps():
    """
    Tüm tester uygulamalarını arka planda SESSİZCE başlatır.
    (Yeni konsol pencereleri AÇILMAZ)
    """
    tester_files = [
        (os.path.join(base_dir, "phone_info.py")  , 5002),
        (os.path.join(base_dir, "keyboard_tester.py") , 5003),
        (os.path.join(base_dir, "gamepad_tester.py")   , 5004),
        (os.path.join(base_dir, "headphone_tester.py"), 5005),
        (os.path.join(base_dir, "mouse_tester.py")    , 5006),
    ]

    # Windows için "pencere gizleme" bayrağını ayarla
    hide_window_flag = 0
    if sys.platform == 'win32':
        hide_window_flag = subprocess.CREATE_NO_WINDOW

    print("Sessiz modda başlatılıyor (pencereler gizlendi)...")

    for file_name, port in tester_files:
        if not os.path.exists(file_name):
            print(f"⚠️ UYARI: '{file_name}' bulunamadı, atlanıyor...")
            continue

        try:
            # Arka planda SESSİZCE başlat
            process = subprocess.Popen(
                [sys.executable, file_name],
                cwd=base_dir,
                stdout=subprocess.DEVNULL,       # Normal çıktıları gizle (boşluğa gönder)
                stderr=subprocess.DEVNULL,       # Hata çıktılarını gizle (boşluğa gönder)
                creationflags=hide_window_flag   # Konsol penceresi oluşturma (Windows'a özel)
            )
            TESTER_PROCESSES.append(process)
            print(f"✅ {file_name} sessizce başlatıldı (Port: {port})")

        except Exception as e:
            print(f"❌ HATA: {file_name} başlatılamadı - {e}")

    print(f"\n🚀 Toplam {len(TESTER_PROCESSES)} tester uygulaması arka planda başlatıldı.\n")


# === YENİ FONKSİYONU BURAYA EKLEYİN ===
def stop_tester_apps():
    """
    'start_tester_apps' ile başlatılan tüm subprocess'leri sonlandırır.
    """
    print(f"\n\n🛑 {len(TESTER_PROCESSES)} adet tester uygulaması durduruluyor...")
    count = 0
    for process in TESTER_PROCESSES:
        try:
            process.terminate()  # Süreci sonlandır (terminate SIGTERM gönderir)
            print(f"PID {process.pid} sonlandırıldı.")
            count += 1
        except Exception as e:
            print(f"❌ HATA: PID {process.pid} sonlandırılamadı - {e}")

    print(f"\n✅ Toplam {count} tester uygulaması başarıyla durduruldu.")

# ==============================================================================
# 1. GEMINI VE API ANAHTARI YÖNETİMİ
# ==============================================================================
#  Windows kullanıcı isminizi aşağıya ekleyiniz kendi apikey inizi ilgili konumdaki txt dosyasına ekleyiniz :  Users/Your_Username
def get_api_key_from_file(file_path: str = os.path.join(base_dir, "Your_Gemini_Api_Key.txt")) -> str:
    """Belirtilen dosyadan API anahtarını okur."""
    environment_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if environment_key:
        return environment_key
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            api_key = f.read().strip()
            if not api_key:
                raise ValueError("API anahtarı dosyada boş.")
            return api_key
    except FileNotFoundError:
        print(f"HATA: '{file_path}' dosyası bulunamadı.")
        return None
    except Exception as e:
        print(f"Dosya okuma hatası: {e}")
        return None

API_KEY = get_api_key_from_file()
if not API_KEY:
    print("UYARI: API anahtarı yüklenemedi. Program Gemini özellikleri olmadan çalışmayabilir.")
else:
    print("Gemini API anahtarı başarıyla yüklendi.")



# ==============================================================================
# 2. GEMINI GÖRSEL ANALİZ FONKSİYONLARI (PyTorch Modelinin Yerine Geçti)
# ==============================================================================
# BU FONKSİYONU GÜNCELLEYİN
# MEVCUT analyze_device_surface FONKSİYONUNU SİLİP BUNU YAPIŞTIRIN



import re
import json
import traceback
from PIL import Image
import io



def analyze_device_surface(image_bytes, surface_type: str, genai_client):
    """
    Cihazın bir yüzünü (ön veya arka) analiz eder ve detaylı bilgiler döndürür.
    """
    img = Image.open(io.BytesIO(image_bytes))
    model_name = 'gemini-2.5-flash'

    prompt = f"""
    Sen, ikinci el elektronik cihazların kozmetik durumunu ve fiziksel özelliklerini analiz eden bir uzmansın.
    Sana verilen fotoğraftaki cihazın '{surface_type.upper()}' YÜZÜNÜ dikkatlice incele.
    Tüm analizinin sonucunu, BAŞKA HİÇBİR AÇIKLAMA EKLEMEDEN, sadece ve sadece aşağıdaki formatta geçerli bir JSON nesnesi olarak döndür.

    {{
      "cihaz_turu": "Cihazın ana türünü belirt (Örn: Klavye, Telefon, Oyun Konsolu Kolu, Dizüstü Bilgisayar).",
      "cihaz_alt_turu": "Cihazın daha spesifik türünü belirt (Örn: Kablosuz Mekanik Klavye, Akıllı Telefon).",
      "kozmetik_puan": "Bu yüzün kozmetik durumunu 0.0 (çok kötü/kırık) ile 10.0 (yepyeni/kusursuz) arasında ondalıklı bir sayı olarak puanla.",
      "puan_gerekcesi": "Bu puanı neden verdiğini; çizik, leke, kırık, ezik, renk solması gibi kusurları veya kusursuzluğunu 1-2 cümle ile açıkla.",
      "marka": "Görseldeki marka logosunu veya tasarım dilini kullanarak markayı tespit et (Örn: Apple, Samsung, Logitech). Eğer belirgin değilse 'Bilinmiyor' yaz.",
      "model": "Eğer model belirginse yaz (Örn: Magic Keyboard, Galaxy S23 Ultra). Eğer belirgin değilse 'Bilinmiyor' yaz.",
      "ek_gozlemler": {{
        "renk": "Cihazın baskın rengini belirt (Örn: Gümüş, Uzay Grisi).",
        "tus_duzeni": "Eğer bir klavye ise tuş düzenini belirt (Örn: Türkçe Q, İngilizce QWERTY). Değilse 'Uygulanamaz' yaz.",
        "baglanti_tipi": "Görselde kablo görünüp görünmediğine bakarak bağlantı tipini tahmin et (Örn: Kablosuz (Bluetooth), Kablolu (USB-C)).",
        "tasarim_detaylari": "Tasarımıyla ilgili kompakt olması, sayısal tuş takımı olup olmaması gibi ek detayları belirt."
      }}
    }}
    """

    raw_text = ""
    try:
        response = genai_client.models.generate_content(
            model=model_name,
            contents=[prompt, img]
        )
        raw_text = response.text.strip()

        # JSON'u esnek bir şekilde ayıklama
        json_str = None
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            start_index = raw_text.find('{')
            end_index = raw_text.rfind('}')
            if start_index != -1 and end_index != -1 and end_index > start_index:
                json_str = raw_text[start_index:end_index+1]

        if not json_str:
            raise json.JSONDecodeError("Metin içinde JSON nesnesi bulunamadı.", raw_text, 0)

        full_analysis_data = json.loads(json_str)

        # Geriye uyumlu format için veriyi düzenle
        return_data = {
            "predicted_class": full_analysis_data.get("cihaz_turu", "hata"),
            "cosmetic_score": round(float(full_analysis_data.get("kozmetik_puan", 5.0)), 2),
            "analysis_commentary": full_analysis_data.get("puan_gerekcesi", "Yorum alınamadı."),
            "full_analysis": full_analysis_data,
            "surface_type": surface_type  # Hangi yüz olduğunu ekle
        }
        return return_data

    except json.JSONDecodeError as e:
        print(f"!!! {surface_type.capitalize()} YÜZÜ ANALİZİ JSON PARSE HATASI !!!")
        print(f"Hata Mesajı: {e}\n--- Gemini'den Gelen Ham Metin ---\n{raw_text}\n--------------------")
        return {
            "predicted_class": "json_hatasi",
            "cosmetic_score": 5.0,
            "analysis_commentary": f"{surface_type.capitalize()} yüzü analizi sırasında JSON formatı anlaşılamadı.",
            "full_analysis": {"hata": "JSON parse hatası", "gelen_metin": raw_text},
            "surface_type": surface_type
        }
    except Exception as e:
        print(f"{surface_type.capitalize()} Yüzü Analizi Genel Hatası: {e}")
        traceback.print_exc()
        return {
            "predicted_class": "genel_hata",
            "cosmetic_score": 5.0,
            "analysis_commentary": f"{surface_type.capitalize()} yüzü analizi sırasında genel bir hata oluştu: {e}",
            "full_analysis": {"hata": "Genel analiz hatası", "mesaj": str(e)},
            "surface_type": surface_type
        }

def ai_log_formatla(front_data, back_data, combined_score):
    """
    Detaylı AI analiz logunu formatlar.
    """
    # Ana bilgileri başarılı olan analizden al (öncelikle ön yüz)
    front_analysis = front_data.get("full_analysis", {})
    back_analysis = back_data.get("full_analysis", {})

    # Hangi analiz daha güvenilir bilgi içeriyor?
    primary_source = front_analysis if "hata" not in front_analysis else back_analysis
    ek_gozlemler = primary_source.get("ek_gozlemler", {})

    # Genel durum özeti oluştur
    if combined_score >= 9:
        genel_durum = "Mükemmel - Neredeyse yeni gibi, minimal kullanım izi"
    elif combined_score >= 8:
        genel_durum = "Çok İyi - Hafif kullanım izleri, genel olarak harika durumda"
    elif combined_score >= 7:
        genel_durum = "İyi - Normal kullanım izleri, fonksiyonel olarak sorunsuz"
    elif combined_score >= 6:
        genel_durum = "Orta - Belirgin kullanım izleri mevcut"
    elif combined_score >= 5:
        genel_durum = "Vasat - Çok sayıda kozmetik kusur var"
    else:
        genel_durum = "Kötü - Ciddi hasar veya aşınma mevcut"

    log_text = f"""
═══════════════════════════════════════════════════════════════
📱 CİHAZ BİLGİLERİ
═══════════════════════════════════════════════════════════════
Cihaz Türü      : {primary_source.get('cihaz_turu', 'Bilinmiyor')}
Cihaz Alt Türü  : {primary_source.get('cihaz_alt_turu', 'Bilinmiyor')}
Marka           : {primary_source.get('marka', 'Bilinmiyor')}
Model           : {primary_source.get('model', 'Bilinmiyor')}

═══════════════════════════════════════════════════════════════
🎨 TASARIM VE GÖZLEMLER
═══════════════════════════════════════════════════════════════
Renk            : {ek_gozlemler.get('renk', 'Belirtilmemiş')}
Bağlantı Tipi   : {ek_gozlemler.get('baglanti_tipi', 'Belirtilmemiş')}
Tuş Düzeni      : {ek_gozlemler.get('tus_duzeni', 'Uygulanamaz')}
Tasarım Detayları: {ek_gozlemler.get('tasarim_detaylari', 'Ek bilgi yok')}

═══════════════════════════════════════════════════════════════
💎 BİRLEŞİK KOZMETİK DURUM
═══════════════════════════════════════════════════════════════
Genel Puan      : {combined_score} / 10
Değerlendirme   : {genel_durum}
Hesaplama       : Ön yüz %60 + Arka yüz %40 ağırlıklı ortalama

═══════════════════════════════════════════════════════════════
🔍 ÖN YÜZ ANALİZİ (Ağırlık: %60)
═══════════════════════════════════════════════════════════════
Puan: {front_analysis.get('kozmetik_puan', '?')}/10
Tespit Edilen Sınıf: {front_data.get('predicted_class', 'Bilinmiyor')}

Detaylı Değerlendirme:
{front_data.get('analysis_commentary', 'Ön yüz analizi bulunamadı.')}

═══════════════════════════════════════════════════════════════
🔍 ARKA YÜZ ANALİZİ (Ağırlık: %40)
═══════════════════════════════════════════════════════════════
Puan: {back_analysis.get('kozmetik_puan', '?')}/10
Tespit Edilen Sınıf: {back_data.get('predicted_class', 'Bilinmiyor')}

Detaylı Değerlendirme:
{back_data.get('analysis_commentary', 'Arka yüz analizi bulunamadı.')}

═══════════════════════════════════════════════════════════════
"""

    # Eğer hatalar varsa ekle
    if "hata" in front_analysis:
        log_text += f"\n⚠️ ÖN YÜZ UYARI: {front_analysis.get('hata', 'Bilinmeyen hata')}\n"
    if "hata" in back_analysis:
        log_text += f"\n⚠️ ARKA YÜZ UYARI: {back_analysis.get('hata', 'Bilinmeyen hata')}\n"

    return log_text


# ==============================================================================
# 3. WEB SCRAPING VE FİYATLANDIRMA
# ==============================================================================
def fetch_prices(urun_adi):
    """
    Akakçe ve Letgo'dan ürün fiyatlarını çeker. Bu fonksiyon,
    doğru çalıştığını belirttiğiniz ilk kodunuzdan alınmıştır.
    """
    letgo_sonuclari = []
    akakce_sonuclari = []
    minimum_akakce_fiyat = None

    # --- Akakçe Bölümü ---
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        akakce_url = f"https://www.akakce.com/arama/?q={requests.utils.quote(urun_adi)}"
        driver.get(akakce_url)
        time.sleep(3)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        astro_island_tag = soup.find("astro-island", attrs={"component-export": "SearchWrapper"})

        if astro_island_tag:
            props_data = json.loads(astro_island_tag['props'])
            search_data = props_data.get('searchData', [None, {}])[1]
            product_list_wrapper = search_data.get('productList', [None, {}])[1]
            products_raw = product_list_wrapper.get('products', [None, []])[1]

            if products_raw and len(products_raw) > 0:
                for product_item in products_raw[:5]:
                    product_data = product_item[1]
                    urun_ismi = product_data.get('name', [None, ''])[1]
                    fiyat_raw = product_data.get('price', [None, 0])[1]
                    renk_variants = product_data.get('colorVariants', [None, []])[1]

                    if minimum_akakce_fiyat is None or fiyat_raw < minimum_akakce_fiyat:
                        minimum_akakce_fiyat = fiyat_raw

                    akakce_sonuclari.append({
                        "urun": urun_ismi,
                        "renk": renk_variants[0][1] if renk_variants else "Renk bilgisi yok",
                        "fiyat": f"{fiyat_raw:,.2f} TL".replace(',', '.'),
                        "fiyat_raw": fiyat_raw
                    })

        driver.quit()
    except Exception as e:
        print(f"Akakce hatasi: {e}")
        if 'driver' in locals() and driver:
            driver.quit()

    # --- Letgo Bölümü ---
    try:
        letgo_url = f"https://www.letgo.com/arama?query_text={requests.utils.quote(urun_adi)}&isSearchCall=true"
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        options.add_argument('--headless')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(letgo_url)

        wait = WebDriverWait(driver, 15)
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Kabul Et')]"))).click()
            time.sleep(1)
        except TimeoutException:
            pass # Popup yoksa devam et

        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".item-card-container")))
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        listings = soup.select(".item-card-container")

        if listings:
            for listing in listings:
                title_tag = listing.find("span", class_="item-title")
                price_tag = listing.find("div", class_="item-price")
                title_text = title_tag.get_text(strip=True) if title_tag else ""
                price_text = price_tag.get_text(strip=True) if price_tag else "Fiyat Bilgisi Yok"

                if title_text and price_text != "Fiyat Bilgisi Yok":
                    score = fuzz.token_set_ratio(urun_adi, title_text)

                    try:
                        fiyat_text = price_text.replace('TL', '').replace('.', '').replace(',', '.').strip()
                        fiyat_text = fiyat_text.split('taksit')[0].split('kargo')[0].strip()
                        fiyat_numeric = float(fiyat_text.split()[0])

                        # Fiyatın mantıklı bir aralıkta olduğunu kontrol et
                        if minimum_akakce_fiyat and fiyat_numeric >= (minimum_akakce_fiyat * 0.4):
                            letgo_sonuclari.append({
                                "title": title_text,
                                "price": price_text,
                                "fiyat_numeric": fiyat_numeric,
                                "score": score
                            })
                    except:
                        continue

            letgo_sonuclari = sorted(letgo_sonuclari, key=lambda x: x['score'], reverse=True)

        driver.quit()
    except Exception as e:
        print(f"Letgo hatasi: {e}")
        if 'driver' in locals() and driver:
            driver.quit()

    return akakce_sonuclari, letgo_sonuclari, minimum_akakce_fiyat



def calculate_price(cosmetic_score, akakce_sonuclari, letgo_sonuclari):
    """
    Kozmetik puana ve piyasa verilerine göre fiyatı hesaplar. Bu fonksiyon,
    doğru çalıştığını belirttiğiniz ilk kodunuzdan alınmıştır.
    """
    if not akakce_sonuclari:
        return None

    min_sifir_fiyat = min(item['fiyat_raw'] for item in akakce_sonuclari if item['fiyat_raw'] > 0)

    if cosmetic_score >= 9.7:
        deger_kaybi = 0.10
    elif cosmetic_score >= 9.5:
        deger_kaybi = 0.15
    elif cosmetic_score >= 9:
        deger_kaybi = 0.20
    elif cosmetic_score >= 8.5:
        deger_kaybi = 0.28
    elif cosmetic_score >= 8:
        deger_kaybi = 0.30
    elif cosmetic_score >= 7:
        deger_kaybi = 0.35
    elif cosmetic_score >= 6:
        deger_kaybi = 0.40
    elif cosmetic_score >= 5:
        deger_kaybi = 0.55
    else:
        deger_kaybi = 0.70

    tahmini_fiyat_sifir_based = min_sifir_fiyat * (1 - deger_kaybi)
    letgo_fiyatlari_raw = [item['fiyat_numeric'] for item in letgo_sonuclari if 'fiyat_numeric' in item]

    # Filtreleme
    upper_limit = min_sifir_fiyat * 0.95
    lower_limit = min_sifir_fiyat * 0.40
    filtered_letgo_fiyatlari = [f for f in letgo_fiyatlari_raw if lower_limit <= f <= upper_limit]

    if filtered_letgo_fiyatlari:
        ortalama_letgo_fiyat = sum(filtered_letgo_fiyatlari) / len(filtered_letgo_fiyatlari)
        # Ağırlıklı Ortalama: %70 sıfır fiyata dayalı tahmin, %30 ikinci el piyasasına dayalı tahmin
        tahmini_fiyat = (tahmini_fiyat_sifir_based * 0.70) + (ortalama_letgo_fiyat * 0.30)
        letgo_avg = round(ortalama_letgo_fiyat, 2)
    else:
        tahmini_fiyat = tahmini_fiyat_sifir_based
        letgo_avg = None

    return {
        "tahmini_fiyat": round(tahmini_fiyat, 2),
        "min_fiyat": round(tahmini_fiyat * 0.9, 2),
        "max_fiyat": round(tahmini_fiyat * 1.1, 2),
        "sifir_fiyat": min_sifir_fiyat,
        "deger_kaybi": round(deger_kaybi * 100, 0),
        "letgo_ortalama": letgo_avg,
        "cosmetic_score": cosmetic_score
    }


# ==============================================================================
# 4. YARDIMCI FONKSİYONLAR VE ROTALAR
# ==============================================================================
def get_product_category(cihaz_turu: str) -> (str, str):
    """
    Gemini'den gelen 'cihaz_turu' bilgisine göre kategori ve tester URL'sini belirler.
    """
    if not cihaz_turu:
        return None, None

    cihaz_turu_lower = cihaz_turu.lower()

    # TESTER_APP_MAP içinde eşleşme ara
    for anahtar, (kategori_adi, url) in TESTER_APP_MAP.items():
        if anahtar in cihaz_turu_lower:
            return kategori_adi, url

    return None, None

# ==============================================================================
# 5. ANA FLASK ROTALARI (FRONTEND VE ANALİZ İŞLEMLERİ)
# ==============================================================================
@app.route('/')
def index():
    html = '''
    <!DOCTYPE html>
    <html lang="tr">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cihaz Değerlendirme Sistemi</title>
    <style>
        :root {
            --c-bg-grad-start: #667eea; --c-bg-grad-end: #764ba2; --c-body-bg: #f0f2f5; --c-text: #333; --c-text-secondary: #666; --c-container-bg: white; --c-shadow: 0 10px 30px rgba(0,0,0,0.1); --c-upload-border: #667eea; --c-upload-hover-bg: #f8f9ff; --c-upload-drag-bg: #e0e7ff; --c-input-border: #d1d5db; --c-input-focus-border: #667eea; --c-result-card-bg: #ffffff; --c-price-border: #667eea; --c-price-value: #667eea; --c-score-excellent: #10b981; --c-score-good: #f59e0b; --c-score-bad: #ef4444; --c-spinner-color: #667eea; --c-primary: #667eea;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --c-body-bg: #111827; --c-text: #e5e7eb; --c-text-secondary: #9ca3af; --c-container-bg: #1f2937; --c-shadow: 0 10px 30px rgba(0,0,0,0.5); --c-upload-border: #818cf8; --c-upload-hover-bg: #374151; --c-upload-drag-bg: #4b5563; --c-input-border: #4b5563; --c-input-focus-border: #818cf8; --c-result-card-bg: #1f2937; --c-price-border: #818cf8; --c-price-value: #818cf8; --c-score-excellent: #34d399; --c-score-good: #fbbf24; --c-score-bad: #f87171; --c-spinner-color: #818cf8; --c-primary: #818cf8;
            }
        }
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;background:var(--c-body-bg);color:var(--c-text);min-height:100vh;padding:20px;transition:background-color .3s,color .3s;line-height:1.6}
        .container{max-width:800px;margin:40px auto;background:var(--c-container-bg);border-radius:12px;padding:30px;box-shadow:var(--c-shadow);transition:background-color .3s,box-shadow .3s}
        h1{text-align:center;color:var(--c-primary);margin-bottom:25px;font-size:2em;font-weight:600}
        .upload-container{display:flex;gap:15px;margin-bottom:20px}
        .upload-area{border:2px dashed var(--c-upload-border);border-radius:8px;text-align:center;cursor:pointer;transition:all .2s ease-in-out;color:var(--c-text);flex:1;padding:25px 15px;margin-bottom:0;display:flex;flex-direction:column;justify-content:center;align-items:center;min-height:160px;background-color:var(--c-container-bg)}
        .upload-area:hover{background:var(--c-upload-hover-bg);border-color:var(--c-primary);transform:translateY(-2px)}
        .upload-area.dragover{background:var(--c-upload-drag-bg);border-style:solid}
        .upload-area p:first-of-type{font-size:2.5rem;margin-bottom:8px}
        .upload-area p:nth-of-type(2){font-size:1rem;font-weight:500;color:var(--c-text)}
        .upload-area p:nth-of-type(3){font-size:.85rem;color:var(--c-text-secondary);margin-top:4px}
        .upload-area .upload-success p:first-of-type{font-size:1.8rem;color:var(--c-score-excellent);margin-bottom:5px}
        .upload-area .upload-success p:last-of-type{color:var(--c-primary);font-size:.9rem;font-weight:500;word-break:break-all;padding:0 10px}
        input[type=file]{display:none}
        input[type=text]{width:100%;padding:12px 15px;border:1px solid var(--c-input-border);border-radius:6px;font-size:1rem;margin-bottom:20px;transition:border-color .2s,box-shadow .2s;background-color:var(--c-body-bg);color:var(--c-text)}
        input[type=text]:focus{outline:none;border-color:var(--c-input-focus-border);box-shadow:0 0 0 3px rgba(102,126,234,.2)}
        button#analyzeBtn{width:100%;padding:12px 15px;background:linear-gradient(135deg,var(--c-bg-grad-start) 0%,var(--c-bg-grad-end) 100%);color:#fff;border:none;border-radius:6px;font-size:1.1rem;font-weight:600;cursor:pointer;transition:transform .15s ease-out,box-shadow .15s ease-out}
        button#analyzeBtn:hover{transform:scale(1.015);box-shadow:0 4px 15px rgba(0,0,0,.2)}
        button#analyzeBtn:disabled{opacity:.6;cursor:not-allowed;transform:none;box-shadow:none}
        .results{display:none;margin-top:30px}
        .result-card{background:var(--c-container-bg);border:1px solid var(--c-input-border);border-radius:8px;padding:20px;margin-bottom:20px;transition:background-color .3s,border-color .3s}
        .ai-log-details summary,.result-card h3{color:var(--c-primary);margin-bottom:15px;font-size:1.2rem;font-weight:600;border-bottom:1px solid var(--c-input-border);padding-bottom:10px}
        .score-badge{display:inline-block;padding:8px 18px;border-radius:50px;font-size:1.4rem;font-weight:700;margin:5px 0 15px;color:#fff}
        .score-excellent{background:var(--c-score-excellent)}
        .score-good{background:var(--c-score-good)}
        .score-bad{background:var(--c-score-bad)}
        .price-box{background:var(--c-result-card-bg);border:1px solid var(--c-price-border);border-radius:8px;padding:20px;text-align:center;margin:15px 0}
        .price-big{font-size:2rem;font-weight:700;color:var(--c-price-value);margin:8px 0}
        .price-box p{font-size:.9rem}
        .loading{text-align:center;padding:40px;display:none}
        .spinner{border:4px solid var(--c-input-border);border-top:4px solid var(--c-spinner-color);border-radius:50%;width:40px;height:40px;animation:spin 1s linear infinite;margin:0 auto 15px}
        @keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
        .image-preview-container{display:flex;gap:10px;margin-bottom:20px}
        .preview-image{max-width:100%;border-radius:6px;flex:1;margin:0;object-fit:cover;max-height:250px;border:1px solid var(--c-input-border)}
        .price-detail{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid var(--c-input-border);font-size:.9rem}
        .price-detail:last-child{border-bottom:none}
        .price-label{font-weight:500;color:var(--c-text)}
        .price-value{color:var(--c-price-value);font-weight:500}
        .ai-log-details summary{border-bottom:none;padding-bottom:0;margin-bottom:0;cursor:pointer;list-style:none;display:flex;justify-content:space-between;align-items:center}
        .ai-log-details summary::-webkit-details-marker{display:none}
        .details-arrow{display:inline-block;width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-top:5px solid var(--c-text-secondary);transition:transform .2s;transform-origin:center;margin-left:10px}
        .ai-log-details[open]>summary .details-arrow{transform:rotate(180deg)}
        #aiLogResult{white-space:pre-wrap;font-family:Consolas,Monaco,'Andale Mono','Ubuntu Mono',monospace;font-size:.85rem;background:var(--c-body-bg);padding:12px;border-radius:6px;margin-top:15px;color:var(--c-text);border:1px solid var(--c-input-border);max-height:300px;overflow-y:auto}
        #testerButtonContainer button{background:var(--c-score-excellent);margin-top:10px;width:100%;padding:12px 15px;color:#fff;border:none;border-radius:6px;font-size:1.1rem;font-weight:600;cursor:pointer;transition:transform .15s ease-out,box-shadow .15s ease-out}
        #testerButtonContainer button:hover{background:#0f996d;transform:scale(1.015);box-shadow:0 4px 15px rgba(0,0,0,.2)}
    </style>
    </head>
    <body>
    <div class="container">
        <h1>Cihaz Değerlendirme</h1>
        <form id="analyzeForm">
            <div class="upload-container">
                <div class="upload-area" id="uploadAreaFront">
                    <p>📱</p><p>1. Ürünün Ön Fotoğrafı</p><p>(Ekran dahil)</p>
                    <input type="file" id="imageInputFront" accept="image/*" required>
                </div>
                <div class="upload-area" id="uploadAreaBack">
                    <p>📸</p><p>2. Ürünün Arka Fotoğrafı</p><p>(Kasa ve Kamera dahil)</p>
                    <input type="file" id="imageInputBack" accept="image/*" required>
                </div>
            </div>
            <input type="text" id="productName" placeholder="Urun adini girin (ornek: iPhone 14)" required>
            <button type="submit" id="analyzeBtn">Analiz Et ve Fiyatlandir</button>
        </form>
        <div class="loading" id="loading"><div class="spinner"></div><p>Analiz ediliyor, lütfen bekleyin...</p></div>
        <div class="results" id="results">
            <div class="image-preview-container">
                <img id="previewImageFront" class="preview-image" alt="Ön Görsel Önizleme">
                <img id="previewImageBack" class="preview-image" alt="Arka Görsel Önizleme">
            </div>
            <div class="result-card"><h3>Kozmetik Puanı</h3><div id="predictionResult"></div></div>
            <div class="result-card">
                <details class="ai-log-details" id="aiLogDetails">
                    <summary>Yapay Zeka Düşünce Logu<span class="details-arrow"></span></summary>
                    <div id="aiLogResult">Yapay zeka analizi sonrasinda yorum burada gorunecektir.</div>
                </details>
            </div>
            <div class="result-card"><h3>Tahmini Fiyat</h3><div id="priceResult"></div></div>
            <div class="result-card" id="testerButtonContainer" style="display:none; border: none; padding: 0;"></div>
            <div class="result-card"><h3>Piyasa Karsilastirma</h3><div id="marketResult"></div></div>
        </div>
    </div>
    <script>
        const form=document.getElementById("analyzeForm"),loading=document.getElementById("loading"),results=document.getElementById("results"),uploadAreaFront=document.getElementById("uploadAreaFront"),imageInputFront=document.getElementById("imageInputFront"),uploadAreaBack=document.getElementById("uploadAreaBack"),imageInputBack=document.getElementById("imageInputBack"),aiLogDetails=document.getElementById("aiLogDetails");function setupUploadArea(e,t){e.addEventListener("dragover",t=>{t.preventDefault(),e.classList.add("dragover")}),e.addEventListener("dragleave",()=>{e.classList.remove("dragover")}),e.addEventListener("drop",o=>{o.preventDefault(),e.classList.remove("dragover"),o.dataTransfer.files&&o.dataTransfer.files.length>0&&(t.files=o.dataTransfer.files,updateUploadText(e,t.files[0].name,!0))}),t.addEventListener("change",()=>{t.files&&t.files.length>0&&updateUploadText(e,t.files[0].name,!0)})}function updateUploadText(e,t,o){o?e.innerHTML='<div class="upload-success"><p>✅</p><p>'+escapeHtml(t.substring(0,25)+(t.length>25?"...":""))+"</p></div>":e.innerHTML=e.id.includes("Front")?'<p>📱</p><p>1. Ürünün Ön Fotoğrafı</p><p>(Ekran dahil)</p>':'<p>📸</p><p>2. Ürünün Arka Fotoğrafı</p><p>(Kasa ve Kamera dahil)</p>'}function escapeHtml(e){return e?e.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;"):""}function displayResults(e){document.getElementById("previewImageFront").src=e.image_front_b64||"",document.getElementById("previewImageFront").alt="Ön Görsel Önizleme",document.getElementById("previewImageBack").src=e.image_back_b64||"",document.getElementById("previewImageBack").alt="Arka Görsel Önizleme";const t=e.prediction||{},o=void 0!==t.combined_cosmetic_score?t.combined_cosmetic_score:"?";let a="score-bad";"number"==typeof o&&(o>=8?a="score-excellent":o>=6&&(a="score-good")),document.getElementById("predictionResult").innerHTML=`<div class="score-badge ${a}">${o}/10</div><p style="text-align:center; margin-bottom: 10px;"><strong>Genel Kozmetik Puanı</strong></p><div class="price-detail"><span class="price-label">Ön Yüz Puanı</span><span class="price-value">${void 0!==t.front_score?t.front_score:"?"}/10 (${escapeHtml(t.front_class||"?")})</span></div><div class="price-detail"><span class="price-label">Arka Yüz Puanı</span><span class="price-value">${void 0!==t.back_score?t.back_score:"?"}/10 (${escapeHtml(t.back_class||"?")})</span></div>`,
        document.getElementById("aiLogResult").textContent = t.detailed_ai_log || `--- EKRAN ANALİZİ ---\n${escapeHtml(t.front_commentary||"Yorum yok.")}\n\n--- KASA ANALİZİ ---\n${escapeHtml(t.back_commentary||"Yorum yok.")}`;
        const i=document.getElementById("priceResult");if(e.price){const t=e.price,o=t.letgo_ortalama?`<div class="price-detail"><span class="price-label">Ortalama İkinci El Fiyatı</span><span class="price-value">${t.letgo_ortalama.toLocaleString("tr-TR")} TL</span></div>`:"",a="number"==typeof t.sifir_fiyat?t.sifir_fiyat.toLocaleString("tr-TR")+" TL":t.sifir_fiyat||"Bulunamadı";i.innerHTML=`<div class="price-box"><p style="color:var(--c-text-secondary);">Tahmini Satis Degeri</p><div class="price-big">${(void 0!==t.tahmini_fiyat?t.tahmini_fiyat.toLocaleString("tr-TR"):"?")} TL</div><p style="color:var(--c-text-secondary);">${(void 0!==t.min_fiyat?t.min_fiyat.toLocaleString("tr-TR"):"?")} - ${(void 0!==t.max_fiyat?t.max_fiyat.toLocaleString("tr-TR"):"?")} TL (Onerilen Aralik)</p></div><div class="result-card" style="padding:15px; background:var(--c-body-bg); border-color: var(--c-input-border);"><div class="price-detail"><span class="price-label">Kozmetik Puanına Gore Deger Kaybi</span><span class="price-value"><strong>%${void 0!==t.deger_kaybi?t.deger_kaybi:"?"}</strong></span></div>${o}<div class="price-detail"><span class="price-label">Sifir Piyasa Fiyati (Akakce Min.)</span><span class="price-value">${a}</span></div></div>`}else i.innerHTML='<p style="color:var(--c-text-secondary); text-align:center;">Fiyat tahmini için yeterli piyasa verisi bulunamadı.</p>';let r='<h4>Akakce (Sifir Piyasa)</h4>';e.akakce&&e.akakce.length>0?e.akakce.forEach(e=>{r+=`<div style="font-size:0.9rem; padding:5px 0;">• ${escapeHtml(e.urun.substring(0,60))}... (${escapeHtml(e.fiyat)})</div>`}):r+='<p style="font-size:0.9rem; color:var(--c-text-secondary);">Akakcede benzer urun bulunamadi.</p>',r+='<h4 style="margin-top:20px;">Letgo (Ikinci El Fiyatlari)</h4>',e.letgo&&e.letgo.length>0?e.letgo.forEach(e=>{r+=`<div style="font-size:0.9rem; padding:5px 0;">• ${escapeHtml(e.title.substring(0,60))}... (${escapeHtml(e.price)})</div>`}):r+='<p style="font-size:0.9rem; color:var(--c-text-secondary);">Letgoda benzer urun bulunamadi.</p>',document.getElementById("marketResult").innerHTML=r;const l=document.getElementById("testerButtonContainer");e.tester_url&&e.product_category?(l.innerHTML=`<h3 style="margin-bottom: 15px;">Sonraki Adım</h3><p style="margin-bottom: 15px; color: var(--c-text-secondary);">Cihazın fiyatlandırması tamamlandı. Fonksiyonel teste devam etmek için butona tıklayın.</p><a href="${escapeHtml(e.tester_url)}" target="_blank" style="text-decoration: none;"><button>Fonksiyon Testine Başla (Cihaz Tipi: ${escapeHtml(e.product_category)})</button></a>`,l.style.display="block"):l.style.display="none",results.style.display="block"}uploadAreaFront.addEventListener("click",()=>imageInputFront.click()),uploadAreaBack.addEventListener("click",()=>imageInputBack.click()),setupUploadArea(uploadAreaFront,imageInputFront),setupUploadArea(uploadAreaBack,imageInputBack),form.addEventListener("submit",async e=>{if(e.preventDefault(),!imageInputFront.files||0===imageInputFront.files.length||!imageInputBack.files||0===imageInputBack.files.length)return void alert("Lütfen hem ön hem de arka fotoğrafı yükleyin.");const t=new FormData;t.append("image_front",imageInputFront.files[0]),t.append("image_back",imageInputBack.files[0]),t.append("product_name",document.getElementById("productName").value),loading.style.display="block",results.style.display="none",aiLogDetails.removeAttribute("open");try{const e=await fetch("/analyze",{method:"POST",body:t}),o=await e.json();e.ok&&o.success?displayResults(o):alert("Hata: "+(o.error||`Sunucu hatası: ${e.status}`))}catch(e){console.error("Fetch hatası:",e),alert("Bir ağ hatası oluştu: "+e.message)}finally{loading.style.display="none",form.reset(),updateUploadText(uploadAreaFront,"",!1),updateUploadText(uploadAreaBack,"",!1)}});
    </script>
    </body>
    </html>
    '''
    return render_template_string(html)


@app.route('/analyze', methods=['POST'])
def analyze():
    if not API_KEY:
        return jsonify({"success": False, "error": "Sunucu API anahtarı yapılandırılamadı."}), 500

    try:
        genai_client = genai.Client(api_key=API_KEY)
    except Exception as e:
        print(f"Gemini istemci oluşturma hatası: {e}")
        return jsonify({"success": False, "error": f"Gemini istemcisi oluşturulamadı: {e}"}), 500

    try:
        # 1. Girdileri Al
        image_file_front = request.files.get('image_front')
        image_file_back = request.files.get('image_back')
        urun_adi = request.form.get('product_name')

        if not all([image_file_front, image_file_back, urun_adi]):
            return jsonify({"success": False, "error": "Eksik bilgi: Lütfen iki görseli de yükleyin ve ürün adını girin."}), 400

        image_bytes_front = image_file_front.read()
        image_bytes_back = image_file_back.read()

        # 2. Gemini ile Görselleri Analiz Et
        print("Ön yüz analizi başlıyor...")
        front_data = analyze_device_surface(image_bytes_front, "ön", genai_client)
        print(f"Ön yüz analizi sonucu: {front_data}")

        print("Arka yüz analizi başlıyor...")
        back_data = analyze_device_surface(image_bytes_back, "arka", genai_client)
        print(f"Arka yüz analizi sonucu: {back_data}")

        # 3. Kozmetik Puanları Birleştir (Ön yüz %60, Arka yüz %40 ağırlıklı)
        combined_score = round((front_data['cosmetic_score'] * 0.6) + (back_data['cosmetic_score'] * 0.4), 1)

        # 4. Detaylı AI Logu Oluştur
        detailed_ai_log = ai_log_formatla(front_data, back_data, combined_score)

        # 5. Fiyatları Çek ve Hesapla
        print(f"'{urun_adi}' için piyasa fiyatları çekiliyor...")
        akakce, letgo, min_price = fetch_prices(urun_adi)
        print("Fiyat hesaplaması yapılıyor...")
        price_info = calculate_price(combined_score, akakce, letgo)
        print(f"Fiyat hesaplama sonucu: {price_info}")

        # 6. Tester URL'ini Belirle
        # 6. Tester URL'ini Belirle (Gemini'den gelen cihaz türünü kullan)
        cihaz_turu = front_data.get('full_analysis', {}).get('cihaz_turu', '')
        category, tester_url = get_product_category(cihaz_turu)

        # 7. Yanıtı Hazırla
        image_base64_front = base64.b64encode(image_bytes_front).decode('utf-8')
        image_base64_back = base64.b64encode(image_bytes_back).decode('utf-8')

        response_data = {
            "success": True,
            "image_front_b64": f"data:{image_file_front.mimetype};base64,{image_base64_front}",
            "image_back_b64": f"data:{image_file_back.mimetype};base64,{image_base64_back}",
            "prediction": {
                "front_score": front_data.get('cosmetic_score'),
                "front_class": front_data.get('predicted_class'),
                "front_commentary": front_data.get('analysis_commentary'),
                "front_full_analysis": front_data.get('full_analysis'),
                "back_score": back_data.get('cosmetic_score'),
                "back_class": back_data.get('predicted_class'),
                "back_commentary": back_data.get('analysis_commentary'),
                "back_full_analysis": back_data.get('full_analysis'),
                "combined_cosmetic_score": combined_score,
                "detailed_ai_log": detailed_ai_log  # YENİ: Detaylı log
            },
            "price": price_info,
            "akakce": akakce[:5],
            "letgo": letgo[:5],
            "tester_url": tester_url,
            "product_category": category
        }
        return jsonify(response_data)

    except Exception as e:
        print(f"ANALİZ SIRASINDA BEKLENMEDİK HATA: {e}")
        traceback.print_exc()
        return jsonify({"success": False, "error": "Beklenmedik bir sunucu hatası oluştu. Lütfen tekrar deneyin."}), 500

# ==============================================================================
# 6. UYGULAMAYI BAŞLATMA
# ==============================================================================

if __name__ == '__main__':
    if not API_KEY:
        print("="*50)
        print("HATA: 'api_key.txt' dosyası bulunamadı veya boş.")
        print("="*50)
    else:
        print("="*60)
        print("🔧 TESTER UYGULAMALARI BAŞLATILIYOR...")
        print("="*60)
        start_tester_apps()

        print("="*60)
        print("🌐 ANA UYGULAMA BAŞLATILIYOR (Port: 5001)")
        print("="*60)

        try:
            app.run(debug=False, host='0.0.0.0', port=5001, use_reloader=False)
        except KeyboardInterrupt:
            print("\n\n⚠️ Uygulama durduruluyor...")
        finally:
            stop_tester_apps()


