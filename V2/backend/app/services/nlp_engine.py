"""Pure, versioned text analysis. No DB, provider, or snapshot mutation."""
from __future__ import annotations

import copy
import hashlib
import hmac
import math
import re
import threading
import unicodedata
from functools import lru_cache

import numpy as np
import spacy
from sklearn.feature_extraction.text import HashingVectorizer
from spacy.matcher import PhraseMatcher
from spacy.symbols import ORTH, PROPN
from spacy.language import Language

from app.services.privacy import EMAIL_RE, PHONE_RE, URL_RE, DATE_RE, strip_identifiers

VERSION = "sanctuary.nlp.v2"
FEATURES = ["entity_continuity", "connective_density", "hedge_density", "topic_novelty"]
HEDGES = ["maybe", "perhaps", "probably", "possibly", "I think", "I guess", "I suppose", "not sure", "kind of", "sort of"]
STRATEGIES = {
    "closure": "Reflect the expressed completion in one brief sentence.",
    "insufficient": "Acknowledge the brief expression without adding a new interpretation.",
    "correction": "Reflect the user's explicit correction, treating the current wording as authoritative and not repeating the superseded framing.",
    "contrast": "Reflect the two stated contrasting clauses together in one grounded observation.",
    "recurring": "Reflect the repeated topic using only the supplied user evidence.",
    "explanation": "Reflect the explicitly stated explanation without introducing another cause.",
    "standard": "Reflect the expressed experience with concise grounded wording.",
}
FALLBACKS = {
    "closure": "This feels like a place to pause for now.",
    "insufficient": "There is space for what you have expressed here.",
    "correction": "Your current clarification takes precedence over the earlier framing.",
    "contrast": "Two different parts of this experience sit alongside each other.",
    "recurring": "This topic has appeared across several of your reflections.",
    "explanation": "You have connected what happened with the reason you described.",
    "standard": "You have put part of this experience into words.",
}
# POS/dependency gating and orientation are checked in alongside the implementation.
CUE_RULES = {
    "because": {"relation": "cause", "deps": ["mark"], "pos": ["SCONJ"], "orientation": "arg2_to_arg1"},
    "since": {"relation": "cause", "deps": ["mark"], "pos": ["SCONJ"], "orientation": "arg2_to_arg1"},
    "if": {"relation": "condition", "deps": ["mark"], "pos": ["SCONJ"], "orientation": "arg2_to_arg1"},
    "although": {"relation": "contrast", "deps": ["mark"], "pos": ["SCONJ"], "orientation": "symmetric"},
    "but": {"relation": "contrast", "deps": ["cc"], "pos": ["CCONJ"], "orientation": "symmetric"},
    "however": {"relation": "contrast", "deps": ["advmod"], "pos": ["ADV"], "orientation": "symmetric"},
    "therefore": {"relation": "result", "deps": ["advmod"], "pos": ["ADV"], "orientation": "arg1_to_arg2"},
    "so": {"relation": "result", "deps": ["cc", "advmod", "mark"], "pos": ["CCONJ", "SCONJ", "ADV"], "orientation": "arg1_to_arg2"},
    "while": {"relation": "temporal", "deps": ["mark"], "pos": ["SCONJ"], "orientation": "symmetric"},
    "after": {"relation": "temporal", "deps": ["mark"], "pos": ["SCONJ"], "orientation": "arg2_to_arg1"},
    "before": {"relation": "temporal", "deps": ["mark"], "pos": ["SCONJ"], "orientation": "arg1_to_arg2"},
    "then": {"relation": "temporal", "deps": ["advmod"], "pos": ["ADV"], "orientation": "arg1_to_arg2"},
    "for example": {"relation": "example", "deps": ["prep"], "pos": ["ADP"], "orientation": "arg1_to_arg2"},
    "in particular": {"relation": "example", "deps": ["prep"], "pos": ["ADP"], "orientation": "arg1_to_arg2"},
}
_PARSE_LOCK = threading.RLock()


@Language.component("anonymous_entity_tags")
def anonymous_entity_tags(doc):
    for token in doc:
        if re.fullmatch(r"\[entity_e\d+\]", token.text):
            token.pos = PROPN
            token.tag = doc.vocab.strings.add("NNP")
            token.lemma = doc.vocab.strings.add(token.text)
    return doc


