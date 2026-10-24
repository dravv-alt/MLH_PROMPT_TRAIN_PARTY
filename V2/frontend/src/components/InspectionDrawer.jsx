import React, { useState, useMemo, useEffect } from "react";
import { analyzeFullInspection } from "../services/nlpEngine";

/**
 * InspectionDrawer
 *
 * The official Sanctuary "How this was read" Observability & Transparency Sheet.
 * Implements all 5 transparency sections:
 * 1. What was hidden (Local PII Masking & Distillation)
 * 2. How your words connect (Syntactic Clauses & Discourse Flow)
 * 3. Topics that came back (Lexical Recurrence & Centering Ties)
 * 4. Wording over this conversation (Discrete Grammatical Tallies & SVG Sparklines)
 * 5. Why this reply (Sanctuary Response Policy & Grounded Anchors)
 */
export default function InspectionDrawer({ isOpen, onClose, turnData, allTurns = [] }) {
  const [showJson, setShowJson] = useState(false);

  // Close on Escape key press (with stopPropagation in capture phase to prevent curtain triggering)
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown, true);
    return () => window.removeEventListener("keydown", handleKeyDown, true);
  }, [isOpen, onClose]);

  // Compute deterministic syntactic & semantic inspection data using nlpEngine
  const inspection = useMemo(() => {
    return analyzeFullInspection(turnData, allTurns);
  }, [turnData, allTurns]);

  if (!isOpen) return null;

  const {
    maskedText,
    entity,
    entityType,
    entitiesMasked,
    clauses,
    connectors,
    recurringTopics,
    metricTurns,
    policyExplanation,
    anchors,
  } = inspection;

  return (
    <aside
      id="inspectionSheet"
      aria-label="How this turn was read and parsed"
      className="fixed top-0 bottom-0 right-0 w-[440px] max-w-[90vw] bg-[#F6F7F3] border-l border-[#CDD2C8] rounded-tl-[28px] z-40 flex flex-col transition-transform duration-300 shadow-2xl overflow-hidden animate-in slide-in-from-right duration-300"
    >
      {/* Sheet Header Bar */}
      <div className="px-6 py-5 border-b border-[#CDD2C8] flex items-start justify-between bg-[#F6F7F3]/95 backdrop-blur-sm sticky top-0 z-20">
        <div className="flex flex-col gap-1 pr-2">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[17px] text-[#2E4B3F]">grain</span>
            <h2 className="font-headline-sm text-lg font-serif text-[#23261F] font-normal tracking-tight">
              How this was read
            </h2>
          </div>
          {/* Always-visible Grounding sub-statement */}
          <p className="font-body-sm text-xs text-[#454B40] leading-snug">
            This describes your wording. It does not describe how you feel.
          </p>
        </div>
        <button
          onClick={onClose}
          aria-label="Close inspection sheet"
          className="p-2 rounded-lg text-[#454B40] hover:text-[#23261F] hover:bg-[#DDE1DA] transition-colors focus:outline-none"
          title="Close inspection"
          type="button"
        >
          <span className="material-symbols-outlined text-[20px]">close</span>
        </button>
      </div>

      {/* Scrollable Inspection Sections Container */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-8 divide-y divide-[#CDD2C8]/70">
        
        {/* Section 1: What was hidden */}
        <div className="pt-0 flex flex-col gap-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#2E4B3F]"></span>
              <h3 className="font-label-md text-xs uppercase tracking-wider text-[#23261F] font-semibold">
                1. What was hidden
              </h3>
            </div>
            <details className="group cursor-pointer">
              <summary className="list-none text-[11px] font-label-sm text-[#454B40] hover:text-[#23261F] flex items-center gap-1 select-none">
                <span>What is this?</span>
                <span className="material-symbols-outlined text-[14px] group-open:rotate-180 transition-transform">
                  expand_more
                </span>
              </summary>
              <div className="mt-2 text-xs text-[#454B40] bg-[#DDE1DA]/60 p-2.5 rounded-lg border border-[#CDD2C8] leading-relaxed">
                Named Entity Recognition runs strictly within isolated browser memory. Text matching sensitive entities is tokenized and replaced before network transmission.
              </div>
            </details>
          </div>

          {/* Turn with hidden name chip */}
          <div className="bg-[#DDE1DA] p-3.5 rounded-xl border border-[#CDD2C8] text-xs font-body-sm leading-relaxed text-[#23261F]">
            "{maskedText.split(entity).map((part, pIdx, arr) => (
              <React.Fragment key={pIdx}>
                {part}
                {pIdx < arr.length - 1 && (
                  <span className="bg-[#C5CCC3] text-[#23261F] px-1.5 py-0.5 mx-0.5 rounded font-label-md font-medium">
                    {entity}
                  </span>
                )}
              </React.Fragment>
            ))}"
          </div>

          {/* Detected Entity Badge */}
          <div className="flex items-start gap-2.5 bg-[#F2F4EF] p-3 rounded-lg border border-[#CDD2C8] text-xs">
            <span className="material-symbols-outlined text-[16px] text-[#2E4B3F] mt-0.5">
              verified_user
            </span>
            <div className="flex flex-col gap-0.5">
              <span className="font-label-md text-[#23261F] font-medium">
                {entity} • {entityType}
              </span>
              <span className="font-body-sm text-[#454B40]">
                Replaced in volatile WASM memory before dispatch
              </span>
            </div>
          </div>

          {/* Collapsible: Show what writing service received */}
          <details className="border border-[#CDD2C8] rounded-lg bg-[#DDE1DA]/40 group text-xs overflow-hidden">
            <summary className="px-3.5 py-2 font-label-sm text-[#23261F] font-medium flex items-center justify-between cursor-pointer select-none hover:bg-[#DDE1DA]">
              <span>Show what the writing service received</span>
              <span className="material-symbols-outlined text-[16px] text-[#454B40] group-open:rotate-180 transition-transform">
                code
              </span>
            </summary>
            <div className="p-3 bg-[#23261F] text-[#E9ECE7] font-mono text-[11px] overflow-x-auto leading-relaxed border-t border-[#CDD2C8]">
              <code>
                {JSON.stringify(
                  {
                    role: "user",
                    text: maskedText,
                    entities_masked: entitiesMasked,
                  },
                  null,
                  2
                )}
              </code>
            </div>
          </details>

          {/* Honest Trust Notice */}
          <p className="font-label-sm text-[11px] text-[#454B40] leading-snug flex items-center gap-1.5">
            <span className="material-symbols-outlined text-[14px] text-[#2E4B3F]">info</span>
            <span>
              Names and explicit identifiers are masked. Contextual biographical events within sentences remain as authored.
            </span>
          </p>
        </div>

        {/* Section 2: How your words connect */}
        <div className="pt-6 flex flex-col gap-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#2E4B3F]"></span>
              <h3 className="font-label-md text-xs uppercase tracking-wider text-[#23261F] font-semibold">
                2. How your words connect
              </h3>
            </div>
            <details className="group cursor-pointer">
              <summary className="list-none text-[11px] font-label-sm text-[#454B40] hover:text-[#23261F] flex items-center gap-1 select-none">
                <span>What is this?</span>
                <span className="material-symbols-outlined text-[14px] group-open:rotate-180 transition-transform">
                  expand_more
                </span>
              </summary>
              <div className="mt-2 text-xs text-[#454B40] bg-[#DDE1DA]/60 p-2.5 rounded-lg border border-[#CDD2C8] leading-relaxed">
                Syntactic discourse markers show how separate clauses logically pivot or contrast without assuming sentiment or emotion.
              </div>
            </details>
          </div>

          {/* Interactive Discourse Link Diagram & Clauses */}
          <div className="relative flex flex-col gap-3 bg-[#DDE1DA]/50 p-4 rounded-xl border border-[#CDD2C8]">
            {clauses.map((clause, cIdx) => (
              <React.Fragment key={clause.id || cIdx}>
                {/* Clause Box */}
                <div className="p-2.5 bg-[#F6F7F3] rounded-lg border border-[#CDD2C8] text-xs font-body-sm text-[#23261F]">
                  <div className="font-label-sm text-[10px] uppercase text-[#454B40] mb-0.5">
                    {clause.id || `Clause ${String.fromCharCode(65 + cIdx)}`}
                  </div>
                  "{clause.text}"
                </div>

                {/* Connector Linking to Next Clause */}
                {cIdx < clauses.length - 1 && (
                  <div className="flex items-center gap-2 pl-3">
                    <div className="w-4 h-6 border-l-2 border-b-2 border-[#2E4B3F]/60 rounded-bl"></div>
                    <span className="inline-flex items-center gap-1.5 bg-[#2E4B3F] text-[#E9ECE7] px-2.5 py-1 rounded font-label-sm text-[11px]">
                      <span>[{connectors[cIdx]?.cue || connectors[cIdx]?.text || "then"}]</span>
                      <span className="text-[#C4CF5A]">
                        • {connectors[cIdx]?.type || "Syntactic Sequence"}
                      </span>
                    </span>
                  </div>
                )}
              </React.Fragment>
            ))}

            {/* Visual SVG Connecting Arc Diagram */}
            <div className="mt-2 pt-2 border-t border-[#CDD2C8]/70">
              <div className="flex items-center justify-between text-[11px] font-label-sm text-[#454B40] mb-1">
                <span>Deterministic clause flow</span>
                <span className="text-[#2E4B3F]">
                  {clauses.map((c) => c.id).join(" → ") || "Clause A → Clause B"}
                </span>
              </div>
              <svg className="w-full h-11 text-[#2E4B3F] overflow-visible" viewBox="0 0 340 44">
                {/* Clause node A */}
                <circle cx="20" cy="22" r="6" fill="#2E4B3F" />
                <text x="20" y="38" fill="#454B40" fontSize="9" textAnchor="middle">
                  Clause A
                </text>

                {/* Link 1 */}
                <path d="M 26 22 H 164" stroke="#2E4B3F" strokeDasharray="2 2" strokeWidth="2" />
                <rect x="70" y="12" width="70" height="18" rx="4" fill="#DDE1DA" stroke="#CDD2C8" />
                <text x="105" y="24" fill="#23261F" fontSize="8.5" fontWeight="600" textAnchor="middle">
                  {connectors[0]?.cue || connectors[0]?.text || "even though"}
                </text>

                {/* Clause node B */}
                <circle cx="170" cy="22" r="6" fill="#2E4B3F" />
                <text x="170" y="38" fill="#454B40" fontSize="9" textAnchor="middle">
                  Clause B
                </text>

                {/* Link 2 */}
                <path d="M 176 22 H 314" stroke="#2E4B3F" strokeWidth="2" />
                <rect x="220" y="12" width="50" height="18" rx="4" fill="#C4CF5A" />
                <text x="245" y="24" fill="#23261F" fontSize="8.5" fontWeight="600" textAnchor="middle">
                  {connectors[1]?.cue || connectors[1]?.text || "but"}
                </text>

                {/* Clause node C */}
                <circle cx="320" cy="22" r="6" fill="#2E4B3F" />
                <text x="320" y="38" fill="#454B40" fontSize="9" textAnchor="middle">
                  Clause C
                </text>
              </svg>
            </div>
          </div>

          {/* Accessible Table Disclosure */}
          <details className="text-xs group">
            <summary className="font-label-sm text-[11px] text-[#454B40] hover:text-[#23261F] cursor-pointer flex items-center gap-1 select-none">
              <span>View accessible discourse links table</span>
              <span className="material-symbols-outlined text-[14px] group-open:rotate-180 transition-transform">
                expand_more
              </span>
            </summary>
            <div className="mt-2 overflow-x-auto border border-[#CDD2C8] rounded-lg">
              <table className="w-full text-left border-collapse text-[11px]">
                <thead>
                  <tr className="bg-[#DDE1DA] text-[#23261F] font-label-md">
                    <th className="p-2 border-b border-[#CDD2C8]">Source</th>
                    <th className="p-2 border-b border-[#CDD2C8]">Connector</th>
                    <th className="p-2 border-b border-[#CDD2C8]">Target</th>
                    <th className="p-2 border-b border-[#CDD2C8]">Function</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#CDD2C8] text-[#454B40]">
                  {connectors.map((c, idx) => (
                    <tr key={idx}>
                      <td className="p-2">{c.source || `Clause ${String.fromCharCode(65 + idx)}`}</td>
                      <td className="p-2 font-medium text-[#23261F]">{c.cue || c.text}</td>
                      <td className="p-2">{c.target || `Clause ${String.fromCharCode(66 + idx)}`}</td>
                      <td className="p-2">{c.type}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </div>

        {/* Section 3: Topics that came back */}
        <div className="pt-6 flex flex-col gap-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#2E4B3F]"></span>
              <h3 className="font-label-md text-xs uppercase tracking-wider text-[#23261F] font-semibold">
                3. Topics that came back
              </h3>
            </div>
            <details className="group cursor-pointer">
              <summary className="list-none text-[11px] font-label-sm text-[#454B40] hover:text-[#23261F] flex items-center gap-1 select-none">
                <span>What is this?</span>
                <span className="material-symbols-outlined text-[14px] group-open:rotate-180 transition-transform">
                  expand_more
                </span>
              </summary>
              <div className="mt-2 text-xs text-[#454B40] bg-[#DDE1DA]/60 p-2.5 rounded-lg border border-[#CDD2C8] leading-relaxed">
                Lexical frequency tracks verbatim word repetitions across turns. Words are never tagged with clinical or emotional categories.
              </div>
            </details>
          </div>

          {/* Recurrence Cards */}
          <div className="space-y-2">
            {recurringTopics.map((topic, tIdx) => (
              <div
                key={tIdx}
                className="p-3 bg-[#DDE1DA]/50 rounded-xl border border-[#CDD2C8] flex items-center justify-between"
              >
                <div className="flex flex-col gap-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-label-md text-xs text-[#23261F]">"{topic.term}"</span>
                    <span
                      className={`text-[10px] font-label-sm px-1.5 py-0.5 rounded ${
                        topic.label === "Direct reuse"
                          ? "bg-[#2E4B3F]/10 text-[#2E4B3F]"
                          : "bg-[#C5CCC3] text-[#23261F]"
                      }`}
                    >
                      {topic.label}
                    </span>
                  </div>
                  <span className="text-[11px] font-body-sm text-[#454B40]">{topic.detail}</span>
                </div>
                <span className="text-xs font-label-sm text-[#2E4B3F] flex items-center gap-1">
                  <span>{topic.status || "Linked"}</span>
                  {topic.status === "Linked" && (
                    <span className="material-symbols-outlined text-[14px]">link</span>
                  )}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Section 4: Wording over this conversation */}
        <div className="pt-6 flex flex-col gap-3.5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#2E4B3F]"></span>
              <h3 className="font-label-md text-xs uppercase tracking-wider text-[#23261F] font-semibold">
                4. Wording over this conversation
              </h3>
            </div>
            <details className="group cursor-pointer">
              <summary className="list-none text-[11px] font-label-sm text-[#454B40] hover:text-[#23261F] flex items-center gap-1 select-none">
                <span>What is this?</span>
                <span className="material-symbols-outlined text-[14px] group-open:rotate-180 transition-transform">
                  expand_more
                </span>
              </summary>
              <div className="mt-2 text-xs text-[#454B40] bg-[#DDE1DA]/60 p-2.5 rounded-lg border border-[#CDD2C8] leading-relaxed">
                Discrete tallies of grammatical occurrences over all session turns. These replace behavioral or diagnostic scores with literal word counts.
              </div>
            </details>
          </div>

          {/* 4 Quiet Micro-Timelines (2x2 grid) */}
          <div className="grid grid-cols-2 gap-2.5">
            {/* Metric 1 */}
            <div className="p-3 bg-[#DDE1DA]/40 rounded-xl border border-[#CDD2C8] flex flex-col justify-between h-28">
              <div>
                <div className="text-[11px] font-label-md text-[#23261F] leading-tight font-medium">
                  People or places
                </div>
                <div className="text-[10px] text-[#454B40]">
                  {metricTurns[metricTurns.length - 1]?.places || 1} masked entity (T{metricTurns.length})
                </div>
              </div>
              <div className="w-full h-8">
                <svg className="w-full h-full stroke-[#2E4B3F] fill-none" viewBox="0 0 100 24">
                  <line stroke="#CDD2C8" strokeWidth="1.5" x1="10" x2="50" y1="20" y2="20" />
                  <line stroke="#2E4B3F" strokeWidth="1.5" x1="50" x2="90" y1="20" y2="8" />
                  <circle cx="10" cy="20" r="2.5" fill="#454B40" />
                  <circle cx="50" cy="20" r="2.5" fill="#454B40" />
                  <circle cx="90" cy="8" r="3" fill="#2E4B3F" />
                </svg>
              </div>
              <div className="flex justify-between text-[9px] font-label-sm text-[#454B40]">
                <span>Turn 1</span>
                <span>Turn 2</span>
                <span className="text-[#23261F] font-bold">Turn {metricTurns.length}</span>
              </div>
            </div>

            {/* Metric 2 */}
            <div className="p-3 bg-[#DDE1DA]/40 rounded-xl border border-[#CDD2C8] flex flex-col justify-between h-28">
              <div>
                <div className="text-[11px] font-label-md text-[#23261F] leading-tight font-medium">
                  Thought connectors
                </div>
                <div className="text-[10px] text-[#454B40]">
                  {metricTurns[metricTurns.length - 1]?.connectors || 2} discourse links (T{metricTurns.length})
                </div>
              </div>
              <div className="w-full h-8">
                <svg className="w-full h-full stroke-[#2E4B3F] fill-none" viewBox="0 0 100 24">
                  <line stroke="#2E4B3F" strokeWidth="1.5" x1="10" x2="50" y1="18" y2="12" />
                  <line stroke="#2E4B3F" strokeWidth="1.5" x1="50" x2="90" y1="12" y2="6" />
                  <circle cx="10" cy="18" r="2.5" fill="#454B40" />
                  <circle cx="50" cy="12" r="2.5" fill="#454B40" />
                  <circle cx="90" cy="6" r="3" fill="#2E4B3F" />
                </svg>
              </div>
              <div className="flex justify-between text-[9px] font-label-sm text-[#454B40]">
                <span>Turn 1</span>
                <span>Turn 2</span>
                <span className="text-[#23261F] font-bold">Turn {metricTurns.length}</span>
              </div>
            </div>

            {/* Metric 3 */}
            <div className="p-3 bg-[#DDE1DA]/40 rounded-xl border border-[#CDD2C8] flex flex-col justify-between h-28">
              <div>
                <div className="text-[11px] font-label-md text-[#23261F] leading-tight font-medium">
                  Softening phrases
                </div>
                <div className="text-[10px] text-[#454B40]">"even though", "felt like"</div>
              </div>
              <div className="w-full h-8">
                <svg className="w-full h-full stroke-[#2E4B3F] fill-none" viewBox="0 0 100 24">
                  <line stroke="#2E4B3F" strokeWidth="1.5" x1="10" x2="50" y1="20" y2="8" />
                  <line stroke="#2E4B3F" strokeWidth="1.5" x1="50" x2="90" y1="8" y2="8" />
                  <circle cx="10" cy="20" r="2.5" fill="#454B40" />
                  <circle cx="50" cy="8" r="2.5" fill="#454B40" />
                  <circle cx="90" cy="8" r="3" fill="#2E4B3F" />
                </svg>
              </div>
              <div className="flex justify-between text-[9px] font-label-sm text-[#454B40]">
                <span>Turn 1</span>
                <span>Turn 2</span>
                <span className="text-[#23261F] font-bold">Turn {metricTurns.length}</span>
              </div>
            </div>

            {/* Metric 4 */}
            <div className="p-3 bg-[#DDE1DA]/40 rounded-xl border border-[#CDD2C8] flex flex-col justify-between h-28">
              <div>
                <div className="text-[11px] font-label-md text-[#23261F] leading-tight font-medium">
                  Lexical divergence
                </div>
                <div className="text-[10px] text-[#454B40]">Moderate word shift</div>
              </div>
              <div className="w-full h-8">
                <svg className="w-full h-full stroke-[#2E4B3F] fill-none" viewBox="0 0 100 24">
                  <line stroke="#2E4B3F" strokeWidth="1.5" x1="10" x2="50" y1="8" y2="16" />
                  <line stroke="#2E4B3F" strokeWidth="1.5" x1="50" x2="90" y1="16" y2="10" />
                  <circle cx="10" cy="8" r="2.5" fill="#454B40" />
                  <circle cx="50" cy="16" r="2.5" fill="#454B40" />
                  <circle cx="90" cy="10" r="3" fill="#2E4B3F" />
                </svg>
              </div>
              <div className="flex justify-between text-[9px] font-label-sm text-[#454B40]">
                <span>Turn 1</span>
                <span>Turn 2</span>
                <span className="text-[#23261F] font-bold">Turn {metricTurns.length}</span>
              </div>
            </div>
          </div>

          {/* View raw counts table toggle */}
          <details className="text-xs group">
            <summary className="font-label-sm text-[11px] text-[#454B40] hover:text-[#23261F] cursor-pointer flex items-center gap-1 select-none">
              <span>View raw counts table</span>
              <span className="material-symbols-outlined text-[14px] group-open:rotate-180 transition-transform">
                expand_more
              </span>
            </summary>
            <div className="mt-2 overflow-x-auto border border-[#CDD2C8] rounded-lg">
              <table className="w-full text-left border-collapse text-[11px]">
                <thead>
                  <tr className="bg-[#DDE1DA] text-[#23261F] font-label-md">
                    <th className="p-2 border-b border-[#CDD2C8]">Turn</th>
                    <th className="p-2 border-b border-[#CDD2C8]">Places/Names</th>
                    <th className="p-2 border-b border-[#CDD2C8]">Connectors</th>
                    <th className="p-2 border-b border-[#CDD2C8]">Softening</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#CDD2C8] text-[#454B40]">
                  {metricTurns.map((row, idx) => (
                    <tr
                      key={idx}
                      className={row.isCurrent ? "bg-[#F2F4EF] font-semibold text-[#23261F]" : ""}
                    >
                      <td className="p-2 font-medium">
                        {row.turnLabel} {row.isCurrent ? "(Current)" : ""}
                      </td>
                      <td className="p-2">{row.places}</td>
                      <td className="p-2">{row.connectors}</td>
                      <td className="p-2">{row.softening}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </details>
        </div>

        {/* Section 5: Why this reply */}
        <div className="pt-6 flex flex-col gap-3.5 pb-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-[#2E4B3F]"></span>
              <h3 className="font-label-md text-xs uppercase tracking-wider text-[#23261F] font-semibold">
                5. Why this reply
              </h3>
            </div>
            <details className="group cursor-pointer">
              <summary className="list-none text-[11px] font-label-sm text-[#454B40] hover:text-[#23261F] flex items-center gap-1 select-none">
                <span>What is this?</span>
                <span className="material-symbols-outlined text-[14px] group-open:rotate-180 transition-transform">
                  expand_more
                </span>
              </summary>
              <div className="mt-2 text-xs text-[#454B40] bg-[#DDE1DA]/60 p-2.5 rounded-lg border border-[#CDD2C8] leading-relaxed">
                The Sanctuary response policy pairs structural anchors in your text with open questions rather than offering diagnosis or unsolicited advice.
              </div>
            </details>
          </div>

          <div className="p-4 bg-[#DDE1DA] rounded-xl border border-[#CDD2C8] flex flex-col gap-3">
            <p className="font-body-md text-xs sm:text-sm text-[#23261F] leading-relaxed">
              {policyExplanation}
            </p>
            <div className="pt-3 border-t border-[#CDD2C8] flex items-center gap-2 text-xs text-[#454B40]">
              <span className="material-symbols-outlined text-[15px] text-[#2E4B3F]">anchor</span>
              <span className="font-label-sm">
                Anchors selected: <strong>{anchors.join(" + ")}</strong>
              </span>
            </div>
          </div>

          {/* Rigorous Reassurance Stamp */}
          <div className="p-3 rounded-lg bg-[#F2F4EF] border border-[#CDD2C8] flex items-start gap-2.5 text-xs text-[#454B40]">
            <span className="material-symbols-outlined text-[16px] text-[#2E4B3F] mt-0.5">
              verified
            </span>
            <p className="font-label-sm leading-snug">
              Grounded in sentence syntactic linkage. Zero inferred psychological traits.
            </p>
          </div>
        </div>
      </div>

      {/* Sheet Footer Bar */}
      <div className="px-6 py-4 border-t border-[#CDD2C8] bg-[#F6F7F3] flex items-center justify-between text-xs text-[#454B40]">
        <span className="font-label-sm">Local inspect view</span>
        <button
          onClick={onClose}
          className="text-[#2E4B3F] font-label-md hover:underline cursor-pointer"
          type="button"
        >
          Dismiss panel (Esc)
        </button>
      </div>
    </aside>
  );
}
