"""PWA: manifest, ikonlar, service worker, internetsiz açılış, eski önbelleğin silinmesi, iPhone güvenli alan boşlukları."""
import asyncio, socket, subprocess, sys
from playwright.async_api import async_playwright
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
(ROOT / 'tests' / 'shots').mkdir(exist_ok=True)
SP = str(ROOT / 'tests') + '/'

def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close(); return port
PORT = free_port()
BASE = f'http://127.0.0.1:{PORT}/'

errs = []
def check(ok, msg):
    print(('ok ' if ok else 'HATA ') + msg)
    if not ok: errs.append(msg)

async def onboard(pg, url):
    await pg.goto(url)
    await pg.fill('#ob_name','Test'); await pg.click('[data-act=obNext]')
    await pg.fill('#ob_age','30'); await pg.fill('#ob_height','180'); await pg.fill('#ob_weight','85'); await pg.fill('#ob_waist','92'); await pg.fill('#ob_neck','39'); await pg.click('[data-act=obNext]')
    await pg.click('[data-act=obNext]'); await pg.fill('#ob_goal','8'); await pg.click('[data-act=obNext]')
    await pg.check('#ob_commit'); await pg.click('[data-act=obNext]'); await pg.wait_for_timeout(1300)

async def sw_ready(pg):
    await pg.evaluate("navigator.serviceWorker.ready")
    for _ in range(50):
        if await pg.evaluate("!!navigator.serviceWorker.controller"): return True
        await pg.wait_for_timeout(100)
    return False