@lru_cache(maxsize=1)
def pipeline():
    try:
        nlp = spacy.load("en_core_web_sm")
        nlp.add_pipe("anonymous_entity_tags", before="parser")
        return nlp, f"en_core_web_sm:{nlp.meta['version']}", None
    except OSError:
        nlp = spacy.blank("en")
        nlp.add_pipe("sentencizer")
        return nlp, "sentence_fallback", "dependency_model_unavailable"


def canonical(surface):
    return re.sub(r"['’]s$", "", " ".join(unicodedata.normalize("NFKC", surface).casefold().split()))


def alias_hash(surface, key):
    return hmac.new(key.encode(), canonical(surface).encode(), hashlib.sha256).hexdigest()


def redact(text, entities, key):
    """Return redacted spans; surface mappings/coordinate map never enter state delta."""
    nlp, _, _ = pipeline()
    with _PARSE_LOCK:
        doc = nlp(text)
    spans = []
    for regex, kind in [(EMAIL_RE, "EMAIL"), (PHONE_RE, "PHONE"), (URL_RE, "URL"), (DATE_RE, "DATE"), (re.compile(r"@\w+"), "HANDLE")]:
        spans.extend((m.start(), m.end(), kind) for m in regex.finditer(text))
    spans.extend((e.start_char, e.end_char, e.label_) for e in doc.ents if e.label_ in {"PERSON", "ORG", "GPE", "LOC", "FAC", "NORP"})
    # Prefer structured regex and longest span at a shared start; reject overlaps.
    selected = []
    for start, end, kind in sorted(spans, key=lambda s: (s[0], -(s[1] - s[0]))):
        if not selected or start >= selected[-1][1]:
            selected.append((start, end, kind))
    registry = copy.deepcopy(entities)
    mapping, segments, mentions, chunks = {}, [], [], []
    cursor = offset = 0
    for start, end, kind in selected:
        if start > cursor:
            chunks.append(text[cursor:start])
            segments.append({"original": [cursor, start], "redacted": [offset, offset + start - cursor], "replacement": False})
            offset += start - cursor
        surface = text[start:end]
        # A unique known PERSON alias may override a model's NORP misclassification.
        if kind == "NORP" and len(canonical(surface).split()) == 1:
            known = [e for e in registry if e["kind"] == "PERSON" and alias_hash(surface, key) in e["aliases"]]
            if len(known) == 1:
                kind = "PERSON"
        exact = alias_hash(surface, key)
        words = canonical(surface).split()
        aliases = sorted({exact, *(alias_hash(w, key) for w in words if kind == "PERSON")})
        matches = [e for e in registry if e["kind"] == kind and exact == e["exact_hash"]]
        if not matches and kind == "PERSON":
            # Only partial-to-full matching; shared first names never merge two full names.
            matches = [e for e in registry if e["kind"] == kind and (len(words) == 1 or e["name_tokens"] == 1) and set(aliases).intersection(e["aliases"])]
        if len(matches) == 1:
            entity = matches[0]
            entity["aliases"] = sorted(set(entity["aliases"] + aliases))
            if len(words) > entity["name_tokens"]:
                entity["name_tokens"], entity["exact_hash"] = len(words), exact
        else:
            next_id=max((int(e['id'][1:]) for e in registry),default=0)+1
            entity = {"id": f"e{next_id:06d}", "kind": kind, "exact_hash": exact, "aliases": aliases, "name_tokens": len(words)}
            registry.append(entity)
        token = f"[entity_{entity['id']}]"
        chunks.append(token)
        mapping[token] = surface
        mentions.append({"entity_id": entity["id"], "kind": kind, "span": [offset, offset + len(token)]})
        segments.append({"original": [start, end], "redacted": [offset, offset + len(token)], "replacement": True})
        offset += len(token)
        cursor = end
    chunks.append(text[cursor:])
    if cursor < len(text):
        segments.append({"original": [cursor, len(text)], "redacted": [offset, offset + len(text) - cursor], "replacement": False})
    return "".join(chunks), registry, mentions, {"mapping": mapping, "offset_map": segments}


def parse(text):
    nlp, backend, reason = pipeline()
    with _PARSE_LOCK:
        for token in sorted(set(re.findall(r"\[entity_e\d+\]", text))):
            nlp.tokenizer.add_special_case(token, [{ORTH: token}])
        doc = nlp(text)
        for token in doc:
            if re.fullmatch(r"\[entity_e\d+\]", token.text):
                token.pos = PROPN
    return doc, backend, reason


