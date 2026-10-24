"""Playwright verification against Vite on 5173; uses installed local Edge."""
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright

def main():
    fixture=Path(__file__).resolve().parents[2]/'frontend/public/submission-demo.json'
    data=json.loads(fixture.read_text(encoding='utf-8'))
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='msedge',headless=True)
        page=browser.new_page()
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.route('**/nlp/analyze',lambda route:route.fulfill(json={'status':'preview','revision':0,'nlp_analysis':data['samples'][0]['analysis']}))
        page.goto('http://127.0.0.1:5173/tests/harness.html')
        page.get_by_role('button',name='Analyze preview').click()
        page.get_by_role('heading',name='Text analysis',exact=True).wait_for()
        page.get_by_role('button',name='Select but relation').click()
        assert 'Arg1:' in page.get_by_test_id('arguments').inner_text()
        assert page.locator('.span-highlight').count()>0
        page.get_by_role('button',name='t000001',exact=False).click()
        if data['samples'][0]['analysis'].get('pwm'):
            from app.services.memory_tools import memory_graph
            import copy
            memory=copy.deepcopy(data['samples'][0]['analysis']['pwm'])
            memory['revision']=1
            memory['unresolved']=[{'id':'u000001','type':'unfinished_expression','status':'open'}]
            page.route('**/nlp/memory',lambda route:route.fulfill(json=memory))
            page.route('**/nlp/memory/graph',lambda route:route.fulfill(json=memory_graph(memory)))
            def review(route):
                body=route.request.post_data_json
                assert body['expected_revision']==memory['revision']
                memory['unresolved'][0]['status']=body['status'];memory['revision']+=1
                route.fulfill(json={'revision':memory['revision'],'item':memory['unresolved'][0]})
            page.route('**/nlp/memory/unresolved/*',review)
            page.get_by_role('button',name='Load my world memory',exact=True).click()
            page.get_by_role('heading',name='World memory connections',exact=True).wait_for()
            page.get_by_role('button',name='dismissed',exact=True).click()
            page.get_by_text('u000001: unfinished_expression · dismissed',exact=True).wait_for()
        page.unroute('**/nlp/analyze')
        page.route('**/nlp/analyze',lambda route:route.fulfill(status=503,json={'error':{'code':'ai_unavailable','message':'Mocked provider unavailable'}}))
        page.get_by_role('button',name='Analyze preview').click()
        page.get_by_role('alert').filter(has_text='Mocked provider unavailable').wait_for()
        # Backend provider-failure path is covered in pytest; here exercise its UI contract.
        a=data['samples'][0]['analysis']
        page.route('**/chat',lambda route:route.fulfill(json={'session_id':'synthetic-session','response_text':data['samples'][0]['response'],'safety_mode':'deterministic_outage','nlp_analysis':a}))
        page.route('**/sessions/*/analysis',lambda route:route.fulfill(json={'records':[{'turn_id':1,'analysis':a}]}))
        page.goto('http://127.0.0.1:5173/tests/harness.html?chat=1')
        page.locator('textarea').fill('I wanted to speak but stayed quiet because the meeting felt tense.')
        page.get_by_role('button',name='Send',exact=True).click()
        page.get_by_role('status').filter(has_text='Provider unavailable').wait_for()
        page.get_by_role('heading',name='Text analysis',exact=True).wait_for()
        page.get_by_label('Inspect committed turn',exact=True).select_option('0')
        page.goto('http://127.0.0.1:5173/demo.html')
        page.get_by_role('heading',name='Text analysis',exact=True).wait_for()
        assert 'deterministic reflection' in page.get_by_role('status').inner_text()
        page.get_by_label('Scenario',exact=True).select_option('3')
        page.get_by_role('button',name='t000001',exact=False).click()
        assert not errors, errors
        print('Playwright: preview, relation/topic selection, world-memory graph/review, error display, chat outage, and walkthrough PASS')
        browser.close()

if __name__=='__main__': main()
