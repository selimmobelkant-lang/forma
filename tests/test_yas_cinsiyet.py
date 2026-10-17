"""Yaş, deneyim ve 'Belirtmek istemiyorum': kalori formülü, alt sınır, yağ oranı, önerilen program, tükenişsiz setler, uyarı notları."""
import asyncio, math
from playwright.async_api import async_playwright
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / 'index.html').as_uri()
(ROOT / 'tests' / 'shots').mkdir(exist_ok=True)
SP = str(ROOT / 'tests') + '/'
errs = []
def jsround(x): return math.floor(x + 0.5)
def check(ok, msg):
    print(('ok ' if ok else 'HATA ') + msg)
    if not ok: errs.append(msg)

async def onboard(b, sex, age, exp, hip=None, shot=None):
    c = await b.new_context(viewport={'width':390,'height':844}, is_mobile=True, has_touch=True)
    pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.goto(URL + '?bugun=2026-10-19')
    await pg.fill('#ob_name', 'Test'); await pg.click('[data-act=obNext]')
    await pg.check(f'input[name=ob_sex][value={sex}]')
    await pg.fill('#ob_age', str(age)); await pg.fill('#ob_height', '170'); await pg.fill('#ob_weight', '75'); await pg.fill('#ob_waist', '88'); await pg.fill('#ob_neck', '36')
    if hip: await pg.fill('#ob_hip', str(hip))
    await pg.click('[data-act=obNext]'); await pg.click('[data-act=obNext]')
    await pg.select_option('#ob_exp', exp); await pg.wait_for_timeout(150)
    rec = await pg.evaluate("[document.querySelector('input[name=ob_prog]:checked')?.value, [...document.querySelectorAll('.opt')].find(o => o.querySelector('.pill.acc'))?.querySelector('input')?.value, document.querySelector('.note.warn')?.textContent || '']")
    if shot: await pg.screenshot(path=SP + 'shots/' + shot, full_page=True)
    if await pg.locator('#ob_goal').count(): await pg.fill('#ob_goal', '5')
    await pg.click('[data-act=obNext]')
    await pg.check('#ob_commit'); await pg.click('[data-act=obNext]'); await pg.wait_for_timeout(1300)
    return c, pg, rec

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # belirtmek istemiyorum, 70 yaş
        c, pg, rec = await onboard(b, 'x', 70, 'mid', hip=100, shot='y_ob3_70.png')
        pr = await pg.evaluate("[S.profile.sex, S.plan.bmr, minKcal(S.profile.sex), bodyFat('x', 170, 88, 36, 100), bodyFat('m', 170, 88, 36), bodyFat('f', 170, 88, 36, 100), S.profile.program]")
        print('x/70:', pr, rec)
        check(pr[1] == jsround(10*75 + 6.25*170 - 5*70 - 78), f'BMR iki formülün ortalaması ({pr[1]})')
        check(pr[2] == 1200, 'alt sınır 1.200 kcal')
        check(abs(pr[3] - (pr[4] + pr[5]) / 2) < 0.11, 'yağ oranı iki formülün ortalaması')
        check(rec[0] == 'joint3' and rec[1] == 'joint3', '70 yaşta önerilen ve seçili program: eklem dostu')
        check('65 yaş' in rec[2], 'kurulumda 65+ notu')
        await pg.click('.tabs [data-tab=antrenman]'); await pg.wait_for_timeout(200)
        check('65 yaş' in await pg.evaluate("document.querySelector('#main').textContent"), "ANTRENMAN'da 65+ notu")
        await pg.evaluate("S.profile.program = 'ul4'; render()")
        fails = await pg.evaluate("Object.values(PROGRAMS.ul4.days).flatMap(d => dayEx(d)).filter(e => e.fail).length")
        check(fails == 0, '65+ için tükeniş hedefi yok')
        await pg.click('.mhead [data-tab=ayarlar]'); await pg.wait_for_timeout(200)
        check(await pg.evaluate("document.querySelector('#s_sex').value") == 'x', "Ayarlar'da cinsiyet görünüyor")
        await pg.click('.tabs [data-tab=kontrol]'); await pg.wait_for_timeout(200)
        check(await pg.locator('#k_hip').count() == 1, 'haftalık kontrolde kalça ölçüsü isteniyor')
        await c.close()
        # yeni başlayan, 30 yaş, erkek
        c, pg, rec = await onboard(b, 'm', 30, 'new')
        check(rec[0] == 'fb_mc', f'yeni başlayana önerilen: tüm vücut makine ({rec[0]})')
        fails = await pg.evaluate("Object.values(PROGRAMS.ul4.days).flatMap(d => dayEx(d)).filter(e => e.fail).length")
        check(fails == 0 and await pg.evaluate("S.profile.exp") == 'new', 'yeni başlayan için tükeniş yok')
        await pg.evaluate("S.profile.exp = 'pro'; render()")
        check(await pg.evaluate("Object.values(PROGRAMS.ul4.days).flatMap(d => dayEx(d)).filter(e => e.fail).length") > 0, 'deneyimli için programdaki tükeniş hedefleri duruyor')
        await c.close()
        # 16 yaş, kadın
        c, pg, rec = await onboard(b, 'f', 16, 'mid', hip=96)
        check('18 yaş' in rec[2], '18 yaş altı notu')
        check(await pg.evaluate("[S.plan.bmr, minKcal('f')]") == [jsround(10*75 + 6.25*170 - 5*16 - 161), 1200], 'kadın formülü değişmedi')
        await c.close(); await b.close()
    print('ERRORS', errs)

asyncio.run(main())
