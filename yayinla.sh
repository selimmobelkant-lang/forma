#!/bin/bash
# Forma'yı GitHub Pages'te yayınlar.
# Kullanım: ./yayinla.sh "ne değişti"
# Sırasıyla: testleri çalıştırır, sw.js'teki önbellek sürümünü bir artırır,
# değişiklikleri commit'ler, GitHub'a gönderir ve yayının bitmesini bekler.
set -euo pipefail
cd "$(dirname "$0")"
DEPO="selimmobelkant-lang/forma"
ADRES="https://selimmobelkant-lang.github.io/forma/"
MESAJ="${1:-}"

git fetch -q origin main
if [ -z "$(git status --porcelain)" ] && [ -z "$(git rev-list origin/main..HEAD)" ]; then
  echo "Yayınlanacak yeni değişiklik yok. Adres: $ADRES"; exit 0
fi

echo "1/4 Testler çalışıyor..."
if ! python3 tests/hepsi.py > /tmp/forma-test.log 2>&1; then
  tail -20 /tmp/forma-test.log; echo "Testler geçmedi, yayın yapılmadı. Ayrıntı: /tmp/forma-test.log"; exit 1
fi
echo "    hepsi geçti"

ESKI=$(grep -oE "SURUM = 'v[0-9]+'" sw.js | grep -oE '[0-9]+')
YENI=$((ESKI + 1))
sed -i '' "s/SURUM = 'v$ESKI'/SURUM = 'v$YENI'/" sw.js
echo "2/4 Önbellek sürümü: v$ESKI -> v$YENI"

git add -A
git status --short
git commit -q -m "${MESAJ:+$MESAJ (}yayın v$YENI${MESAJ:+)}"
echo "3/4 GitHub'a gönderiliyor..."
git push -q origin HEAD:main
SHA=$(git rev-parse HEAD)

echo "4/4 Yayın bekleniyor..."
for _ in $(seq 1 60); do
  read -r DURUM COMMIT <<< "$(gh api "repos/$DEPO/pages/builds/latest" --jq '.status + " " + .commit' 2>/dev/null || echo "bekliyor -")"
  if [ "$COMMIT" = "$SHA" ] && [ "$DURUM" = "built" ]; then echo "Yayında (v$YENI): $ADRES"; exit 0; fi
  if [ "$COMMIT" = "$SHA" ] && [ "$DURUM" = "errored" ]; then echo "Yayın hata verdi. https://github.com/$DEPO/actions adresine bak."; exit 1; fi
  sleep 5
done
echo "Gönderildi ama yayın 5 dakikada bitmedi. Birazdan $ADRES adresini kontrol et."
