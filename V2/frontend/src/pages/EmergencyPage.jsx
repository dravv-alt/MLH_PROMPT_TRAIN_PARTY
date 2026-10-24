import { useEffect, useState } from "react";
import { getEmergencyResources } from "../services/api";

const FALLBACK_RESOURCES = [
  {
    label: "988 Suicide and Crisis Lifeline",
    region: "United States",
    contact: "Call or text 988",
    type: "hotline",
  },
  {
    label: "Find A Helpline",
    region: "Global",
    contact: "https://findahelpline.com",
    type: "directory",
  },
  {
    label: "Crisis Text Line",
    region: "US/UK/CA/IE",
    contact: "Text HOME to 741741 (US)",
    type: "text",
  },
];

export default function EmergencyPage() {
  const [resources, setResources] = useState(FALLBACK_RESOURCES);

  useEffect(() => {
    getEmergencyResources().then(setResources).catch(() => setResources(FALLBACK_RESOURCES));
  }, []);

  return (
    <section className="page-panel emergency-panel">
      <h1>Emergency support</h1>
      <p className="muted">If you need immediate support, use one of these resources now.</p>
      <div className="card-grid">
        {resources.map((resource) => (
          <article key={resource.label} className="card">
            <p className="eyebrow">{resource.type}</p>
            <h3>{resource.label}</h3>
            <p>{resource.region}</p>
            <p className="resource-contact">{resource.contact}</p>
          </article>
        ))}
      </div>
      <article className="card">
        <h3>Quick grounding</h3>
        <p>
          Try 5-4-3-2-1: name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, and 1 you can taste.
        </p>
      </article>
    </section>
  );
}