def clause_graph(doc, fallback):
    clauses, token_owner, head_ids = [], {}, {}
    for sentence_index, sentence in enumerate(doc.sents):
        if fallback:
            heads = [sentence[0]]
        else:
            heads = [t for t in sentence if t.dep_ == "ROOT" or t.dep_ in {"advcl", "ccomp", "relcl", "parataxis"} or (t.dep_ == "conj" and t.pos_ in {"VERB", "AUX"})]
            heads = heads or [sentence.root]
        heads = sorted(heads, key=lambda t: t.i)
        head_set = {h.i for h in heads}
        for head in heads:
            cid = f"c{len(clauses)}"
            head_ids[head.i] = cid
            tokens = list(sentence) if fallback else []
            # Ownership is determined by nearest clause ancestor, retaining discontiguous spans.
            if not fallback:
                tokens = []
                for t in sentence:
                    ancestry = [t, *t.ancestors]
                    nearest = next((a for a in ancestry if a.i in head_set), None)
                    if nearest is not None and nearest.i == head.i:
                        tokens.append(t)
            spans = []
            for t in sorted(tokens, key=lambda t: t.i):
                token_owner[t.i] = cid
                if spans and (not doc.text[spans[-1][1]:t.idx] or doc.text[spans[-1][1]:t.idx].isspace()):
                    spans[-1][1] = t.idx + len(t)
                else:
                    spans.append([t.idx, t.idx + len(t)])
            if spans:
                clauses.append({"id": cid, "sentence": sentence_index, "head": head.i, "spans": spans, "text": " … ".join(doc.text[a:b] for a, b in spans)})
    edges = []
    if fallback:
        return clauses, edges
    for t in doc:
        cue = t.lower_
        if cue in {"for", "in"} and t.i + 1 < len(doc):
            cue = f"{cue} {doc[t.i + 1].lower_}"
        rule = CUE_RULES.get(cue)
        if not rule or t.dep_ not in rule["deps"] or t.pos_ not in rule["pos"]:
            continue
        owner = token_owner.get(t.i)
        arg2, arg1 = owner, None
        clause = next((c for c in clauses if c["id"] == owner), None)
        if not clause:
            continue
        if t.dep_ == "mark":
            if t.head.dep_ != "advcl" or t.head.pos_ not in {"VERB", "AUX"}:
                continue
            if cue == "since":  # temporal since is deliberately not guessed.
                continue
            arg2 = head_ids.get(t.head.i)
            arg1 = token_owner.get(t.head.head.i)
        elif cue in {"but", "so"}:
            right = next((c for c in clauses if c["sentence"] == clause["sentence"] and c["head"] > t.i), None)
            if not right or doc[right["head"]].dep_ != "conj":
                continue
            arg2 = right["id"]
            arg1 = token_owner.get(doc[right["head"]].head.i)
        else:
            # Sentence-initial discourse adverbial/example, with preceding sentence evidence.
            preceding = [c for c in clauses if c["sentence"] == clause["sentence"] - 1]
            first = min((a for c in clauses if c["sentence"] == clause["sentence"] for a, _ in c["spans"]), default=0)
            if not preceding or t.idx - first > 3:
                continue
            arg1 = preceding[-1]["id"]
        if not arg1 or not arg2 or arg1 == arg2:
            continue
        reverse = rule["orientation"] == "arg2_to_arg1"
        cue_end = doc[t.i + 1].idx + len(doc[t.i + 1]) if " " in cue else t.idx + len(t)
        edges.append({"id": f"r{len(edges)}", "cue": cue, "cue_span": [t.idx, cue_end], "relation": rule["relation"], "arg1": arg1, "arg2": arg2, "source": arg2 if reverse else arg1, "target": arg1 if reverse else arg2, "symmetric": rule["orientation"] == "symmetric"})
    return clauses, edges


def vector(lemmas):
    h = HashingVectorizer(n_features=16384, alternate_sign=False, norm=None, lowercase=False, tokenizer=str.split, token_pattern=None, dtype=np.float64)
    v = h.transform([" ".join(lemmas)]).toarray()[0]
    norm = np.linalg.norm(v)
    return {str(i): float(v[i] / norm) for i in np.flatnonzero(v)} if norm else {}


