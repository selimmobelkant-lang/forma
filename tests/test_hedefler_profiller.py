import asyncio, json
from playwright.async_api import async_playwright
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / 'index.html').as_uri()
(ROOT / 'tests' / 'shots').mkdir(exist_ok=True)
SP = str(ROOT / 'tests' / 'shots') + '/'

errs=[]
async def onboard(pg, name, goal, weight, weeks=None, date='2026-10-19'):
    await pg.goto(URL+'?bugun='+date)
    await pg.fill('#ob_name',name); await pg.click('[data-act=obNext]')
    await pg.fill('#ob_age','30'); await pg.fill('#ob_height','180'); await pg.fill('#ob_weight',weight); await pg.fill('#ob_waist','86'); await pg.fill('#ob_neck','38'); await pg.click('[data-act=obNext]')
    await pg.click(f'label.opt:has(input[name=ob_goaltype][value={goal}])'); await pg.wait_for_timeout(150)
    await pg.screenshot(path=SP+f'f_ob2_{goal}.png', full_page=True)
    await pg.click('[data-act=obNext]')
    if weeks is not None: await pg.select_option('#ob_weeks', str(weeks))
    if await pg.query_selector('#ob_goal'): await pg.fill('#ob_goal','4')
    await pg.fill('#ob_start', date)
    await pg.click('[data-act=obNext]')
    await pg.check('#ob_commit'); await pg.click('[data-act=obNext]'); await pg.wait_for_timeout(300)
async def checkin(pg, date, w, waist):
    await pg.goto(URL+'?bugun='+date)
    await pg.click('.sb-item[data-tab=kontrol]')
    await pg.fill('#k_weight', w); await pg.fill('#k_waist', waist)
    for a in ['kcal','cardio','train','sleep']: await pg.check('#a_'+a)
    await pg.click('[data-act=saveCheckin]'); await pg.wait_for_selector('#modal')
    t = await pg.inner_text('#modal h2'); await pg.click('#modal [data-act=applyDecision] >> nth=0'); return t
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(locale='tr-TR', viewport={'width':1440,'height':950})
        pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        # profile 1: gain, 16 weeks
        await onboard(pg,'Ahmet','gain','70', 16)
        print('gain targets', await pg.evaluate("[targets().kcal, targets().P, targets().C, targets().F, S.profile.weeks, S.profile.goal, cardioTarget(3)]"))
        await pg.screenshot(path=SP+'f_gain_today.png')
        print('G1', await checkin(pg,'2026-10-26','71','86'))   # +1 week1 → erken
        print('G2', await checkin(pg,'2026-11-02','71','86'))   # 0 → yavas
        print('G3', await checkin(pg,'2026-11-09','71,3','86')) # +0.3 iyi
        print('G4', await checkin(pg,'2026-11-16','72','87,2')) # +0.7 waist +1.2 → yaglanma
        print('adj', await pg.evaluate("S.adjustments.map(a=>a.desc)"))
        # session thumb + exinfo
        await pg.click('.sb-item[data-tab=antrenman]'); await pg.click('.daytile >> nth=0')
        await pg.screenshot(path=SP+'f_session.png')
        await pg.click('.exthumb >> nth=0'); await pg.wait_for_timeout(300)
        await pg.screenshot(path=SP+'f_exinfo.png'); await pg.click('#modal [data-act=closeModal]')
        await pg.click('[data-act=cancelSession]')
        # new block: maintain, süresiz
        await pg.click('.sb-item[data-tab=ayarlar]')
        await pg.click('[data-act=newBlock] >> nth=0'); await pg.wait_for_timeout(200)
        await pg.click('label.opt:has(input[name=nb_goal][value=maintain])'); await pg.wait_for_timeout(150)
        await pg.select_option('#nb_weeks','0'); await pg.fill('#nb_start','2026-11-16')
        await pg.screenshot(path=SP+'f_newblock.png')
        await pg.click('[data-act=nbStart]'); await pg.wait_for_timeout(400)
        print('maintain', await pg.evaluate("[S.profile.goal, S.profile.weeks, targets().kcal, S.plan.tdee, S.blocks.length, blockCheckins().length, cardioTarget(5)]"))
        await pg.screenshot(path=SP+'f_maintain_today.png')
        print('M1', await checkin(pg,'2026-11-23','72,2','87'))
        print('M2', await checkin(pg,'2026-11-30','73','87,5'))
        print('M3', await checkin(pg,'2026-12-07','71,6','87'))
        await pg.goto(URL+'?bugun=2026-12-30'); await pg.click('.sb-item[data-tab=ilerleme]')
        await pg.screenshot(path=SP+'f_progress.png', full_page=True)
        # profiles
        await pg.click('.sb-user'); await pg.wait_for_timeout(200)
        await pg.click('[data-act=addProfile]'); await pg.wait_for_timeout(300)
        print('new profile onboarding shown:', await pg.is_visible('#ob_name'))
        await onboard(pg,'Elif','cut','68', 13, '2026-12-30')
        await pg.click('.sb-user'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=SP+'f_profiles.png')
        await pg.click('[data-act=switchProfile]'); await pg.wait_for_timeout(300)
        print('switched to:', await pg.evaluate("[S.profile.name, PIDX.list.length, PIDX.list.map(x=>x.name)]"))
        await pg.click('.sb-user'); await pg.click('[data-act=deleteProfile]'); await pg.wait_for_timeout(200)
        print('after delete:', await pg.evaluate("[PIDX.list.map(x=>x.name), Object.keys(localStorage).filter(k=>k.startsWith('forma_state'))]"))
        await b.close()
    print('ERRORS', errs)
asyncio.run(main())
