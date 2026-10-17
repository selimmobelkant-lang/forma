import asyncio, json
from playwright.async_api import async_playwright
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / 'index.html').as_uri()
(ROOT / 'tests' / 'shots').mkdir(exist_ok=True)
SP = str(ROOT / 'tests') + '/'

errs=[]; reqs=[]
MOCK={"content":[{"type":"text","text":"```json\n{\"items\":[{\"name\":\"Tavuk sote\",\"grams\":180,\"kcal\":290,\"protein\":38,\"carbs\":8,\"fat\":11},{\"name\":\"Pirinç pilavı\",\"grams\":150,\"kcal\":230,\"protein\":4,\"carbs\":44,\"fat\":4},{\"name\":\"Çoban salata (zeytinyağlı)\",\"grams\":120,\"kcal\":95,\"protein\":1,\"carbs\":6,\"fat\":7}],\"confidence\":\"orta\",\"notes\":\"Pilavın yağ miktarı belirsiz.\"}\n```"}]}
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':1440,'height':950})
        pg=await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: asyncio.ensure_future(d.accept()))
        async def handle(route, request):
            reqs.append((request.url, request.headers, json.loads(request.post_data)))
            await route.fulfill(status=200, content_type='application/json', body=json.dumps(MOCK), headers={'access-control-allow-origin':'*'})
        await pg.route('https://api.anthropic.com/**', handle)
        await pg.goto(URL+'?bugun=2026-10-19')
        await pg.fill('#ob_name','Test'); await pg.click('[data-act=obNext]')
        await pg.fill('#ob_age','30'); await pg.fill('#ob_height','180'); await pg.fill('#ob_weight','85'); await pg.fill('#ob_waist','92'); await pg.fill('#ob_neck','39'); await pg.click('[data-act=obNext]')
        await pg.click('[data-act=obNext]'); await pg.fill('#ob_goal','8'); await pg.click('[data-act=obNext]')
        await pg.check('#ob_commit'); await pg.screenshot(path=SP+'shots/h_ob4.png'); await pg.click('[data-act=obNext]')
        await pg.wait_for_timeout(1300); await pg.screenshot(path=SP+'shots/h_today.png')
        await pg.click('.sb-item[data-tab=antrenman]'); await pg.wait_for_timeout(300)
        await pg.screenshot(path=SP+'shots/h_training.png')
        await pg.click('.daytile >> nth=0'); await pg.wait_for_timeout(400)
        await pg.screenshot(path=SP+'shots/h_session.png')
        await pg.click('.exthumb >> nth=2'); await pg.wait_for_timeout(500)
        await pg.screenshot(path=SP+'shots/h_exinfo.png'); await pg.click('#modal [data-act=closeModal]')
        await pg.click('[data-act=cancelSession]')
        await pg.click('.sb-item[data-tab=beslenme]'); await pg.screenshot(path=SP+'shots/h_nutrition.png')
        await pg.click('[data-act=aiOpen]'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=SP+'shots/h_ai_setup.png')
        await pg.fill('#ai_key','sk-ant-test'); await pg.click('#modal [data-act=aiSaveConf]'); await pg.wait_for_timeout(200)
        await pg.set_input_files('#ai_file', SP+'ornek-foto.jpg'); await pg.wait_for_timeout(500)
        await pg.fill('#ai_note','tavuk sote ve pilav')
        await pg.screenshot(path=SP+'shots/h_ai_photo.png')
        await pg.click('[data-act=aiRun]'); await pg.wait_for_selector('.aitable'); await pg.wait_for_timeout(200)
        await pg.screenshot(path=SP+'shots/h_ai_result.png')
        await pg.fill('input[data-ai="1"][data-k=grams]','100'); await pg.press('input[data-ai="1"][data-k=grams]','Tab'); await pg.wait_for_timeout(200)
        await pg.click('#modal [data-act=aiAdd]')
        foods = await pg.evaluate("S.days[today()].foods.map(f=>[f.n,f.amt,Math.round(f.k)])")
        print('foods', foods)
        u,h,body = reqs[0]
        print('req', u, h.get('anthropic-dangerous-direct-browser-access'), body['model'], body['messages'][0]['content'][0]['type'], len(body['messages'][0]['content'][0]['source']['data']))
        # error path
        await pg.unroute('https://api.anthropic.com/**')
        await pg.route('https://api.anthropic.com/**', lambda r, q: asyncio.ensure_future(r.fulfill(status=401, content_type='application/json', body=json.dumps({"type":"error","error":{"type":"authentication_error","message":"invalid x-api-key"}}), headers={'access-control-allow-origin':'*'})))
        await pg.click('[data-act=aiOpen]'); await pg.set_input_files('#ai_file', SP+'ornek-foto.jpg'); await pg.wait_for_timeout(400)
        await pg.click('[data-act=aiRun]'); await pg.wait_for_selector('#modal .note.bad')
        print('error shown:', await pg.inner_text('#modal .note.bad'))
        await pg.screenshot(path=SP+'shots/h_ai_error.png')
        # dark mobile session
        ctx2=await b.new_context(viewport={'width':400,'height':860}, device_scale_factor=2, color_scheme='dark')
        st = await pg.evaluate("JSON.stringify({ix:localStorage.getItem(PKEY), st:localStorage.getItem(SKEY(PIDX.cur))})")
        await ctx2.add_init_script("var d=%s; if(!localStorage.getItem('forma_profiles')){localStorage.setItem('forma_profiles', d.ix); localStorage.setItem('forma_state_p1', d.st);}" % st)
        m=await ctx2.new_page(); m.on('pageerror', lambda e: errs.append('m:'+str(e)))
        await m.goto(URL+'?bugun=2026-10-20'); await m.wait_for_timeout(500)
        await m.click('.tabs [data-tab=antrenman]'); await m.click('.daytile >> nth=1'); await m.wait_for_timeout(400)
        await m.screenshot(path=SP+'shots/h_mobile_session.png')
        await b.close()
    print('ERRORS', errs)
asyncio.run(main())
