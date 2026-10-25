"""Format and print the complete multi-turn conversation with transformer inputs/outputs."""
import json
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "evaluation" / "achievement_10turn_reflective_v2.jsonl"

def main():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    print(f"Loaded {len(records)} turns from {DATA_FILE.name}\n")
    for r in records:
        turn_id = r["turn_id"]
        user_prompt = r["user_prompt"]
        response_text = r["response_text"]
        mode = r.get("response_mode", "unknown")
        latency = r.get("latency_seconds", 0.0)
        strategy = r.get("strategy", "standard")

        plan = r.get("response_plan", {})
        claims = [c.get("text") for c in plan.get("claims_to_communicate", [])]

        gen = r.get("generation", {})
        attempts = gen.get("attempts", [])

        print(f"================================================================================")
        print(f"TURN {turn_id} | Strategy: {strategy} | Mode: {mode} | Latency: {latency:.2f}s")
        print(f"================================================================================")
        print(f"USER INPUT:")
        print(f"  \"{user_prompt}\"\n")
        print(f"APPROVED CLAIMS TO COMMUNICATE ({len(claims)}):")
        for c in claims:
            print(f"  - {c}")
        print()

        print(f"TRANSFORMER GENERATION ATTEMPTS ({len(attempts)}):")
        for a in attempts:
            att_id = a.get("attempt")
            profile = a.get("profile")
            status = a.get("status")
            in_tok = a.get("input_tokens")
            out_tok = a.get("output_tokens")
            gen_sec = a.get("generation_seconds")
            val = a.get("validation", {})
            sem_val = a.get("semantic_validation", {})
            score = sem_val.get("score")
            print(f"  * Attempt {att_id} [{profile} profile]:")
            print(f"      Status: {status} | Tokens: {in_tok} in -> {out_tok} out | Generation Time: {gen_sec:.2f}s")
            if score is not None:
                print(f"      Semantic Grounding Score: {score:.4f} (Copy similarity: {sem_val.get('copy_similarity', 0.0):.4f})")
            if val.get("violations"):
                print(f"      Violations: {val.get('violations')}")
        print()

        print(f"SYSTEM RESPONSE OUTPUT:")
        print(f"  \"{response_text}\"")
        print()

if __name__ == "__main__":
    main()
