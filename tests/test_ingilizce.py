"""İngilizce arayüz: uygulamayı İngilizce modda baştan sona gezer, çevirisi bulunamayan metinleri ve ekranda kalan Türkçe harfleri arar.
Kullanım: python3 tests/test_ingilizce.py        (test)
          python3 tests/test_ingilizce.py --dump (eksik çevirileri tests/shots/i18n_eksik.json'a yazar)"""
import asyncio, json, re, sys
from playwright.async_api import async_playwright
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
URL = (ROOT / 'index.html').as_uri()
(ROOT / 'tests' / 'shots').mkdir(exist_ok=True)
SP = str(ROOT / 'tests') + '/'
DUMP = '--dump' in sys.argv
errs, miss, turk = [], set(), set()
ctx = {}
TR_CHARS = re.compile(r'[çğıöşüÇĞİÖŞÜ]')
# kullanıcı içeriği ve özel adlar: ekranda Türkçe harfle görünmesi hata değildir
ALLOW = {'Test', 'Zümrüt'}

async def collect(pg, where=''):
    got = await pg.evaluate("I18N_MISS ? [...I18N_MISS] : []")
    miss.update(got)
    if DUMP:
        c = await pg.evaluate("""(() => { const out = {}; if (!I18N_MISS) return out; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
          for (let n = w.nextNode(); n; n = w.nextNode()){ const s = n.nodeValue.trim(); if (!s || !I18N_MISS.has(s)) continue;
            const b = n.parentElement?.closest('li,p,td,label,button,h2,h3,summary,.note,.kicker,.small,div'); const tx = (b?.textContent || '').replace(/\\s+/g, ' ').trim();
            if (tx && tx !== s) out[s] = tx.slice(0, 300); } return out; })()""")
        for k, v in c.items(): ctx.setdefault(k, v)
    vis = await pg.evaluate("""(() => { const out = []; const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      for (let n = w.nextNode(); n; n = w.nextNode()){ const p = n.parentElement; if (!p || p.closest('script,style,textarea,[data-notr]')) continue;
        const s = n.nodeValue.trim(); if (s && /[çğıöşüÇĞİÖŞÜ]/.test(s)) out.push(s); }
      document.querySelectorAll('[placeholder],[title],[aria-label]').forEach(e => ['placeholder','title','aria-label'].forEach(a => { const v = e.getAttribute(a); if (v && /[çğıöşüÇĞİÖŞÜ]/.test(v) && !e.closest('[data-notr]')) out.push(v); }));
      return out; })()""")
    for v in vis:
        if v not in ALLOW: turk.add(v)
    # grafik içindeki yazılar (canvas): veri etiketleri, eksen başlıkları, kategori adları
    cv = await pg.evaluate("""(typeof CHARTS === 'undefined' ? [] : CHARTS).filter(c => c.canvas.isConnected).flatMap(c => [...(c.data.labels || []), ...c.data.datasets.map(d => d.label),
      ...Object.values(c.options.scales || {}).map(s => s.title && s.title.text).filter(Boolean)]).filter(x => typeof x === 'string')""")
    for v in cv:
        if TR_CHARS.search(v): turk.add('GRAFİK: ' + v)

async def onboard(pg, age=34, sex='m', exp='mid'):
    await pg.fill('#ob_name', 'Test'); await pg.click('[data-act=obNext]'); await collect(pg)
    await pg.check(f'input[name=ob_sex][value={sex}]')
    await pg.fill('#ob_age', str(age)); await pg.fill('#ob_height', '178'); await pg.fill('#ob_weight', '92'); await pg.fill('#ob_waist', '100'); await pg.fill('#ob_neck', '40')
    if sex != 'm': await pg.fill('#ob_hip', '104')
    await collect(pg); await pg.click('[data-act=obNext]'); await collect(pg)
    for g in ['maintain', 'gain', 'cut']:
        await pg.check(f'input[name=ob_goaltype][value={g}]'); await pg.wait_for_timeout(80); await collect(pg)
    await pg.click('[data-act=obNext]')
    await pg.select_option('#ob_exp', exp); await pg.wait_for_timeout(80); await collect(pg)
    if await pg.locator('#ob_goal').count(): await pg.fill('#ob_goal', '8')
    await pg.click('[data-act=obNext]'); await collect(pg)
    await pg.check('#ob_commit'); await pg.click('[data-act=obNext]'); await pg.wait_for_timeout(1200); await collect(pg)

