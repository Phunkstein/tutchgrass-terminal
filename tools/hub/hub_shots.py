from playwright.sync_api import sync_playwright
B='http://127.0.0.1:8811/terminal/'
P=[('hub',''),('lab','lab/'),('terps','terps/'),('terps_sleep','terps/sleep/'),('terps_entourage','terps/entourage/'),('science','science/'),('news','news/'),('dispensary','dispensary/'),('quiz','quiz/'),('duel','duel/'),('report_cards','report-cards/'),('report_card_one','report-cards/looper/'),('account','account/'),('leaderboards','leaderboards/'),('brand','looper/')]
with sync_playwright() as pw:
    br=pw.chromium.launch(executable_path='/usr/bin/google-chrome'); ctx=br.new_context(viewport={'width':390,'height':844},device_scale_factor=2,is_mobile=True,has_touch=True)
    pg=ctx.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.on('console',lambda m:m.type=='error' and errs.append('console:'+m.text))
    for n,u in P:
        errs.clear(); pg.goto(B+u,wait_until='networkidle'); pg.wait_for_timeout(400)
        ov=pg.evaluate('document.documentElement.scrollWidth-document.documentElement.clientWidth')
        wide=pg.evaluate('''[...document.querySelectorAll("body *")].filter(e=>e.getBoundingClientRect().right>innerWidth+1&&getComputedStyle(e).position!="fixed").slice(0,4).map(e=>e.tagName+"."+e.className)''')
        pg.screenshot(path=f'screenshots/hub_{n}.png')
        print(n,'overflow',ov,wide if ov>0 else '','ERR' if errs else '',errs[:3])
    # quiz play
    pg.goto(B+'quiz/',wait_until='networkidle')
    for i in range(5):
        b=pg.locator('[data-quiz] button.qo, .quiz button').first
        if not b.count(): break
        b.click(); pg.wait_for_timeout(250)
    pg.screenshot(path='screenshots/hub_quiz_result.png',full_page=False); print('quiz result shot')
    pg.goto(B+'duel/',wait_until='networkidle'); pg.locator('.duel button, [data-duel] button').first.click(); pg.wait_for_timeout(500)
    pg.screenshot(path='screenshots/hub_duel_reveal.png'); print('duel shot',errs)
    pg.goto(B+'terps/sleep/',wait_until='networkidle'); pg.screenshot(path='screenshots/hub_terps_sleep_full.png',full_page=True)
    br.close()
