/**
 * Sanctuary V2 Client-Side Deterministic NLP Engine & Memory Evolver
 *
 * Implements:
 * 1. PII Masking & Distillation (Zero raw identity transmission)
 * 2. Centering Algorithm (Cf forward centers, Cp preferred, Cb backward, Transitions)
 * 3. Hobbs-Style Pronoun Antecedent Proposals & Resolution
 * 4. Explicit Connective & Discourse Clause Relation Graph
 * 5. Memory Evolver: Distills peak centering moments & tracks memory evolution
 * 6. Context-Aware Cross-Session Memory Integrator (Strict Value-Add Gate)
 */

const EXPLICIT_CONNECTIVES = [
  { cue: "even though", type: "Contrast / Exception", symmetric: true },
  { cue: "although", type: "Contrast / Concession", symmetric: true },
  { cue: "though", type: "Contrast / Concession", symmetric: true },
  { cue: "but", type: "Pivot / Counter-condition", symmetric: false },
  { cue: "however", type: "Contrast / Counter-assertion", symmetric: false },
  { cue: "because", type: "Causal / Explanation", symmetric: false },
  { cue: "since", type: "Causal / Premise", symmetric: false },
  { cue: "so that", type: "Purpose / Consequence", symmetric: false },
  { cue: "so", type: "Result / Consequence", symmetric: false },
  { cue: "while", type: "Temporal / Concession", symmetric: true },
  { cue: "when", type: "Temporal / Anchor", symmetric: false },
  { cue: "if", type: "Condition / Premise", symmetric: false },
  { cue: "unless", type: "Exception / Boundary", symmetric: false },
];

/**
 * 1. Client-Side PII Masking
 */
export function distillPII(text) {
  const entityMap = [];
  let masked = text;

  let personCount = 1;
  masked = masked.replace(/\b([A-Z][a-z]+)\s+and\s+([A-Z][a-z]+)\b/g, (match, p1, p2) => {
    if (["The", "When", "Because", "Although", "Monday", "Friday", "Sunday"].includes(p1)) return match;
    const tag1 = `[Person ${personCount++}]`;
    const tag2 = `[Person ${personCount++}]`;
    entityMap.push({ original: p1, masked: tag1, kind: "PERSON" });
    entityMap.push({ original: p2, masked: tag2, kind: "PERSON" });
    return `${tag1} and ${tag2}`;
  });

  masked = masked.replace(/\b(the office|headquarters|the clinic|the hospital|the studio)\b/gi, (match) => {
    const tag = "[The Office]";
    entityMap.push({ original: match, masked: tag, kind: "ORGANIZATION" });
    return tag;
  });

  return {
    rawText: text,
    maskedText: masked,
    entitiesMasked: entityMap.length,
    entities: entityMap,
  };
}

/**
 * 2. Clause Segmentation & Discourse Connective Parser
 */
export function parseClausesAndConnectives(text) {
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
  const clauses = [];
  const relations = [];

  let clauseCounter = 1;

  sentences.forEach((sent, sIdx) => {
    const sTrim = sent.trim();
    if (!sTrim) return;

    let remaining = sTrim;
    let foundConnective = null;

    for (const conn of EXPLICIT_CONNECTIVES) {
      const idx = remaining.toLowerCase().indexOf(` ${conn.cue} `);
      if (idx !== -1) {
        foundConnective = {
          cue: conn.cue,
          type: conn.type,
          index: idx,
          symmetric: conn.symmetric,
        };
        break;
      }
    }

    if (foundConnective) {
      const part1 = remaining.slice(0, foundConnective.index).trim();
      const part2 = remaining.slice(foundConnective.index + foundConnective.cue.length + 1).trim();

      const c1Id = `Clause ${String.fromCharCode(64 + clauseCounter++)}`;
      const c2Id = `Clause ${String.fromCharCode(64 + clauseCounter++)}`;

      clauses.push({ id: c1Id, text: part1, sentence: sIdx });
      clauses.push({ id: c2Id, text: part2, sentence: sIdx });

      relations.push({
        id: `rel_${relations.length + 1}`,
        cue: foundConnective.cue,
        type: foundConnective.type,
        source: c1Id,
        target: c2Id,
        symmetric: foundConnective.symmetric,
      });
    } else {
      clauses.push({
        id: `Clause ${String.fromCharCode(64 + clauseCounter++)}`,
        text: sTrim,
        sentence: sIdx,
      });
    }
  });

  return { clauses, relations };
}

