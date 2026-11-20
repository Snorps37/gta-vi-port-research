# Project NATIVE

Codex, Claude Code ve Concord için yerel bir deneme projesi. Örnek Python kodu, süreyi kare sayısından milisaniyeye çeviriyor. Ek Python paketi gerekmez.

## Çalıştır

```powershell
cd D:\gta6\ProjectNative
python harness.py
python harness.py --review both
python harness.py --show RUN_ID
```

İlk komut dört yerel testi çalıştırır. İkinci komut, testler geçerse Codex ve Claude Code'a örneğin iki kaynak dosyasını ayrı ayrı gönderir. Tek model için `--review codex` veya `--review claude` kullan. Her denetim bir çağrıyla sınırlı ve çağrı başına zaman aşımı 90 saniye. CLI oturumu açık olmalı. Harness temel API anahtarı ve sağlayıcı ortam değişkenlerini alt süreçten çıkarır ve ücretli API'ye otomatik geçiş yapmaz. Abonelik kotası ve hesapta etkin ek kullanım, sağlayıcı tarafında yönetilir.

Terminaldeki çalışma kimliğiyle test çıktısını, model yanıtlarını ve süreç durumunu `--show` ile açabilirsin. Yerel SQLite dosyası `.native/runs.sqlite3`. Kesilen bir çalışma `running` olarak kalabilir. Yeni bir deneme ayrı kimlik alır. Model komutunun başarıyla çıkması yanıtın alındığını gösterir. Yanıttaki bulgular ayrıca değerlendirilir.

## Codex, Claude Code ve Concord

1. **Codex** uygulama görevini Concord'da `start_work` ile alır, dokunacağı dosyaları bildirir ve değişikliği üzerinde çalıştığı dalda test eder.
2. **Concord** görevin sahibini, dosya çakışmalarını ve devri kaydeder. Codex test kimliğini ve commit SHA'sını görev kaydına ekler. Claude'a devir için `transfer_work` kullanılır.
3. **Claude Code** interaktif oturumdan `inspect_work` ile görevi ve commit'i okur. İnceleme bulgularını Concord'a döner. Ayrı bir düzeltme görevi verilirse kendi Git worktree'sinde, dosyaları önceden kaydederek çalışır.
4. **Python harness** yerel test ve otomatik inceleme çağrılarını sırayla yürütür. **SQLite** her komutun durumunu ve çıktısını tutar. CLI deneme çağrıları araçsız inceleme içindir. Concord'daki iş devri interaktif Codex ve Claude oturumlarında yapılır.

Önce `python harness.py` ile yerel döngüyü doğrula. Rutin Claude incelemesi Sonnet kullanır. Opus'u çözümü belirsiz bir mimari karar veya iki inceleme arasında anlaşmazlık olduğunda interaktif oturumda çağır.
