import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { parseHobbsPronouns } from '../src/services/nlpEngine.js';
import {algorithmCatalog} from '../src/services/algorithmCatalog.js';

test('pronouns without antecedents stay unresolved, never invent an obligation', () => {
  const rows = parseHobbsPronouns('He spoke to her. She thanked him.');
  assert.equal(rows.length, 4);
  for (const row of rows) {
    assert.equal(row.status, 'unresolved');
    assert.equal(row.resolvedAntecedent, 'unresolved');
    assert.deepEqual(row.candidates, []);
  }
});

test('inventory preserves missing, pending and unavailable states', () => {
  const rows = algorithmCatalog({hobbs: {status:'unavailable', reason:'missing_parser'},
    classification:{status:'pending'}, mathematical_models:{confidence_calibration:{status:'unavailable'}}});
  assert.equal(rows.find(r=>r.id==='hobbs').status, 'unavailable');
  assert.equal(rows.find(r=>r.id==='nli').status, 'pending');
  assert.equal(rows.find(r=>r.id==='ssm').status, 'not recorded');
  assert.equal(rows.find(r=>r.id==='calibration').status, 'unavailable');
});

test('inventory exposes all five experimental filter results separately', () => {
  const names = ['linear_kf','extended_kf','unscented_kf','ensemble_kf','particle_filter'];
  const rows = algorithmCatalog({mathematical_models:{filters:Object.fromEntries(names.map(n=>[n,{estimate:[.5]}]))}});
  for(const name of names) assert.equal(rows.find(r=>r.id===name).status, 'recorded');
});

test('legacy entity-only preview cannot claim full syntactic resolution', () => {
  const [row] = parseHobbsPronouns('He left.', [{masked:'[Place 1]', kind:'ORG'}]);
  assert.equal(row.status, 'unresolved');
});

test('production entry preserves the original UI; backend workspace remains available in source', () => {
  const main = readFileSync(new URL('../src/main.jsx', import.meta.url), 'utf8');
  const app = readFileSync(new URL('../src/IntegratedApp.jsx', import.meta.url), 'utf8');
  const analysis = readFileSync(new URL('../src/pages/AnalysisPage.jsx', import.meta.url), 'utf8');
  assert.match(main, /from "\.\/App"/);
  assert.doesNotMatch(main, /integration\.css/);
  assert.match(main, /ClerkProvider/);
  assert.match(app, /how-this-was-read.*AnalysisPage/);
  assert.match(analysis, /await analyzeText\(/);
  assert.doesNotMatch(analysis, /services\/nlpEngine/);
});