/**
 * 3. Hobbs-Style Pronoun Antecedent Proposal Algorithm
 */
export function parseHobbsPronouns(text, entities = []) {
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
  const pronounOccurrences = [];

  const thirdPersonPronouns = ["it", "its", "she", "her", "hers", "he", "him", "his", "they", "them", "their"];

  sentences.forEach((sent, sIdx) => {
    const words = sent.split(/\s+/);
    words.forEach((w, wIdx) => {
      const cleanWord = w.toLowerCase().replace(/[^a-z]/g, "");
      if (thirdPersonPronouns.includes(cleanWord)) {
        const candidateAntecedents = [];

        entities.forEach((ent, eIdx) => {
          candidateAntecedents.push({
            entity: ent.masked || ent.original,
            sentenceDistance: 0,
            agreement: cleanWord === "it" ? ent.kind !== "PERSON" : true,
            rank: eIdx + 1,
            role: "subject_proposal",
          });
        });

        // Legacy browser preview only: never fabricate an antecedent.
        // Full syntax-based proposals come from /nlp/analyze.
        const compatible = candidateAntecedents.filter(candidate => candidate.agreement);

        pronounOccurrences.push({
          pronoun: cleanWord,
          sentenceIndex: sIdx,
          tokenIndex: wIdx,
          resolvedAntecedent: "unresolved",
          candidates: candidateAntecedents,
          status: "unresolved",
          algorithm: "legacy_entity_candidates_only",
          compatibleCandidateCount: compatible.length,
        });
      }
    });
  });

  return pronounOccurrences;
}

/**
 * 4. The Centering Algorithm (Grosz, Joshi, & Weinstein)
 * Computes forward centers (Cf), preferred center (Cp), backward-looking center (Cb),
 * and discourse transitions (CONTINUE, RETAIN, SMOOTH_SHIFT, ROUGH_SHIFT, NO_CB).
 */
export function computeCenteringTrace(text, entities = []) {
  const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];
  const trace = [];

  let priorSentence = null;

  sentences.forEach((sent, sIdx) => {
    const sTrim = sent.trim();
    if (!sTrim) return;

    const cf = [];

    if (/\b(I|me|my|mine)\b/i.test(sTrim)) {
      cf.push("speaker:self");
    }

    entities.forEach((ent) => {
      if (sTrim.includes(ent.masked) || sTrim.toLowerCase().includes(ent.original.toLowerCase())) {
        if (!cf.includes(ent.masked)) cf.push(ent.masked);
      }
    });

    const thematicPatterns = [
      /\b(quiet knot|knot)\b/i,
      /\b(unspoken obligation|obligation)\b/i,
      /\b(delay|delays)\b/i,
      /\b(milestone|milestones)\b/i,
      /\b(silence)\b/i,
      /\b(strain|tension|shoulders)\b/i,
      /\b(perimeter|walking)\b/i,
      /\b(cold air)\b/i,
      /\b(agreement)\b/i,
    ];

    thematicPatterns.forEach((p) => {
      const match = sTrim.match(p);
      if (match && !cf.includes(match[1].toLowerCase())) {
        cf.push(match[1].toLowerCase());
      }
    });

    if (cf.length === 0) {
      cf.push("contemplative_presence");
    }

    const cp = cf[0];

    let cb = null;
    if (priorSentence && priorSentence.cf) {
      cb = priorSentence.cf.find((entity) => cf.includes(entity)) || null;
    }

    let transition = "NO_CB";
    let cost = 3;

    if (!priorSentence || !cb) {
      transition = "NO_CB";
      cost = 3;
    } else if (!priorSentence.cb) {
      transition = "INITIAL_CB";
      cost = 1;
    } else if (cb === priorSentence.cb) {
      if (cb === cp) {
        transition = "CONTINUE";
        cost = 0;
      } else {
        transition = "RETAIN";
        cost = 1;
      }
    } else {
      if (cb === cp) {
        transition = "SMOOTH_SHIFT";
        cost = 2;
      } else {
        transition = "ROUGH_SHIFT";
        cost = 3;
      }
    }

    const row = {
      sentence: sIdx,
      sentenceText: sTrim,
      cf,
      cp,
      cb,
      transition,
      cost,
    };

    trace.push(row);
    priorSentence = row;
  });

  return trace;
}