async def tabs(pg, guide=False):
    for t in ['bugun', 'antrenman', 'beslenme', 'kontrol', 'ilerleme', 'rehber']:
        await pg.click(f'.tabs [data-tab={t}]'); await pg.wait_for_timeout(120)
        if t == 'rehber' or guide: await pg.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
        await collect(pg)
    await pg.click('.mhead [data-tab=ayarlar]'); await pg.wait_for_timeout(120); await collect(pg)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        c = await b.new_context(locale='en-US', viewport={'width':390,'height':844}, is_mobile=True, has_touch=True)
        pg = await c.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('dialog', lambda d: (miss.add('DIALOG:' + d.message) if TR_CHARS.search(d.message) else None, asyncio.ensure_future(d.dismiss())))
        await pg.goto(URL + '?bugun=2026-10-19')
        lang = await pg.evaluate("[LANG, document.documentElement.lang]")
        if lang != ['en', 'en']: errs.append('İngilizce cihazda dil otomatik İngilizce olmadı: ' + str(lang))
        await pg.evaluate("I18N_MISS = new Set(); translateTree(document.body); render()")
        await collect(pg)
        await onboard(pg, age=70, sex='x', exp='new')
        await tabs(pg)

        # veri tabloları: hareketler, programlar, besinler, öğünler, hedefler, evreler, sözler...
        await pg.evaluate("""(() => { const seen = new Set();
          const walk = v => { if (typeof v === 'string'){ if (!/^data:|^ex\\/|^[a-z0-9_]+$|^[A-Z0-9]{1,4}$|^[A-Za-z0-9-]*_[A-Za-z0-9_()-]*$|^oklch|^#|^https?:/.test(v) && /[A-Za-zÇĞİÖŞÜçğıöşü]/.test(v)) trText(v.replace(/<[^>]+>/g, ' ').replace(/\\s+/g, ' ')); return; }
            if (!v || typeof v !== 'object' || seen.has(v)) return; seen.add(v); (Array.isArray(v) ? v : Object.values(v)).forEach(walk); };
          [LIB, PROGRAMS, FOODS, MEALS, GOALS, WEEK_OPTS, PHASES, ACT, MUSCLES, LIMITS, EQ, LEVELS, PATTERNS, PROG_CATS, EXP, QUOTES, ZONES, TABS, TAB_NAMES, THEMES, SOS, AI_PROVIDERS].forEach(walk); })()""")
        await collect(pg)

        # pencereler
        for act in ['appearance', 'profiles', 'programs']:
            await pg.evaluate(f"A['{act}']()"); await pg.wait_for_timeout(80)
            await pg.evaluate("document.querySelectorAll('#modal details').forEach(d => d.open = true)"); await collect(pg)
            if act == 'programs':
                for cat in await pg.evaluate("Object.keys(PROG_CATS)"):
                    await pg.evaluate(f"A.progCat({{dataset:{{v:'{cat}'}}}})"); await pg.evaluate("document.querySelectorAll('#modal details').forEach(d => d.open = true)"); await collect(pg)
            await pg.evaluate("closeModal(true)")
        for k in ['bad', 'miss', 'out', 'quit', 'weak']:
            await pg.evaluate(f"A.sos({{dataset:{{k:'{k}'}}}})"); await collect(pg); await pg.evaluate("closeModal(true)")
        # tüm hareket kartları, tüm kısıtlar açıkken
        await pg.evaluate("S.profile.limits = Object.fromEntries(Object.keys(LIMITS).map(k => [k, true])); save()")
        await pg.evaluate("LIB.forEach(e => { modal(exInfoModal(EX_BY_ID[e.id] || e)); }); closeModal(true)"); await collect(pg)
        # tüm programların tüm günleri: seans ekranı ve hareket kartı (programdan açılınca)
        for k in await pg.evaluate("PROG_ORDER"):
            nd = await pg.evaluate(f"(() => {{ S.profile.program = '{k}'; S.profile.trainingDays = PROGRAMS['{k}'].defaultDays.slice(); UI.session = null; UI.tab = 'antrenman'; render(); return PROGRAMS['{k}'].days.length; }})()")
            await collect(pg)
            for i in range(nd):
                await pg.click(f'.daytile >> nth={i}'); await pg.wait_for_timeout(60); await collect(pg)
                await pg.click('.ex >> nth=0 >> .linkbtn'); await pg.wait_for_timeout(60); await collect(pg); await pg.evaluate("closeModal(true); UI.session = null; render()")
        await pg.evaluate("S.profile.program = 'ul4'; S.profile.trainingDays = [1,2,4,5]; S.profile.limits = {}; S.profile.exp = 'pro'; S.profile.age = 34; save(); UI.tab = 'antrenman'; render()")
        await collect(pg)
        # deneyimli profil: tükeniş hedefleri ve hareket kartındaki reçete (tüm programlar)
        for k in await pg.evaluate("PROG_ORDER"):
            await pg.evaluate(f"S.profile.program = '{k}'; UI.session = null; UI.tab = 'antrenman'; render()")
            for i in range(await pg.evaluate(f"PROGRAMS['{k}'].days.length")):
                await pg.click(f'.daytile >> nth={i}'); await pg.wait_for_timeout(40)
                for e in range(await pg.locator('.ex').count()):
                    await pg.evaluate(f"A.exInfo(document.querySelectorAll('.ex .linkbtn')[{e}])"); await collect(pg)
                await pg.evaluate("closeModal(true); UI.session = null; render()")
        await pg.evaluate("S.profile.program = 'ul4'; save(); render()")
        # seans: set gir, dinlenme, kaydet, özet (dolgu set, uzun seans)
        await pg.click('.daytile >> nth=0'); await pg.wait_for_timeout(80)
        await pg.fill('.ex >> nth=0 >> input[data-k=kg] >> nth=0', '40'); await pg.fill('.ex >> nth=0 >> input[data-k=reps] >> nth=0', '10'); await pg.wait_for_timeout(80); await collect(pg)
        await pg.select_option('.ex >> nth=0 >> select[data-k=rir] >> nth=0', '4')
        await pg.evaluate("UI.session.startedAt = Date.now() - 95 * 60000"); await pg.click('[data-act=saveWorkout]'); await pg.wait_for_timeout(150); await collect(pg)
        await pg.evaluate("closeModal(true); stopRest()")
        # bir hafta sonra aynı gün: ilerleme ipuçları ve güç düşüşü
        await pg.goto(URL + '?bugun=2026-10-26'); await pg.wait_for_timeout(200); await pg.evaluate("I18N_MISS = I18N_MISS || new Set()")
        await pg.evaluate("I18N_MISS = new Set()"); await pg.click('.tabs [data-tab=antrenman]'); await pg.click('.daytile >> nth=0'); await pg.wait_for_timeout(80); await collect(pg)
        await pg.fill('.ex >> nth=0 >> input[data-k=kg] >> nth=0', '30'); await pg.fill('.ex >> nth=0 >> input[data-k=reps] >> nth=0', '6')
        await pg.fill('.ex >> nth=1 >> input[data-k=kg] >> nth=0', '20'); await pg.fill('.ex >> nth=1 >> input[data-k=reps] >> nth=0', '6')
        await pg.click('[data-act=saveWorkout]'); await pg.wait_for_timeout(150); await collect(pg); await pg.evaluate("closeModal(true); stopRest()")

        # beslenme: arama, ekleme, örnek öğün, el ile, dünü tekrarla, AI
        await pg.click('.tabs [data-tab=beslenme]'); await pg.wait_for_timeout(80)
        if await pg.locator('#food_q').count():
            await pg.fill('#food_q', 'chicken'); await pg.wait_for_timeout(80); await collect(pg)
            await pg.fill('#food_q', 'tavuk'); await pg.wait_for_timeout(80); await collect(pg)
            if await pg.locator('#food_res li').count(): await pg.click('#food_res li >> nth=0'); await pg.wait_for_timeout(80); await collect(pg)
        for act in ['addMeal', 'aiOpen', 'aiSetup']:
            loc = pg.locator(f'[data-act={act}]')
            if await loc.count():
                await loc.first.click(); await pg.wait_for_timeout(120); await collect(pg); await pg.evaluate("closeModal(true)")
        await pg.evaluate("render()"); await collect(pg)

        # kontrol ve karar motoru: farklı senaryolar
        await pg.evaluate("""(() => {
          const base = lastCheckin(); const mk = (wk, dw, dwa, adh, extra = {}) => ({ id:'t' + wk + dw + Math.random(), date:addDays(base.date, 7 * wk), weight:base.weight - dw, waist:base.waist - dwa, neck:base.neck, hip:base.hip,
            adherence: adh || { kcal:true, cardio:true, train:true, sleep:true }, ...extra });
          for (let i = 0; i < 21; i++){ const d = addDays(base.date, i); S.days[d] = S.days[d] || { foods:[], water:0, walks:0 }; S.days[d].steps = i < 14 ? 9000 : 5000; S.days[d].sleep = 6; }
          const out = []; const show = (goal, cur, prev = base) => { S.profile.goal = goal; const d = decide(prev, cur); const ci = { ...cur, decision:d }; out.push(ci); modal(decisionModal(ci)); };
          show('cut', mk(1, 2.5, 1)); show('cut', mk(4, 2.5, 1)); show('cut', mk(4, 0.6, 1)); show('cut', mk(4, 0, 1.5)); show('cut', mk(2, 0, 0)); show('cut', mk(2, -0.5, 0));
          show('cut', mk(5, 0, -0.5)); show('cut', mk(5, -0.6, -1)); show('cut', mk(5, 0.1, 0)); show('cut', mk(3, 0.3, 0, { kcal:false, cardio:false, train:true, sleep:true }, { creatine:true }));
          show('cut', mk(14, 0.5, 0.5));
          S.profile.weeks = null; show('maintain', mk(2, 0.2, 0)); show('maintain', mk(2, -1, -1.2)); show('maintain', mk(2, 1, 0));
          show('gain', mk(1, -1, 0)); show('gain', mk(4, -1, -1.2)); show('gain', mk(4, -1, 0)); show('gain', mk(4, 0, 0)); show('gain', mk(4, -0.3, 0));
          S.profile.goal = 'cut'; S.profile.weeks = 13;
          S.checkins.push(...out.slice(0, 6).map((c, i) => ({ ...c, date:addDays(base.date, 7 * (i + 1)) }))); save(); closeModal(true);
        })()""")
        await collect(pg)
        for t in ['kontrol', 'ilerleme']:
            await pg.click(f'.tabs [data-tab={t}]'); await pg.wait_for_timeout(120); await collect(pg)
        sd = pg.locator('[data-act=showDecision]')
        if await sd.count(): await sd.first.click(); await pg.wait_for_timeout(80); await collect(pg); await pg.evaluate("closeModal(true)")
        ad = await pg.evaluate("(() => { const c = S.checkins[S.checkins.length - 1]; c.decision.applied = null; modal(decisionModal(c)); return !!document.querySelector('#modal [data-act=applyDecision]'); })()")
        if ad: await pg.click('#modal [data-act=applyDecision] >> nth=0'); await pg.wait_for_timeout(80); await collect(pg); await pg.evaluate("closeModal(true)")

        # etkinlik modu, yeni dönem, ayarlar, profiller
        await pg.click('.mhead [data-tab=ayarlar]'); await pg.wait_for_timeout(80)
        if await pg.locator('[data-act=eventStart]').count(): await pg.click('[data-act=eventStart]'); await pg.wait_for_timeout(120); await collect(pg)
        for d in ['2026-10-26', '2026-11-09', '2026-11-20']:
            await pg.goto(URL + f'?bugun={d}'); await pg.evaluate("I18N_MISS = new Set()"); await tabs(pg); await collect(pg)
        if await pg.locator('[data-act=eventCancel]').count(): await pg.click('[data-act=eventCancel]')
        await pg.evaluate("A.newBlock ? A.newBlock() : null"); await pg.wait_for_timeout(100); await collect(pg); await pg.evaluate("closeModal(true)")
        for d in ['2026-10-12', '2027-01-25']:
            await pg.goto(URL + f'?bugun={d}'); await pg.evaluate("I18N_MISS = new Set()"); await tabs(pg, guide=True); await collect(pg)
        await pg.evaluate("A.jwStart && A.jwStart()"); await pg.wait_for_timeout(100); await collect(pg); await pg.evaluate("A.jwStop && A.jwStop(); closeModal(true)")
        await pg.evaluate("A.addProfile()"); await pg.wait_for_timeout(150); await collect(pg)
        await onboard(pg, age=16, sex='f', exp='mid'); await collect(pg)
        await pg.evaluate("A.profiles()"); await collect(pg); await pg.evaluate("closeModal(true)")
        await pg.screenshot(path=SP + 'shots/en_today.png')

        # dil değişimi: Türkçeye dön, metin geri gelsin
        await pg.click('.mhead [data-tab=ayarlar]'); await pg.click('[data-act=setLang][data-v=tr]'); await pg.wait_for_timeout(150)
        tr = await pg.evaluate("[LANG, document.documentElement.lang, document.querySelector('.tabs [data-tab=bugun] span').textContent, document.querySelector('#restbar .small').textContent]")
        if tr != ['tr', 'tr', 'Bugün', 'Dinlen']: errs.append('Türkçeye dönüş eksik: ' + str(tr))
        await pg.click('[data-act=setLang][data-v=en]'); await pg.wait_for_timeout(150)
        en = await pg.evaluate("[LANG, localStorage.getItem('forma_lang')]")
        if en != ['en', 'en']: errs.append('İngilizceye geçiş kaydedilmedi: ' + str(en))
        await c.close(); await b.close()

    # ayıklama: ayırıcıyla birleşik listelerin parçaları zaten listede ise bütünü at
    DATE = re.compile(r'(?:(?:Sunday|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday),? )?\d{1,2} (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sept?(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b')
    def norm(s): return re.sub(r'\d+(?:[.,]\d+)*', '#', DATE.sub('@', s.strip()))
    keys = {norm(m) for m in miss if m.strip()}
    keys = {k for k in keys if re.search('[A-Za-zÇĞİÖŞÜçğıöşü]', k.replace('@', ''))}
    keys = {k for k in keys if not any(sep in k and all(norm(x) in keys or not re.search('[A-Za-zÇĞİÖŞÜçğıöşü]', x) for x in k.split(sep)) for sep in (' · ', ', ', ' / ', ' → '))}
    print('eksik çeviri:', len(keys), '· ekranda Türkçe harfli metin:', len(turk))
    if DUMP:
        cn = {norm(k): v for k, v in ctx.items()}
        (ROOT / 'tests' / 'shots' / 'i18n_eksik.json').write_text(json.dumps([[k, cn.get(k, '')] for k in sorted(keys)], ensure_ascii=False, indent=0))
        (ROOT / 'tests' / 'shots' / 'i18n_turkce.json').write_text(json.dumps(sorted(turk), ensure_ascii=False, indent=0))
    else:
        for k in sorted(keys)[:25]: print('  eksik:', k[:120])
        for k in sorted(turk)[:15]: print('  türkçe:', k[:120])
        if keys: errs.append(f'{len(keys)} eksik çeviri')
        if turk: errs.append(f'{len(turk)} Türkçe metin ekranda')
    print('ERRORS', errs)

asyncio.run(main())
