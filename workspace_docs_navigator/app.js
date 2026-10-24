const state = { query: '', category: '', collection: '', sort: 'title', selectedPath: '', graph: null, mapMode: 'graph' };
const $ = (selector) => document.querySelector(selector);
const escapeHtml = (text) => String(text).replace(/[&<>'"]/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[character]));

function debounce(callback, delay = 180) {
  let timer;
  return (...args) => { clearTimeout(timer); timer = setTimeout(() => callback(...args), delay); };
}

async function getJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}

function makeFacet(label, count, kind, value) {
  const button = document.createElement('button');
  button.className = 'facet';
  button.dataset.kind = kind;
  button.dataset.value = value;
  button.innerHTML = `<span>${escapeHtml(label)}</span><span class="facet-count">${count}</span>`;
  button.addEventListener('click', () => {
    state.category = kind === 'category' ? value : '';
    state.collection = kind === 'collection' ? value : '';
    state.selectedPath = '';
    markActiveFacet();
    loadDocuments();
  });
  return button;
}

function markActiveFacet() {
  document.querySelectorAll('.facet').forEach((button) => {
    const active = (!state.category && !state.collection && button.dataset.kind === 'all')
      || (button.dataset.kind === 'category' && button.dataset.value === state.category)
      || (button.dataset.kind === 'collection' && button.dataset.value === state.collection);
    button.classList.toggle('active', active);
  });
}

async function loadFacets() {
  const facets = await getJson('/api/facets');
  $('#total-count').textContent = `${facets.total} files`;
  const categories = $('#category-facets');
  const collections = $('#collection-facets');
  categories.replaceChildren(...Object.entries(facets.categories).sort().map(([label, count]) => makeFacet(label, count, 'category', label)));
  collections.replaceChildren(...Object.entries(facets.collections).sort().map(([label, count]) => makeFacet(label, count, 'collection', label)));
  markActiveFacet();
}

function renderChips(categories) { return categories.map((category) => `<span class="chip">${escapeHtml(category)}</span>`).join(''); }

function resultButton(record) {
  const button = document.createElement('button');
  button.className = `result${record.path === state.selectedPath ? ' selected' : ''}`;
  button.innerHTML = `
    <h2>${escapeHtml(record.title)}</h2>
    <div class="path">${escapeHtml(record.path)}</div>
    <p class="preview">${escapeHtml(record.preview || 'No readable preview.')}</p>
    <div class="chips">${renderChips(record.categories)}</div>
    <div class="meta">${record.word_count.toLocaleString()} words · updated ${new Date(record.updated).toLocaleDateString()}</div>`;
  button.addEventListener('click', () => openDocument(record.path));
  return button;
}

async function loadDocuments() {
  const parameters = new URLSearchParams({ q: state.query, category: state.category, collection: state.collection, sort: state.sort });
  const { documents } = await getJson(`/api/documents?${parameters}`);
  const results = $('#results');
  const scope = state.category || state.collection || 'all documents';
  $('#result-summary').textContent = `${documents.length} result${documents.length === 1 ? '' : 's'} in ${scope}${state.query ? ` for “${state.query}”` : ''}.`;
  if (!documents.length) {
    results.innerHTML = '<div class="no-results">No matching Markdown note. Try fewer terms, another category, or refresh the index.</div>';
    return;
  }
  results.replaceChildren(...documents.map(resultButton));
}

function inlineMarkdown(value) {
  let text = escapeHtml(value);
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
  text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  text = text.replace(/\[([^\]]+)\]\(([^\s)]+)(?:\s+&quot;[^&]*&quot;)?\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>');
  return text;
}

function renderMarkdown(source) {
  const lines = source.replace(/\r\n/g, '\n').split('\n');
  const blocks = [];
  let paragraph = [];
  let list = null;
  let code = null;
  const flushParagraph = () => { if (paragraph.length) { blocks.push(`<p>${inlineMarkdown(paragraph.join(' '))}</p>`); paragraph = []; } };
  const flushList = () => { if (list) { blocks.push(`<${list.type}>${list.items.map((item) => `<li>${inlineMarkdown(item)}</li>`).join('')}</${list.type}>`); list = null; } };
  for (const line of lines) {
    if (line.startsWith('```')) {
      flushParagraph(); flushList();
      if (code === null) code = [];
      else { blocks.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`); code = null; }
      continue;
    }
    if (code !== null) { code.push(line); continue; }
    const heading = line.match(/^(#{1,3})\s+(.+?)\s*#*\s*$/);
    const listItem = line.match(/^\s*([-+*]|\d+\.)\s+(.+)$/);
    if (heading) { flushParagraph(); flushList(); const level = heading[1].length; blocks.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`); continue; }
    if (listItem) { flushParagraph(); const type = /\d+\./.test(listItem[1]) ? 'ol' : 'ul'; if (!list || list.type !== type) { flushList(); list = { type, items: [] }; } list.items.push(listItem[2]); continue; }
    if (/^>\s?/.test(line)) { flushParagraph(); flushList(); blocks.push(`<blockquote>${inlineMarkdown(line.replace(/^>\s?/, ''))}</blockquote>`); continue; }
    if (!line.trim()) { flushParagraph(); flushList(); continue; }
    if (/^---+$/.test(line.trim())) { flushParagraph(); flushList(); blocks.push('<hr>'); continue; }
    paragraph.push(line.trim());
  }
  flushParagraph(); flushList();
  if (code !== null) blocks.push(`<pre><code>${escapeHtml(code.join('\n'))}</code></pre>`);
  return blocks.join('\n');
}

async function openDocument(path) {
  const { document: record, content } = await getJson(`/api/document?path=${encodeURIComponent(path)}`);
  state.selectedPath = path;
  const outline = record.headings.length
    ? `<aside class="outline"><h2>Outline</h2><ul>${record.headings.map((heading) => `<li style="margin-left:${(heading.level - 1) * 10}px">${escapeHtml(heading.text)}</li>`).join('')}</ul></aside>`
    : '';
  hideMap();
  $('#reader').classList.remove('empty');
  $('#reader').hidden = false;
  $('#reader').innerHTML = `<header class="reader-header"><p class="eyebrow">${escapeHtml(record.collection)} · ${record.categories.map(escapeHtml).join(' · ')}</p><h1>${escapeHtml(record.title)}</h1><div class="reader-meta">${escapeHtml(record.path)} · ${record.word_count.toLocaleString()} words · modified ${new Date(record.updated).toLocaleString()}</div></header>${outline}<section class="markdown">${renderMarkdown(content)}</section>`;
  await loadDocuments();
}

const graphPalette = ['#a24120', '#54736b', '#826430', '#79516f', '#3f667f', '#756f3d', '#a25058'];
function collectionColor(name) {
  let total = 0;
  for (const character of name) total = (total * 31 + character.charCodeAt(0)) >>> 0;
  return graphPalette[total % graphPalette.length];
}

function layoutGraph(nodes) {
  const grouped = new Map();
  nodes.forEach((node) => { if (!grouped.has(node.collection)) grouped.set(node.collection, []); grouped.get(node.collection).push(node); });
  const groups = [...grouped.entries()].sort(([left], [right]) => left.localeCompare(right));
  const centreX = 490; const centreY = 310;
  return nodes.map((node) => {
    const groupIndex = groups.findIndex(([collection]) => collection === node.collection);
    const group = groups[groupIndex][1]; const localIndex = group.findIndex((item) => item.id === node.id);
    const outerAngle = (Math.PI * 2 * groupIndex / Math.max(groups.length, 1)) - Math.PI / 2;
    const clusterRadius = groups.length === 1 ? 0 : 205;
    const clusterX = centreX + Math.cos(outerAngle) * clusterRadius;
    const clusterY = centreY + Math.sin(outerAngle) * clusterRadius;
    const localAngle = Math.PI * 2 * localIndex / Math.max(group.length, 1);
    const localRadius = group.length === 1 ? 0 : 20 + Math.min(108, 17 * Math.sqrt(group.length) + 9 * Math.floor(localIndex / 7));
    return { ...node, x: clusterX + Math.cos(localAngle) * localRadius, y: clusterY + Math.sin(localAngle) * localRadius };
  });
}

function svgElement(name, attributes = {}) {
  const element = document.createElementNS('http://www.w3.org/2000/svg', name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
}

function renderGraph(graph) {
  const svg = $('#graph');
  svg.replaceChildren();
  const laidOut = layoutGraph(graph.nodes);
  const byId = new Map(laidOut.map((node) => [node.id, node]));
  graph.edges.forEach((edge) => {
    const source = byId.get(edge.source); const target = byId.get(edge.target);
    if (source && target) svg.append(svgElement('line', { x1: source.x, y1: source.y, x2: target.x, y2: target.y, class: 'graph-edge' }));
  });
  laidOut.forEach((node) => {
    const group = svgElement('g', { tabindex: '0', role: 'button', 'aria-label': `Open ${node.title}` });
    group.append(svgElement('circle', { cx: node.x, cy: node.y, r: Math.min(12, 5 + node.incoming + node.outgoing), fill: collectionColor(node.collection), class: 'graph-node' }));
    const label = svgElement('text', { x: node.x + 9, y: node.y - 8, class: 'graph-label' });
    label.textContent = node.title.length > 28 ? `${node.title.slice(0, 27)}…` : node.title;
    group.append(label);
    group.addEventListener('click', () => openDocument(node.id));
    group.addEventListener('keydown', (event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); openDocument(node.id); } });
    svg.append(group);
  });
  $('#map-summary').textContent = `${graph.nodes.length} Markdown documents · ${graph.edges.length} explicit document links. Node color = top-level collection.`;
}

