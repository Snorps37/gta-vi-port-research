# Project NATIVE

Codex, Claude Code ve Concord için yerel bir deneme projesi. Örnek Python kodu, süreyi kare sayısından milisaniyeye çeviriyor. Ek Python paketi gerekmez.

## Çalıştır

```powershell
cd D:\gta6\ProjectNative
python harness.py
python harness.py --review claude
python harness.py --show RUN_ID
python harness.py --handoff RUN_ID
```

İlk komut sadece yerel testleri çalıştırır. Model çağrıları testler geçince başlar. `--review codex` bağımsız Codex incelemesi, `--review claude` Sonnet incelemesi ister. `--review both` bu ikisini sırayla çağırır. Çözülmemiş tek bir teknik soru için ayrı bir `--escalate "Soru"` çağrısı Opus'u açar. Her sağlayıcı için çağrı başına 90 saniye sınır var. Claude oturumu süresi dolduysa `claude auth login` ile yenile. Harness temel API anahtarı ve sağlayıcı ortam değişkenlerini alt süreçten çıkarır ve ücretli API'ye otomatik geçiş yapmaz. Abonelik kotası ve hesapta etkin ek kullanım, sağlayıcı tarafında yönetilir.

Terminaldeki çalışma kimliğiyle test çıktısını, model yanıtlarını ve süreç durumunu `--show` ile açabilirsin. Yerel SQLite dosyası `.native/runs.sqlite3`. Kesilen bir çalışma `running` olarak kalabilir. Yeni bir deneme ayrı kimlik alır. Model komutunun başarıyla çıkması yanıtın alındığını gösterir. Yanıttaki bulgular ayrıca değerlendirilir.

`--handoff` temiz çalışma ağacında çalıştırılan test için commit SHA'sını ve adım durumlarını çıkarır. Bu özeti Concord kaydına ekle. SQLite yerel kaldığı için başka bir worktree'deki incelemeci aynı commit'te testi yeniden çalıştırır. Önceki çalışmalarda commit kaydı yoksa temiz commit'te tekrar test et.

## Codex, Claude Code ve Concord

| Rol | Ne zaman kullanılır? | Teslim ettiği |
| --- | --- | --- |
| Codex | Küçük değişiklikler, testler ve entegrasyon | Commit, test sonucu, incelemeciye açık soru |
| Claude Code / Sonnet | Codex değişikliğinin ilk bağımsız incelemesi | Dosya ve girdiyle yeniden üretilebilir bulgu |
| Codex CLI | Bir Sonnet değişikliğinin bağımsız incelemesi veya Sonnet oturumu geçici olarak kapalıysa ek görüş | Kısa inceleme ve eksik test önerisi |
| Claude Code / Opus | İki inceleme çeliştiğinde veya zor bir teknik karar kaldığında | Tek soruya gerekçeli karar ve doğrulama önerisi |
| Concord | Dosya sahipliği, çakışma kontrolü, devir ve görev durumu | Görev kaydı, commit ve test kanıtı |

1. Uygulayan agent `start_work` ile dosyaları üstlenir. Aynı anda ikinci bir agent yazacaksa kendi worktree'sini ve dosya kapsamını kullanır.
2. Uygulayan agent commit'i oluşturur, temiz çalışma ağacında testi çalıştırır ve `--handoff RUN_ID` özetini Concord'a ekler. İncelemeci bağlıysa `transfer_work` ile devreder.
3. İncelemeci `inspect_work` ile commit'i ve kabul ölçütünü okur, bulguları Concord'a kaydeder. CLI incelemesi örnek kaynakla sınırlıdır. Codex salt okunur çalışır. Claude araçları kapalıdır.
4. Test başarısızsa önce yerelde düzelt. Bir model çağrısı erişim veya kota nedeniyle başarısızsa kayda geçir ve yerel testle devam et. Ayrı bir sağlayıcıya veya Opus'a geçiş açık bir çağrıyla yapılır.

## Yerel Claude eklentisi ve Concord

Proje klasöründe, OpenAI'ın resmî Codex eklentisini yerel kapsamda kur:

```powershell
claude plugin marketplace add openai/codex-plugin-cc --scope local
claude plugin install codex@openai-codex --scope local
```

Claude Code'u proje kökünden aç. `/codex:setup` yerel Codex oturumunu kontrol eder. Claude'un değişikliğini incelemek için testten sonra feature dalında `/codex:review --base main` çalıştır. Otomatik inceleme kapısını kapalı tut.

Concord görevlerinin çalışma alanı Git deposunun köküdür. Üst klasörden veya ayrı bir worktree'den açılan oturumda `concord -C <proje-kökü> status` ile bu alanın kimliğini al ve Concord çağrılarında `workspace_id` olarak kullan. Projeyi aynı klasörden açan Claude Code ve Codex aynı NATIVE görevini görmeli.

## İndirme tamamlanınca çalışma planı

| Zaman | Sorumlu | İş ve kabul ölçütü |
| --- | --- | --- |
| İndirme sürerken | Codex | Temiz commit üzerinde `python harness.py` çalıştır. Beş test geçince çalışma kimliğini ve commit'i Concord'a kaydet. |
| Tamamlandıktan sonraki ilk 15 dakika | Codex | İstemcinin seçili dosyalar için tamamlandı durumunu ve atlanan dosya olup olmadığını kontrol et. Yerelde dosya yollarını ve boyutlarını listele. Manifestteki çalıştırılabilir dosya yolunun mevcut olup olmadığını kaydet. |
| Sonraki 15–60 dakika | Codex | Eksik veya tutarsız dosya varsa hangisi olduğunu raporla. Torrent parça doğrulaması gerekiyorsa süreyi disk hızına göre ayrıca ölç. Parça doğrulaması indirilen veriyi torrent tanımıyla karşılaştırır. Yayıncı kökenini doğrulamak için bağımsız bir imza veya güvenilir referans gerekir. |
| İlk geliştirme turu | Codex ve Sonnet | Kendi küçük test projemizde geçerli ve eksik dosyaya işaret eden iki örnek manifest oluştur. Denetleyicinin birini kabul ettiğini, diğerinde eksik yolu bildirdiğini otomatik testle göster. Sonnet oturumu açıksa commit'i bağımsız incelesin. |
| Karar ve devir | Codex | Çalıştırılabilir dosya eksikse paket için çalışma zamanı denemesini bloklu kaydet. Mevcutsa hedef platformu, kökeni ve yetkili test ortamını değerlendir. Her iki durumda da envanter ve test sonuçlarını ayrı kaydet. |

Ham paket ve yerel envanter indirme makinesinde tutulur. Ortak Git deposuna kendi araçlarımız, sentetik örnekler ve tekrarlanabilir testler girer.
