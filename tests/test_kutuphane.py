"""Hareket kütüphanesi: katalog, filtre, sürümler, alternatifler, programda değiştirme ve geri dönüş, eski veride swaps."""
import asyncio, json
from playwright.async_api import async_playwright
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / 'index.html').as_uri()
(ROOT / 'tests' / 'shots').mkdir(exist_ok=True)
SP = str(ROOT / 'tests') + '/'
errs = []
def check(ok, msg):
    print(('ok ' if ok else 'HATA ') + msg)
    if not ok: errs.append(msg)

async def onboard(pg):
    await pg.goto(URL + '?bugun=2026-10-19')
    await pg.fill('#ob_name','Test'); await pg.click('[data-act=obNext]')
    await pg.fill('#ob_age','30'); await pg.fill('#ob_height','180'); await pg.fill('#ob_weight','85'); await pg.fill('#ob_waist','92'); await pg.fill('#ob_neck','39'); await pg.click('[data-act=obNext]')
    await pg.click('[data-act=obNext]'); await pg.fill('#ob_goal','8'); await pg.click('[data-act=obNext]')
    await pg.check('#ob_commit'); await pg.click('[data-act=obNext]'); await pg.wait_for_timeout(1300)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c = await b.new_context(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True, device_scale_factor=2)
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await onboard(pg)
        st = await pg.evaluate("""(() => { const bad = []; LIB.forEach(e => { if (!EQ[e.eq]) bad.push(e.id + ' eq'); if (!PATTERNS[e.pat]) bad.push(e.id + ' pat'); if (!LEVELS[e.lvl]) bad.push(e.id + ' lvl');
          Object.keys(e.m || {}).forEach(k => { if (!MUSCLES[k]) bad.push(e.id + ' kas ' + k); }); if (!(e.tips || []).length) bad.push(e.id + ' ipucu'); });
          const ids = LIB.map(e => e.id); const dup = ids.filter((x, i) => ids.indexOf(x) !== i);
          const eqs = [...new Set(libList().map(e => e.eq))];
          return { n:libList().length, bad, dup, eqs, pats:Object.keys(PATTERNS).filter(k => !libList().some(e => e.pat === k)) }; })()""")
        print('katalog', st['n'], st['eqs'])
        check(st['n'] >= 130, f"kütüphanede {st['n']} hareket")
        check(not st['bad'] and not st['dup'], 'katalog alanları geçerli ' + str(st['bad'][:5] + st['dup'][:5]))
        check(not st['pats'], 'her kalıpta en az bir hareket var ' + str(st['pats']))
        check(all(k in st['eqs'] for k in ['bw','db','bb','kb','mc','cb','band']), 'tüm ekipman türleri var')
        # her kalıpta en az bir başlangıç seviyesi hareket
        nolvl1 = await pg.evaluate("Object.keys(PATTERNS).filter(k => !libList().some(e => e.pat === k && e.lvl === 1))")
        check(not nolvl1, 'her kalıpta başlangıç seviyesi hareket var ' + str(nolvl1))

        await pg.click('.tabs [data-tab=antrenman]'); await pg.wait_for_timeout(300)
        await pg.select_option('#lib_eq', 'bw'); await pg.select_option('#lib_m', 'gogus'); await pg.wait_for_timeout(200)
        names = await pg.evaluate("[...document.querySelectorAll('#lib_res li b')].map(x => x.textContent)")
        print('vücut ağırlığı + göğüs:', names)
        check('Şınav' in names and len(names) >= 3, 'filtre: vücut ağırlığıyla göğüs hareketleri')
        await pg.fill('#lib_q', 'kettlebell'); await pg.select_option('#lib_eq', ''); await pg.select_option('#lib_m', ''); await pg.wait_for_timeout(200)
        check(await pg.evaluate("document.querySelectorAll('#lib_res li').length") >= 4, 'arama: kettlebell')
        await pg.fill('#lib_q', ''); await pg.wait_for_timeout(100)

        # seans: sürümler ve değiştirme
        await pg.click('.daytile >> nth=0'); await pg.wait_for_timeout(300)
        first = await pg.evaluate("document.querySelector('.ex .nm').textContent")
        await pg.click('.ex >> nth=0 >> .linkbtn'); await pg.wait_for_timeout(300)
        chips = await pg.evaluate("[...document.querySelectorAll('#modal .vchip')].map(b => b.textContent)")
        check(any(x.startswith('Vücut ağırlığı') for x in chips) and any(x.startswith('Kablo') for x in chips), 'lat pulldown sürümleri: vücut ağırlığı ve kablo ' + str(chips[:4]))
        alts = await pg.evaluate("document.querySelectorAll('#modal .list li').length")
        check(alts >= 3, f'alternatif sayısı {alts}')
        await pg.screenshot(path=SP + 'shots/k_modal.png')
        await pg.click("#modal .vchip:has-text('Barfiks') >> nth=0"); await pg.wait_for_timeout(300)
        await pg.click('#modal [data-act=swapEx]'); await pg.wait_for_timeout(300)
        sw = await pg.evaluate("JSON.stringify(S.swaps)"); now = await pg.evaluate("document.querySelector('.ex .nm').textContent")
        check(sw == '{"latpd":"pullup"}' and now.startswith('Barfiks'), f'değiştirme kaydedildi: {sw} / {now}')
        # değiştirilen hareketle set gir, kaydet, hacimde say
        await pg.fill('.ex >> nth=0 >> input[data-k=kg] >> nth=0', '0'); await pg.fill('.ex >> nth=0 >> input[data-k=reps] >> nth=0', '8')
        await pg.evaluate("stopRest && stopRest()")
        await pg.click('[data-act=saveWorkout]'); await pg.wait_for_timeout(400)
        saved = await pg.evaluate("Object.keys(S.workouts[S.workouts.length - 1].sets)")
        check('pullup' in saved, 'set değiştirilen hareketin adıyla kaydedildi ' + str(saved))
        vol = await pg.evaluate("weekVolume(weekIndex('2026-10-19')).vol.sirt || 0")
        check(vol >= 1, f'hacim haritası değiştirilen hareketi sayıyor ({vol})')
        await pg.click('#modal [data-act=closeModal]')
        await pg.reload(); await pg.wait_for_timeout(300)
        check(await pg.evaluate("S.swaps.latpd") == 'pullup', 'değiştirme yeniden açılışta duruyor')
        # geri dön
        await pg.click('.tabs [data-tab=antrenman]'); await pg.click('.daytile >> nth=0'); await pg.wait_for_timeout(300)
        await pg.click('.ex >> nth=0 >> .linkbtn'); await pg.wait_for_timeout(300)
        await pg.click('#modal [data-act=swapEx]'); await pg.wait_for_timeout(300)
        check(await pg.evaluate("JSON.stringify(S.swaps)") == '{}' and (await pg.evaluate("document.querySelector('.ex .nm').textContent")) == first, 'ilk harekete dönüldü')

        # süreli hareketle değiştirme: yan plank -> mekik (tekrara döner)
        u = await pg.evaluate("(() => { S.swaps.g_splank = 'crunch'; const e = effEx(EX_BY_ID.g_splank); S.swaps = {}; return [e.name, e.unit || 'tekrar', e.lo, e.hi]; })()")
        check(u[1] == 'tekrar' and u[2] == 10, 'süreli hareket tekrarlı hareketle değişince tekrar hedefi ' + str(u))
        check(await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), 'telefonda yatay taşma yok')
        await c.close()

        # eski veri (swaps alanı yok) sorunsuz açılır
        o = await b.new_context(); op = await o.new_page(); op.on('pageerror', lambda e: errs.append('eski:' + str(e)))
        await onboard(op)
        await op.evaluate("(() => { const k = 'forma_state_' + JSON.parse(localStorage.getItem('forma_profiles')).cur; const st = JSON.parse(localStorage.getItem(k)); delete st.swaps; localStorage.setItem(k, JSON.stringify(st)); })()")
        await op.reload(); await op.wait_for_timeout(300)
        await op.click('.sb-item[data-tab=antrenman]'); await op.wait_for_timeout(200)
        check(await op.evaluate("JSON.stringify(S.swaps)") == '{}', 'swaps alanı olmayan eski veri taşındı')
        await o.close(); await b.close()
    print('ERRORS', errs)

asyncio.run(main())
