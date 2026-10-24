"""Local experimental mathematical models for inspectable narrative-state research.

These models produce hypotheses and diagnostics, never psychological facts.  They
are dependency-light (NumPy only), deterministic for a fixed snapshot/config,
and deliberately separate from response selection.
"""
from __future__ import annotations

import copy
import hashlib
import math
import re
from dataclasses import asdict, dataclass
from typing import Callable

import numpy as np


VERSION = "sanctuary.math.v1"
DIMENSIONS = ("entity_continuity", "connective_density", "hedge_density", "topic_novelty")
PHASES = ("event", "explanation", "contrast", "revision", "closure")
CLAUSE_LABELS = ("event", "cause", "contrast", "intention", "uncertainty", "correction")


@dataclass(frozen=True)
class MathematicalConfig:
    profile: str = "balanced"
    process_noise: tuple[float, ...] = (.01, .01, .0001, .01)
    ukf_alpha: float = .3
    ukf_beta: float = 2.
    ukf_kappa: float = 0.
    ensemble_size: int = 32
    particle_count: int = 128
    resample_ratio: float = .5
    evidence_decay: float = .98
    max_propositions: int = 128
    max_graph_nodes: int = 256


def configuration(profile: str = "balanced", overrides: dict | None = None) -> MathematicalConfig:
    presets = {
        "low_resource": dict(ensemble_size=16, particle_count=64, max_propositions=64, max_graph_nodes=128),
        "balanced": {},
        "high_fidelity": dict(ensemble_size=64, particle_count=256, max_propositions=256, max_graph_nodes=512),
        "responsive": dict(process_noise=(.02, .02, .0002, .02), ukf_alpha=.5),
        "stable": dict(process_noise=(.004, .004, .00004, .004), evidence_decay=.995),
    }
    if profile not in presets:
        raise ValueError(f"unknown mathematical profile: {profile}")
    values = {"profile": profile, **presets[profile], **(overrides or {})}
    cfg = MathematicalConfig(**values)
    if cfg.ensemble_size < 8 or cfg.particle_count < 32:
        raise ValueError("ensemble_size >= 8 and particle_count >= 32 are required")
    return cfg


def _sym(matrix: np.ndarray) -> np.ndarray:
    return (matrix + matrix.T) / 2.


def _psd(matrix: np.ndarray, floor: float = 1e-10) -> np.ndarray:
    values, vectors = np.linalg.eigh(_sym(matrix))
    return _sym((vectors * np.maximum(values, floor)) @ vectors.T)


def _sigmoid(value: np.ndarray) -> np.ndarray:
    clipped = np.clip(value, -30., 30.)
    return 1. / (1. + np.exp(-clipped))


def _logit(value: float) -> float:
    bounded = min(1. - 1e-5, max(1e-5, float(value)))
    return math.log(bounded / (1. - bounded))


def _measurement_variance(observations: list[float | None], denominators: list[int], indices: list[int] | None = None) -> np.ndarray:
    values = []
    selected = range(len(observations)) if indices is None else indices
    for index in selected:
        observation = observations[index]
        if observation is None:
            continue
        variance = (1. / max(1, denominators[index]) if index == 3 else observation * (1. - observation) / max(1, denominators[index])) + 1e-4
        values.append(max(variance, 1e-6))
    return np.asarray(values, dtype=np.float64)


def _initialize_latent(observations: list[float | None], prior: dict | None) -> tuple[np.ndarray, np.ndarray, list[bool]]:
    x = np.asarray(prior.get("latent", [0.] * 4) if prior else [0.] * 4, dtype=np.float64)
    covariance = np.asarray(prior.get("P", np.eye(4).tolist()) if prior else np.eye(4), dtype=np.float64)
    initialized = list(prior.get("initialized", [False] * 4) if prior else [False] * 4)
    for index, observation in enumerate(observations):
        if observation is not None and not initialized[index]:
            x[index] = _logit(observation)
            initialized[index] = True
    return x, covariance, initialized


