import {algorithmCatalog} from '../services/algorithmCatalog';

export default function AlgorithmInventory({analysis}) {
  return <section aria-label="Algorithm execution inventory"><h3>Algorithms in this turn</h3>
    <p>Actual backend results. An empty result can be valid; not recorded does not mean the algorithm ran. Experimental diagnostics do not automatically influence generation.</p>
    <div className="algorithm-inventory">{algorithmCatalog(analysis).map(row => <details key={row.id}>
      <summary>{row.name} — {row.status}</summary><p>{row.role}</p>
      {row.note && <p role="status">{row.note}</p>}
      {row.value != null ? <pre>{JSON.stringify(row.value, null, 2)}</pre> : <p>No result recorded for this turn.</p>}
    </details>)}</div>
    <p>Research-only items without executable resources, including BabelNet, grammar induction, alternative trained neural architectures and LoRA, are not replaced with mock results.</p>
  </section>;
}
