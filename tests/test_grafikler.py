"""Grafikler (Chart.js): haftalık aktivite ve kalori tahmini, kas dağılımı radarı, kilo/bel/yağ çizgileri, tahmini 1RM ve haftalık hacim,
dokununca değer kutucuğu, tema renkleri, Chart.js yokken eski SVG grafiğe dönüş, telefonda taşma."""
import asyncio
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

# 6 hafta: haftada iki ağırlık antrenmanı (55 ve 48 dk), iki kardiyo (30 dk eğimli yürüyüş, 40 dk bisiklet), haftalık ölçüm
SEED = """(() => {
  const s = startDate();
  const mk = (d, dur, kg, dayId) => ({ id:uid(), date:addDays(s, d), dayId, duration:dur, note:'', sets:{ latpd:[{kg, reps:10, rir:1},{kg, reps:9, rir:1}], shpress:[{kg:kg-20, reps:10}], legpress:[{kg:kg*2, reps:12}] } });
  for (let wk = 0; wk < 6; wk++){ S.workouts.push(mk(wk * 7, 55, 50 + wk * 2.5, 'U1'), mk(wk * 7 + 3, 48, 48 + wk * 2, 'L1'));
    S.cardio.push({ id:uid(), date:addDays(s, wk * 7 + 1), min:30, type:'Eğimli yürüyüş', hr:125 }, { id:uid(), date:addDays(s, wk * 7 + 5), min:40, type:'Bisiklet', hr:130 }); }
  const b = S.checkins[0]; for (let i = 1; i <= 6; i++) S.checkins.push({ ...b, id:uid(), baseline:false, date:addDays(b.date, 7 * i), weight:b.weight - 0.6 * i, waist:b.waist - 0.5 * i, bf:(b.bf || 28) - 0.4 * i, decision:null });
  save(); })()"""

async def onboard(pg):
    await pg.goto(URL + '?bugun=2026-10-19')
    await pg.fill('#ob_name','Test'); await pg.click('[data-act=obNext]')
    await pg.fill('#ob_age','30'); await pg.fill('#ob_height','180'); await pg.fill('#ob_weight','85'); await pg.fill('#ob_waist','92'); await pg.fill('#ob_neck','39'); await pg.click('[data-act=obNext]')
    await pg.click('[data-act=obNext]'); await pg.fill('#ob_goal','8'); await pg.click('[data-act=obNext]')
    await pg.check('#ob_commit'); await pg.click('[data-act=obNext]'); await pg.wait_for_timeout(1300)