def cosine(a, b):
    denominator = math.sqrt(sum(v*v for v in a.values()) * sum(v*v for v in b.values()))
    return min(1., max(0., sum(v * b.get(k, 0.) for k, v in a.items()) / denominator)) if denominator else 0.


def _map_original_span(span, segments):
    """Map a raw-text span into canonical redacted coordinates."""
    start, end = span
    mapped = []
    for segment in segments:
        original_start, original_end = segment["original"]
        redacted_start, redacted_end = segment["redacted"]
        overlap_start, overlap_end = max(start, original_start), min(end, original_end)
        if overlap_start >= overlap_end:
            continue
        if segment["replacement"]:
            candidate = [redacted_start, redacted_end]
        else:
            candidate = [redacted_start + overlap_start - original_start, redacted_start + overlap_end - original_start]
        if mapped and candidate[0] <= mapped[-1][1]:
            mapped[-1][1] = max(mapped[-1][1], candidate[1])
        else:
            mapped.append(candidate)
    return mapped


def _canonicalize_local_structure(redacted, clauses, edges, hedge_spans, lesk_result, segments, private_spans):
    """Remove raw coordinates and surface forms before analysis leaves the request."""
    canonical_clauses = []
    for clause in clauses:
        spans = []
        for span in clause["spans"]:
            spans.extend(_map_original_span(span, segments))
        spans = [span for i, span in enumerate(spans) if not i or span != spans[i-1]]
        if spans:
            canonical_clauses.append({**clause, "spans": spans, "text": " … ".join(redacted[a:b] for a, b in spans)})
    valid_ids = {clause["id"] for clause in canonical_clauses}
    canonical_edges = []
    for edge in edges:
        mapped = _map_original_span(edge["cue_span"], segments)
        if mapped and edge["arg1"] in valid_ids and edge["arg2"] in valid_ids:
            canonical_edges.append({**edge, "cue_span": mapped[0]})
    canonical_hedges = [mapped[0] for span in hedge_spans if (mapped := _map_original_span(span, segments))]
    if lesk_result.get("status") == "ready":
        senses = []
        for sense in lesk_result.get("senses", []):
            if any(sense["span"][0] < end and start < sense["span"][1] for start, end in private_spans):
                continue
            mapped = _map_original_span(sense["span"], segments)
            if mapped:
                senses.append({**sense, "span": mapped[0]})
        lesk_result = {**lesk_result, "senses": senses}
    return canonical_clauses, canonical_edges, sorted(canonical_hedges), lesk_result


def _sanitize_dmrst(result, placeholder_mapping):
    """DMRST may inspect raw text locally; its returned EDU strings must not retain it."""
    if result.get("status") != "ready":
        return result
    cleaned = copy.deepcopy(result)
    replacements = sorted(placeholder_mapping.items(), key=lambda item: -len(item[1]))
    for edu in cleaned.get("edus", []):
        value = edu.get("text", "")
        for placeholder, surface in replacements:
            value = value.replace(surface, placeholder)
        edu["text"] = strip_identifiers(value)
    return cleaned


def _scrub_ephemeral_surfaces(value, placeholder_mapping):
    """Defense in depth: remove raw identifier fragments from outward model diagnostics."""
    if isinstance(value, dict):
        return {key: _scrub_ephemeral_surfaces(item, placeholder_mapping) for key, item in value.items()}
    if isinstance(value, list):
        return [_scrub_ephemeral_surfaces(item, placeholder_mapping) for item in value]
    if not isinstance(value, str):
        return value
    cleaned = value
    for placeholder, surface in sorted(placeholder_mapping.items(), key=lambda item: -len(item[1])):
        variants = [surface, *(token for token in re.findall(r"[\w'-]+", surface, re.UNICODE) if len(token) >= 3)]
        for variant in sorted(set(variants), key=len, reverse=True):
            cleaned = re.sub(re.escape(variant), placeholder, cleaned, flags=re.IGNORECASE)
    return cleaned