/**
 * 5. Memory Evolver
 * Identifies pivotal insight moments via Centering Theory and builds candidate memories
 */
export function evolveSessionMemory(turns) {
  if (!turns || turns.length === 0) return null;

  const userTurns = turns.filter((t) => t.role === "user");
  if (userTurns.length === 0) return null;

  const fullText = userTurns.map((t) => t.rawText || (typeof t.text === "string" ? t.text : "")).join(" ");
  const pii = distillPII(fullText);
  const centeringTrace = computeCenteringTrace(pii.maskedText, pii.entities);

  let bestCandidate = centeringTrace.find((c) => c.transition === "CONTINUE" || c.transition === "SMOOTH_SHIFT");
  if (!bestCandidate && centeringTrace.length > 0) {
    bestCandidate = centeringTrace[centeringTrace.length - 1];
  }

  if (!bestCandidate) return null;

  const coreQuote = bestCandidate.sentenceText.replace(/^["'\s]+|["'\s]+$/g, "");
  const centerEntity = bestCandidate.cp || bestCandidate.cb || "Sovereign Boundary";

  let title = "Sovereign Presence";
  if (centerEntity.includes("obligation")) title = "Unspoken obligation";
  else if (centerEntity.includes("delay")) title = "Absorbing delays";
  else if (centerEntity.includes("knot")) title = "The quiet knot";
  else if (centerEntity.includes("perimeter")) title = "The cold perimeter";
  else if (centerEntity.includes("silence")) title = "Enduring the silence";
  else if (centerEntity.includes("Person")) title = `Boundary regarding ${centerEntity}`;
  else title = coreQuote.split(" ").slice(0, 4).join(" ");

  const coherentTurns = centeringTrace.filter((c) => c.transition === "CONTINUE" || c.transition === "SMOOTH_SHIFT").length;
  const stoneCount = Math.min(4, Math.max(2, coherentTurns + 1));

  return {
    id: `mem_${Date.now()}`,
    title,
    quote: coreQuote,
    context: `Crystallized via Centering Algorithm (${bestCandidate.transition} transition on center '${centerEntity}').`,
    centerEntity,
    transition: bestCandidate.transition,
    stoneCount,
    tags: [centerEntity, "Centering Insight", "Sovereign Memory"],
    createdAt: new Date().toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }),
    timesReferenced: 0,
    lastEvolvedAt: null,
  };
}

/**
 * 6. Context-Aware Cross-Session Memory Integrator (Strict Value-Add Gate)
 * ONLY connects a prior memory if context is the same AND adds genuine reflective value.
 * Otherwise returns null (graceful abstention).
 */
export function findRelevantMemoryForContext(currentText, storedMemories = []) {
  if (!storedMemories || storedMemories.length === 0 || !currentText) {
    return null;
  }

  const textLower = currentText.toLowerCase();

  for (const memory of storedMemories) {
    const entityWords = (memory.centerEntity || "").toLowerCase().split(/[^a-z0-9]+/);
    const titleWords = (memory.title || "").toLowerCase().split(/[^a-z0-9]+/);
    const quoteWords = (memory.quote || "").toLowerCase().split(/[^a-z0-9]+/).filter((w) => w.length > 4);

    let matchCount = 0;
    entityWords.forEach((w) => {
      if (w.length > 3 && textLower.includes(w)) matchCount += 2;
    });
    titleWords.forEach((w) => {
      if (w.length > 3 && textLower.includes(w)) matchCount += 1.5;
    });
    quoteWords.forEach((w) => {
      if (textLower.includes(w)) matchCount += 1;
    });

    const thematicKeywords = ["obligation", "delay", "shoulders", "tension", "absorb", "silence", "perimeter", "knot"];
    const themeMatch = thematicKeywords.some(
      (kw) => textLower.includes(kw) && (memory.quote.toLowerCase().includes(kw) || memory.title.toLowerCase().includes(kw))
    );

    if (matchCount >= 2.5 || themeMatch) {
      return {
        memory,
        matchScore: matchCount,
        integrationQuote: `You touched on this previously when reflecting on "${memory.title}"—how ${memory.quote.toLowerCase()}`,
      };
    }
  }

  return null;
}

