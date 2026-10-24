"""HTTP-mocked browser contracts: independent of Clerk/provider quality."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright,expect

data=json.loads((Path(__file__).resolve().parents[2]/'frontend/public/submission-demo.json').read_text(encoding='utf-8'))
analysis=data['samples'][0]['analysis']
with sync_playwright() as p:
    browser=p.chromium.launch(channel='msedge',headless=True);page=browser.new_page();errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    preference={'share_history_with_provider':False};calls=[]
    def prefs(route):
        if route.request.method=='PATCH':preference.update(route.request.post_data_json);calls.append(preference.copy())
        route.fulfill(json=preference)
    page.route('**/nlp/preferences',prefs)
    page.route('**/nlp/analyze',lambda r:r.fulfill(json={'nlp_analysis':analysis}))
    match={'scene_id':'scene000001','source_turn_id':1,'source_session_id':'synthetic','excerpt':'A remembered project report.','query_excerpt':'project report','lexical_score':.3,'semantic_score':.8,'fusion_score':.032787}
    page.route('**/nlp/memory/search',lambda r:r.fulfill(json={'status':'ready','method':'rrf60','index_revision':1,'coverage':{'indexed_scenes':1,'eligible_scenes':1},'results':[match]}))
    label={'label':'work','group':'topic','entailment':.7,'neutral':.2,'contradiction':.1,'adjusted_score':.3,'spans':[[0,10]]}
    result={'status':'ready','premise_count':1,'suggestions':[label],'labels':[label],'redacted_text':analysis['redacted_text']}
    page.route('**/nlp/classification/preview',lambda r:r.fulfill(json=result))
    page.goto('http://127.0.0.1:5173/tests/harness.html');page.get_by_role('button',name='Analyze preview',exact=True).click()
    toggle=page.get_by_role('checkbox',name='Allow historical excerpts in provider responses');toggle.wait_for();assert not toggle.is_checked()
    page.get_by_label('Search conversation memory',exact=True).fill('project report');page.get_by_role('button',name='Search local memory',exact=True).click()
    page.get_by_text('A remembered project report.',exact=True).wait_for();assert 'turn_id=1' in page.get_by_role('link',name='Source turn 1').get_attribute('href')
    toggle.click();expect(toggle).to_be_checked();assert calls and calls[-1]['share_history_with_provider']
    page.get_by_text('Experimental zero-shot suggestions',exact=True).click();page.get_by_role('button',name='Classify preview locally').click()
    page.get_by_text('topic: work',exact=True).wait_for()
    committed={**analysis,'classification':{'status':'pending','turn_id':1}};polls=[]
    page.route('**/chat',lambda r:r.fulfill(json={'session_id':'synthetic','response_text':'A deterministic reflection.','safety_mode':'deterministic_outage','nlp_analysis':committed}))
    page.route('**/sessions/*/analysis',lambda r:r.fulfill(json={'records':[]}))
    def polling(route):
        polls.append(1);route.fulfill(json={'status':'pending'} if len(polls)==1 else result)
    page.route('**/nlp/turns/1/classification',polling)
    page.goto('http://127.0.0.1:5173/tests/harness.html?chat=1');page.locator('textarea').fill('The office project report needs discussion.');page.get_by_role('button',name='Send',exact=True).click()
    page.get_by_text('Experimental zero-shot suggestions',exact=True).click();page.get_by_text('topic: work',exact=True).wait_for()
    assert len(polls)==2;page.wait_for_timeout(2500);assert len(polls)==2
    page.get_by_text('Experimental zero-shot suggestions',exact=True).click();assert not errors,errors
    print('Neural Playwright PASS: default-off opt-in, search/excerpt provenance, preview, pending-to-ready polling and terminal stop')
    browser.close()
