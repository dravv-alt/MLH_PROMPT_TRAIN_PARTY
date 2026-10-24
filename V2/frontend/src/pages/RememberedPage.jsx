import React, { useState } from "react";
import { Link } from "react-router-dom";

export default function RememberedPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedTopicId, setExpandedTopicId] = useState("topic-1");
  const [deletionScopeTopicId, setDeletionScopeTopicId] = useState(null);
  const [editingPersonId, setEditingPersonId] = useState(null);
  const [personAliases, setPersonAliases] = useState({
    person1: "my project teammate at Studio",
    place1: "The North Branch studio",
    org1: "Current Employer",
  });
  const [unresolvedItems, setUnresolvedItems] = useState([
    {
      id: "unres-1",
      title: "Candidate topic: “The Tuesday morning train delay”",
      note: "Mentioned casually in Talk session on Oct 22 and Oct 25.",
    },
    {
      id: "unres-2",
      title: "Candidate entity: “Cedar Grove trail marker”",
      note: "Detected in recent Calm reflection session.",
    },
  ]);
  const [revealedPlaceholders, setRevealedPlaceholders] = useState(false);
  const [exportFeedback, setExportFeedback] = useState(false);

  const initialTopics = [
    {
      id: "topic-1",
      title: "“Watching the rain on the side mirror”",
      tag: "2 Linked Occurrences",
      lastActive: "Last recalled Oct 24",
      provenance:
        "Appeared in 2 conversations · First recorded Oct 12, 2024 · Last recorded Oct 24, 2024",
      extracts: [
        {
          meta: "Oct 24 — Twilight reflection (Turn 04)",
          text: "“We sat in the car for twenty minutes before walking in. Neither of us said anything, but watching the rain slide down the side mirror felt like the only honest thing to do.”",
        },
        {
          meta: "Oct 18 — Evening passage (Turn 02)",
          text: "“The rain started hitting the passenger window while I was waiting outside the station.”",
        },
      ],
      hash: "sha256:7e9a...32b1",
    },
    {
      id: "topic-2",
      title: "“Walking around the block to delay entering”",
      tag: "Avoidance Pattern · 4 occurrences",
      lastActive: "Last active Sep 30",
      provenance: "Associated with 3 dialogue transcripts · Avoidance Pattern",
      extracts: [
        {
          meta: "Sep 30 — Morning entrance",
          text: "“I took the long path twice around the perimeter just to watch the dry fallen leaves rather than stepping inside the glass doors.”",
        },
      ],
      hash: "sha256:4a8b...9f20",
    },
    {
      id: "topic-3",
      title: "“Arranging files before an unpredictable phone call”",
      tag: "Core Tension · 1 occurrence",
      lastActive: "Last active Sep 14",
      provenance: "Linked to 11 reflection sessions · Recurring on Mondays",
      extracts: [
        {
          meta: "Sep 14 — Afternoon Casement",
          text: "“Every folder on the desktop was aligned to an imaginary grid before I dialed. It didn't change what they said, but my hands were steady.”",
        },
      ],
      hash: "sha256:11ec...6d88",
    },
    {
      id: "topic-4",
      title: "“Night air through the study casement”",
      tag: "Anchor · 2 entries",
      lastActive: "Added 3 weeks ago",
      provenance: "Linked to 2 entries · Evening contemplation",
      extracts: [
        {
          meta: "Sep 08 — Casement Breeze",
          text: "“Cold mineral air flowing across the drafting desk kept the room still when thoughts felt heavy.”",
        },
      ],
      hash: "sha256:99f2...00ab",
    },
  ];

  const [topics, setTopics] = useState(initialTopics);

  const filteredTopics = topics.filter((t) =>
    t.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleExportJSON = () => {
    const data = {
      enclave: "Sanctuary Sovereign Client Ledger v2.4",
      timestamp: new Date().toISOString(),
      topics,
      anonymized_personae: personAliases,
      unresolved: unresolvedItems,
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sanctuary_sovereign_memory_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setExportFeedback(true);
    setTimeout(() => setExportFeedback(false), 3000);
  };

  const handleDismissUnresolved = (id) => {
    setUnresolvedItems((prev) => prev.filter((item) => item.id !== id));
  };

  const handleAcknowledgeUnresolved = (item) => {
    setTopics((prev) => [
      ...prev,
      {
        id: `topic-${Date.now()}`,
        title: item.title.replace("Candidate topic: ", "").replace("Candidate entity: ", ""),
        tag: "Newly Acknowledged · 1 occurrence",
        lastActive: "Just added",
        provenance: item.note,
        extracts: [{ meta: "Today", text: item.note }],
        hash: "sha256:auto...new",
      },
    ]);
    handleDismissUnresolved(item.id);
  };

  const handleRemoveTopic = (id) => {
    setTopics((prev) => prev.filter((t) => t.id !== id));
    if (expandedTopicId === id) setExpandedTopicId(null);
    if (deletionScopeTopicId === id) setDeletionScopeTopicId(null);
  };

  return (
    <div className="w-full min-h-screen bg-background text-on-surface">
      <div className="w-full max-w-6xl xl:max-w-7xl mx-auto px-6 lg:px-12 xl:px-16 py-8 lg:py-12 flex flex-col gap-10">
        {/* Top Ledger Header & Query Controls */}
        <header className="flex flex-col gap-5">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-2xl bg-surface-container-high border border-outline-variant/40 flex items-center justify-center text-primary shadow-2xs">
                <span className="material-symbols-outlined text-[24px] text-secondary">history_edu</span>
              </div>
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="w-2 h-2 rounded-full bg-secondary"></span>
                  <span className="font-label-sm text-xs uppercase tracking-wider text-secondary">
                    Local Ledger · Sovereign Memory
                  </span>
                </div>
                <h1 className="font-headline-lg text-3xl lg:text-4xl text-primary font-serif tracking-tight">
                  Remembered
                </h1>
                <p className="font-body-md text-sm lg:text-base text-on-surface-variant mt-1 max-w-xl">
                  Topics, recurring tensions, and cryptographic anchors kept from earlier conversations.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-container text-secondary font-label-sm text-xs">
                <span className="material-symbols-outlined text-base">database</span>
                <span>{topics.length} items in local enclave</span>
              </div>
              <button
                type="button"
                onClick={handleExportJSON}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface font-label-sm text-xs transition-colors"
              >
                <span className="material-symbols-outlined text-base">file_download</span>
                <span>{exportFeedback ? "Exported!" : "Export raw JSON"}</span>
              </button>
            </div>
          </div>

          {/* Mineral Search Box */}
          <div className="relative w-full">
            <span className="material-symbols-outlined absolute left-4 top-1/2 -translate-y-1/2 text-on-surface-variant text-xl">
              search
            </span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Find a remembered topic, occurrence, or local alias..."
              className="w-full bg-surface-container-low focus:bg-surface-container-lowest text-on-surface placeholder:text-outline text-sm pl-12 pr-28 py-3.5 rounded-xl transition-all border border-transparent focus:border-outline-variant outline-none"
            />
            <div className="absolute right-3.5 top-1/2 -translate-y-1/2 flex items-center gap-1">
              <kbd className="px-2 py-0.5 rounded bg-surface-container text-outline font-label-sm text-xs tracking-widest">
                ⌘K
              </kbd>
            </div>
          </div>
        </header>

        {/* SECTION 1: Active Topics Ledger */}
        <section className="flex flex-col gap-4">
          <div className="flex items-baseline justify-between border-b border-surface-container-highest pb-2">
            <h2 className="font-headline-sm text-lg text-primary font-serif">
              Remembered topics{" "}
              <span className="font-body-sm text-xs text-on-surface-variant font-normal font-sans">
                ({filteredTopics.length} entries matching)
              </span>
            </h2>
            <span className="font-label-sm text-xs text-secondary font-sans">
              Zero Model Training Enclave
            </span>
          </div>

          <div className="flex flex-col gap-3">
            {filteredTopics.map((topic) => {
              const isExpanded = expandedTopicId === topic.id;
              const isUnderDeletionScope = deletionScopeTopicId === topic.id;

              return (
                <article
                  key={topic.id}
                  className="flex flex-col bg-surface-container-low rounded-xl overflow-hidden border border-outline-variant/40 transition-all"
                >
                  {/* Topic Row Bar */}
                  <div
                    onClick={() => {
                      if (!isUnderDeletionScope) {
                        setExpandedTopicId(isExpanded ? null : topic.id);
                      }
                    }}
                    className={`px-5 py-4 flex items-center justify-between gap-4 cursor-pointer select-none transition-colors ${
                      isExpanded
                        ? "bg-secondary-container/40"
                        : "hover:bg-surface-container"
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="material-symbols-outlined text-primary text-xl">
                        {isExpanded ? "unfold_less" : "unfold_more"}
                      </span>
                      <h3 className="font-headline-sm text-base lg:text-lg text-primary font-serif truncate">
                        {topic.title}
                      </h3>
                      <span className="px-2.5 py-0.5 rounded-full bg-secondary-fixed text-on-secondary-fixed font-label-sm text-[11px] shrink-0 font-sans">
                        {topic.tag}
                      </span>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <span className="font-label-sm text-xs text-on-surface-variant hidden md:inline font-sans">
                        {topic.lastActive}
                      </span>
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedTopicId(isExpanded ? null : topic.id);
                        }}
                        className="w-8 h-8 flex items-center justify-center rounded-lg bg-surface-container-low text-primary hover:bg-surface-container transition-colors"
                        title={isExpanded ? "Collapse inspection" : "Inspect provenance"}
                      >
                        <span className="material-symbols-outlined text-lg">
                          {isExpanded ? "expand_less" : "expand_more"}
                        </span>
                      </button>
                    </div>
                  </div>

                  {/* Deletion Scope Confirmation Mode */}
                  {isUnderDeletionScope && (
                    <div className="p-5 bg-surface-container-highest flex flex-col gap-4 m-3 rounded-lg border border-error/30 animate-fadeIn">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 rounded-full bg-error-container text-on-error-container flex items-center justify-center shrink-0 mt-0.5">
                          <span className="material-symbols-outlined text-lg">warning</span>
                        </div>
                        <div className="flex flex-col gap-1">
                          <h4 className="font-headline-sm text-base text-primary font-serif">
                            Remove {topic.title}?
                          </h4>
                          <p className="font-body-md text-xs lg:text-sm text-on-surface leading-relaxed">
                            This will remove this recurring topic tag from your local index and unlink it from conversation entries. The original conversation text itself will not be altered. This action cannot be undone.
                          </p>
                        </div>
                      </div>

                      <div className="bg-surface-container-low p-3 rounded-lg flex items-center gap-3">
                        <input
                          id={`chk-${topic.id}`}
                          type="checkbox"
                          defaultChecked
                          className="w-4 h-4 rounded text-primary-container accent-primary-container cursor-pointer"
                        />
                        <label
                          htmlFor={`chk-${topic.id}`}
                          className="font-body-sm text-xs text-on-surface cursor-pointer select-none"
                        >
                          Also remove from local autocomplete suggestions and predictive reflections
                        </label>
                      </div>

                      <div className="flex items-center justify-end gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => setDeletionScopeTopicId(null)}
                          className="px-4 py-1.5 text-xs font-medium text-on-surface bg-surface-container-low hover:bg-surface-container rounded-lg transition-colors"
                        >
                          Cancel
                        </button>
                        <button
                          type="button"
                          onClick={() => handleRemoveTopic(topic.id)}
                          className="px-4 py-1.5 text-xs font-medium text-on-error bg-error hover:bg-on-error-container rounded-lg transition-colors flex items-center gap-1.5"
                        >
                          <span className="material-symbols-outlined text-sm">delete_forever</span>
                          <span>Remove from Remembered</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Deep Provenance Inspection Drawer */}
                  {isExpanded && !isUnderDeletionScope && (
                    <div className="p-5 lg:p-6 flex flex-col gap-5 border-t border-outline-variant/30 bg-surface-container-low/50">
                      {/* Provenance Metadata Shelf */}
                      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 p-4 bg-surface-container rounded-lg">
                        <div className="flex flex-col gap-1">
                          <span className="font-label-sm text-[11px] uppercase tracking-wider text-secondary font-semibold">
                            Topic Provenance & Dialogue Linkages
                          </span>
                          <p className="font-body-sm text-xs text-on-surface-variant font-sans">
                            {topic.provenance}
                          </p>
                        </div>

                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            type="button"
                            onClick={() => {
                              const newTitle = prompt("Update topic title:", topic.title);
                              if (newTitle) {
                                setTopics((prev) =>
                                  prev.map((t) =>
                                    t.id === topic.id ? { ...t, title: `“${newTitle.replace(/“|”/g, '')}”` } : t
                                  )
                                );
                              }
                            }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container-lowest hover:bg-surface-container-high text-primary font-label-sm text-xs transition-colors"
                          >
                            <span className="material-symbols-outlined text-sm">edit</span>
                            <span>Edit label</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => setDeletionScopeTopicId(topic.id)}
                            className="inline-flex items-center gap-1 px-3 py-1.5 text-error hover:bg-error-container/30 rounded-lg font-label-sm text-xs transition-colors"
                          >
                            <span className="material-symbols-outlined text-sm">delete_sweep</span>
                            <span>Forget topic</span>
                          </button>
                        </div>
                      </div>

                      {/* Linked Extracts Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {topic.extracts.map((extract, idx) => (
                          <div
                            key={idx}
                            className="flex flex-col justify-between p-4 rounded-xl bg-surface-container-lowest border border-outline-variant/30"
                          >
                            <div className="flex flex-col gap-2">
                              <div className="flex items-center justify-between">
                                <span className="font-label-sm text-xs text-secondary tracking-wide">
                                  {extract.meta}
                                </span>
                                <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                              </div>
                              <blockquote className="font-body-md text-xs lg:text-sm text-on-surface italic leading-relaxed pt-1 font-serif">
                                {extract.text}
                              </blockquote>
                            </div>
                            <div className="pt-3 flex items-center justify-end">
                              <Link
                                to="/talk"
                                className="inline-flex items-center gap-1 text-primary hover:text-secondary font-label-sm text-xs transition-colors group"
                              >
                                <span>View in Talk</span>
                                <span className="material-symbols-outlined text-sm group-hover:translate-x-0.5 transition-transform">
                                  arrow_forward
                                </span>
                              </Link>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Sovereign Vector Boundary Strip */}
                      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 px-4 py-2.5 rounded-lg bg-surface-container text-on-surface-variant font-label-sm text-xs">
                        <div className="flex items-center gap-2">
                          <span className="material-symbols-outlined text-secondary text-base">
                            verified_user
                          </span>
                          <span className="text-on-surface font-medium">Sovereign Vector Boundary:</span>
                          <span>Stored in client SQLite · Unlinked from cloud models · Zero behavioral tracking</span>
                        </div>
                        <span className="font-mono text-[11px] text-outline">{topic.hash}</span>
                      </div>
                    </div>
                  )}
                </article>
              );
            })}

            {filteredTopics.length === 0 && (
              <div className="flex flex-col items-center justify-center py-12 px-4 bg-surface-container-low rounded-2xl border border-outline-variant/30 text-center">
                <div className="w-14 h-14 rounded-2xl bg-surface-container-high border border-outline-variant/40 flex items-center justify-center text-secondary mb-2">
                  <span className="material-symbols-outlined text-[28px]">search_off</span>
                </div>
                <h3 className="font-headline-sm text-lg text-primary font-serif mt-2">
                  No remembered topics match “{searchQuery}”
                </h3>
                <p className="font-body-sm text-xs text-on-surface-variant max-w-sm mt-1">
                  Sanctuary found no local index matches or cryptographic aliases matching this query.
                </p>
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="mt-4 px-4 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-primary font-label-sm text-xs transition-colors"
                >
                  Clear search
                </button>
              </div>
            )}
          </div>
        </section>

        {/* SECTION 2: Hidden Names & Local Labels */}
        <section className="flex flex-col gap-4">
          <div className="flex items-center justify-between border-b border-surface-container-highest pb-2">
            <div>
              <h2 className="font-headline-sm text-lg text-primary font-serif">
                Hidden names & local labels
              </h2>
              <p className="font-body-sm text-xs text-on-surface-variant mt-0.5">
                Masked entities substituted with local cryptographic aliases.
              </p>
            </div>
            <button
              type="button"
              onClick={() => setRevealedPlaceholders(!revealedPlaceholders)}
              className="inline-flex items-center gap-1 text-primary hover:text-secondary font-label-sm text-xs transition-colors"
            >
              <span className="material-symbols-outlined text-base">
                {revealedPlaceholders ? "visibility_off" : "visibility"}
              </span>
              <span>{revealedPlaceholders ? "Mask placeholders" : "Reveal placeholders"}</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Person 1 */}
            <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/30 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded bg-surface-container text-secondary font-label-sm text-xs">
                  Person 1
                </span>
                <span className="material-symbols-outlined text-outline text-base">lock</span>
              </div>
              {editingPersonId === "person1" ? (
                <div className="flex flex-col gap-2">
                  <input
                    type="text"
                    value={personAliases.person1}
                    onChange={(e) =>
                      setPersonAliases({ ...personAliases, person1: e.target.value })
                    }
                    className="w-full bg-surface-container-lowest text-primary font-body-md text-sm px-3 py-1.5 rounded-lg border-2 border-primary-container outline-none"
                  />
                  <div className="flex items-center justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setEditingPersonId(null)}
                      className="px-2 py-1 text-xs text-on-surface bg-surface-container rounded"
                    >
                      Done
                    </button>
                  </div>
                </div>
              ) : (
                <div
                  className="font-headline-sm text-lg text-primary font-serif cursor-pointer hover:underline"
                  onClick={() => setEditingPersonId("person1")}
                >
                  “{revealedPlaceholders ? personAliases.person1 : "M."}”
                </div>
              )}
              <span className="font-body-sm text-xs text-on-surface-variant">
                Appears in 8 journal turns · Pinned private
              </span>
            </div>

            {/* Place 1 */}
            <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/30 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded bg-surface-container text-secondary font-label-sm text-xs">
                  Place 1
                </span>
                <span className="material-symbols-outlined text-outline text-base">lock</span>
              </div>
              <div className="font-headline-sm text-lg text-primary font-serif">
                “{revealedPlaceholders ? personAliases.place1 : "[Location 1]"}”
              </div>
              <span className="font-body-sm text-xs text-on-surface-variant">
                Appears in 5 journal turns · Geotag stripped
              </span>
            </div>

            {/* Organization 1 */}
            <div className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/30 flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="px-2 py-0.5 rounded bg-surface-container text-secondary font-label-sm text-xs">
                  Organization 1
                </span>
                <span className="material-symbols-outlined text-outline text-base">lock</span>
              </div>
              <div className="font-headline-sm text-lg text-primary font-serif">
                “{revealedPlaceholders ? personAliases.org1 : "[Organization 1]"}”
              </div>
              <span className="font-body-sm text-xs text-on-surface-variant">
                Appears in 12 journal turns · Alias strictly local
              </span>
            </div>
          </div>
        </section>

        {/* SECTION 3: Unresolved items ledger */}
        {unresolvedItems.length > 0 && (
          <section className="flex flex-col gap-3">
            <div className="flex items-baseline justify-between border-b border-surface-container-highest pb-2">
              <div>
                <h2 className="font-headline-sm text-lg text-primary font-serif">
                  Unresolved items
                </h2>
                <p className="font-body-sm text-xs text-on-surface-variant mt-0.5">
                  Recurring references Sanctuary identified that await confirmation before preservation.
                </p>
              </div>
              <span className="px-2.5 py-0.5 rounded bg-surface-container text-secondary font-label-sm text-xs">
                {unresolvedItems.length} pending review
              </span>
            </div>

            <div className="flex flex-col gap-2 mt-1">
              {unresolvedItems.map((item) => (
                <div
                  key={item.id}
                  className="p-4 rounded-xl bg-surface-container-low border border-outline-variant/30 flex flex-col md:flex-row md:items-center justify-between gap-4"
                >
                  <div className="flex items-start gap-3">
                    <span className="material-symbols-outlined text-secondary mt-0.5 text-xl">
                      help_center
                    </span>
                    <div className="flex flex-col">
                      <span className="font-body-lg text-sm font-medium text-primary">
                        {item.title}
                      </span>
                      <p className="font-body-sm text-xs text-on-surface-variant mt-0.5">
                        {item.note}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 self-end md:self-auto">
                    <button
                      type="button"
                      onClick={() => handleAcknowledgeUnresolved(item)}
                      className="px-3.5 py-1.5 rounded-lg bg-primary text-on-primary font-label-sm text-xs hover:bg-primary-container transition-colors"
                    >
                      Acknowledge
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDismissUnresolved(item.id)}
                      className="px-3.5 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high text-on-surface-variant font-label-sm text-xs transition-colors"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Sovereign Storage Footer Status Strip */}
        <footer className="pt-4 border-t border-surface-container-highest flex flex-col sm:flex-row items-center justify-between gap-4 text-on-surface-variant font-label-sm text-xs">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-primary-container"></span>
            <span>Local Enclave: 148 KB allocated · Zero cloud transmission</span>
          </div>
          <div className="flex items-center gap-4">
            <span>Sanctuary Monastic Core v2.4</span>
            <span className="text-outline">·</span>
            <span className="text-secondary font-mono">SQLite Sovereign Sandbox</span>
          </div>
        </footer>
      </div>
    </div>
  );
}