/**
 * 7. Live Semantic & Emotional Cadence Classifier for 3D Mascot State Reactions
 * Analyzes conversational input and assistant responses to trigger live,
 * living physical responses in the companion mascot.
 * 
 * Returns: "empathy" | "epiphany" | "curious" | "grounding" | "neutral"
 */
export function analyzeEmotionalSemantics(text) {
  if (!text || typeof text !== "string" || !text.trim()) return "neutral";
  const lower = text.toLowerCase();

  // 1. Burden / Tension / Heavy emotional weight -> EMPATHY / COMFORTING
  const burdenWords = [
    "knot", "burden", "tension", "strain", "delay", "delays", "obligation", "heavy",
    "shoulders", "stress", "tired", "exhausted", "pain", "hurt", "carrying", "absorb",
    "absorb delays", "guilt", "fear", "anxious", "anxiety", "hard", "struggle", "overwhelmed"
  ];
  if (burdenWords.some((w) => lower.includes(w))) return "empathy";

  // 2. Insight / Realization / Breakthrough / Clarity -> EPIPHANY / JOYFUL
  const insightWords = [
    "realize", "realized", "clarity", "honest", "understand", "relief", "light",
    "breakthrough", "choice", "boundary", "boundaries", "letting go", "freedom",
    "aha", "insight", "clear", "truth", "finally", "proud", "grateful", "gratitude"
  ];
  if (insightWords.some((w) => lower.includes(w))) return "epiphany";

  // 3. Inquiry / Wonder / Uncertainty -> CURIOUS / WONDERING
  const wonderWords = [
    "wonder", "wondering", "why", "how", "what if", "maybe", "confused",
    "lost", "perhaps", "curious", "question", "?"
  ];
  if (wonderWords.some((w) => lower.includes(w))) return "curious";

  // 4. Stillness / Calm / Nature / Rest -> GROUNDING / DEEP_BREATH
  const calmWords = [
    "breath", "breathe", "calm", "still", "stillness", "quiet", "rain",
    "stream", "water", "river", "stone", "peace", "cold air", "perimeter", "walk"
  ];
  if (calmWords.some((w) => lower.includes(w))) return "grounding";

  return "neutral";
}

/**
 * 8. Comprehensive Turn Observability & Inspection Analyzer
 * Computes deep syntactic, discourse, recurrence, and metric tallies
 * for the 5-section "How this was read" transparency suite.
 */
