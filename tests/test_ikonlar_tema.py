import asyncio
from playwright.async_api import async_playwright
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / 'index.html').as_uri()
(ROOT / 'tests' / 'shots').mkdir(exist_ok=True)
SP = str(ROOT / 'tests') + '/'

errs=[]
async def onboard(pg):
    await pg.goto(URL+'?bugun=2026-10-19')
    await pg.fill('#ob_name','Test'); await pg.click('[data-act=obNext]')
    await pg.fill('#ob_age','30'); await pg.fill('#ob_height','180'); await pg.fill('#ob_weight','85'); await pg.fill('#ob_waist','92'); await pg.fill('#ob_neck','39'); await pg.click('[data-act=obNext]')
    await pg.screenshot(path=SP+'shots/i_ob3.png')
    await pg.click('[data-act=obNext]'); await pg.fill('#ob_goal','8'); await pg.click('[data-act=obNext]')
    await pg.check('#ob_commit'); await pg.click('[data-act=obNext]'); await pg.wait_for_timeout(1300)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':1440,'height':950})
        pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await onboard(pg)
        await pg.screenshot(path=SP+'shots/i_today.png')
        print('h3 decorated', await pg.evaluate("[...document.querySelectorAll('.card .hd h3')].map(h=>h.dataset.i+':'+h.textContent.trim()).join(' | ')"))
        await pg.click('[data-act=sos][data-k=weak]'); await pg.wait_for_timeout(300)
        await pg.screenshot(path=SP+'shots/i_sos.png'); await pg.click('#modal [data-act=closeModal]')
        await pg.click('.sb-item[data-tab=rehber]'); await pg.wait_for_timeout(300)
        await pg.evaluate("document.querySelectorAll('details').forEach((d,i)=>{ if(i==2||i==9) d.open=true })")
        await pg.screenshot(path=SP+'shots/i_guide.png')
        await pg.evaluate("window.scrollTo(0, document.querySelectorAll('details')[9].offsetTop-80)")
        await pg.screenshot(path=SP+'shots/i_guide2.png')
        await pg.click('.sb-item[data-tab=antrenman]'); await pg.click('.daytile >> nth=0'); await pg.wait_for_timeout(300)
        await pg.click('.exthumb >> nth=1'); await pg.wait_for_timeout(300)
        await pg.screenshot(path=SP+'shots/i_exinfo.png'); await pg.click('#modal [data-act=closeModal]')
        await pg.click('[data-act=cancelSession]')
        # mobil + neon koyu
        m=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2)
        mp=await m.new_page(); mp.on('pageerror', lambda e: errs.append(str(e)))
        await onboard(mp)
        await mp.evaluate("S.settings.theme='neon'; S.settings.mode='dark'; save(); applyTheme(); render()")
        await mp.wait_for_timeout(300); await mp.screenshot(path=SP+'shots/i_m_today.png')
        qt=await mp.evaluate("document.querySelector('.qcard .qtext')?.textContent || ''"); print('günün cümlesi', qt)
        if len(qt) < 10: errs.append('günün cümlesi yok')
        await mp.click('.tabs [data-tab=rehber]'); await mp.wait_for_timeout(300)
        await mp.evaluate("document.querySelectorAll('details')[4].open=true; document.querySelectorAll('details')[12].open=true")
        await mp.screenshot(path=SP+'shots/i_m_guide.png', full_page=True)
        await mp.click('.tabs [data-tab=beslenme]'); await mp.wait_for_timeout(300)
        await mp.screenshot(path=SP+'shots/i_m_nutr.png', full_page=True)
        # açılış ekranı, varsayılan tema, günün cümlesi
        s=await b.new_context(viewport={'width':390,'height':844})
        await s.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>false})")
        sp=await s.new_page(); sp.on('pageerror', lambda e: errs.append(str(e)))
        await sp.goto(URL+'?bugun=2026-10-19'); await sp.wait_for_timeout(300)
        acik=await sp.evaluate("[!!document.querySelector('#splash:not(.out)'), document.querySelector('#spQuote').textContent.length > 10, document.documentElement.dataset.theme]")
        await sp.wait_for_timeout(2400)
        kapandi=await sp.evaluate("!document.querySelector('#splash')")
        print('splash', acik, kapandi)
        if acik != [True, True, 'zumrut'] or not kapandi: errs.append('açılış ekranı veya varsayılan tema hatalı')
        await sp.goto(URL+'?bugun=2026-10-19'); await sp.click('#splash'); await sp.wait_for_timeout(600)
        if not await sp.evaluate("!document.querySelector('#splash')"): errs.append('dokununca açılış ekranı kapanmadı')
        await s.close()
        print('ERRORS', errs)
        await b.close()
asyncio.run(main())
