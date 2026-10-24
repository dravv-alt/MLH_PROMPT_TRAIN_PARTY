import inspect
from pathlib import Path

from scripts.evaluate_sanctuary_dataset import inference_only, load_dataset


DATASET = Path(__file__).resolve().parents[3] / "sanctuary_v2_evaluation_dataset.json"


def test_dataset_has_eight_independent_topics_and_eighty_unique_turns():
    dataset = load_dataset(DATASET)
    identities = [
        (topic["topic_id"], turn["turn_id"])
        for topic in dataset["topics"]
        for turn in topic["turns"]
    ]
    assert len(dataset["topics"]) == 8
    assert len(identities) == 80
    assert len(set(identities)) == 80


def test_inference_boundary_has_no_gold_annotation_parameter():
    parameters = set(inspect.signature(inference_only).parameters)
    assert parameters == {"prompt", "state", "service", "mode", "profile"}
    assert "expected_state" not in parameters
    assert "gold" not in parameters
