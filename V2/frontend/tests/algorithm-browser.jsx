// Explicit browser-only fixtures. Production routes never import this module.
import React from 'react';
import {createRoot} from 'react-dom/client';
import {BrowserRouter} from 'react-router-dom';
import {AnalysisWorkspace} from '../src/pages/AnalysisPage';
const calls = [];
const filters = Object.fromEntries(['linear_kf','extended_kf','unscented_kf','ensemble_kf','particle_filter'].map(key=>[key,{estimate:[.5],initialized:[true],observation_mask:[true]}]));
const analysis = {
  redacted_text:'He left because work was tiring.', schema_version:'browser-fixture',
  clauses:[{id:'c0',text:'He left',spans:[[0,7]]},{id:'c1',text:'work was tiring',spans:[[16,31]]}],
  relations:[{id:'r0',cue:'because',cue_span:[8,15],arg1:'c0',arg2:'c1',source:'c1',target:'c0',relation:'cause'}],
  hobbs:{status:'ready',backend:'fixture_dependency_fallback',limitation:'Not full Hobbs traversal.',pronouns:[{pronoun:'He',span:[0,2],antecedent:null,candidates:[]}]},
  centering:{status:'ready',trace:[]}, dmrst:{status:'unavailable',reason:'browser_mock_outage'},
  mathematical_models:{filters,dimensions:['topic_novelty'],profile:'stable'},
  classification:{status:'pending',turn_id:99},
};
window.fetch = async (url, options={}) => {
  const path=String(url); calls.push({path,body:options.body&&JSON.parse(options.body)});
  let data;
  if(path.endsWith('/sessions'))data={sessions:[]};
  else if(path.endsWith('/nlp/preferences'))data={share_history_with_provider:false};
  else if(path.endsWith('/nlp/analyze'))data={status:'preview',nlp_analysis:analysis};
  else if(path.endsWith('/nlp/experiments'))data={document_count:1,boundary:'Browser fixture only',tokenization:{porter:{status:'ready',tokens:[{stem:'walk'}]}},language_models:{status:'unavailable',reason:'requires_prior_session_turns'},retrieval:{}};
  else if(path.includes('/classification'))data={status:'ready',premise_count:1,suggestions:[],labels:[]};
  else return new Response(JSON.stringify({error:{message:'Unexpected fixture request'}}),{status:500});
  return new Response(JSON.stringify(data),{status:200,headers:{'Content-Type':'application/json'}});
};
const token=async()=> 'synthetic-browser-fixture';
createRoot(document.getElementById('root')).render(<BrowserRouter><AnalysisWorkspace getToken={token}/></BrowserRouter>);
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(predicate) { for(let i=0;i<100;i++){if(predicate())return;await sleep(50);}throw Error('UI wait timed out'); }
function check(value,message){if(!value)throw Error(message);}
async function run(){
  await until(()=>document.querySelector('textarea'));
  const textarea=document.querySelector('textarea');
  Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(textarea,'He left because work was tiring.');
  textarea.dispatchEvent(new Event('input',{bubbles:true}));
  const profile=document.querySelector('[aria-label="Mathematical profile"]');
  profile.value='stable';profile.dispatchEvent(new Event('change',{bubbles:true}));
  await sleep(50);
  document.querySelector('form').dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));
  await until(()=>document.querySelector('[aria-label="Algorithm execution inventory"]'));
  check(calls.find(c=>c.path.endsWith('/nlp/analyze'))?.body.mathematical_profile==='stable','Profile did not reach API');
  check(document.body.textContent.includes('unresolved'),'Unresolved pronoun not visible');
  check(!document.body.textContent.includes('[unspoken obligation]'),'Fabricated antecedent leaked');
  check(document.body.textContent.includes('browser_mock_outage'),'DMRST outage hidden');
  for(const key of Object.keys(filters))check(document.body.textContent.includes(key.replaceAll('_',' ')),`Missing filter ${key}`);
  document.querySelector('[aria-label="Select because relation"]').click();
  await until(()=>document.querySelector('[data-testid="arguments"]'));
  check(document.querySelectorAll('.span-highlight').length>0,'Arc highlighting missing');
  [...document.querySelectorAll('summary')].find(s=>s.textContent.includes('Experimental zero-shot suggestions')).click();
  await until(()=>document.body.textContent.includes('Classification: ready'));
  [...document.querySelectorAll('button')].find(b=>b.textContent==='Run algorithm comparisons').click();
  await until(()=>document.querySelector('[aria-label="Algorithm experiments"]').textContent.includes('porter'));
  check(calls.some(c=>c.path.endsWith('/nlp/experiments')),'Experiments did not reach API');
  document.getElementById('result').textContent='BROWSER_SMOKE_PASS: profile API, inventory, unresolved pronoun, missing DMRST, arc selection/highlight, pending-to-ready NLI, experiment API';
}
run().catch(e=>{document.getElementById('result').textContent='BROWSER_SMOKE_FAIL: '+e.message;});