def filtered(observations, denominators, prior=None):
    q = np.array([.01, .01, .0001, .01], dtype=np.float64)
    x = np.array(prior["x"] if prior else [0.] * 4, dtype=np.float64)
    p = np.array(prior["P"] if prior else np.eye(4), dtype=np.float64)
    initialized = list(prior["initialized"] if prior else [False] * 4)
    if prior:
        p = p + np.diag(q)
    observed, variance = [], []
    for i, z in enumerate(observations):
        if z is None:
            continue
        if not initialized[i]:
            x[i], initialized[i] = z, True
        else:
            observed.append(i)
            variance.append((1. / max(1, denominators[i]) if i == 3 else z*(1-z)/max(1, denominators[i])) + 1e-4)
    if observed:
        h = np.eye(4)[observed]
        r = np.diag(variance)
        gain = np.linalg.solve(h @ p @ h.T + r, h @ p).T
        x = x + gain @ (np.array([observations[i] for i in observed]) - h @ x)
        residual = np.eye(4) - gain @ h
        p = residual @ p @ residual.T + gain @ r @ gain.T
    p = (p + p.T) / 2
    return {"x": x.tolist(), "P": p.tolist(), "initialized": initialized, "observation_mask": [v is not None for v in observations], "parameter_version": "kalman.v1"}


def rank_turns(turns):
    eligible = [t for t in turns if t.get("topic_id") and t.get("vector")]
    n = len(eligible)
    if not n:
        return []
    weights = np.array([[cosine(a["vector"], b["vector"]) if i != j else 0. for j, b in enumerate(eligible)] for i, a in enumerate(eligible)], dtype=np.float64)
    sums = weights.sum(axis=1)
    transition = np.array([row/s if s else np.ones(n)/n for row, s in zip(weights, sums)])
    scores = np.ones(n)/n
    for _ in range(200):
        updated = .15/n + .85 * transition.T @ scores
        if np.max(np.abs(updated-scores)) < 1e-8:
            scores = updated
            break
        scores = updated
    topics = sorted({t["topic_id"] for t in eligible}, key=lambda k: (-sum(t["topic_id"] == k for t in eligible), k))[:3]
    selected = []
    for topic in topics:
        index = min((i for i,t in enumerate(eligible) if t["topic_id"] == topic), key=lambda i: (-scores[i], eligible[i]["turn_index"]))
        t = eligible[index]
        selected.append({"turn_index": t["turn_index"], "text": t["text"], "topic_id": topic, "centrality": float(scores[index])})
    return sorted(selected, key=lambda t: t["turn_index"])


def response_evidence(text, has_prior, prior_similarity):
    """Select one current-turn sentence as auditable response evidence."""
    sentences=[]
    for match in re.finditer(r"[^.!?]+[.!?]?",text):
        start,end=match.span()
        while start<end and text[start].isspace():start+=1
        while end>start and text[end-1].isspace():end-=1
        if start<end:sentences.append([start,end])
    correction_match = re.search(
        r"(?:^|[.!?]\s+)(actually\b|i\s+(?:do\s+not|don't)\s+think\b|rather\b|instead\b|"
        r"looking\s+at\s+it\s+again\b|that\s+changes\s+how\s+i\s+see\s+it\b|"
        r"you\s+keep\s+making\s+this\s+sound\s+like\b|i\s+(?:have\s+not|haven't)\s+said\b)",
        text,
        re.I,
    ) if has_prior else None
    cue=correction_match.group(1).casefold() if correction_match else ""
    # "I don't think" can be a fresh belief rather than a correction. Require
    # lexical continuity for that weaker cue; explicit revision markers stand
    # on their own when a prior turn exists.
    weak_cue = bool(re.fullmatch(r"i\s+(?:do\s+not|don't)\s+think", cue))
    detected=bool(correction_match and (not weak_cue or prior_similarity>=.30))
    correction = {
        "detected": detected,
        "cue_span": list(correction_match.span(1)) if detected else None,
        "prior_turn_similarity": prior_similarity if has_prior else None,
    }
    if not sentences:
        return correction, None
    # The final complete statement is the safest extractive representation of
    # the user's current emphasis, especially after an explicit correction.
    span=sentences[-1]
    evidence={"kind":"current_turn_sentence","span":span,"text":text[span[0]:span[1]]}
    return correction,evidence