function folderTree(nodes) {
  const root = {};
  nodes.forEach((node) => {
    const parts = node.id.split('/'); let cursor = root;
    parts.forEach((part, index) => {
      if (index === parts.length - 1) cursor[part] = { __document: node };
      else cursor = cursor[part] ||= {};
    });
  });
  return root;
}

function renderTree(graph) {
  const tree = $('#tree-view'); tree.replaceChildren();
  const buildBranch = (branch) => {
    const fragment = document.createDocumentFragment();
    Object.entries(branch).sort(([left], [right]) => left.localeCompare(right)).forEach(([name, value]) => {
      if (value.__document) {
        const button = document.createElement('button'); button.className = 'tree-file'; button.textContent = value.__document.title;
        button.title = value.__document.id; button.addEventListener('click', () => openDocument(value.__document.id)); fragment.append(button);
      } else {
        const details = document.createElement('details'); details.open = name === 'docs' || name === 'Memory';
        const summary = document.createElement('summary'); summary.textContent = name; details.append(summary, buildBranch(value)); fragment.append(details);
      }
    });
    return fragment;
  };
  tree.append(buildBranch(folderTree(graph.nodes)));
}

function setMapMode(mode) {
  state.mapMode = mode;
  $('#graph-view').hidden = mode !== 'graph'; $('#tree-view').hidden = mode !== 'tree';
  document.querySelectorAll('.map-tab').forEach((tab) => tab.classList.toggle('active', tab.dataset.mapMode === mode));
}

