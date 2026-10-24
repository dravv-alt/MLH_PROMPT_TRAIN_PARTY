import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {buildSync} from 'esbuild';

const compiled = buildSync({
  entryPoints:[fileURLToPath(new URL('./render-algorithms.fixture.jsx', import.meta.url))],
  bundle:true, write:false, platform:'node', format:'cjs', packages:'external',
  jsx:'automatic', define:{'import.meta.env':'{}'}, logLevel:'silent',
}).outputFiles[0].text;
const loaded = {exports:{}};
new Function('require','module','exports',compiled)(createRequire(import.meta.url), loaded, loaded.exports);
const {render} = loaded.exports;

test('historical record lacking new algorithm fields still renders', () => {
  const html = render({redacted_text:'An older turn.', posterior:null, hobbs:{}, centering:{}}, [{analysis:{redacted_text:'Another old turn.'}}]);
  assert.match(html, /An older turn/);
  assert.match(html, /not recorded/);
  assert.match(html, /DMRST unavailable/);
});

test('unresolved pronouns and missing neural resources are not relabelled resolved', () => {
  const html = render({redacted_text:'He left.', hobbs:{status:'ready', algorithm:'dependency_ranked_antecedent_fallback',
    limitation:'Not full Hobbs traversal.', pronouns:[{pronoun:'He',span:[0,2],antecedent:null,candidates:[]}]},
    dmrst:{status:'unavailable',reason:'missing_local_resources'}});
  assert.match(html, /unresolved/);
  assert.match(html, /Not full Hobbs traversal/);
  assert.match(html, /missing_local_resources/);
  assert.doesNotMatch(html, /unspoken obligation/);
});
