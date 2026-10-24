import React, { useState } from "react";
import { Link } from "react-router-dom";
import {
  distillPII,
  computeCenteringTrace,
  parseHobbsPronouns,
  parseClausesAndConnectives,
  evolveSessionMemory,
} from "../services/nlpEngine";

export default function HowThisWasReadPage() {
  const sampleTurns = [
    {
      id: "turn1",
      title: "Turn 1: Monday Agreement & Unspoken Obligation",
      text: "I've been carrying this quiet knot about the agreement we made on Monday. Person 1 assumed I would absorb the delays without adjusting any milestones, and when Colleague 2 stepped away, the silence felt like an unspoken obligation. I can physically feel the strain in my shoulders, but I haven't spoken up because nobody explicitly asked me to carry it—it just landed.",
    },
    {
      id: "turn2",
      title: "Turn 2: Pacing the Perimeter",
      text: "I walked past The Office building this morning even though I had nowhere to be. I knew there were dishes in the sink and unanswered emails, but the cold air felt like the only thing that wasn't demanding a decision from me.",
    },
    {
      id: "turn3",
      title: "Turn 3: Setting Down the Burden",
      text: "Setting down the belief that if I don't buffer the fallout, I am the one causing the delay. Enduring the silence isn't the same as choosing the burden, because silence is simply empty space.",
    },
  ];

  const [activeTurnId, setActiveTurnId] = useState("turn1");
  const [customText, setCustomText] = useState(sampleTurns[0].text);
  const [isCustomMode, setIsCustomMode] = useState(false);

  const activeText = isCustomMode
    ? customText
    : sampleTurns.find((t) => t.id === activeTurnId)?.text || sampleTurns[0].text;

  // Run deterministic NLP engine on active text
  const piiResult = distillPII(activeText);
  const centeringTrace = computeCenteringTrace(piiResult.maskedText, piiResult.entities);
  const hobbsPronouns = parseHobbsPronouns(piiResult.maskedText, piiResult.entities);
  const clauseResult = parseClausesAndConnectives(piiResult.maskedText);
  const evolvedCandidate = evolveSessionMemory([{ role: "user", text: activeText }]);

  return (
    <div className="w-full min-h-screen bg-background font-body-md text-on-surface antialiased select-none pb-24">
      {/* Header Container */}
      <div className="w-full border-b border-surface-container-highest/80 bg-surface-container-low/40 backdrop-blur-md">
        <div className="w-full max-w-[1540px] mx-auto px-6 lg:px-12 xl:px-16 py-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-surface-container-high border border-outline-variant/60 flex items-center justify-center text-primary shadow-2xs">
              <span className="material-symbols-outlined text-[26px] text-secondary">visibility</span>
            </div>
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-lichen animate-pulse"></span>
                <span className="font-label-sm text-xs uppercase tracking-wider text-secondary font-semibold">
                  Transparency & Observability Suite
                </span>
              </div>
              <h1 className="text-primary text-3xl sm:text-4xl font-normal tracking-tight font-serif">
                How this was read.
              </h1>
              <p className="text-on-surface-variant text-sm sm:text-base font-normal max-w-2xl leading-relaxed">
                Deterministic syntactic mapping, privacy masking, and Centering traces. Sanctuary describes the shape of your wording without psychological evaluation or opaque black-box scoring.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <Link
              to="/talk"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-surface-container hover:bg-surface-container-high text-primary border border-surface-container-highest font-label-md text-xs font-medium transition-colors"
            >
              <span className="material-symbols-outlined text-base">forum</span>
              <span>Back to Conversation</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Main Suite Container */}
      <div className="w-full max-w-[1540px] mx-auto px-6 lg:px-12 xl:px-16 pt-8 flex flex-col gap-10">
        
        {/* Turn Selector & Custom Input Bar */}
        <section className="bg-surface-container-low p-6 rounded-3xl border border-surface-container-highest flex flex-col gap-5 shadow-2xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <span className="font-label-sm text-xs uppercase tracking-wider text-secondary font-semibold">
              Select an archival turn or test your own sentences:
            </span>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setIsCustomMode(false)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                  !isCustomMode
                    ? "bg-primary text-on-primary shadow-xs"
                    : "bg-surface-container text-secondary hover:text-primary"
                }`}
              >
                Sample Turns
              </button>
              <button
                type="button"
                onClick={() => setIsCustomMode(true)}
                className={`px-3 py-1 rounded-lg text-xs font-medium transition-all ${
                  isCustomMode
                    ? "bg-primary text-on-primary shadow-xs"
                    : "bg-surface-container text-secondary hover:text-primary"
                }`}
              >
                Custom Live Tester
              </button>
            </div>
          </div>

          {!isCustomMode ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {sampleTurns.map((turn) => (
                <button
                  key={turn.id}
                  type="button"
                  onClick={() => setActiveTurnId(turn.id)}
                  className={`p-4 rounded-2xl text-left border transition-all flex flex-col gap-1.5 ${
                    activeTurnId === turn.id
                      ? "bg-surface-container-lowest border-primary shadow-xs"
                      : "bg-surface-container border-surface-container-highest/80 hover:bg-surface-container-high"
                  }`}
                >
                  <span className="font-headline-sm text-xs font-serif text-primary font-semibold">
                    {turn.title}
                  </span>
                  <p className="font-body-sm text-[11px] text-on-surface-variant line-clamp-2">
                    "{turn.text}"
                  </p>
                </button>
              ))}
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              <textarea
                value={customText}
                onChange={(e) => setCustomText(e.target.value)}
                placeholder="Type or paste any contemplative sentence to inspect how Sanctuary parses it..."
                rows={3}
                className="w-full bg-surface-container-lowest border border-surface-container-highest rounded-2xl p-3 text-xs sm:text-sm font-body-md text-on-surface focus:outline-none focus:border-primary transition-all resize-y"
              />
              <span className="text-[11px] font-label-sm text-secondary">
                Running live client-side Centering, Hobbs resolution, and PII distiller.
              </span>
            </div>
          )}
        </section>

        {/* 1. Privacy Distiller & Client Anonymization */}
        <section className="bg-surface-container-low p-6 lg:p-8 rounded-3xl border border-surface-container-highest flex flex-col gap-6">
          <div className="flex items-center justify-between border-b border-surface-container-highest pb-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-serif font-bold text-sm">
                01
              </div>
              <div>
                <h2 className="font-headline-sm text-xl font-serif text-primary">
                  1. What was hidden: Client Anonymization
                </h2>
                <p className="font-body-sm text-xs text-secondary mt-0.5">
                  Names, entities, and identifying titles are scrubbed in volatile memory before network transmission.
                </p>
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-surface-container border border-surface-container-highest text-secondary text-xs">
              <span className="material-symbols-outlined text-[16px] text-primary">shield</span>
              <span>{piiResult.entitiesMasked} entities distilled</span>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <span className="font-label-sm text-xs uppercase tracking-wider text-secondary font-semibold">
                Original Author Text
              </span>
              <div className="p-4 rounded-2xl bg-surface-container-lowest border border-surface-container-highest text-xs sm:text-sm font-body-md leading-relaxed text-on-surface">
                {piiResult.rawText}
              </div>
            </div>

            <div className="flex flex-col gap-2">
              <span className="font-label-sm text-xs uppercase tracking-wider text-secondary font-semibold flex items-center gap-1.5">
                <span>Sanctuary Masked Stream</span>
                <span className="text-lichen text-[10px] font-mono bg-primary px-1.5 py-0.2 rounded">Encrypted</span>
              </span>
              <div className="p-4 rounded-2xl bg-[#E8EDE5] border border-[#CCD2C6] text-xs sm:text-sm font-body-md leading-relaxed text-primary">
                {piiResult.maskedText}
              </div>
            </div>
          </div>

          {piiResult.entities.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-2">
              <span className="text-xs font-label-sm text-secondary mr-2">Protected Tokens:</span>
              {piiResult.entities.map((ent, idx) => (
                <div
                  key={idx}
                  className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-surface-container-high border border-surface-container-highest text-xs font-label-sm text-primary"
                >
                  <span className="text-secondary">{ent.original}</span>
                  <span className="material-symbols-outlined text-[12px]">arrow_forward</span>
                  <span className="font-semibold">{ent.masked}</span>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* 2. The Centering Algorithm (Discourse Coherence & Transitions) */}
        <section className="bg-surface-container-low p-6 lg:p-8 rounded-3xl border border-surface-container-highest flex flex-col gap-6">
          <div className="flex items-center justify-between border-b border-surface-container-highest pb-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-serif font-bold text-sm">
                02
              </div>
              <div>
                <h2 className="font-headline-sm text-xl font-serif text-primary">
                  2. Centering Algorithm (Grosz, Joshi, & Weinstein)
                </h2>
                <p className="font-body-sm text-xs text-secondary mt-0.5">
                  Tracks attentional focus and local discourse coherence across successive sentences.
                </p>
              </div>
            </div>
            <span className="hidden sm:inline font-mono text-[11px] text-secondary">
              Role Salience: Subject &gt; Object &gt; Other
            </span>
          </div>

          {/* Centering Trace Table */}
          <div className="w-full overflow-x-auto rounded-2xl border border-surface-container-highest bg-surface-container-lowest">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-surface-container-high/60 border-b border-surface-container-highest text-secondary uppercase font-label-sm text-[11px]">
                  <th className="py-3 px-4">Sentence</th>
                  <th className="py-3 px-4">Text Excerpt</th>
                  <th className="py-3 px-4">Forward Centers (Cf)</th>
                  <th className="py-3 px-4">Preferred (Cp)</th>
                  <th className="py-3 px-4">Backward (Cb)</th>
                  <th className="py-3 px-4">Transition</th>
                  <th className="py-3 px-4 text-right">Coherence Cost</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-container-highest/60 font-body-sm">
                {centeringTrace.map((row) => (
                  <tr key={row.sentence} className="hover:bg-surface-container-low/50 transition-colors">
                    <td className="py-3 px-4 font-mono font-medium text-primary">
                      S{row.sentence + 1}
                    </td>
                    <td className="py-3 px-4 text-on-surface-variant max-w-[320px] truncate" title={row.sentenceText}>
                      "{row.sentenceText}"
                    </td>
                    <td className="py-3 px-4 text-primary">
                      <div className="flex flex-wrap gap-1">
                        {row.cf.map((c, i) => (
                          <span key={i} className="px-1.5 py-0.5 rounded bg-surface-container text-[11px]">
                            {c}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3 px-4 font-medium text-primary">
                      {row.cp || "—"}
                    </td>
                    <td className="py-3 px-4 font-medium text-secondary">
                      {row.cb || "—"}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-label-sm font-semibold tracking-wide ${
                          row.transition === "CONTINUE"
                            ? "bg-lichen/30 text-primary border border-lichen"
                            : row.transition === "SMOOTH_SHIFT"
                            ? "bg-secondary-container text-primary"
                            : row.transition === "RETAIN"
                            ? "bg-surface-container-high text-secondary"
                            : "bg-surface-container text-outline"
                        }`}
                      >
                        {row.transition}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-secondary">
                      {row.cost}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Centering Theory Legend */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
            <div className="p-3.5 bg-surface-container rounded-xl border border-surface-container-highest">
              <span className="font-semibold text-primary block">CONTINUE (Cost 0)</span>
              <p className="text-secondary mt-1 text-[11px]">
                The backward center is maintained and is the primary topic of this sentence. Peak narrative stability.
              </p>
            </div>
            <div className="p-3.5 bg-surface-container rounded-xl border border-surface-container-highest">
              <span className="font-semibold text-primary block">RETAIN (Cost 1)</span>
              <p className="text-secondary mt-1 text-[11px]">
                Prior center is kept, but a new preferred entity is introduced. Preparing for transition.
              </p>
            </div>
            <div className="p-3.5 bg-surface-container rounded-xl border border-surface-container-highest">
              <span className="font-semibold text-primary block">SMOOTH SHIFT (Cost 2)</span>
              <p className="text-secondary mt-1 text-[11px]">
                Attentional center shifts smoothly to the entity that was prepared in the previous turn.
              </p>
            </div>
            <div className="p-3.5 bg-surface-container rounded-xl border border-surface-container-highest">
              <span className="font-semibold text-primary block">ROUGH SHIFT / NO CB (Cost 3)</span>
              <p className="text-secondary mt-1 text-[11px]">
                Center changes abruptly without prior setup, or sentence introduces an isolated subject.
              </p>
            </div>
          </div>
        </section>

        {/* 3. Hobbs Pronoun Resolution & Explicit Clause Relations */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Hobbs Pronouns */}
          <section className="bg-surface-container-low p-6 lg:p-8 rounded-3xl border border-surface-container-highest flex flex-col gap-5">
            <div className="flex items-center gap-3 border-b border-surface-container-highest pb-4">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-serif font-bold text-sm">
                03
              </div>
              <div>
                <h2 className="font-headline-sm text-lg font-serif text-primary">
                  3. Hobbs Antecedent Proposals
                </h2>
                <p className="font-body-sm text-xs text-secondary mt-0.5">
                  Constituency & dependency proposal order for pronoun coreference.
                </p>
              </div>
            </div>

            {hobbsPronouns.length > 0 ? (
              <div className="space-y-3">
                {hobbsPronouns.map((item, idx) => (
                  <div key={idx} className="p-4 bg-surface-container-lowest rounded-2xl border border-surface-container-highest flex flex-col gap-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-label-md font-semibold text-primary">
                        Pronoun: "{item.pronoun}"
                      </span>
                      <span className="px-2 py-0.5 rounded-full bg-secondary-container text-primary font-label-sm text-[10px]">
                        Resolved → {item.resolvedAntecedent}
                      </span>
                    </div>
                    <div className="text-[11px] text-secondary flex flex-col gap-1">
                      <span>Syntactic candidates considered:</span>
                      <ul className="list-disc pl-4 space-y-0.5">
                        {item.candidates.map((c, cIdx) => (
                          <li key={cIdx}>
                            Rank {c.rank}: <strong>{c.entity}</strong> (Distance {c.sentenceDistance}, agreement {String(c.agreement)})
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-secondary italic">
                No third-person pronouns requiring Hobbs antecedent proposals detected in this passage.
              </p>
            )}
          </section>

          {/* Explicit Connective Clause Arcs */}
          <section className="bg-surface-container-low p-6 lg:p-8 rounded-3xl border border-surface-container-highest flex flex-col gap-5">
            <div className="flex items-center gap-3 border-b border-surface-container-highest pb-4">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-serif font-bold text-sm">
                04
              </div>
              <div>
                <h2 className="font-headline-sm text-lg font-serif text-primary">
                  4. Explicit Connectives & Clause Graph
                </h2>
                <p className="font-body-sm text-xs text-secondary mt-0.5">
                  Rhetorical structure and semantic pivots linking adjacent clauses.
                </p>
              </div>
            </div>

            {clauseResult.relations.length > 0 ? (
              <div className="space-y-3">
                {clauseResult.relations.map((rel) => (
                  <div key={rel.id} className="p-4 bg-surface-container-lowest rounded-2xl border border-surface-container-highest flex flex-col gap-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-primary">
                        [{rel.cue}] • {rel.type}
                      </span>
                      <span className="font-mono text-[10px] text-secondary">
                        {rel.source} → {rel.target}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-[11px] text-secondary pt-1">
                      <div className="p-2 rounded-lg bg-surface-container">
                        <strong>Source:</strong> "{clauseResult.clauses.find((c) => c.id === rel.source)?.text}"
                      </div>
                      <div className="p-2 rounded-lg bg-surface-container">
                        <strong>Target:</strong> "{clauseResult.clauses.find((c) => c.id === rel.target)?.text}"
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-secondary italic">
                No explicit coordinating or subordinating connectives found. Sentences stand in paratactic stillness.
              </p>
            )}
          </section>
        </div>

        {/* 5. Memory Evolver & Strict Context Cross-Referencing Gate */}
        <section className="bg-surface-container-low p-6 lg:p-8 rounded-3xl border border-surface-container-highest flex flex-col gap-6">
          <div className="flex items-center justify-between border-b border-surface-container-highest pb-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center text-primary font-serif font-bold text-sm">
                05
              </div>
              <div>
                <h2 className="font-headline-sm text-xl font-serif text-primary">
                  5. The Memory Evolver & Sovereign Consecration
                </h2>
                <p className="font-body-sm text-xs text-secondary mt-0.5">
                  How pivotal centering moments become sovereign memory cairns, and how future conversations reference them.
                </p>
              </div>
            </div>
            <span className="px-3 py-1 rounded-full bg-surface-container border border-surface-container-highest text-secondary text-xs">
              Opt-in Sovereign Consent
            </span>
          </div>

          {evolvedCandidate ? (
            <div className="p-6 rounded-2xl bg-surface-container-lowest border border-outline-variant/50 flex flex-col md:flex-row items-start justify-between gap-6">
              <div className="flex flex-col gap-2 max-w-2xl">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-lichen"></span>
                  <span className="font-label-sm text-xs text-secondary uppercase font-semibold">
                    Crystallized Candidate Moment
                  </span>
                </div>
                <h3 className="font-headline-sm text-xl font-serif text-primary">
                  {evolvedCandidate.title}
                </h3>
                <p className="font-body-md text-sm sm:text-base text-on-surface italic font-serif">
                  "{evolvedCandidate.quote}"
                </p>
                <p className="font-body-sm text-xs text-secondary">
                  {evolvedCandidate.context}
                </p>
              </div>

              <div className="flex flex-col gap-3 shrink-0 p-4 rounded-xl bg-surface-container text-xs">
                <div className="flex items-center justify-between gap-4">
                  <span className="text-secondary">Center Entity:</span>
                  <span className="font-semibold text-primary">{evolvedCandidate.centerEntity}</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span className="text-secondary">Cairn Weight:</span>
                  <span className="font-semibold text-primary">{evolvedCandidate.stoneCount} stones</span>
                </div>
                <div className="flex items-center justify-between gap-4">
                  <span className="text-secondary">Transition:</span>
                  <span className="font-semibold text-secondary">{evolvedCandidate.transition}</span>
                </div>
              </div>
            </div>
          ) : null}

          {/* Cross-Session Integration Policy Callout */}
          <div className="p-5 rounded-2xl bg-[#E8EDE5]/70 border border-[#CBD3C6] flex flex-col gap-2 text-xs sm:text-sm text-primary leading-relaxed">
            <div className="flex items-center gap-2 font-semibold">
              <span className="material-symbols-outlined text-base">psychology</span>
              <span>The Strict Memory Integration Gate:</span>
            </div>
            <p>
              In future conversations, Sanctuary evaluates new user sentences against existing sovereign memories.
              <strong> Sanctuary will NEVER force memories into the response indiscriminately.</strong> A past memory is ONLY integrated if the semantic context matches AND the historical distinction adds genuine reflective value. If context is different or memory adds no clarity, Sanctuary gracefully abstains.
            </p>
          </div>
        </section>

      </div>
    </div>
  );
}