def linear_kf(observations: list[float | None], denominators: list[int], prior: dict | None, cfg: MathematicalConfig) -> dict:
    x = np.asarray(prior.get("x", [0.] * 4) if prior else [0.] * 4, dtype=np.float64)
    covariance = np.asarray(prior.get("P", np.eye(4).tolist()) if prior else np.eye(4), dtype=np.float64)
    initialized = list(prior.get("initialized", [False] * 4) if prior else [False] * 4)
    if prior:
        covariance += np.diag(cfg.process_noise)
    observed = []
    for index, observation in enumerate(observations):
        if observation is None:
            continue
        if not initialized[index]:
            x[index] = observation
            initialized[index] = True
        else:
            observed.append(index)
    if observed:
        h = np.eye(4, dtype=np.float64)[observed]
        r = np.diag(_measurement_variance(observations, denominators, observed))
        innovation_covariance = h @ covariance @ h.T + r
        gain = np.linalg.solve(innovation_covariance, h @ covariance).T
        innovation = np.asarray([observations[index] for index in observed]) - h @ x
        x += gain @ innovation
        residual = np.eye(4) - gain @ h
        covariance = residual @ covariance @ residual.T + gain @ r @ gain.T
    covariance = _psd(covariance)
    return _filter_result("linear_kf", x, covariance, initialized, observations, state={"x": x.tolist(), "P": covariance.tolist(), "initialized": initialized})


def extended_kf(observations: list[float | None], denominators: list[int], prior: dict | None, cfg: MathematicalConfig) -> dict:
    latent, covariance, initialized = _initialize_latent(observations, prior)
    if prior:
        covariance += np.diag(cfg.process_noise)
    observed = [i for i, value in enumerate(observations) if value is not None and prior and prior.get("initialized", [False] * 4)[i]]
    if observed:
        expected = _sigmoid(latent)
        h = np.zeros((len(observed), 4), dtype=np.float64)
        for row, index in enumerate(observed):
            h[row, index] = expected[index] * (1. - expected[index])
        r = np.diag(_measurement_variance(observations, denominators, observed))
        innovation_covariance = h @ covariance @ h.T + r
        gain = np.linalg.solve(innovation_covariance, h @ covariance).T
        latent += gain @ (np.asarray([observations[i] for i in observed]) - expected[observed])
        residual = np.eye(4) - gain @ h
        covariance = residual @ covariance @ residual.T + gain @ r @ gain.T
    covariance = _psd(covariance)
    display = _sigmoid(latent)
    state = {"latent": latent.tolist(), "P": covariance.tolist(), "initialized": initialized}
    return _filter_result("extended_kf", display, covariance, initialized, observations, state=state, latent=latent)


def _sigma_points(mean: np.ndarray, covariance: np.ndarray, alpha: float, beta: float, kappa: float):
    dimension = mean.size
    lam = alpha * alpha * (dimension + kappa) - dimension
    scale = dimension + lam
    root = np.linalg.cholesky(_psd(covariance) * scale)
    points = [mean]
    for column in root.T:
        points.extend((mean + column, mean - column))
    wm = np.full(2 * dimension + 1, 1. / (2. * scale), dtype=np.float64)
    wc = wm.copy()
    wm[0] = lam / scale
    wc[0] = wm[0] + (1. - alpha * alpha + beta)
    return np.asarray(points), wm, wc


def unscented_kf(observations: list[float | None], denominators: list[int], prior: dict | None, cfg: MathematicalConfig) -> dict:
    latent, covariance, initialized = _initialize_latent(observations, prior)
    covariance += np.diag(cfg.process_noise) if prior else 0.
    old_initialized = prior.get("initialized", [False] * 4) if prior else [False] * 4
    observed = [i for i, value in enumerate(observations) if value is not None and old_initialized[i]]
    if observed:
        sigma, wm, wc = _sigma_points(latent, covariance, cfg.ukf_alpha, cfg.ukf_beta, cfg.ukf_kappa)
        predicted_mean = np.sum(sigma * wm[:, None], axis=0)
        state_delta = sigma - predicted_mean
        predicted_covariance = np.einsum("i,ij,ik->jk", wc, state_delta, state_delta)
        measurements = _sigmoid(sigma)[:, observed]
        measurement_mean = np.sum(measurements * wm[:, None], axis=0)
        measurement_delta = measurements - measurement_mean
        r = np.diag(_measurement_variance(observations, denominators, observed))
        innovation_covariance = np.einsum("i,ij,ik->jk", wc, measurement_delta, measurement_delta) + r
        cross = np.einsum("i,ij,ik->jk", wc, state_delta, measurement_delta)
        gain = np.linalg.solve(innovation_covariance, cross.T).T
        latent = predicted_mean + gain @ (np.asarray([observations[i] for i in observed]) - measurement_mean)
        covariance = predicted_covariance - gain @ innovation_covariance @ gain.T
    covariance = _psd(covariance)
    display = _sigmoid(latent)
    state = {"latent": latent.tolist(), "P": covariance.tolist(), "initialized": initialized}
    return _filter_result("unscented_kf", display, covariance, initialized, observations, state=state, latent=latent,
                          extra={"alpha": cfg.ukf_alpha, "beta": cfg.ukf_beta, "kappa": cfg.ukf_kappa})