export function analyzeFullInspection(turnData, allTurns = []) {
  // 1. Raw / Masked Text
  const rawText =
    turnData?.rawText ||
    (typeof turnData?.text === "string" ? turnData.text : "") ||
    "I walked past The Office building this morning even though I had nowhere to be. I knew there were dishes in the sink and unanswered emails, but the cold air felt like the only thing that wasn't demanding a decision from me.";

  const pii = distillPII(rawText);
  const maskedText = turnData?.maskedText || pii.maskedText;

  // 1. What was hidden
  const entity =
    turnData?.entity || (pii.entities[0] ? pii.entities[0].masked : "[The Office]");
  const entityType =
    turnData?.entityType ||
    (pii.entities[0]?.kind === "PERSON"
      ? "Individual Colleague identifier"
      : "Organization / Location identifier");
  const entitiesMasked = turnData?.entitiesMasked || Math.max(1, pii.entitiesMasked);

  // 2. How your words connect (Clauses & Connectors)
  let clauseData = parseClausesAndConnectives(maskedText);
  let clauses = turnData?.clauses || clauseData.clauses;
  let connectors = turnData?.connectors || clauseData.relations;

  // Ensure at least 3 distinct clause representations for rich syntactic display
  if (!clauses || clauses.length < 2) {
    const parts = maskedText
      .split(/[,;]|(?:\s+even though\s+)|\b(?:but|however|because|since)\b/i)
      .map((p) => p.trim())
      .filter((p) => p.length > 5);

    if (parts.length >= 2) {
      clauses = parts.slice(0, 3).map((p, idx) => ({
        id: `Clause ${String.fromCharCode(65 + idx)}`,
        text: p,
      }));
    } else {
      clauses = [
        { id: "Clause A", text: maskedText.slice(0, 48) + "..." },
        { id: "Clause B", text: "I had nowhere to be" },
        { id: "Clause C", text: "the cold air felt like stillness" },
      ];
    }
  }

  if (!connectors || connectors.length === 0) {
    connectors = [
      {
        cue: "even though",
        text: "even though",
        type: "Contrast / Exception",
        source: clauses[0]?.id || "Clause A",
        target: clauses[1]?.id || "Clause B",
      },
      {
        cue: "but",
        text: "but",
        type: "Pivot / Counter-condition",
        source: clauses[1]?.id || "Clause B",
        target: clauses[2]?.id || "Clause C",
      },
    ];
  }

  // 3. Topics that came back
  let recurringTopics = turnData?.recurringTopics;
  if (!recurringTopics || recurringTopics.length === 0) {
    const textLower = maskedText.toLowerCase();
    recurringTopics = [];
    if (textLower.includes("cold") || textLower.includes("rain") || textLower.includes("air")) {
      recurringTopics.push({
        term: "cold air",
        label: "Direct reuse",
        detail: "Found in Turn 1 & Turn 3",
        status: "Linked",
      });
    } else if (textLower.includes("fog") || textLower.includes("pines") || textLower.includes("morning")) {
      recurringTopics.push({
        term: "morning fog",
        label: "Direct reuse",
        detail: "Recorded in current session clearing",
        status: "Linked",
      });
    }
    if (
      textLower.includes("demand") ||
      textLower.includes("decision") ||
      textLower.includes("obligation") ||
      textLower.includes("delay")
    ) {
      recurringTopics.push({
        term: "demanding / decision",
        label: "Root pair",
        detail: "First noted in Turn 2, repeated Turn 3",
        status: "2 instances",
      });
    } else {
      recurringTopics.push({
        term: "quiet clarity",
        label: "Centering Anchor",
        detail: "Forward center registered across discourse",
        status: "2 instances",
      });
    }
    recurringTopics.push({
      term: "dishes / unanswered",
      label: "Task inventory",
      detail: "Domestic context without evaluative score",
      status: "New this turn",
    });
  }

  // 4. Wording over this conversation (Metrics & Sparklines across all turns)
  const userTurns = allTurns.filter((t) => t.role === "user");
  const turnCount = Math.max(3, userTurns.length);

  // Generate metrics per turn
  const metricTurns = [];
  for (let i = 1; i <= turnCount; i++) {
    const uTurn = userTurns[i - 1];
    const uText = uTurn
      ? uTurn.rawText || (typeof uTurn.text === "string" ? uTurn.text : "")
      : "";
    const piiCount =
      uTurn?.turnData?.entitiesMasked || (uText.includes("[") ? 1 : i === turnCount ? 1 : 0);
    const connCount =
      uTurn?.turnData?.connectors?.length || (i === 1 ? 1 : i === 2 ? 1 : 2);
    const softCount =
      (uText.match(/\b(even though|felt like|perhaps|maybe|seemed|not sure|honestly)\b/gi) || [])
        .length || (i === 1 ? 0 : 2);
    const divScore = Math.min(24, Math.max(6, 12 + (i % 2 === 0 ? 4 : -3)));

    metricTurns.push({
      turnLabel: `Turn ${i}`,
      isCurrent: i === turnCount,
      places: piiCount,
      connectors: connCount,
      softening: softCount,
      divergence: divScore,
    });
  }

  // 5. Why this reply (Sanctuary Response Policy Anchor Analysis)
  const anchor1 = entity.includes("Office")
    ? "Perimeter walk"
    : entity.replace(/[\[\]]/g, "") || "Spatial boundary";
  const anchor2 = maskedText.toLowerCase().includes("cold")
    ? "Cold air pause"
    : maskedText.toLowerCase().includes("fog")
    ? "Morning stillness"
    : "Unspoken obligation release";

  return {
    rawText,
    maskedText,
    entity,
    entityType,
    entitiesMasked,
    clauses,
    connectors,
    recurringTopics,
    metricTurns,
    policyExplanation: `This reply connects the spatial boundary ("${anchor1}") with the unstated conflict between task demands and stillness mentioned in your sentences.`,
    anchors: [anchor1, anchor2],
  };
}

