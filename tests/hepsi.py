"""Tüm testleri sırayla çalıştırır. Kullanım: python3 tests/hepsi.py"""
import subprocess, sys
from pathlib import Path
T = Path(__file__).resolve().parent
ok = True
for f in ['test_yag_yakma.py', 'test_hedefler_profiller.py', 'test_gorsel_ai.py', 'test_ikonlar_tema.py', 'test_pwa.py', 'test_kutuphane.py', 'test_yas_cinsiyet.py', 'test_ingilizce.py']:
    print(f'\n=== {f}')
    r = subprocess.run([sys.executable, str(T / f)], capture_output=True, text=True, timeout=600)
    out = (r.stdout + r.stderr).strip()
    print(out[-2500:])
    if r.returncode != 0 or 'ERRORS []' not in out:
        ok = False; print('>>> SORUN VAR')
print('\nSONUÇ:', 'hepsi geçti' if ok else 'en az bir test başarısız')
sys.exit(0 if ok else 1)
