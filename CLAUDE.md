# Forma — proje talimatları

Forma, kişisel antrenman ve beslenme koçu uygulaması. Arayüz Türkçe. Hedefler: yağ yakmak, formu korumak, kas kazanmak. Aynı cihazda birden fazla profil tutulabiliyor. Sahibi Sese (Arif Selim Cankurt).

## Önce oku
- Teknik yapı (her oturumda yüklenir): @/Users/satisdestek/Documents/Obsidian\ Vault/Forma/Teknik\ Yapı.md
- Koçluk kurallarına (kalori, makro, karar motoru, antrenman) dokunmadan önce şunu oku: `/Users/satisdestek/Documents/Obsidian Vault/Forma/Kural Kitabı.md`
- Sıradaki iş ve hazır görevler: `/Users/satisdestek/Documents/Obsidian Vault/Forma/Yol Haritası.md`

## Dosyalar
- `index.html` — uygulamanın tamamı (HTML + CSS + JS tek dosyada, yaklaşık 1,9 MB).
- `tests/` — Playwright testleri. `python3 tests/hepsi.py` hepsini çalıştırır.
- `ex/` — kütüphanedeki yeni hareketlerin görselleri (free-exercise-db, kamu malı). `sw.js` içindeki `EX_RESIMLER` listesiyle önbelleğe alınır; görsel ekleyince listeyi de güncelle.
- `vendor/chart.umd.min.js` — Chart.js 4.5.1 (MIT), grafikler için yerel kopya; `sw.js` önbelleğe alır. CDN'den yüklenmez. Güncellerken npm'den indir, bütünlüğünü (sha512) doğrula.
- `manifest.webmanifest`, `sw.js`, `icons/` — PWA dosyaları. `yayinla.sh` — GitHub Pages'e yayın.

## index.html ile çalışırken
- Dosyanın tamamını okuma. Büyüklüğün çoğu `EX_FRAMES` satırındaki gömülü egzersiz görselleri (base64). O satırı asla yeniden yazma, kısaltma ya da biçimlendirme.
- Bölümleri `/* ---------- bölüm adı ---------- */` yorumlarıyla bul. grep ve satır aralığıyla oku.
- Derleme adımı yok, framework yok. Çalışma anında dış CDN'e bağımlılık ekleme; uygulama internetsiz çalışmalı. Fotoğraftan kalori özelliği tek istisna, o zaten kullanıcının kendi API anahtarıyla çalışıyor.
- İkonlar `ICONS` objesinde, Tabler Icons (MIT) ve Lucide (ISC) kaynaklı, 24px çizgi ikonlar. Yeni ikonu da bu iki setten al ve aynı biçimde ekle.

## Veri güvenliği (en önemli kural)
- Kullanıcı verisi tarayıcıda duruyor: localStorage'da `forma_profiles` ve `forma_state_<id>`, eski sürümden gelen `kocum90_v1`, AI ayarı için `forma_ai`. İlerleme fotoğrafları IndexedDB'de (`kocum90_photos`).
- Bu anahtarları ve veri biçimini bozacak değişiklik yapma. Biçim değişecekse `migrate()` içine geriye dönük uyumlu bir geçiş yaz ve eski veriyle test et.
- Dışa aktarma etiketi `forma`. İçe aktarma eski `kocum90` etiketini de kabul etmeye devam etmeli.

## Dil ve ton (arayüz metinleri)
- Samimi ama profesyonel. Kullanıcıya arkadaşı gibi davranma, argo ve laubali ifade kullanma ("Hadi bakalım", "panik yok" gibi). Kullanıcıya adıyla yalnızca üst köşedeki "Merhaba, <ad>" selamlamasında seslenilir; metinlerin içinde ad kullanma.
- Kaynak isimleri (video sahibi, rapor adları) arayüzde görünmez. Kaynaklar yalnızca Obsidian notlarında durur.

## İki dil (Türkçe / İngilizce)
- Arayüz Türkçe yazılır; İngilizce, ekrana basılan metni `I18N_EN` sözlüğüyle çeviren katmanla gelir (bölüm: "dil (Türkçe / İngilizce)", sözlük: "çeviri sözlüğü (İngilizce)").
- Yeni bir Türkçe metin eklediğinde İngilizcesini de `I18N_EN`'e ekle. Sayılar anahtarda `#`, tarihler `@` olur; sıra değişiyorsa `#1`, `#2` kullan. Kodda doğrudan çeviri gerekiyorsa (onay pencereleri, bildirimler): `t('Metin {ad}', { ad })`.
- Kullanıcı içeriğini (ad, not, özel besin) `data-notr` ile çeviri dışı bırak.
- `python3 tests/test_ingilizce.py --dump` eksik çevirileri `tests/shots/i18n_eksik.json`'a (bağlamıyla) yazar. Test "hepsi geçti" için eksik 0 olmalı.
- İngilizce metinler de samimi ama profesyonel; argo yok.

## Test
- Her değişiklikten sonra `python3 tests/hepsi.py` çalıştır. Sonuç "hepsi geçti" olmalı ve sayfa hatası çıkmamalı.
- Tarih gerektiren senaryolar için adrese `?bugun=YYYY-MM-DD` ekle (ör. `index.html?bugun=2026-10-19`).
- Görsel değişikliklerde ekran görüntüsü al ve kendin bak (`tests/shots/`). Açık ve koyu modu, masaüstü ve telefon genişliğini kontrol et.
- Playwright kurulu değilse: `pip3 install playwright` ve ardından `python3 -m playwright install chromium`.

## Yayın
- Uygulama GitHub Pages'te: https://selimmobelkant-lang.github.io/forma/ (depo `selimmobelkant-lang/forma`, `main` dalı).
- Sese "yayınla" dediğinde `./yayinla.sh "kısa açıklama"` çalıştır. Betik testleri çalıştırır, `sw.js` içindeki `SURUM`'ü artırır, commit'leyip gönderir ve yayının bitmesini bekler. `SURUM`'ü elle değiştirme.

## Çalışma biçimi
- Sese ile Türkçe, sade bir dille konuş. Otomatik kalın yazı kullanma.
- Büyük işlere başlamadan önce kısa bir plan göster.
- Anlamlı her değişiklikten sonra Obsidian notlarını güncelle: `Teknik Yapı.md` (yapı değiştiyse), `Yol Haritası.md` (biten maddeyi işaretle), `Proje Geçmişi.md` (tarihli bir satır ekle).
- Git kullan: her tamamlanan iş için açıklayıcı, Türkçe bir commit at.
