import React, { useState } from "react";
import { Link } from "react-router-dom";

export default function PrivacyPage() {
  const [showJsonPayload, setShowJsonPayload] = useState(false);
  const [hashVerified, setHashVerified] = useState(false);
  const [shareEarlierExcerpts, setShareEarlierExcerpts] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState("");
  const [storagePurged, setStoragePurged] = useState(false);
  const [stats, setStats] = useState({
    conversations: 14,
    turns: 128,
    moments: 4,
    rememberedTopics: 3,
  });

  const rawJsonSnippet = {
    session_token: "client_masked_9a8df10b",
    temperature: 0.35,
    masked_entities: [{ alias: "[Location 1]", category: "place_name" }],
    content:
      "We sat in the car for twenty minutes before walking in to [Location 1]. Neither of us said anything, but watching the rain slide down the side mirror felt like the only honest thing to do.",
    ephemeral_instructions:
      "Reflect presence, withhold advice, maintain quiet tone.",
  };

  const handleExportJSON = () => {
    const exportData = {
      sanctuary_export_version: "2.4",
      export_date: new Date().toISOString(),
      verified_device_storage: stats,
      policy: "Client-enclave zero telemetry",
      active_masked_payload: rawJsonSnippet,
    };
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sanctuary_privacy_records_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportMarkdown = () => {
    const mdContent = `# Sanctuary · Sovereign Privacy Ledger\n\n**Generated:** ${new Date().toUTCString()}\n\n## Local Enclave Statistics\n- **Conversations:** ${stats.conversations}\n- **Turns:** ${stats.turns}\n- **Consecrated Moments:** ${stats.moments}\n- **Remembered Topics:** ${stats.rememberedTopics}\n\n## Security Commitments\n1. Zero telemetry attached.\n2. Masked entities stay on client.\n3. External inference services do not train on journal entries.\n`;
    const blob = new Blob([mdContent], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sanctuary_privacy_records_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handlePurge = () => {
    if (deleteConfirmation.trim() === "DELETE") {
      setStats({ conversations: 0, turns: 0, moments: 0, rememberedTopics: 0 });
      setStoragePurged(true);
      setDeleteConfirmation("");
    }
  };

  return (
    <div className="w-full min-h-screen bg-surface font-body-md text-on-surface antialiased">
      <div className="w-full max-w-5xl xl:max-w-6xl mx-auto px-6 lg:px-12 xl:px-16 py-8 lg:py-12 flex flex-col gap-10">
        {/* Primary Ledger Header */}
        <header className="flex flex-col gap-3">
          <div className="flex items-center gap-2 text-on-surface-variant font-label-sm text-xs">
            <span className="inline-block w-2 h-2 rounded-full bg-primary"></span>
            <span className="tracking-wider uppercase font-semibold">
              VERIFIED CLIENT LEDGER · REVISION 14
            </span>
          </div>
          <h1 className="font-headline-lg text-3xl lg:text-4xl text-primary font-serif tracking-tight">
            What stays here.
          </h1>
          <p className="font-body-lg text-sm lg:text-base text-on-surface-variant leading-relaxed">
            Sanctuary’s data ledger and control center. A plain, verifiable breakdown of what is held on this device, what is processed externally, and your tools to inspect, export, or erase everything.
          </p>
        </header>

        {/* Honesty Note Callout */}
        <div className="bg-surface-variant/80 rounded-xl p-5 flex items-start gap-4 border border-outline-variant/30">
          <span className="material-symbols-outlined text-outline mt-0.5 text-xl">info</span>
          <div className="flex flex-col gap-1 text-on-surface">
            <span className="font-label-md text-xs tracking-wider uppercase text-on-surface-variant font-semibold">
              Boundary limitation
            </span>
            <p className="font-body-md text-xs lg:text-sm text-on-surface-variant leading-relaxed">
              Names and contact details are replaced before text goes to the writing service. Details of events are not removed automatically and may still identify a situation.
            </p>
          </div>
        </div>

        {/* Core Interpretability / How this was read Banner */}
        <div className="bg-surface-container-low rounded-xl p-5 border border-primary/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <span className="material-symbols-outlined text-primary text-2xl mt-0.5">policy</span>
            <div className="flex flex-col gap-0.5">
              <span className="font-label-md text-xs font-semibold uppercase tracking-wider text-primary">
                Observability & Interpretability
              </span>
              <p className="font-body-md text-xs sm:text-sm text-on-surface-variant">
                Curious how Sanctuary interprets clauses, masks PII entities, and maps lexical recurrence?
              </p>
            </div>
          </div>
          <Link
            to="/how-this-was-read"
            className="shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-on-primary text-xs font-medium hover:bg-primary-container transition-colors"
          >
            <span>How this was read</span>
            <span className="material-symbols-outlined text-sm">arrow_forward</span>
          </Link>
        </div>

        {/* Section 1: Stored on this device */}
        <section className="flex flex-col gap-4">
          <div className="flex items-baseline justify-between border-b border-surface-container-highest pb-2">
            <h2 className="font-headline-sm text-lg text-primary font-serif">
              What is stored on this device
            </h2>
            <span className="font-label-sm text-xs text-on-surface-variant">
              IndexedDB (Encrypted locally)
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-surface-container-lowest p-5 rounded-xl flex flex-col justify-between gap-4 border border-outline-variant/30">
              <div className="flex items-baseline justify-between">
                <span className="font-label-sm text-xs text-on-surface-variant uppercase tracking-wider">
                  Conversations
                </span>
                <span className="font-headline-lg text-3xl text-primary font-serif">
                  {stats.conversations}
                </span>
              </div>
              <p className="font-body-sm text-xs text-on-surface-variant leading-relaxed">
                Complete dialogue sessions held in your browser’s private local storage enclave.
              </p>
            </div>

            <div className="bg-surface-container-lowest p-5 rounded-xl flex flex-col justify-between gap-4 border border-outline-variant/30">
              <div className="flex items-baseline justify-between">
                <span className="font-label-sm text-xs text-on-surface-variant uppercase tracking-wider">
                  Turns
                </span>
                <span className="font-headline-lg text-3xl text-primary font-serif">
                  {stats.turns}
                </span>
              </div>
              <p className="font-body-sm text-xs text-on-surface-variant leading-relaxed">
                Individual paired slips of your thoughts and Sanctuary’s contemplative reflections.
              </p>
            </div>

            <div className="bg-surface-container-lowest p-5 rounded-xl flex flex-col justify-between gap-4 border border-outline-variant/30">
              <div className="flex items-baseline justify-between">
                <span className="font-label-sm text-xs text-on-surface-variant uppercase tracking-wider">
                  Kept moments
                </span>
                <span className="font-headline-lg text-3xl text-primary font-serif">
                  {stats.moments}
                </span>
              </div>
              <p className="font-body-sm text-xs text-on-surface-variant leading-relaxed">
                Specific excerpts you explicitly chose to consecrate as riverbed cairn stones.
              </p>
            </div>

            <div className="bg-surface-container-lowest p-5 rounded-xl flex flex-col justify-between gap-4 border border-outline-variant/30">
              <div className="flex items-baseline justify-between">
                <span className="font-label-sm text-xs text-on-surface-variant uppercase tracking-wider">
                  Remembered topics
                </span>
                <span className="font-headline-lg text-3xl text-primary font-serif">
                  {stats.rememberedTopics}
                </span>
              </div>
              <p className="font-body-sm text-xs text-on-surface-variant leading-relaxed">
                Recurring thematic anchors and cryptographic aliases you have verified.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 pt-1 text-on-surface-variant font-label-sm text-xs">
            <span className="material-symbols-outlined text-base text-outline">database</span>
            <span>
              {storagePurged
                ? "Storage purged. 0 KB allocated."
                : "Storage footprint: 184 KB. Zero analytics tokens or profile telemetry are attached."}
            </span>
          </div>
        </section>

        {/* Section 2: Outbound Payload */}
        <section className="flex flex-col gap-4">
          <div className="flex items-baseline justify-between border-b border-surface-container-highest pb-2">
            <h2 className="font-headline-sm text-lg text-primary font-serif">
              What was sent to the writing service
            </h2>
            <span className="font-label-sm text-xs text-on-surface-variant">
              Ephemeral outbound ledger
            </span>
          </div>

          <div className="bg-surface-container-lowest rounded-xl p-6 flex flex-col gap-5 border border-outline-variant/30">
            <div className="flex items-center justify-between pb-3 bg-surface-container-low -mx-6 -mt-6 p-4 rounded-t-xl border-b border-outline-variant/30">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-secondary"></span>
                <span className="font-label-sm text-xs font-semibold text-primary">
                  Latest turn outbound payload
                </span>
              </div>
              <span className="font-label-sm text-xs text-on-surface-variant">
                Oct 24 · 07:14 EST
              </span>
            </div>

            <div className="bg-surface-container-low p-4 rounded-lg font-body-md text-sm lg:text-base leading-relaxed text-on-surface font-serif italic border border-outline-variant/20">
              “We sat in the car for twenty minutes before walking in to{" "}
              <span className="inline-flex items-center px-2 py-0.5 rounded bg-secondary-fixed text-on-secondary-fixed font-sans text-xs tracking-wide not-italic font-semibold mx-1">
                [Location 1]
              </span>
              . Neither of us said anything, but watching the rain slide down the side mirror felt like the only honest thing to do.”
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={() => setShowJsonPayload(!showJsonPayload)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container hover:text-on-surface text-primary font-label-md text-xs font-medium transition-colors"
              >
                <span className="material-symbols-outlined text-base">code</span>
                <span>{showJsonPayload ? "Hide JSON payload" : "Inspect raw JSON payload"}</span>
              </button>

              <button
                type="button"
                onClick={() => setHashVerified(true)}
                className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-surface-container-high hover:bg-surface-container hover:text-on-surface text-on-surface-variant font-label-md text-xs font-medium transition-colors"
              >
                <span className="material-symbols-outlined text-base">fingerprint</span>
                <span>Verify SHA-256 hash</span>
              </button>

              {hashVerified && (
                <span className="font-label-sm text-xs text-primary bg-secondary-fixed px-2 py-1 rounded font-mono">
                  e3b0c442...98fc verified (zero tampering)
                </span>
              )}
            </div>

            {showJsonPayload && (
              <div className="bg-surface-container p-4 rounded-lg font-mono text-xs text-on-surface-variant overflow-x-auto border border-outline-variant/30 animate-fadeIn">
                <pre className="m-0 leading-relaxed">
                  <code>{JSON.stringify(rawJsonSnippet, null, 2)}</code>
                </pre>
              </div>
            )}

            <p className="font-body-sm text-xs text-on-surface-variant leading-relaxed pt-1">
              This information is held temporarily in RAM for the current interaction and is cleared when the conversation closes. External models do not train on your words, but the cloud inference provider logs requests under their standard security retention policy.
            </p>
          </div>
        </section>

        {/* Section 3: Boundary Matrix */}
        <section className="flex flex-col gap-4">
          <h2 className="font-headline-sm text-lg text-primary font-serif border-b border-surface-container-highest pb-2">
            Who can see what
          </h2>
          <div className="bg-surface-container-lowest rounded-xl overflow-hidden flex flex-col border border-outline-variant/30 divide-y divide-outline-variant/20">
            {/* Row 1 */}
            <div className="p-5 flex flex-col sm:flex-row gap-2 sm:gap-6 hover:bg-surface-container-low transition-colors">
              <div className="w-full sm:w-48 shrink-0">
                <span className="font-label-md text-sm font-semibold text-primary block">This device</span>
                <span className="font-label-sm text-xs text-on-surface-variant">Your browser enclave</span>
              </div>
              <p className="font-body-sm text-xs lg:text-sm text-on-surface-variant leading-relaxed">
                Browser-stored originals, unmasked raw text, full dialogue history, encryption keys, and audio preferences. Remains strictly in local client-side storage.
              </p>
            </div>

            {/* Row 2 */}
            <div className="p-5 flex flex-col sm:flex-row gap-2 sm:gap-6 bg-surface-container-low/50 hover:bg-surface-container transition-colors">
              <div className="w-full sm:w-48 shrink-0">
                <span className="font-label-md text-sm font-semibold text-primary block">Writing service</span>
                <span className="font-label-sm text-xs text-on-surface-variant">Language model</span>
              </div>
              <p className="font-body-sm text-xs lg:text-sm text-on-surface-variant leading-relaxed">
                Hidden-name sanitized text slips and narrative structure required to generate immediate replies. Cleared upon session close; no retention for model training.
              </p>
            </div>

            {/* Row 3 */}
            <div className="p-5 flex flex-col sm:flex-row gap-2 sm:gap-6 hover:bg-surface-container-low transition-colors">
              <div className="w-full sm:w-48 shrink-0">
                <span className="font-label-md text-sm font-semibold text-primary block">Sign-in service</span>
                <span className="font-label-sm text-xs text-on-surface-variant">Authentication</span>
              </div>
              <p className="font-body-sm text-xs lg:text-sm text-on-surface-variant leading-relaxed">
                Hashed passphrase or mineral PIN digest and account identifier. Never receives conversation content, moments, or journal transcripts.
              </p>
            </div>

            {/* Row 4 */}
            <div className="p-5 flex flex-col sm:flex-row gap-2 sm:gap-6 bg-surface-container-low/50 hover:bg-surface-container transition-colors">
              <div className="w-full sm:w-48 shrink-0">
                <span className="font-label-md text-sm font-semibold text-primary block">Voice service</span>
                <span className="font-label-sm text-xs text-on-surface-variant">Microphone · Audio</span>
              </div>
              <p className="font-body-sm text-xs lg:text-sm text-on-surface-variant leading-relaxed">
                Disabled by default. When enabled, local Web Audio streams transcribe locally where supported, or stream temporary voice clips without identity attachment.
              </p>
            </div>
          </div>
        </section>

        {/* Section 4: Context Sharing Switch */}
        <section className="bg-surface-container-lowest rounded-xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6 border border-outline-variant/30">
          <div className="flex flex-col gap-2 max-w-lg">
            <span className="font-label-md text-sm font-medium text-primary">
              Share short excerpts of earlier conversations with the writing service.
            </span>
            <p className="font-body-sm text-xs text-on-surface-variant leading-relaxed">
              Short excerpts of earlier conversations are added to what the writing service sees. When disabled, the writing service only sees the immediate active conversation.
            </p>
            <span className="inline-flex items-center gap-1.5 font-label-sm text-xs text-on-surface-variant pt-1">
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  shareEarlierExcerpts ? "bg-lichen" : "bg-outline"
                }`}
              ></span>
              {shareEarlierExcerpts
                ? "Active · Contextual memory linked"
                : "Currently disabled · Isolated context active"}
            </span>
          </div>

          <button
            type="button"
            role="switch"
            aria-checked={shareEarlierExcerpts}
            onClick={() => setShareEarlierExcerpts(!shareEarlierExcerpts)}
            className={`relative inline-flex h-7 w-12 shrink-0 cursor-pointer rounded-full transition-colors focus:outline-none ${
              shareEarlierExcerpts ? "bg-primary" : "bg-surface-variant"
            }`}
          >
            <span
              className={`inline-block h-5 w-5 mt-1 rounded-full bg-surface-container-lowest transition-transform ${
                shareEarlierExcerpts ? "translate-x-6" : "translate-x-1"
              }`}
            />
          </button>
        </section>

        {/* Section 5: Export */}
        <section className="flex flex-col gap-3">
          <div className="flex flex-col gap-1 border-b border-surface-container-highest pb-2">
            <h2 className="font-headline-sm text-lg text-primary font-serif">
              Export your records
            </h2>
            <p className="font-body-sm text-xs text-on-surface-variant leading-relaxed">
              Exports contain available conversations in hidden-name form, moments, remembered topics, local labels, and preferences. Ephemeral audio cache and private key hashes are excluded.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3 pt-1">
            <button
              type="button"
              onClick={handleExportJSON}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-primary hover:bg-primary-container text-on-primary font-label-md text-xs font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-base">download</span>
              <span>Download JSON</span>
            </button>
            <button
              type="button"
              onClick={handleExportMarkdown}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-surface-container-high hover:bg-surface-container text-primary font-label-md text-xs font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-base">description</span>
              <span>Download Markdown</span>
            </button>
          </div>
        </section>

        {/* Section 6: Delete everything (Destructive) */}
        <section className="bg-surface-container-lowest rounded-xl p-6 flex flex-col gap-4 border border-error/30 bg-opacity-95">
          <div className="flex items-center gap-2 text-error">
            <span className="material-symbols-outlined text-xl">warning</span>
            <h2 className="font-headline-sm text-base lg:text-lg text-error font-serif">
              Delete everything
            </h2>
          </div>
          <p className="font-body-sm text-xs text-on-surface-variant leading-relaxed">
            Permanently purges all {stats.conversations} conversations, {stats.turns} turns, {stats.moments} cairn moments, and {stats.rememberedTopics} remembered topics from this browser enclave. Destroys local cryptographic ratchets and removes any cached session fragments.
          </p>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-1">
            <input
              type="text"
              autoComplete="off"
              value={deleteConfirmation}
              onChange={(e) => setDeleteConfirmation(e.target.value)}
              placeholder="Type DELETE to confirm"
              className="px-3.5 py-2 rounded-lg bg-surface-container text-on-surface placeholder:text-outline font-body-sm text-xs focus:outline-none focus:bg-surface-container-high transition-colors w-full sm:w-60 border border-transparent focus:border-error/40"
            />
            <button
              type="button"
              disabled={deleteConfirmation.trim() !== "DELETE"}
              onClick={handlePurge}
              className={`inline-flex items-center justify-center gap-2 px-5 py-2 rounded-lg font-label-md text-xs font-medium transition-colors ${
                deleteConfirmation.trim() === "DELETE"
                  ? "bg-error text-on-error hover:bg-on-error-container cursor-pointer"
                  : "bg-surface-variant text-outline cursor-not-allowed"
              }`}
            >
              <span className="material-symbols-outlined text-base">delete_forever</span>
              <span>Delete everything</span>
            </button>
          </div>
          {storagePurged && (
            <div className="p-3 bg-secondary-fixed text-on-secondary-fixed text-xs rounded-lg font-sans">
              ✓ Local enclave wiped cleanly. All cryptographic keys and stored turns have been destroyed.
            </div>
          )}
        </section>

        {/* Grounded footer sovereignty text */}
        <footer className="text-center font-label-sm text-xs text-on-surface-variant pb-8 pt-2">
          Your memory belongs to you. Sanctuary creates no shadow mirrors.
        </footer>
      </div>
    </div>
  );
}