def ensemble_kf(observations: list[float | None], denominators: list[int], prior: dict | None, cfg: MathematicalConfig, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    old_initialized = prior.get("initialized", [False] * 4) if prior else [False] * 4
    initialized = list(old_initialized)
    if prior and len(prior.get("ensemble", [])) == cfg.ensemble_size:
        ensemble = np.asarray(prior["ensemble"], dtype=np.float64)
    else:
        base = np.asarray([_logit(v) if v is not None else 0. for v in observations], dtype=np.float64)
        ensemble = base + rng.normal(0., .25, size=(cfg.ensemble_size, 4))
    ensemble += rng.normal(0., np.sqrt(cfg.process_noise), size=ensemble.shape)
    observed = []
    for i, value in enumerate(observations):
        if value is None:
            continue
        if not initialized[i]:
            ensemble[:, i] = _logit(value) + rng.normal(0., .1, cfg.ensemble_size)
            initialized[i] = True
        elif old_initialized[i]:
            observed.append(i)
    if observed:
        predicted = _sigmoid(ensemble)[:, observed]
        x_delta = ensemble - ensemble.mean(axis=0)
        y_delta = predicted - predicted.mean(axis=0)
        denominator = max(1, cfg.ensemble_size - 1)
        r_values = _measurement_variance(observations, denominators, observed)
        gain = (x_delta.T @ y_delta / denominator) @ np.linalg.pinv(y_delta.T @ y_delta / denominator + np.diag(r_values))
        perturbations = rng.normal(0., np.sqrt(r_values), size=(cfg.ensemble_size, len(observed)))
        target = np.asarray([observations[i] for i in observed]) + perturbations
        ensemble += (target - predicted) @ gain.T
    display_ensemble = _sigmoid(ensemble)
    mean = display_ensemble.mean(axis=0)
    covariance = _psd(np.cov(display_ensemble, rowvar=False))
    state = {"ensemble": ensemble.tolist(), "initialized": initialized}
    return _filter_result("ensemble_kf", mean, covariance, initialized, observations, state=state,
                          extra={"ensemble_size": cfg.ensemble_size})


def particle_filter(observations: list[float | None], denominators: list[int], prior: dict | None, cfg: MathematicalConfig, seed: int) -> dict:
    rng = np.random.default_rng(seed + 17)
    old_initialized = prior.get("initialized", [False] * 4) if prior else [False] * 4
    initialized = list(old_initialized)
    if prior and len(prior.get("particles", [])) == cfg.particle_count:
        particles = np.asarray(prior["particles"], dtype=np.float64)
        weights = np.asarray(prior["weights"], dtype=np.float64)
    else:
        base = np.asarray([_logit(v) if v is not None else 0. for v in observations], dtype=np.float64)
        particles = base + rng.normal(0., .35, size=(cfg.particle_count, 4))
        weights = np.full(cfg.particle_count, 1. / cfg.particle_count)
    particles += rng.normal(0., np.sqrt(cfg.process_noise), size=particles.shape)
    available = [i for i, value in enumerate(observations) if value is not None]
    for i in available:
        if not initialized[i]:
            particles[:, i] = _logit(observations[i]) + rng.normal(0., .12, cfg.particle_count)
            initialized[i] = True
    observed = [i for i in available if old_initialized[i]]
    if observed:
        r_values = _measurement_variance(observations, denominators, observed)
        predicted = _sigmoid(particles)[:, observed]
        target = np.asarray([observations[i] for i in observed])
        log_likelihood = -.5 * np.sum((predicted - target) ** 2 / r_values + np.log(2. * math.pi * r_values), axis=1)
        log_weights = np.log(np.maximum(weights, 1e-300)) + log_likelihood
        log_weights -= np.max(log_weights)
        weights = np.exp(log_weights)
        weights /= weights.sum()
    ess = 1. / np.sum(weights * weights)
    resampled = False
    if ess < cfg.resample_ratio * cfg.particle_count:
        positions = (rng.random() + np.arange(cfg.particle_count)) / cfg.particle_count
        indexes = np.searchsorted(np.cumsum(weights), positions, side="right")
        particles = particles[np.minimum(indexes, cfg.particle_count - 1)]
        weights = np.full(cfg.particle_count, 1. / cfg.particle_count)
        resampled = True
    display_particles = _sigmoid(particles)
    mean = np.average(display_particles, axis=0, weights=weights)
    delta = display_particles - mean
    covariance = _psd(np.einsum("i,ij,ik->jk", weights, delta, delta))
    state = {"particles": particles.tolist(), "weights": weights.tolist(), "initialized": initialized}
    return _filter_result("particle_filter", mean, covariance, initialized, observations, state=state,
                          extra={"particle_count": cfg.particle_count, "effective_sample_size": float(ess), "resampled": resampled})


def _filter_result(name, mean, covariance, initialized, observations, state, latent=None, extra=None):
    result = {
        "model": name,
        "estimate": np.asarray(mean, dtype=np.float64).tolist(),
        "covariance": np.asarray(covariance, dtype=np.float64).tolist(),
        "initialized": initialized,
        "observation_mask": [value is not None for value in observations],
        "state": state,
    }
    if latent is not None:
        result["latent_mean"] = np.asarray(latent).tolist()
    result.update(extra or {})
    return result


def _emission_scores(features: dict, correction: dict, strategy: str) -> np.ndarray:
    scores = np.full(len(PHASES), .05, dtype=np.float64)
    scores[0] += .6
    if strategy == "explanation" or (features.get("connective_density") or 0.) > .2:
        scores[1] += 1.2
    if strategy == "contrast":
        scores[2] += 1.5
    if correction.get("detected"):
        scores[3] += 2.
    if strategy == "closure":
        scores[4] += 2.
    if features.get("topic_novelty") is not None:
        scores[0] += .2 * features["topic_novelty"]
    return scores


def hmm_update(features: dict, correction: dict, strategy: str, prior: dict | None) -> dict:
    transition = np.asarray([
        [.55,.20,.10,.10,.05], [.15,.55,.10,.15,.05], [.15,.15,.45,.20,.05],
        [.20,.20,.10,.45,.05], [.25,.05,.05,.05,.60],
    ], dtype=np.float64)
    emission = _emission_scores(features, correction, strategy)
    emission = np.exp(emission - emission.max()); emission /= emission.sum()
    previous = np.asarray(prior.get("posterior", np.full(5, .2)) if prior else np.full(5, .2), dtype=np.float64)
    predicted = previous @ transition
    posterior = predicted * emission
    posterior /= posterior.sum()
    history = list(prior.get("emissions", []) if prior else []) + [np.log(np.maximum(emission, 1e-12)).tolist()]
    history = history[-100:]
    delta = np.log(transition)
    path = np.asarray(history[0]) - math.log(len(PHASES)); back = []
    for row in history[1:]:
        values = path[:, None] + delta
        pointers = values.argmax(axis=0); path = values[pointers, np.arange(len(PHASES))] + np.asarray(row); back.append(pointers)
    state_index = int(path.argmax()); decoded = [state_index]
    for pointers in reversed(back):
        state_index = int(pointers[state_index]); decoded.append(state_index)
    decoded.reverse()
    return {"states": list(PHASES), "posterior": posterior.tolist(), "current_state": PHASES[int(posterior.argmax())],
            "viterbi_path": [PHASES[i] for i in decoded], "state": {"posterior": posterior.tolist(), "emissions": history},
            "interpretation": "fixed heuristic emissions; not a trained or validated latent-state model"}


def crf_decode(text: str, clauses: list[dict], relations: list[dict]) -> dict:
    if not clauses:
        return {"labels": [], "status": "unavailable", "reason": "no_clauses"}
    transition = np.full((len(CLAUSE_LABELS), len(CLAUSE_LABELS)), -.2)
    np.fill_diagonal(transition, .25)
    transition[CLAUSE_LABELS.index("event"), CLAUSE_LABELS.index("cause")] = .5
    transition[CLAUSE_LABELS.index("event"), CLAUSE_LABELS.index("contrast")] = .5
    relation_by_clause = {}
    for edge in relations:
        relation_by_clause.setdefault(edge["arg2"], set()).add(edge["relation"])
    emissions = []
    for clause in clauses:
        value = clause.get("text", "").casefold()
        row = np.zeros(len(CLAUSE_LABELS), dtype=np.float64); row[0] = .25
        related = relation_by_clause.get(clause["id"], set())
        if related & {"cause", "result"}: row[1] += 1.5
        if "contrast" in related or re.search(r"\b(?:but|although|however)\b", value): row[2] += 1.5
        if re.search(r"\b(?:want|intend|plan|will|going to)\b", value): row[3] += 1.2
        if re.search(r"\b(?:maybe|perhaps|not sure|i think|i guess)\b", value): row[4] += 1.2
        if re.search(r"\b(?:actually|rather|instead|i don't think|i do not think)\b", value): row[5] += 1.8
        emissions.append(row)
    scores = emissions[0]; backs = []
    for row in emissions[1:]:
        values = scores[:, None] + transition
        pointers = values.argmax(axis=0); scores = values[pointers, np.arange(len(CLAUSE_LABELS))] + row; backs.append(pointers)
    index = int(scores.argmax()); path = [index]
    for pointers in reversed(backs): index = int(pointers[index]); path.append(index)
    path.reverse()
    return {"status": "ready", "labels": [{"clause_id": clause["id"], "label": CLAUSE_LABELS[label], "spans": clause["spans"]} for clause,label in zip(clauses,path)],
            "interpretation": "linear-chain CRF-form Viterbi decoder with fixed heuristic potentials; not trained"}


def _proposition_type(value: str) -> str:
    lowered = value.casefold()
    if re.search(r"\b(?:should|supposed to|expected to)\s+(?:be|feel)\s+(?:happy|excited|thrilled)\b", lowered):
        return "expected_emotion"
    rules = [
        ("physical_exhaustion", r"\b(?:physically exhausted|tired|fatigued)\b"),
        ("excitement", r"\b(?:excited|happy|thrilled)\b"),
        ("worth_pressure", r"\b(?:prove|worthy|worth the opportunity|deserve)\b"),
        ("present_enjoyment", r"\b(?:enjoy|savor|appreciate).*(?:achievement|moment|this)\b"),
        ("intention", r"\b(?:i want|i intend|i plan|i will)\b"),
        ("uncertainty", r"\b(?:maybe|perhaps|not sure|i think|i guess)\b"),
    ]
    return next((name for name, pattern in rules if re.search(pattern, lowered)), "user_statement")


def evidence_and_propositions(text: str, clauses: list[dict], correction: dict, prior: dict | None, cfg: MathematicalConfig) -> tuple[dict, dict]:
    state = copy.deepcopy(prior or {"evidence": [], "propositions": [], "revision": 0})
    state["revision"] += 1
    turn = state["revision"]
    for proposition in state["propositions"]:
        proposition["alpha"] = 1. + (proposition["alpha"] - 1.) * cfg.evidence_decay
        proposition["beta"] = 1. + (proposition["beta"] - 1.) * cfg.evidence_decay
    evidence_ids = []
    for clause in clauses or [{"id": "fallback", "spans": [[0, len(text)]], "text": text}]:
        normalized = " ".join(clause.get("text", "").split())
        if not normalized:
            continue
        eid = "ev_" + hashlib.sha256(f"{turn}:{clause['id']}:{normalized}".encode()).hexdigest()[:12]
        state["evidence"].append({"id": eid, "turn": turn, "spans": clause["spans"], "text": normalized,
                                  "speaker": "user", "origin": "user_stated", "status": "active"})
        evidence_ids.append(eid)
        pid = "pr_" + hashlib.sha256(f"{_proposition_type(normalized)}:{normalized.casefold()}".encode()).hexdigest()[:12]
        existing = next((p for p in state["propositions"] if p["id"] == pid), None)
        if existing:
            existing["supporting_evidence"] = sorted(set(existing["supporting_evidence"] + [eid]))
            existing["alpha"] += 1.; existing["last_turn"] = turn
            if existing["status"] != "superseded": existing["status"] = "explicitly_stated"
        else:
            state["propositions"].append({"id": pid, "type": _proposition_type(normalized), "claim": normalized,
                "origin": "user_stated", "scope": "session", "status": "explicitly_stated", "supporting_evidence": [eid],
                "contradicting_evidence": [], "alpha": 2., "beta": 1., "created_turn": turn, "last_turn": turn,
                "superseded_by": None, "depends_on": []})
    revisions = []
    if correction.get("detected"):
        reference_stop = {"actually", "rather", "instead", "i", "a", "an", "the", "to", "of", "is", "am", "are", "do", "does", "not", "but", "and", "still", "think", "that", "this"}
        cue_span = correction.get("cue_span") or [0, len(text)]
        sentence_start = max(text.rfind(mark, 0, cue_span[0]) for mark in ".!?") + 1
        sentence_end = min([index for index in (text.find(mark, cue_span[1]) for mark in ".!?") if index >= 0] or [len(text)])
        focus_text = text[sentence_start:sentence_end]
        def normalize_tokens(value):
            tokens = set(re.findall(r"[a-z]+", value.casefold())) - reference_stop
            return {"prove" if token.startswith("prov") else "worth" if token.startswith("worth") else token for token in tokens}
        current_tokens = normalize_tokens(focus_text)
        candidates = [p for p in state["propositions"] if p["last_turn"] < turn and p["status"] not in {"superseded", "deleted"}]
        def similarity(prop):
            tokens = normalize_tokens(prop["claim"])
            return len(tokens & current_tokens) / max(1, len(tokens | current_tokens))
        target = max(candidates, key=lambda p: (similarity(p), p["last_turn"]), default=None)
        if target and len(normalize_tokens(target["claim"]) & current_tokens) >= 2 and similarity(target) >= .12:
            partial = bool(re.search(r"\b(?:but|still|partly|except)\b", text, re.I))
            target["status"] = "disputed" if partial else "superseded"; target["beta"] += 1. if partial else 2.
            target["contradicting_evidence"] = sorted(set(target["contradicting_evidence"] + evidence_ids))
            target["superseded_by"] = None if partial else evidence_ids[0] if evidence_ids else None
            revisions.append({"target": target["id"], "kind": "explicit_partial" if partial else "explicit_full", "evidence_ids": evidence_ids})
            for dependent in state["propositions"]:
                if target["id"] in dependent.get("depends_on", []) and dependent["status"] != "deleted":
                    dependent["status"] = "unresolved"
        else:
            revisions.append({"target": None, "kind": "ambiguous", "evidence_ids": evidence_ids})
    for proposition in state["propositions"]:
        proposition["bayesian_mean"] = proposition["alpha"] / (proposition["alpha"] + proposition["beta"])
        proposition["mass"] = _ds_mass(proposition)
    state["evidence"] = state["evidence"][-cfg.max_propositions * 2:]
    state["propositions"] = state["propositions"][-cfg.max_propositions:]
    public = {"revision": turn, "current_evidence_ids": evidence_ids, "propositions": copy.deepcopy(state["propositions"]),
              "revisions": revisions, "notice": "Bayesian means and Dempster-Shafer masses express configured evidence bookkeeping, not calibrated truth probabilities."}
    return public, state


def _ds_combine(left: dict, right: dict) -> dict:
    truth, falsehood, unknown = "true", "false", "unknown"
    conflict = left[truth] * right[falsehood] + left[falsehood] * right[truth]
    norm = max(1e-12, 1. - conflict)
    return {
        truth: (left[truth]*right[truth] + left[truth]*right[unknown] + left[unknown]*right[truth]) / norm,
        falsehood: (left[falsehood]*right[falsehood] + left[falsehood]*right[unknown] + left[unknown]*right[falsehood]) / norm,
        unknown: left[unknown]*right[unknown] / norm,
        "conflict": conflict,
    }


def _ds_mass(proposition: dict) -> dict:
    mass = {"true": 0., "false": 0., "unknown": 1., "conflict": 0.}
    for _ in proposition.get("supporting_evidence", []):
        mass = _ds_combine(mass, {"true": .75, "false": .05, "unknown": .20})
    for _ in proposition.get("contradicting_evidence", []):
        mass = _ds_combine(mass, {"true": .05, "false": .75, "unknown": .20})
    return {key: round(float(value), 6) for key, value in mass.items()}


def temporal_narrative_graph(text: str, clauses: list[dict], relations: list[dict], ledger: dict, prior: dict | None, cfg: MathematicalConfig) -> tuple[dict, dict]:
    graph = copy.deepcopy(prior or {"nodes": [], "edges": [], "revision": 0})
    graph["revision"] += 1; turn = graph["revision"]
    known_nodes = {node["id"] for node in graph["nodes"]}
    for evidence_id in ledger["current_evidence_ids"]:
        if evidence_id not in known_nodes:
            graph["nodes"].append({"id": evidence_id, "type": "evidence", "turn": turn, "status": "active", "origin": "user_stated"})
            known_nodes.add(evidence_id)
    for proposition in ledger["propositions"]:
        if proposition["id"] not in known_nodes:
            graph["nodes"].append({"id": proposition["id"], "type": "proposition", "turn": proposition["created_turn"],
                                   "status": proposition["status"], "origin": proposition["origin"], "label": proposition["type"]})
            known_nodes.add(proposition["id"])
        else:
            next(node for node in graph["nodes"] if node["id"] == proposition["id"])["status"] = proposition["status"]
        for evidence_id in proposition["supporting_evidence"]:
            if evidence_id in known_nodes and not any(edge["source"] == evidence_id and edge["target"] == proposition["id"] and edge["type"] == "supports" for edge in graph["edges"]):
                graph["edges"].append({"source": evidence_id, "target": proposition["id"], "type": "supports", "origin": "ledger", "status": "active", "confidence": None})
    clause_nodes = {}
    for clause in clauses:
        node_id = f"n{turn}_{clause['id']}"
        ptype = _proposition_type(clause.get("text", ""))
        node_type = "internal_reaction" if ptype in {"physical_exhaustion", "excitement"} else "self_judgment" if ptype == "worth_pressure" else "event"
        node = {"id": node_id, "type": node_type, "turn": turn, "spans": clause["spans"], "status": "active",
                "origin": "user_stated", "evidence_ids": ledger["current_evidence_ids"], "label": ptype}
        graph["nodes"].append(node); clause_nodes[clause["id"]] = node_id
    ordered = [clause_nodes[c["id"]] for c in clauses if c["id"] in clause_nodes]
    for left, right in zip(ordered, ordered[1:]):
        graph["edges"].append({"source": left, "target": right, "type": "before", "origin": "text_order", "status": "active", "confidence": None})
    relation_types = {"cause": "causes", "result": "leads_to", "contrast": "contrasts_with", "condition": "condition_for",
                      "temporal": "temporally_related", "example": "elaborates"}
    for edge in relations:
        if edge["source"] in clause_nodes and edge["target"] in clause_nodes:
            graph["edges"].append({"source": clause_nodes[edge["source"]], "target": clause_nodes[edge["target"]],
                "type": relation_types[edge["relation"]], "origin": "explicit_connective", "status": "active",
                "confidence": None, "relation_id": edge["id"]})
    for revision in ledger.get("revisions", []):
        graph["edges"].append({"source": revision["evidence_ids"][0] if revision["evidence_ids"] else "unknown",
                               "target": revision["target"], "type": "supersedes", "origin": "correction_resolver", "status": "active", "confidence": None})
    graph["nodes"] = graph["nodes"][-cfg.max_graph_nodes:]
    valid = {n["id"] for n in graph["nodes"]} | {p["id"] for p in ledger["propositions"]} | set(ledger["current_evidence_ids"])
    graph["edges"] = [edge for edge in graph["edges"] if edge["source"] in valid and edge["target"] in valid][-cfg.max_graph_nodes * 2:]
    public = {**copy.deepcopy(graph), "schema_version": "temporal-narrative-graph.v1",
              "notice": "Text order, explicit relations, and correction links remain distinct; no implicit causation is added."}
    return public, graph


def temperature_scale(logits: list[list[float]], labels: list[int], iterations: int = 200, learning_rate: float = .02) -> dict:
    """Fit one positive softmax temperature on labelled development data."""
    values = np.asarray(logits, dtype=np.float64); targets = np.asarray(labels, dtype=int)
    if values.ndim != 2 or len(values) != len(targets) or not len(targets):
        return {"status": "unavailable", "reason": "labelled_development_data_required"}
    log_temperature = 0.
    for _ in range(iterations):
        temperature = math.exp(log_temperature); scaled = values / temperature
        scaled -= scaled.max(axis=1, keepdims=True); probs = np.exp(scaled); probs /= probs.sum(axis=1, keepdims=True)
        expected = np.sum(probs * values, axis=1)
        gradient = np.mean((values[np.arange(len(targets)), targets] - expected) / temperature)
        log_temperature -= learning_rate * gradient
        log_temperature = float(np.clip(log_temperature, math.log(.05), math.log(20.)))
    return {"status": "ready", "temperature": math.exp(log_temperature), "method": "single_temperature_nll",
            "notice": "Valid only for the labelled development distribution used to fit it."}


def run_mathematical_suite(text: str, clauses: list[dict], relations: list[dict], features: dict,
                           denominators: list[int], correction: dict, strategy: str,
                           prior: dict | None = None, profile: str = "balanced", overrides: dict | None = None) -> tuple[dict, dict]:
    cfg = configuration(profile, overrides); prior = copy.deepcopy(prior or {})
    observations = [features.get(name) for name in DIMENSIONS]
    turn = int(prior.get("turn", 0)) + 1
    seed = int(hashlib.sha256(f"{VERSION}:{turn}:{text}".encode()).hexdigest()[:16], 16) % (2**32)
    filters = {
        "linear_kf": linear_kf(observations, denominators, prior.get("linear_kf"), cfg),
        "extended_kf": extended_kf(observations, denominators, prior.get("extended_kf"), cfg),
        "unscented_kf": unscented_kf(observations, denominators, prior.get("unscented_kf"), cfg),
        "ensemble_kf": ensemble_kf(observations, denominators, prior.get("ensemble_kf"), cfg, seed),
        "particle_filter": particle_filter(observations, denominators, prior.get("particle_filter"), cfg, seed),
    }
    hmm = hmm_update(features, correction, strategy, prior.get("hmm"))
    crf = crf_decode(text, clauses, relations)
    ledger, ledger_state = evidence_and_propositions(text, clauses, correction, prior.get("ledger"), cfg)
    graph, graph_state = temporal_narrative_graph(text, clauses, relations, ledger, prior.get("graph"), cfg)
    public_filters = {name: {key: value for key, value in result.items() if key != "state"} for name, result in filters.items()}
    state = {"turn": turn, "profile": profile, **{name: result["state"] for name, result in filters.items()},
             "hmm": hmm["state"], "ledger": ledger_state, "graph": graph_state}
    public = {
        "schema_version": VERSION,
        "profile": profile,
        "configuration": {**asdict(cfg), "process_noise": list(cfg.process_noise)},
        "dimensions": list(DIMENSIONS),
        "filters": public_filters,
        "hmm": {key: value for key, value in hmm.items() if key != "state"},
        "crf": crf,
        "evidence_belief_revision": ledger,
        "temporal_narrative_graph": graph,
        "confidence_calibration": {"status": "unavailable", "reason": "labelled_development_data_required", "available_method": "single_temperature_nll"},
        "decision_boundary": "experimental enrichment only; no output selects a response or establishes psychological truth",
    }
    return public, state