function hideMap() { $('#map-panel').hidden = true; }

async function showMap() {
  if (!state.graph) state.graph = await getJson('/api/graph');
  renderGraph(state.graph); renderTree(state.graph); setMapMode(state.mapMode);
  $('#reader').hidden = true; $('#map-panel').hidden = false;
}

async function refreshIndex() {
  const button = $('#refresh');
  button.disabled = true; button.textContent = 'Indexing…';
  try { await getJson('/api/reindex', { method: 'POST' }); state.graph = null; await loadFacets(); await loadDocuments(); }
  finally { button.disabled = false; button.textContent = 'Refresh index'; }
}

function setAllDocuments() { state.category = ''; state.collection = ''; state.selectedPath = ''; markActiveFacet(); loadDocuments(); }

async function start() {
  $('#search').addEventListener('input', debounce((event) => { state.query = event.target.value.trim(); loadDocuments(); }));
  $('#sort').addEventListener('change', (event) => { state.sort = event.target.value; loadDocuments(); });
  $('#refresh').addEventListener('click', refreshIndex);
  $('#current-context').addEventListener('click', () => openDocument('Memory/Agent-Mem/Active Context.md'));
  document.querySelector('[data-kind="all"]').addEventListener('click', setAllDocuments);
  document.addEventListener('keydown', (event) => { if (event.key === '/' && document.activeElement !== $('#search')) { event.preventDefault(); $('#search').focus(); } });
  try {
    const meta = await getJson('/api/meta');
    $('#version').textContent = `v${meta.version} · :${meta.port}`;
    await loadFacets(); await loadDocuments();
    const openPath = new URLSearchParams(window.location.search).get('open');
    if (openPath) await openDocument(openPath);
  }
  catch (error) { $('#result-summary').textContent = `Could not load the local index: ${error.message}`; }
}

start();