async def main():
    srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT), '--bind', '127.0.0.1'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            try: socket.create_connection(('127.0.0.1', PORT), timeout=.2).close(); break
            except OSError: await asyncio.sleep(.1)
        async with async_playwright() as p:
            b = await p.chromium.launch()
            ctx = await b.new_context(locale='tr-TR', viewport={'width':1440,'height':950})
            pg = await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))

            # Eski sürümden kalmış bir önbellek ve başka bir uygulamanın önbelleği (SW kurulmadan önce)
            await pg.goto(BASE + 'manifest.webmanifest')
            await pg.evaluate("Promise.all([caches.open('forma-v0'), caches.open('baska-onbellek')])")

            await pg.goto(BASE + 'index.html?bugun=2026-10-19')
            man = await pg.evaluate("fetch(document.querySelector('link[rel=manifest]').href).then(r=>r.json())")
            check(man['name'] == 'Forma' and man['display'] == 'standalone', 'manifest: ad ve standalone')
            sizes = await pg.evaluate("""Promise.all([...document.querySelectorAll('link[rel=apple-touch-icon]')].map(l=>l.href)
              .concat(%s.map(i=>new URL(i.src, location.href).href)).map(u=>new Promise(r=>{const im=new Image(); im.onload=()=>r(u.split('/').pop()+':'+im.naturalWidth); im.onerror=()=>r(u+':YOK'); im.src=u})))""" % str(man['icons']).replace("'", '"'))
            print('ikonlar', sizes)
            check(sizes == ['apple-touch-icon.png:180', 'icon-192.png:192', 'icon-512.png:512', 'icon-maskable-512.png:512', 'apple-touch-icon.png:180'], 'ikon boyutları')
            check(any(i.get('purpose') == 'maskable' for i in man['icons']), 'maskable ikon var')
            metas = await pg.evaluate("['apple-mobile-web-app-capable','apple-mobile-web-app-status-bar-style','apple-mobile-web-app-title'].map(n=>document.querySelector('meta[name='+n+']')?.content)")
            check(metas == ['yes', 'black-translucent', 'Forma'], 'iPhone meta etiketleri ' + str(metas))

            check(await sw_ready(pg), 'service worker sayfayı kontrol ediyor')
            keys = await pg.evaluate("caches.keys()")
            print('önbellekler', keys)
            check('forma-v0' not in keys and 'baska-onbellek' in keys and any(k.startswith('forma-v') for k in keys), 'eski forma önbelleği silindi, başkasınınki kaldı')
            n = await pg.evaluate("caches.keys().then(ks=>caches.open(ks.find(k=>k.startsWith('forma-v')))).then(c=>c.keys()).then(r=>r.length)")
            check(n >= 6, f'önbellekte {n} dosya')

            await onboard(pg, BASE + 'index.html?bugun=2026-10-19')
            # hareket görselleri arka planda önbelleğe alınıyor
            for _ in range(100):
                n_ex = await pg.evaluate("caches.keys().then(ks=>caches.open(ks.find(k=>k.startsWith('forma-v')))).then(c=>c.keys()).then(r=>r.filter(x=>x.url.includes('/ex/')).length)")
                if n_ex >= 200: break
                await pg.wait_for_timeout(200)
            check(n_ex >= 200, f'hareket görselleri önbellekte ({n_ex})')
            veri = await pg.evaluate("JSON.stringify(Object.keys(localStorage).sort().map(k=>[k, localStorage.getItem(k)]))")

            # İnternetsiz açılış
            await ctx.set_offline(True)
            for adres in ['index.html?bugun=2026-10-20', '']:
                await pg.goto(BASE + adres); await pg.wait_for_timeout(500)
                check(await pg.evaluate("!!document.querySelector('.sidebar .sb-item') && !document.querySelector('#ob_name')"), f'internetsiz açıldı: /{adres}')
            check(await pg.evaluate("JSON.stringify(Object.keys(localStorage).sort().map(k=>[k, localStorage.getItem(k)]))") == veri, 'kullanıcı verisi aynı kaldı')
            img = await pg.evaluate("new Promise(r=>{const im=new Image(); im.onload=()=>r(im.naturalWidth); im.onerror=()=>r(0); im.src='ex/Goblet_Squat/1.jpg'})")
            check(img > 0, f'hareket görseli internetsiz açıldı ({img}px)')
            await pg.screenshot(path=SP + 'shots/p_offline.png')
            await ctx.set_offline(False)

            # Telefon: iPhone çentiği ve alt çizgi (güvenli alan) taklidi, açık ve koyu mod
            for mod in ['light', 'dark']:
                m = await b.new_context(locale='tr-TR', viewport={'width':390,'height':844}, device_scale_factor=2, is_mobile=True, has_touch=True)
                mp = await m.new_page(); mp.on('pageerror', lambda e: errs.append(str(e)))
                cdp = await m.new_cdp_session(mp)
                try: await cdp.send('Emulation.setSafeAreaInsetsOverride', {'insets': {'top':47, 'bottom':34, 'left':0, 'right':0}}); sa = True
                except Exception as e: sa = False; print('güvenli alan taklidi yok:', e)
                await onboard(mp, BASE + 'index.html?bugun=2026-10-19')
                await mp.evaluate(f"S.settings.mode='{mod}'; save(); applyTheme(); render()"); await mp.wait_for_timeout(400)
                if sa:
                    box = await mp.evaluate("""(()=>{const h=document.querySelector('.mhead .in').getBoundingClientRect(), t=document.querySelector('.tabs').getBoundingClientRect();
                      return [Math.round(h.top), Math.round(innerHeight - t.bottom)]})()""")
                    check(box == [47, 34], f'{mod}: başlık çentiğin altında, sekmeler alt çizginin üstünde {box}')
                await mp.screenshot(path=SP + f'shots/p_m_{mod}.png')
                await mp.click('.tabs [data-tab=beslenme]'); await mp.wait_for_timeout(300)
                await mp.evaluate("window.scrollTo(0, document.body.scrollHeight)"); await mp.wait_for_timeout(200)
                await mp.screenshot(path=SP + f'shots/p_m_{mod}_alt.png')
                await m.close()
            await b.close()
    finally:
        srv.terminate()
    print('ERRORS', errs)

asyncio.run(main())
