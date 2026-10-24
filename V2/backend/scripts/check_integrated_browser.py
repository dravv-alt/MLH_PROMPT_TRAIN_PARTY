"""Headless Chrome integration checks; existing browser, no downloads.

Uses a loopback fixture with an in-memory database, synthetic authentication,
and mocked generation/neural workers. Tests real HTTP routes and React views.
"""
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import urllib.request
import websocket

BACKEND=Path(__file__).resolve().parents[1]
FRONTEND=BACKEND.parent/'frontend'
ARTIFACTS=BACKEND.parent/'.runtime'/'integration-check'


def http_json(url):
    with urllib.request.urlopen(url,timeout=3) as response:return json.load(response)


def run():
    ARTIFACTS.mkdir(parents=True,exist_ok=True)
    env={**os.environ,'SANCTUARY_BROWSER_FIXTURE':'1','VITE_API_BASE_URL':'/api','SANCTUARY_BACKEND_URL':'http://127.0.0.1:8107'}
    children=[]; handles=[]; checks=[]; ws=None
    profile=tempfile.mkdtemp(prefix='sanctuary-browser-check-')
    try:
        for name,command,cwd in [
            ('backend',[sys.executable,'-m','uvicorn','scripts.browser_fixture_server:app','--host','127.0.0.1','--port','8107'],BACKEND),
            ('frontend',['node',str(FRONTEND/'node_modules/vite/bin/vite.js'),'--config','vite.integration.config.js','--host','127.0.0.1','--port','5187'],FRONTEND)]:
            handle=(ARTIFACTS/f'{name}.log').open('w',encoding='utf8');handles.append(handle)
            children.append(subprocess.Popen(command,cwd=cwd,env=env,stdout=handle,stderr=handle,creationflags=subprocess.CREATE_NO_WINDOW))
        deadline=time.monotonic()+40
        while True:
            try:
                http_json('http://127.0.0.1:8107/health')
                with urllib.request.urlopen('http://127.0.0.1:5187',timeout=2) as response:
                    assert b'/src/main.jsx' in response.read(), 'Frontend entry missing'
                with urllib.request.urlopen('http://127.0.0.1:5187/src/main.jsx',timeout=2) as response:
                    assert b'/src/IntegratedApp.jsx' in response.read(), 'Normal entry did not mount the connected application'
                break
            except Exception:
                if time.monotonic()>deadline:raise RuntimeError('Fixture servers did not become ready')
                time.sleep(.3)
        chrome=Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe')
        if not chrome.exists():chrome=Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe')
        children.append(subprocess.Popen([str(chrome),'--headless=new','--remote-debugging-port=0','--remote-allow-origins=*',
            '--user-data-dir='+profile,'--no-first-run','--disable-background-networking','--enable-unsafe-swiftshader','about:blank'],
            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=subprocess.CREATE_NO_WINDOW))
        portfile=Path(profile)/'DevToolsActivePort';deadline=time.monotonic()+20
        while not portfile.exists():
            if time.monotonic()>deadline:raise RuntimeError('Chrome debugging endpoint unavailable')
            time.sleep(.2)
        port=portfile.read_text().splitlines()[0]
        page=next(p for p in http_json(f'http://127.0.0.1:{port}/json/list') if p['type']=='page')
        ws=websocket.create_connection(page['webSocketDebuggerUrl'],timeout=30,suppress_origin=True)
        sequence=0
        errors=[]
        def call(method,params=None):
            nonlocal sequence
            sequence+=1;identity=sequence
            ws.send(json.dumps({'id':identity,'method':method,'params':params or {}}))
            while True:
                result=json.loads(ws.recv())
                if result.get('method')=='Runtime.exceptionThrown':errors.append(result['params']['exceptionDetails'].get('text'))
                if result.get('id')==identity:
                    if 'error' in result:raise RuntimeError(str(result['error']))
                    return result.get('result',{})
        def evaluate(expression):
            result=call('Runtime.evaluate',{'expression':expression,'returnByValue':True,'awaitPromise':True})
            if result.get('exceptionDetails'):raise RuntimeError(str(result['exceptionDetails']))
            return result.get('result',{}).get('value')
        def wait(expression,timeout=45):
            deadline=time.monotonic()+timeout
            while not evaluate(expression):
                if time.monotonic()>deadline:raise RuntimeError('Timed out: '+expression)
                time.sleep(.25)
        def navigate(page,extra=''):
            call('Page.navigate',{'url':'http://127.0.0.1:5187/tests/harness.html?page='+page+extra})
            wait('document.readyState === "complete"')
        def fill(selector,value):
            evaluate("(()=>{const e=document.querySelector("+json.dumps(selector)+"); if(!e)throw Error('input missing'); const p=e.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:e.tagName==='SELECT'?HTMLSelectElement.prototype:HTMLInputElement.prototype; Object.getOwnPropertyDescriptor(p,'value').set.call(e,"+json.dumps(value)+");e.dispatchEvent(new Event(e.tagName==='SELECT'?'change':'input',{bubbles:true}));})()")
        def button(text):
            evaluate("(()=>{const e=[...document.querySelectorAll('button')].find(e=>e.textContent.trim()==="+json.dumps(text)+");if(!e)throw Error('button missing');e.click();})()")
        def passed(name):checks.append({'name':name,'passed':True});print('PASS '+name,flush=True)
        call('Page.enable');call('Runtime.enable')
        navigate('chat');wait("!!document.querySelector('#chat-draft')")
        fill('#chat-draft','I feel tired after work, but I enjoyed meeting Priya Sharma.')
        button('Send');wait("document.querySelectorAll('.bubble.assistant').length===1",70)
        sid=evaluate("new URLSearchParams(location.search).get('session_id')")
        passed('chat submission through HTTP, committed analysis and session URL')
        fill('#chat-draft','I still feel tired after work, although the conversation helped.')
        button('Send');wait("document.querySelectorAll('.bubble.assistant').length===2",70)
        passed('second turn in the same conversation')
        evaluate("document.querySelector('details.technical-details').open=true")
        wait("document.body.textContent.includes('unscented kf')")
        passed('all mathematical filters, SSM and canonical memory are renderable')
        button('Turn insights')
        evaluate("[...document.querySelectorAll('.turn-drawer summary')].find(e=>e.textContent.trim()==='Experimental suggestions').click()")
        wait("document.body.textContent.includes('Classification: ready')",15)
        passed('classification pending-to-ready polling')
        navigate('chat','&session_id='+sid);wait("document.querySelectorAll('.bubble.assistant').length===2")
        passed('conversation reload from persisted backend history')
        navigate('moments','&session_id='+sid);wait("document.querySelectorAll('.journal-turn').length===2")
        evaluate("document.querySelector('.journal-turn input').click()")
        fill('input[maxlength="200"]','Browser integration moment')
        button('Save moment');wait("document.body.textContent.includes('Moment saved to your journal.')")
        passed('save selected conversation turn as a journal moment')
        navigate('memory');wait("!!document.querySelector('#memory-query')")
        fill('#memory-query','tired work');button('Search local memory')
        wait("document.querySelectorAll('.memory-result').length>0")
        wait("document.querySelectorAll('svg[aria-label=\"World memory graph\"] circle').length>3")
        passed('memory search and graph including narrative node types')
        navigate('settings');wait("document.querySelectorAll('input[type=checkbox]').length===3")
        wait("!document.querySelector('input[type=checkbox]').disabled")
        evaluate("document.querySelector('input[type=checkbox]').click()")
        wait("document.querySelector('input[type=checkbox]').checked")
        navigate('settings');wait("document.querySelector('input[type=checkbox]')?.checked")
        passed('privacy preference persistence after navigation')
        navigate('journal');wait("!!document.querySelector('textarea')")
        wait("!document.body.textContent.includes('Syncing journal')")
        fill('input[placeholder^="Entry title"]','Quiet evening')
        fill('textarea','I took a short walk and felt calmer.')
        evaluate("[...document.querySelectorAll('button')].find(e=>e.textContent.includes('Save Entry')).click()")
        wait("[...document.querySelectorAll('button')].some(e=>e.querySelector('span:last-child')?.textContent==='Saved')")
        navigate('journal');wait("document.querySelector('input[placeholder^=\"Entry title\"]')?.value==='Quiet evening'")
        assert evaluate("document.querySelector('textarea').value.includes('short walk')")
        passed('calendar journal saves and reloads through account API')
        navigate('chat','&session_id='+sid);wait("document.querySelectorAll('.bubble.assistant').length===2")
        wait("[...document.querySelectorAll('option')].some(e=>e.value==='hosted'&&!e.disabled)")
        fill('select:not([aria-label])','hosted')
        wait("document.body.textContent.includes('Allow this redacted message')")
        fill('#chat-draft','I feel tired after work.')
        assert evaluate("[...document.querySelectorAll('button')].find(e=>e.textContent.trim()==='Send').disabled")
        evaluate("[...document.querySelectorAll('label')].find(e=>e.textContent.includes('Allow this redacted message')).querySelector('input').click()")
        button('Send');wait("document.querySelector('[role=alert]')?.textContent.includes('hosted model did not return')")
        assert evaluate("document.querySelector('#chat-draft').value==='I feel tired after work.'")
        assert evaluate("document.querySelectorAll('.bubble.assistant').length===2")
        passed('hosted consent and outage retain draft without committing a turn')
        screenshot=call('Page.captureScreenshot',{'format':'png','captureBeyondViewport':False})
        (ARTIFACTS/'chat-outage.png').write_bytes(base64.b64decode(screenshot['data']))
        if errors:raise RuntimeError('Browser runtime exceptions: '+repr(errors))
        result={'passed':True,'checks':checks,'boundary':'Synthetic auth; mocked generator, embeddings, NLI, constituency and DMRST; real HTTP routes, spaCy analysis, mathematical suite, isolated SQLite fixture database, memory harness and React.','application_database_writes':False}
    except Exception as exc:
        result={'passed':False,'checks':checks,'error':str(exc)}
        raise
    finally:
        if ws:ws.close()
        for process in reversed(children):
            if process.poll() is None:process.terminate()
        for handle in handles:handle.close()
        if 'result' in locals():
            (ARTIFACTS/'browser-results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
        print('Artifacts: '+str(ARTIFACTS),flush=True)
    return result


if __name__=='__main__':run()