def ch(name): return f"CHARTS.find(c => c.canvas.isConnected && c.canvas.dataset.chart === '{name}')"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c = await b.new_context(locale='tr-TR', viewport={'width':375,'height':812}, is_mobile=True, has_touch=True, device_scale_factor=2)
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await onboard(pg)
        check(await pg.evaluate("window.Chart && Chart.version") == '4.5.1', 'Chart.js 4.5.1 yerel dosyadan yüklendi')
        await pg.evaluate(SEED)
        await pg.goto(URL + '?bugun=2026-11-26'); await pg.wait_for_timeout(700)   # 6. hafta, 4. gün

        # BUGÜN: haftalık aktivite
        wk = await pg.evaluate(f"(() => {{ const c = {ch('week')}; return {{ labels:c.data.labels, w:c.data.datasets[0].data, k:c.data.datasets[1].data, kcal:c.data.datasets[2].data, kg:currentWeight() }}; }})()")
        print('hafta', wk)
        check(wk['w'][0] == 55 and wk['w'][3] == 48 and wk['k'][1] == 30 and wk['k'][5] == 40, 'günlük antrenman ve kardiyo dakikaları doğru')
        kg = wk['kg']; exp1 = round((5 - 1) * kg * 55 / 60); exp2 = round((6 - 1) * kg * 30 / 60)
        check(abs(wk['kcal'][0] - exp1) <= 1 and abs(wk['kcal'][1] - exp2) <= 1, f'kalori tahmini (MET − 1) × kilo × saat ({wk["kcal"][0]} ≈ {exp1}, {wk["kcal"][1]} ≈ {exp2})')
        check(len(wk['labels']) == 7, 'yedi gün etiketi')
        stats = await pg.evaluate("[...document.querySelectorAll('.stat .v')].slice(0, 7).map(x => x.textContent)")
        check(any('/ 7' in x or '/7' in x.replace(' ', '') for x in stats), 'aktif gün özeti görünüyor')
        # dokununca değer kutucuğu
        await pg.locator('canvas[data-chart=week]').scroll_into_view_if_needed(); await pg.wait_for_timeout(500)
        bx = await pg.locator('canvas[data-chart=week]').bounding_box()
        await pg.touchscreen.tap(bx['x'] + bx['width'] * 0.18, bx['y'] + bx['height'] * 0.6); await pg.wait_for_timeout(350)
        tip = await pg.evaluate(f"(() => {{ const c = {ch('week')}; return [c.tooltip.opacity, (c.tooltip.body || []).map(b => b.lines.join(' '))]; }})()")
        print('dokunma', tip)
        check(tip[0] == 1 and len(tip[1]) == 3, 'dokununca değer kutucuğu açılıyor')
        await pg.screenshot(path=SP + 'shots/gr_today.png')

        # ANTRENMAN: kas dağılımı radarı = weekVolume
        await pg.click('.tabs [data-tab=antrenman]'); await pg.wait_for_timeout(600)
        r = await pg.evaluate(f"(() => {{ const c = {ch('radar')}; const v = weekVolume(weekIndex(today())).vol; return [c.data.labels.length, c.data.datasets[0].data, Object.keys(MUSCLES).map(m => Math.round((v[m] || 0) * 10) / 10), c.data.datasets[1].data.some(x => x > 0)]; }})()")
        check(r[0] == 14 and r[1] == r[2] and r[3], 'radar: 14 kas, bu haftanın sert setleri ve program hedefi')
        order = await pg.evaluate("[...document.querySelectorAll('#main .card .hd h3')].map(h => h.dataset.tr || h.textContent.trim())")
        check(order.index('Kas dağılımı') < order.index('Hareket kütüphanesi'), 'radar kütüphaneden önce')
        await pg.locator('canvas[data-chart=radar]').scroll_into_view_if_needed(); await pg.screenshot(path=SP + 'shots/gr_radar.png')

        # İLERLEME: kilo/bel/yağ, 1RM, hacim
        await pg.click('.tabs [data-tab=ilerleme]'); await pg.wait_for_timeout(700)
        w = await pg.evaluate(f"(() => {{ const c = {ch('weight')}; return [c.data.datasets.length, c.data.datasets[0].data.length, c.data.datasets[0].data.map(p => p.y), blockCheckins().map(c => c.weight)]; }})()")
        check(w[0] == 2 and w[1] == 7 and w[2] == [round(x, 2) for x in w[3]], 'kilo grafiği: 7 ölçüm ve plan çizgisi')
        check(await pg.evaluate(f"!!{ch('waist')} && !!{ch('bf')}"), 'bel ve yağ oranı grafikleri')
        e = await pg.evaluate(f"(() => {{ const c = {ch('e1rm')}; return [c.data.datasets[0].data.map(p => p.y), S.workouts.filter(w => w.sets.latpd).sort((a, b) => a.date < b.date ? -1 : 1).map(w => Math.round(bestE1rm(w.sets.latpd) * 10) / 10)]; }})()")
        check(e[0] == e[1] and len(e[0]) == 12, f'tahmini 1RM: lat pulldown, her seansın en iyi seti ({len(e[0])} seans)')
        await pg.select_option('#str_ex', 'legpress'); await pg.wait_for_timeout(500)
        e2 = await pg.evaluate(f"{ch('e1rm')}.data.datasets[0].data.length")
        lp = await pg.evaluate(f"[{ch('e1rm')}.data.datasets[0].data.at(-1).y, Math.round(bestE1rm(S.workouts.filter(w => w.sets.legpress).sort((a, b) => a.date < b.date ? -1 : 1).at(-1).sets.legpress) * 10) / 10]")
        check(e2 == 12 and lp[0] == lp[1] and await pg.evaluate("UI.strEx") == 'legpress', f'hareket seçimi grafiği değiştiriyor (leg press son 1RM {lp[0]})')
        ton = await pg.evaluate(f"(() => {{ const c = {ch('tonnage')}; const v = {{}}; S.workouts.forEach(w => {{ const k = weekIndex(w.date); Object.values(w.sets).forEach(ss => ss.forEach(x => {{ if (x.kg && x.reps) v[k] = (v[k] || 0) + x.kg * x.reps; }})); }}); return [c.data.datasets[0].data.slice(0, 6), [1,2,3,4,5,6].map(k => Math.round(v[k] || 0))]; }})()")
        check(ton[0] == ton[1], 'haftalık hacim (kg × tekrar) doğru')
        await pg.locator('canvas[data-chart=e1rm]').scroll_into_view_if_needed(); await pg.screenshot(path=SP + 'shots/gr_strength.png')
        check(await pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), 'telefonda yatay taşma yok')

        # tema: renkler temadan gelir
        col = lambda: pg.evaluate(f"{ch('weight')}.data.datasets[0].borderColor")
        z = await col()
        await pg.evaluate("S.settings.theme = 'ufuk'; S.settings.mode = 'light'; save(); applyTheme(); render()"); await pg.wait_for_timeout(400)
        u = await col()
        await pg.evaluate("S.settings.theme = 'zumrut'; S.settings.mode = 'dark'; save(); applyTheme(); render()"); await pg.wait_for_timeout(400)
        zd = await col()
        print('renkler', z, u, zd)
        check(z != u and zd != z, 'tema ve mod değişince grafik renkleri değişiyor')
        await pg.screenshot(path=SP + 'shots/gr_dark.png')
        n_old = await pg.evaluate("CHARTS.length")
        await pg.click('.tabs [data-tab=bugun]'); await pg.click('.tabs [data-tab=ilerleme]'); await pg.wait_for_timeout(400)
        check(await pg.evaluate("CHARTS.every(c => c.canvas.isConnected)"), f'eski grafikler temizleniyor ({n_old} → yeni ekran)')

        # Chart.js yoksa: kilo için eski SVG grafik, diğerlerinde not
        await pg.evaluate("window._C = window.Chart; delete window.Chart; render()"); await pg.wait_for_timeout(200)
        fb = await pg.evaluate("[!!document.querySelector('svg.chart'), document.body.textContent.includes('Grafik yüklenemedi')]")
        await pg.evaluate("window.Chart = window._C; render()")
        check(fb == [True, True], 'Chart.js yoksa SVG grafik ve not görünüyor')
        await c.close()

        # boş profil: grafik kartları hatasız, yönlendirici metinlerle
        e = await b.new_context(locale='tr-TR'); ep = await e.new_page(); ep.on('pageerror', lambda x: errs.append('boş:' + str(x)))
        await onboard(ep)
        for t in ['antrenman', 'ilerleme']:
            await ep.click(f'.sb-item[data-tab={t}]'); await ep.wait_for_timeout(300)
        check('Antrenman kaydettikçe' in await ep.evaluate("document.body.textContent"), 'kayıt yokken güç kartı açıklama gösteriyor')
        await e.close(); await b.close()
    print('ERRORS', errs)

asyncio.run(main())