def analyze_turn(text, state_snapshot=None, config=None):
    state = copy.deepcopy(state_snapshot or {})
    config = config or {}
    if not config.get("alias_key"):
        raise ValueError("alias_key is required")
    redacted, entities, mentions, ephemeral = redact(text, state.get("entities", []), config["alias_key"])
    local_unredacted = bool(config.get("local_unredacted", False))
    safe_doc, safe_backend, safe_reason = parse(redacted)
    doc, backend, reason = parse(text) if local_unredacted else (safe_doc, safe_backend, safe_reason)
    private_spans = [segment["original"] for segment in ephemeral["offset_map"] if segment["replacement"]]
    clauses, edges = clause_graph(doc, reason is not None)
    content = [t.lemma_.lower() or t.lower_ for t in doc if t.is_alpha and not t.is_stop and t.pos_ not in {"DET", "PRON", "AUX", "PART"}
               and not any(t.idx < end and start < t.idx + len(t) for start, end in private_spans)]
    lexical = [t for t in doc if t.is_alpha]
    v = vector(content)
    turns, topics = state.get("turns", []), state.get("topics", [])
    turn_index = len(turns) + 1
    topic_id, prior_count = None, 0
    if len(content) >= config.get("min_content_tokens", 4) and v:
        best = min(topics, key=lambda t: (-cosine(v, t["sum"]), t["id"])) if topics else None
        if best and cosine(v, best["sum"]) >= config.get("topic_threshold", .55):
            topic_id, prior_count = best["id"], best["count"]
            for k, value in v.items():
                best["sum"][k] = best["sum"].get(k, 0.) + value
            best["count"] += 1
        else:
            topic_id = f"t{len(topics)+1:06d}"
            topics.append({"id": topic_id, "sum": dict(v), "count": 1})
    comparable = [t for t in turns if t.get("vector") and t.get("topic_id")]
    novelty = 1-max(cosine(v, t["vector"]) for t in comparable) if comparable and topic_id else None
    ids = sorted({m["entity_id"] for m in mentions})
    continuity = len(set(ids).intersection(turns[-1].get("entities", [])))/len(ids) if turns and ids else None
    participating = {e[k] for e in edges for k in ["arg1", "arg2"]}
    density = len(participating)/len(clauses) if clauses else None
    nlp, _, _ = pipeline()
    matcher = PhraseMatcher(nlp.vocab, attr="LEMMA" if not reason else "LOWER")
    with _PARSE_LOCK:
        matcher.add("hedges", [nlp(h) for h in HEDGES])
    matches, occupied = [], set()
    for _, start, end in sorted(matcher(doc), key=lambda m: (-(m[2]-m[1]), m[1])):
        if not occupied.intersection(range(start, end)):
            matches.append([doc[start].idx, doc[end-1].idx + len(doc[end-1])])
            occupied.update(range(start, end))
    hedge = min(1., len(matches)/len(lexical)) if lexical else None
    obs = [continuity, density, hedge, novelty]
    posterior = filtered(obs, [len(ids), len(clauses), len(lexical), len(content)], state.get("posterior"))
    closure = re.fullmatch(r"(?:thank you|we can (?:stop|pause) here|that is enough for now)[.!\s]*", text.strip(), re.I)
    prior_similarity=cosine(v,turns[-1].get("vector",{})) if turns and v else 0.
    correction,response_span=response_evidence(redacted,bool(turns),prior_similarity)
    correction["supersedes_turn"] = turns[-1]["turn_index"] if correction["detected"] else None
    strategy = "closure" if closure else "insufficient" if len(content) < 4 else "correction" if correction["detected"] else "contrast" if any(e["relation"] == "contrast" for e in edges) else "recurring" if prior_count >= 2 else "explanation" if any(e["relation"] in {"cause", "result"} for e in edges) else "standard"
    evidence = {"content_tokens": len(content), "prior_topic_turns": prior_count, "relation_ids": [e["id"] for e in edges], "closure": bool(closure), "correction": correction}
    current = {"turn_index": turn_index, "text": redacted, "vector": v, "topic_id": topic_id, "entities": ids, "correction_of_turn": correction["supersedes_turn"]}
    all_turns = turns + [current]
    window = [t["topic_id"] for t in all_turns if t.get("topic_id")][-10:]
    counts = {k: window.count(k) for k in sorted(set(window))}
    entropy = -sum((n/len(window))*math.log(n/len(window)) for n in counts.values())/math.log(len(counts)) if len(counts) > 1 else None
    from app.services.classical_nlp import lesk, discourse_entities
    from app.services.dmrst import parse_dmrst
    from app.services.pwm import update_world
    from app.services.memory_tools import retrieve_scenes
    local_lesk = lesk(doc)
    if local_unredacted:
        clauses, edges, matches, local_lesk = _canonicalize_local_structure(
            redacted, clauses, edges, matches, local_lesk, ephemeral["offset_map"], private_spans
        )
    from app.services.discourse_context import build_discourse_context
    discourse_context, discourse_state = build_discourse_context(
        redacted,
        safe_doc,
        clauses,
        correction,
        turn_index,
        state.get("discourse_state"),
    )
    working=copy.deepcopy(state.get("working_interpretation"))
    if response_span and len(content)>=4:
        working={"status":"user_stated","source_turn":turn_index,"evidence":response_span,"supersedes_turn":correction["supersedes_turn"]}
    result = {"schema_version": VERSION, "coordinate_system": "redacted_half_open", "vectorizer_version": "hash16384.unit.v1", "model_version": backend, "parser_fallback": reason, "redacted_text": redacted, "local_processing_mode": "unredacted_transient" if local_unredacted else "redacted", "local_processing_scope": ["dependency_parse", "clause_relations", "lexical_features", "lesk", "dmrst"] if local_unredacted else [], "mentions": mentions, "clauses": clauses, "relations": edges, "topic_id": topic_id, "topics": [{"id": t["id"], "count": t["count"]} for t in topics], "topic_entropy": entropy, "hedge_spans": sorted(matches), "features": dict(zip(FEATURES, obs)), "posterior": posterior, "strategy": strategy, "strategy_evidence": evidence, "response_evidence":response_span, "working_interpretation":working, "summary_turns": rank_turns(all_turns), "discourse_context": discourse_context}
    delta = {"entities": entities, "topics": topics, "turns": all_turns, "posterior": posterior, "working_interpretation":working, "discourse_state": discourse_state}
    result['lesk']=local_lesk
    classical, hobbs_history=discourse_entities(safe_doc,mentions,state.get('centering_trace',[]),state.get('hobbs_history',[]),result['lesk'])
    result.update(classical)
    dmrst = parse_dmrst(text if local_unredacted else redacted)
    result['dmrst']=_sanitize_dmrst(dmrst,ephemeral['mapping']) if local_unredacted else dmrst
    result['memory_retrieval']=retrieve_scenes(v,state.get('world'))
    result['pwm'],delta['world']=update_world(safe_doc,result,delta,state.get('world'))
    delta['centering_trace']=(state.get('centering_trace',[])+result['centering']['trace'])[-50:]
    delta['hobbs_history']=hobbs_history
    delta['world_revision']=state.get('world_revision',0)
    from app.services.mathematical_models import run_mathematical_suite
    mathematical, mathematical_state = run_mathematical_suite(
        redacted,
        clauses,
        edges,
        result['features'],
        [len(ids), len(clauses), len(lexical), len(content)],
        correction,
        strategy,
        state.get('mathematical_state'),
        config.get('mathematical_profile', 'balanced'),
        config.get('mathematical_overrides'),
    )
    result['mathematical_models']=mathematical
    delta['mathematical_state']=mathematical_state
    from app.services.revision_classifier import classify_revision
    result['revision_classifier'] = classify_revision(
        redacted,
        turns[-1].get('text') if turns else None,
    )
    from app.services.narrative_engine import NarrativeEngine
    from app.models.schemas import NarrativeStructure
    prior_ssm = [NarrativeStructure.model_validate(item) for item in state.get('ssm_history', [])]
    structure = NarrativeEngine().distill_turn(redacted, prior_ssm)
    result['situational_structure'] = structure.model_dump()
    from app.services.ssm_constraints import constraint_observations, VERSION as CONSTRAINT_VERSION
    constraint_values, constraint_evidence = constraint_observations(redacted)
    result['situational_structure']['constraints'] = constraint_values
    result['ssm_metadata'] = {'version': 'ssm.v2', 'scope': 'current_session',
                              'method': 'conservative_lexical_rules', 'validated': False,
                              'confidence_score_kind': 'legacy_heuristic_not_probability',
                              'constraint_scale': 'self_rating_or_ordinal_engineering_score',
                              'constraint_version': CONSTRAINT_VERSION, 'constraint_evidence': constraint_evidence}
    delta['ssm_history'] = (state.get('ssm_history', []) + [result['situational_structure']])[-50:]
    if local_unredacted:
        result = _scrub_ephemeral_surfaces(result, ephemeral["mapping"])
    return result, delta, ephemeral
