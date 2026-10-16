# 02 — İşlev testleri

CihazAnaliz’in cihaz ve çevre birimlerinin çalışmasını kontrol etmeye yönelik araçları. Görsel inceleme sonrasında cihaz türüne uygun kontrollerin yapılacağı bölüm olarak konumlandırılır.

## Araçlar

Telefon bilgileri, klavye, gamepad, PC sensörleri, kulaklık/ses, ölü piksel, fare, dokunmatik, internet hızı, yazma hızı ve kamera testleri bulunur. Önceki kapsamdan gelen `price_estimator.py` fiyat/kozmetik aracı da korunmuştur; dosyalar yalnızca bölüm adına uyması için silinmedi.

## Kurulum

Windows üzerinde Python 3.11/3.12 ve sanal ortam önerilir. Depo kökünden:

```powershell
python -m pip install -r 02-islev-testleri/requirements.txt
python 02-islev-testleri/main.py
```

Ana panel `http://localhost:5000`; alt servisler 5001–5012 portlarındadır. Tek test bağımsız açılabilir:

```powershell
python 02-islev-testleri/keyboard_tester.py
```

PC modülü Windows WMI/.NET/DLL, bazı kontroller ise fiziksel cihaz ve tarayıcı izni gerektirir. Kamera sertifikası için [ana README](../README.md#kamera-ve-yerel-https) adımlarını izleyin.

**01-gorsel-degerlendirme ile aynı anda çalıştırmayın:** portları ortaktır. Başlatıcı yolları kendi uygulama klasöründen türetilir; klasörün köke taşınması bu hedefleri değiştirmez.

## Görseller

Önceki sürümden gerçek yerel ekran görüntüleri; bazı başlıklarda eski Test Merkezi adı görülebilir.

![İşlev testleri paneli](../maintenance/docs/images/01-dashboard.jpg)

![Klavye kontrolü](../maintenance/docs/images/02-keyboard.jpg)

![Fare kontrolü](../maintenance/docs/images/03-mouse.jpg)

![Yazma kontrolü](../maintenance/docs/images/04-typing.jpg)

Model dosyası, DLL’ler ve üçüncü taraf araçlar korunur. Model yüklenemediğinde eski fiyat/kozmetik kodundaki yer tutucu davranış devam eder. Otomat/kiosk üzerinden gözetimsiz üretim kabul testi bu prototip için doğrulanmış değildir.

[Ana README](../README.md) · [Görsel değerlendirme](../01-gorsel-degerlendirme/README.md)
