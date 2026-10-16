# Dosya ve klasör düzeni

Güncel depo adı `cihaz-analiz`; eski `_RETURN_` GitHub geçmişi ve etiketleri korunarak yeniden adlandırılmıştır. Ara düzen `apps/gemini` ve `apps/test-merkezi`, doğrudan kökteki işlev adlarıyla değiştirilmiştir.

`RETURN/TEST_MERKEZI` → `02-islev-testleri`

`RETURN/ReTurn_With_Gemini` → `01-gorsel-degerlendirme`

| Uygulama | Eski dosya | Yeni dosya |
| --- | --- | --- |
| 02-islev-testleri | `0_Main.py` | `main.py` |
| 02-islev-testleri | `10_speed_tester.py` | `speed_tester.py` |
| 02-islev-testleri | `11_typing_tester.py` | `typing_tester.py` |
| 02-islev-testleri | `12_webcam_tester.py` | `webcam_tester.py` |
| 02-islev-testleri | `1_Fiyat_Ogrenme.py` | `price_estimator.py` |
| 02-islev-testleri | `2_phone_info_app.py` | `phone_info.py` |
| 02-islev-testleri | `3_keyboard_tester.py` | `keyboard_tester.py` |
| 02-islev-testleri | `4_gamepadtester.py` | `gamepad_tester.py` |
| 02-islev-testleri | `5_pctester.py` | `pc_tester.py` |
| 02-islev-testleri | `6_headphone_tester.py` | `headphone_tester.py` |
| 02-islev-testleri | `7_dead_pixel_tester.py` | `dead_pixel_tester.py` |
| 02-islev-testleri | `8_mouse_tester.py` | `mouse_tester.py` |
| 02-islev-testleri | `9_touch_tester.py` | `touch_tester.py` |
| 01-gorsel-degerlendirme | `0_Main.py` | `main.py` |
| 01-gorsel-degerlendirme | `1_phone_info_app_Proje.py` | `phone_info.py` |
| 01-gorsel-degerlendirme | `2_keyboard_tester_Proje.py` | `keyboard_tester.py` |
| 01-gorsel-degerlendirme | `3_gamepadtester_Proje.py` | `gamepad_tester.py` |
| 01-gorsel-degerlendirme | `4_headphone_tester_Proje.py` | `headphone_tester.py` |
| 01-gorsel-degerlendirme | `5_mouse_tester_Proje.py` | `mouse_tester.py` |

Model, DLL, örnek görseller ve üçüncü taraf araçlar korundu. Yerel sertifika ve anahtar dosyaları Git takibinden çıkarıldı.
