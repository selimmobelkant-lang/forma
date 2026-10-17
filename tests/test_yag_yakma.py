import asyncio, json
from playwright.async_api import async_playwright
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / 'index.html').as_uri()
(ROOT / 'tests' / 'shots').mkdir(exist_ok=True)
SP = str(ROOT / 'tests' / 'shots') + '/'

errs=[]
async def checkin(pg, date, w, waist=None, adh=True, creatine=False):
    await pg.goto(URL+'?bugun='+date)
    await pg.click('.tabs [data-tab=kontrol]')
    await pg.fill('#k_weight', w)
    if waist: await pg.fill('#k_waist', waist)
    if adh:
        for a in ['kcal','cardio','train','sleep']: await pg.check('#a_'+a)
    if creatine: await pg.check('#k_creatine')
    await pg.click('[data-act=saveCheckin]'); await pg.wait_for_selector('#modal')
    t = await pg.inner_text('#modal h2'); n = len(await pg.query_selector_all('#modal .note'))
    return t, n
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':430,'height':900})
        pg=await ctx.new_page()
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: errs.append(m.text) if m.type=='error' else None)
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        await pg.goto(URL+'?bugun=2026-10-19')
        await pg.fill('#ob_name','Sese'); await pg.click('[data-act=obNext]')
        await pg.fill('#ob_age','27'); await pg.fill('#ob_height','178'); await pg.fill('#ob_weight','94,6')
        await pg.fill('#ob_waist','104'); await pg.fill('#ob_neck','40'); await pg.click('[data-act=obNext]')
        await pg.click('[data-act=obNext]')
        await pg.fill('#ob_goal','12'); await pg.fill('#ob_start','2026-10-19')
        await pg.click('label:has(input[name=ob_lim][value=diz])')
        await pg.screenshot(path=SP+'01_ob3.png', full_page=True)
        await pg.click('[data-act=obNext]')
        await pg.fill('#ob_r2','3. haftada'); await pg.check('#ob_commit'); await pg.click('[data-act=obNext]')
        await pg.screenshot(path=SP+'02_today.png', full_page=True)
        # steps & sleep for a week
        st = await pg.evaluate("JSON.parse(localStorage.getItem(SKEY(PIDX.cur)))")
        import datetime
        d0 = datetime.date(2026,10,19)
        for i in range(14):
            d = (d0+datetime.timedelta(days=i)).isoformat()
            st['days'][d] = {'foods':[],'water':2,'sleep': 6.2 if i>=7 else 7.5,'steps': 9000 if i<7 else 6000,'walks':2}
        await pg.evaluate("s => localStorage.setItem(SKEY(PIDX.cur), JSON.stringify(s))", st)
        await pg.reload()
        # workout session
        await pg.click('.task [data-act=startWorkout]')
        ins = await pg.query_selector_all('.sets input')
        for i, el in enumerate(ins): await el.fill('40' if i%2==0 else '10')
        sels = await pg.query_selector_all('.sets select')
        for i, el in enumerate(sels): await el.select_option('4' if i<2 else '1')
        # trigger change on a reps field to start rest timer
        await pg.dispatch_event('.sets input[data-k=reps]', 'change')
        await pg.wait_for_timeout(600)
        print('restbar on:', await pg.evaluate("document.getElementById('restbar').classList.contains('on')"), await pg.inner_text('#restT'))
        await pg.screenshot(path=SP+'03_session.png')
        await pg.click('[data-act=saveWorkout]'); await pg.wait_for_selector('#modal')
        print('summary:', (await pg.inner_text('#modal'))[:200].replace('\n',' | '))
        await pg.screenshot(path=SP+'04_summary.png')
        await pg.click('#modal [data-act=closeModal]')
        await pg.screenshot(path=SP+'05_training.png', full_page=True)
        # second session lower performance for drop detection
        await pg.goto(URL+'?bugun=2026-10-23')
        await pg.click('.tabs [data-tab=antrenman]')
        await pg.click('.daytile[data-day=U1]')
        ins = await pg.query_selector_all('.sets input')
        for i, el in enumerate(ins): await el.fill('35' if i%2==0 else '8')
        await pg.click('[data-act=saveWorkout]'); await pg.wait_for_selector('#modal')
        print('drops note:', 'performans düştü' in (await pg.inner_text('#modal')))
        await pg.click('#modal [data-act=closeModal]')
        # JW timer
        await pg.click('[data-act=jwStart] >> nth=0'); await pg.wait_for_timeout(700)
        print('jw:', await pg.inner_text('#jwPh'), await pg.inner_text('#jwBig'))
        await pg.evaluate("UI.jw.start -= 6*60*1000"); await pg.wait_for_timeout(600)
        await pg.click('[data-act=jwStop]')
        # nutrition
        await pg.click('.tabs [data-tab=beslenme]')
        await pg.fill('#food_q','pirinç'); await pg.click('#food_res li >> nth=0')
        await pg.screenshot(path=SP+'06_food_raw.png')
        await pg.check('#food_oil'); await pg.click('[data-act=addFood]')
        await pg.click('[data-act=navDay][data-d="1"]') if False else None
        st = await pg.evaluate("JSON.parse(localStorage.getItem(SKEY(PIDX.cur)))")
        print('foods 10-23:', [f['n'] for f in st['days']['2026-10-23']['foods']], 'cardio:', [(c['type'],c['min']) for c in st['cardio']])
        await pg.goto(URL+'?bugun=2026-10-24'); await pg.click('.tabs [data-tab=beslenme]')
        await pg.click('[data-act=copyYesterday]')
        await pg.screenshot(path=SP+'07_nutrition.png', full_page=True)
        # check-ins
        print('W1', await checkin(pg,'2026-10-26','94,5','104', creatine=True))
        await pg.click('#modal [data-act=applyDecision]')
        print('W2', await checkin(pg,'2026-11-02','94,6','104'))
        await pg.screenshot(path=SP+'08_decision.png')
        await pg.click('#modal [data-act=applyDecision]')
        print('W3', await checkin(pg,'2026-11-09','94,7','104'))
        await pg.click('#modal [data-opt=carb]')
        print('W4', await checkin(pg,'2026-11-16','94,7','104'))
        await pg.click('#modal [data-opt=move]')
        print('W5', await checkin(pg,'2026-11-23','93,6','102'))
        await pg.click('#modal [data-act=applyDecision]')
        # event mode
        await pg.goto(URL+'?bugun=2026-11-30'); await pg.click('.mhead [data-tab=ayarlar]')
        await pg.fill('#ev_start','2026-11-30'); await pg.fill('#ev_date','2026-12-20'); await pg.click('[data-act=eventStart]')
        await pg.goto(URL+'?bugun=2026-12-08')
        await pg.screenshot(path=SP+'09_event_today.png', full_page=True)
        t = await pg.evaluate("[targets().kcal, stepTarget(), cardioTarget(8), eventInfo().phase, eventInfo().week]")
        print('event wk2:', t)
        await pg.goto(URL+'?bugun=2026-12-28')
        print('reverse:', await pg.evaluate("[targets().kcal, eventInfo().phase, S.plan.baseKcal + S.plan.kcalAdjust]"))
        await pg.goto(URL+'?bugun=2027-02-10')
        print('done:', await pg.evaluate("[targets().kcal, eventInfo().phase]"))
        # week13 checkin
        print('W16', await checkin(pg,'2027-02-10','90','98'))
        await pg.click('#modal [data-opt=plus150]')
        await pg.click('.tabs [data-tab=ilerleme]')
        await pg.screenshot(path=SP+'10_progress.png', full_page=True)
        await pg.click('.tabs [data-tab=rehber]')
        await pg.screenshot(path=SP+'11_guide.png', full_page=True)
        # PPL switch
        await pg.click('.mhead [data-tab=ayarlar]'); await pg.select_option('#s_prog','ppl3'); await pg.click('[data-act=saveProfile]')
        await pg.click('.tabs [data-tab=antrenman]')
        await pg.screenshot(path=SP+'12_ppl.png', full_page=True)
        await pg.click('.daytile[data-day=LG]')
        await pg.screenshot(path=SP+'13_ppl_legs.png', full_page=True)
        # migration from v1 state
        ctx2=await b.new_context(viewport={'width':430,'height':900}, color_scheme='dark')
        v1 = {"v":1,"profile":{"name":"X","sex":"m","age":30,"height":180,"weight":90,"act":"moderate","pace":0.5,"goalFatKg":8,"start":"2026-10-10","trainingDays":[1,2,4,5],"reflection":{}},"plan":{"bmr":1900,"tdee":2900,"baseKcal":2350,"kcalAdjust":-200,"stepBonus":0,"cardioStart":120,"cardioCap":300},"checkins":[{"id":"a","date":"2026-10-10","baseline":True,"weight":90,"waist":100,"neck":40,"bf":24,"photos":[]}],"workouts":[{"id":"w","date":"2026-10-12","dayId":"U1","sets":{"latpd":[{"kg":40,"reps":10}]}}],"cardio":[],"days":{},"customFoods":[],"adjustments":[],"settings":{"waterTarget":3,"sleepTarget":7.5,"stepTarget":8000,"bedtime":"23:30"}}
        await ctx2.add_init_script("if(!localStorage.getItem('kocum90_v1')) localStorage.setItem('kocum90_v1', %s)" % json.dumps(json.dumps(v1)))
        pg2=await ctx2.new_page(); pg2.on('pageerror', lambda e: errs.append('v1:'+str(e)))
        await pg2.goto(URL+'?bugun=2026-10-20')
        await pg2.screenshot(path=SP+'14_dark_v1.png', full_page=True)
        await pg2.click('.tabs [data-tab=antrenman]')
        await pg2.screenshot(path=SP+'15_dark_training.png', full_page=True)
        print('migrated:', await pg2.evaluate("[S.v, S.profile.program, S.settings.rest, S.plan.event, nextWorkoutId()]"))
        await b.close()
    print('ERRORS', errs)
asyncio.run(main())