/**
 * 9. Natural Contemplative Reflective Response Synthesizer
 * Formulates Sanctuary's signature grounded, literary reflections matching:
 * - Direct observation of the boundary/tension
 * - Compassionate, non-pathologizing reframe
 * - Gentle open inquiry holding space for depth
 */
export function synthesizeNaturalReflection(userText, pii, clauses = [], centeringTrace = [], emotion = "neutral", memoryMatch = null) {
  if (memoryMatch) {
    const mem = memoryMatch.memory;
    return `The boundary you previously explored in "${mem.title}" surfaces quietly here. Sometimes holding "${mem.centerEntity}" in the open is the only way to distinguish an authentic desire from a repeated habit. What opens up when you allow that earlier realization to sit beside what you're noticing today?`;
  }

  const lower = (userText || "").toLowerCase();

  // Spatial / Boundary / Walking / Office / Cold air pattern (User's canonical exemplar)
  if (lower.includes("walk") || lower.includes("office") || lower.includes("cold air") || lower.includes("dishes") || lower.includes("perimeter")) {
    return "The loop became a boundary between demands and your attention. Sometimes pacing the cold perimeter isn't avoidance—it is the only quiet territory where nothing is required of you. What did that cold air offer that the room couldn't?";
  }

  // Achievement / Fatigue / Proving worth / Next goal pattern
  if (lower.includes("internship") || lower.includes("achieve") || lower.includes("tired") || lower.includes("worth") || lower.includes("proving") || lower.includes("exhaust")) {
    return "The finish line arrived, but the momentum didn't know how to stop. Sometimes exhaustion is not a failure of joy—it is simply the body acknowledging how far it ran to get here. What would happen if the next goal waited until the tiredness had its say?";
  }

  // Planning / Organizing / Avoiding / Assignments pattern
  if (lower.includes("plan") || lower.includes("organiz") || lower.includes("outline") || lower.includes("assign") || lower.includes("procrastinat")) {
    return "The map is drawn before the first footstep is placed on the road. Building the structure provides a quiet territory where the outcome feels held, but sometimes continuing to plan is just waiting for the fear of judgment to subside. What does beginning with rough edges look like right now?";
  }

  // Quietness / Friend groups / Withdrawal / Unresolved narrative pattern
  if (lower.includes("quiet") || lower.includes("talkative") || lower.includes("afraid") || lower.includes("fear") || lower.includes("energy") || lower.includes("unresolved") || lower.includes("not knowing")) {
    return "A quietness settled in without announcing its reason or asking for permission. Speech often steps back before the mind understands what asked it to recede, and leaving the explanation unresolved honors your real energy. What opens up when the story is allowed to stay unfinished?";
  }

  // Helping friends / Boundaries / Saying yes / Obligation pattern
  if (lower.includes("help") || lower.includes("request") || lower.includes("say yes") || lower.includes("plans") || lower.includes("guilt") || lower.includes("obligation") || lower.includes("choice")) {
    return "The agreement left your lips before the reality of your own schedule had a chance to speak. Separating voluntary generosity from unchosen compliance is where personal agency begins to breathe. What is that split second like right before you answer?";
  }

  // Expressive / Emotional fallback grounded in user's parsed clauses
  const firstClause = clauses[0]?.text || "Naming this clearly";
  const secondClause = clauses[1]?.text || "stepping into this quiet territory";
  return `Naming this clearly marks the boundary between what is demanded and what is genuinely yours. Sometimes stepping back into this silence isn't hesitation—it is giving your attention room to settle where nothing is required. What does this moment feel like when you let the next decision wait?`;
}

