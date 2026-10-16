# Bakım ve yayın dosyaları

- `docs/`: Dosya taşıma haritası, sürüm rehberi ve önceki sürümün ekran görüntüleri.
- `scripts/`: Python kaynak kontrolü ve otomatik sürüm seçimi.

Komutu depo kökünden çalıştırın:

```sh
python maintenance/scripts/check_source.py
```

GitHub Actions giriş dosyası `.github/workflows/release.yml` altında kalır; kontrolleri ve sürüm aracını bu klasörden çağırır. Sürüm aracı depo kökündeki `VERSION` dosyasını günceller.

[Sürüm rehberi](docs/SURUMLEME.md) · [Ana README](../README.md)
