from flask import Flask, render_template_string, request, jsonify
import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import io
import base64
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import time
import requests
from thefuzz import fuzz

app = Flask(__name__)

# === MODEL TANIMLAMA ===
IMG_SIZE = 128
CLASS_NAMES = ['groundtruth', 'oil', 'scratch', 'stain']

class SimpleCNN(nn.Module):
    def __init__(self, num_classes):
        super(SimpleCNN, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(kernel_size=2, stride=2)
        )
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * (IMG_SIZE // 8) * (IMG_SIZE // 8), 128),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Modelin yükleneceği yolun güncel olduğundan emin olun!   Users/username olarak değiştirmeyi unutmayın
try:
    model = SimpleCNN(num_classes=len(CLASS_NAMES)).to(device)
    #  Windows kullanıcı isminizi aşağıya ekleyiniz :  Users/Your_Username
    model.load_state_dict(torch.load(os.path.join(os.path.dirname(os.path.abspath(__file__)), "defect_classifier_model.pth"), map_location=device))
    model.eval()
    print("Makine öğrenimi modeli başarıyla yüklendi.")
except Exception as e:
    print(f"UYARI: Model yüklenemedi. Test amaçlı bir model oluşturuluyor. Hata: {e}")
    # Gerçek model yoksa, programın çökmemesi için basit bir yer tutucu model kullanabilirsiniz.
    # Ancak bu durumda tahminler doğru olmayacaktır.
    # Modelin doğru yolu ile değiştirilmelidir.
    class DummyModel:
        def eval(self): pass
        def __call__(self, x): return torch.zeros((1, len(CLASS_NAMES)))
    model = DummyModel()

transform = transforms.Compose([
    transforms.Resize(IMG_SIZE),
    transforms.CenterCrop(IMG_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

def predict_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    input_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = model(input_tensor)

    probabilities = torch.nn.functional.softmax(output[0], dim=0)
    predicted_class_idx = torch.argmax(probabilities).item()
    predicted_class_name = CLASS_NAMES[predicted_class_idx]
    confidence = probabilities[predicted_class_idx].item()

    cosmetic_score = 10.0
    if predicted_class_name != 'groundtruth':
        if predicted_class_name == 'oil':
            cosmetic_score -= (confidence * 2)
        elif predicted_class_name == 'scratch':
            cosmetic_score -= (confidence * 4)
        elif predicted_class_name == 'stain':
            cosmetic_score -= (confidence * 3)
        cosmetic_score = max(0.0, min(10.0, cosmetic_score))

    return {
        "predicted_class": predicted_class_name,
        "confidence": round(confidence * 100, 2),
        "cosmetic_score": round(cosmetic_score, 2)
    }

def fetch_prices(urun_adi):
    letgo_sonuclari = []
    akakce_sonuclari = []
    minimum_akakce_fiyat = None

    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        # ChromeDriverManager otomatik olarak sürücüyü indirir
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

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

    try:
        letgo_url = f"https://www.letgo.com/arama?query_text={requests.utils.quote(urun_adi)}&isSearchCall=true"
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        options.add_argument('--headless')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(letgo_url)

        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import TimeoutException

        wait = WebDriverWait(driver, 15)
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Kabul Et')]"))).click()
            time.sleep(1)
        except TimeoutException:
            pass

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

    return akakce_sonuclari, letgo_sonuclari, minimum_akakce_fiyat

def calculate_price(cosmetic_score, akakce_sonuclari, letgo_sonuclari):
    if not akakce_sonuclari:
        return None

    min_sifir_fiyat = akakce_sonuclari[0]['fiyat_raw']

    if cosmetic_score >= 9:
        deger_kaybi = 0.15
    elif cosmetic_score >= 8:
        deger_kaybi = 0.20
    elif cosmetic_score >= 7:
        deger_kaybi = 0.30
    elif cosmetic_score >= 6:
        deger_kaybi = 0.35
    elif cosmetic_score >= 5:
        deger_kaybi = 0.55
    else:
        deger_kaybi = 0.600

    tahmini_fiyat_sifir_based = min_sifir_fiyat * (1 - deger_kaybi)
    letgo_fiyatlari_raw = [item['fiyat_numeric'] for item in letgo_sonuclari if 'fiyat_numeric' in item]
    upper_limit = min_sifir_fiyat * 0.95
    lower_limit = min_sifir_fiyat * 0.40

    filtered_letgo_fiyatlari = [f for f in letgo_fiyatlari_raw if f <= upper_limit and f >= lower_limit]

    if filtered_letgo_fiyatlari:
        ortalama_letgo_fiyat = sum(filtered_letgo_fiyatlari) / len(filtered_letgo_fiyatlari)
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

@app.route('/')
def index():
    html = '''<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Telefon Degerlendirme Sistemi</title>
<style>
/* --- OTOMATİK TEMA DEĞİŞKENLERİ --- */
:root {
    /* Varsayılan: Aydınlık Tema */
    --c-bg-grad-start: #667eea;
    --c-bg-grad-end: #764ba2;
    --c-body-bg: #f0f2f5;
    --c-text: #333;
    --c-text-secondary: #666;
    --c-container-bg: white;
    --c-shadow: 0 20px 60px rgba(0,0,0,0.3);
    --c-upload-border: #667eea;
    --c-upload-hover-bg: #f8f9ff;
    --c-upload-drag-bg: #e0e7ff;
    --c-input-border: #e0e0e0;
    --c-input-focus-border: #667eea;
    --c-result-card-bg: #f8f9ff;
    --c-price-border: #667eea;
    --c-price-value: #667eea;
    --c-score-excellent: #10b981;
    --c-score-good: #f59e0b;
    --c-score-bad: #ef4444;
    --c-spinner-color: #667eea;
}

@media (prefers-color-scheme: dark) {
    :root {
        /* Karanlık Tema */
        --c-body-bg: #121212;
        --c-text: #e0e0e0;
        --c-text-secondary: #999;
        --c-container-bg: #1e1e1e;
        --c-shadow: 0 20px 60px rgba(0,0,0,0.7);
        --c-upload-border: #818cf8;
        --c-upload-hover-bg: #2c2c31;
        --c-upload-drag-bg: #374151;
        --c-input-border: #444;
        --c-input-focus-border: #818cf8;
        --c-result-card-bg: #2c2c31;
        --c-price-border: #818cf8;
        --c-price-value: #818cf8;
        --c-score-excellent: #34d399;
        --c-score-good: #fbbf24;
        --c-score-bad: #f87171;
        --c-spinner-color: #818cf8;
    }
}
/* --- TEMA DEĞİŞKENLERİ SONU --- */

*{margin:0;padding:0;box-sizing:border-box}
body{
    font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;
    background:var(--c-body-bg);
    color:var(--c-text);
    min-height:100vh;padding:20px;
    transition:background-color 0.3s, color 0.3s;
}
.container{
    max-width:800px;margin:0 auto;
    background:var(--c-container-bg);
    border-radius:20px;padding:40px;
    box-shadow:var(--c-shadow);
    transition:background-color 0.3s, box-shadow 0.3s;
}
h1{text-align:center;color:var(--c-primary);margin-bottom:30px;font-size:2.5em}
.upload-area{
    border:3px dashed var(--c-upload-border);
    border-radius:15px;padding:40px;text-align:center;margin-bottom:30px;
    cursor:pointer;transition:all 0.3s;
    color:var(--c-text);
}
.upload-area:hover{background:var(--c-upload-hover-bg);border-color:var(--c-accent)}
.upload-area.dragover{background:var(--c-upload-drag-bg);border-color:var(--c-primary)}
input[type="file"]{display:none}
input[type="text"]{
    width:100%;padding:15px;
    border:2px solid var(--c-input-border);
    border-radius:10px;font-size:16px;margin-bottom:20px;
    transition:border 0.3s, background-color 0.3s, color 0.3s;
    background-color:var(--c-container-bg);
    color:var(--c-text);
}
input[type="text"]:focus{outline:none;border-color:var(--c-input-focus-border)}
button{
    width:100%;padding:15px;
    background:linear-gradient(135deg,var(--c-bg-grad-start) 0%,var(--c-bg-grad-end) 100%);
    color:white;border:none;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer;
    transition:transform 0.2s;
}
button:hover{transform:scale(1.02)}
button:disabled{opacity:0.6;cursor:not-allowed}
.results{display:none;margin-top:30px}
.result-card{
    background:var(--c-result-card-bg);
    border-radius:15px;padding:20px;margin-bottom:20px;
    transition:background-color 0.3s;
}
.result-card h3{color:var(--c-primary);margin-bottom:15px}
.score-badge{display:inline-block;padding:10px 20px;border-radius:50px;font-size:24px;font-weight:bold;margin:10px 0}
.score-excellent{background:var(--c-score-excellent);color:white}
.score-good{background:var(--c-score-good);color:white}
.score-bad{background:var(--c-score-bad);color:white}
.price-box{
    background:white;
    border:2px solid var(--c-price-border);
    border-radius:10px;padding:20px;text-align:center;margin:15px 0;
    background-color:var(--c-container-bg);
}
.price-big{font-size:36px;font-weight:bold;color:var(--c-price-value);margin:10px 0}
.loading{text-align:center;padding:40px;display:none}
.spinner{
    border:4px solid var(--c-input-border);
    border-top:4px solid var(--c-spinner-color);
    border-radius:50%;width:50px;height:50px;animation:spin 1s linear infinite;margin:0 auto 20px
}
@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
.preview-image{max-width:100%;border-radius:10px;margin:20px 0}
.price-detail{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px dashed var(--c-input-border);font-size:14px}
.price-detail:last-child{border-bottom:none}
.price-label{font-weight:bold;color:var(--c-text)}
.price-value{color:var(--c-price-value)}
</style>
</head>
<body>
<div class="container">
<h1>Telefon Degerlendirme</h1>
<form id="analyzeForm">
<div class="upload-area" id="uploadArea">
<p style="font-size:48px;">📸</p>
<p style="font-size:18px;color:var(--c-text-secondary);">Telefon ekrani fotografini yukle</p>
<p style="font-size:14px;color:var(--c-text-secondary);margin-top:10px;">veya surukle birak</p>
<input type="file" id="imageInput" accept="image/*" required>
</div>
<input type="text" id="productName" placeholder="Urun adini girin (ornek: iPhone 13)" required>
<button type="submit" id="analyzeBtn">Analiz Et ve Fiyatlandir</button>
</form>
<div class="loading" id="loading">
<div class="spinner"></div>
<p>Analiz ediliyor, lutfen bekleyin...</p>
</div>
<div class="results" id="results">
<img id="previewImage" class="preview-image">
<div class="result-card">
<h3>Ekran Durumu</h3>
<div id="predictionResult"></div>
</div>
<div class="result-card">
<h3>Tahmini Fiyat</h3>
<div id="priceResult"></div>
</div>
<div class="result-card">
<h3>Piyasa Karsilastirma</h3>
<div id="marketResult"></div>
</div>
</div>
</div>
<script>
const uploadArea=document.getElementById('uploadArea');
const imageInput=document.getElementById('imageInput');
const form=document.getElementById('analyzeForm');
const loading=document.getElementById('loading');
const results=document.getElementById('results');
uploadArea.addEventListener('click',()=>imageInput.click());
uploadArea.addEventListener('dragover',(e)=>{e.preventDefault();uploadArea.classList.add('dragover');});
uploadArea.addEventListener('dragleave',()=>{uploadArea.classList.remove('dragover');});
uploadArea.addEventListener('drop',(e)=>{e.preventDefault();uploadArea.classList.remove('dragover');imageInput.files=e.dataTransfer.files;updateUploadText();});
imageInput.addEventListener('change',updateUploadText);
function updateUploadText(){if(imageInput.files.length>0){uploadArea.innerHTML='<p style="color:var(--c-primary);">✅ '+imageInput.files[0].name+'</p>';}}
form.addEventListener('submit',async(e)=>{e.preventDefault();const formData=new FormData();formData.append('image',imageInput.files[0]);formData.append('product_name',document.getElementById('productName').value);loading.style.display='block';results.style.display='none';try{const response=await fetch('/analyze',{method:'POST',body:formData});const data=await response.json();if(data.success){displayResults(data);}else{alert('Hata: '+data.error);}}catch(error){alert('Bir hata olustu: '+error);}finally{loading.style.display='none';}});
function displayResults(data){document.getElementById('previewImage').src=data.image;const score=data.prediction.cosmetic_score;let scoreClass='score-bad';if(score>=8)scoreClass='score-excellent';else if(score>=6)scoreClass='score-good';document.getElementById('predictionResult').innerHTML='<div class="score-badge '+scoreClass+'">'+score+'/10</div><p><strong>Tespit:</strong> '+data.prediction.predicted_class+'</p><p><strong>Guven:</strong> %'+data.prediction.confidence+'</p>';if(data.price){const price=data.price;const letgoAvgHtml=price.letgo_ortalama?'<div class="price-detail"><span class="price-label">Ortalama Ikinci El Fiyati (Letgo)</span><span class="price-value">'+price.letgo_ortalama.toLocaleString('tr-TR')+' TL</span></div>':'';document.getElementById('priceResult').innerHTML='<div class="price-box"><p style="color:var(--c-text-secondary);">Tahmini Satis Degeri</p><div class="price-big">'+price.tahmini_fiyat.toLocaleString('tr-TR')+' TL</div><p style="color:var(--c-text-secondary);">'+price.min_fiyat.toLocaleString('tr-TR')+' - '+price.max_fiyat.toLocaleString('tr-TR')+' TL (Onerilen Aralik)</p></div><div class="result-card" style="padding:15px;background:var(--c-container-bg);"><div class="price-detail"><span class="price-label">Kozmetik Puanina Gore Deger Kaybi</span><span class="price-value"><strong>%'+price.deger_kaybi+'</strong></span></div>'+letgoAvgHtml+'<div class="price-detail"><span class="price-label">Sifir Piyasa Fiyati (Akakce Min.)</span><span class="price-value">'+price.sifir_fiyat.toLocaleString('tr-TR')+' TL</span></div></div>';}let marketHTML='<h4>Akakce (Sifir Piyasa)</h4>';if(data.akakce.length>0){data.akakce.forEach(item=>{marketHTML+='<div style="font-size:14px;padding:5px 0;">• '+item.urun.substring(0,50)+'... ('+item.fiyat+')</div>';});}else{marketHTML+='<p style="color:var(--c-text-secondary);">Akakcede sonuc bulunamadi.</p>';}marketHTML+='<h4 style="margin-top:20px;">Letgo (Ikinci El Fiyatlari)</h4>';if(data.letgo.length>0){data.letgo.forEach(item=>{marketHTML+='<div style="font-size:14px;padding:5px 0;">• '+item.title.substring(0,50)+'... ('+item.price+')</div>';});}else{marketHTML+='<p style="color:var(--c-text-secondary);">Letgoda sonuc bulunamadi.</p>';}document.getElementById('marketResult').innerHTML=marketHTML;results.style.display='block';}
</script>
</body>
</html>'''
    return render_template_string(html)

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        image_file = request.files['image']
        urun_adi = request.form['product_name']
        image_bytes = image_file.read()
        prediction = predict_image(image_bytes)
        akakce, letgo, min_price = fetch_prices(urun_adi)
        price_info = calculate_price(prediction['cosmetic_score'], akakce, letgo)
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        return jsonify({
            "success": True,
            "image": f"data:image/jpeg;base64,{image_base64}",
            "prediction": prediction,
            "price": price_info,
            "akakce": akakce[:3],
            "letgo": letgo[:3]
        })
    except Exception as e:
        # Hata mesajı olarak sadece string ifade döndürülüyor
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Modelin yüklenmesi sırasında hata oluşmaması için
    # app.run'dan önce bir deneme bloğu eklenebilir.
    print("Makine Öğrenimi Modeli Yükleniyor...")
    # Model yüklemesi try-except bloğu içinde yapıldığı için bu satırlar
    # modelin yüklü olduğunu varsayacaktır.

    # Not: Bu kodun çalışması için sistemde Chrome ve ChromeDriver'ın doğru ayarlanmış olması,
    # ayrıca defect_classifier_model.pth dosyasının belirtilen yolda olması gerekir.

    app.run(debug=True, host='0.0.0.0', port=5001)
