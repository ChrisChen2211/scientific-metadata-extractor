import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GROUND_TRUTH_FILE = PROJECT_ROOT / "data" / "ground_truth.json"
PREDICTIONS_FILE = PROJECT_ROOT / "outputs" / "predictions.json"

FIELDS = [
    "sample_type",
    "sample_size",
    "experimental_method",
    "intervention",
    "duration",
]


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def normalize(value: Any):
    """Normalize values before comparison."""
    if value is None:
        return None

    if isinstance(value, int):
        return value

    value = str(value).lower().strip()

    # Remove punctuation
    value = re.sub(r"[^\w\s]", "", value)

    # Collapse repeated whitespace
    value = re.sub(r"\s+", " ", value)

    return value


def main():
    ground_truth = load_json(GROUND_TRUTH_FILE)
    predictions = load_json(PREDICTIONS_FILE)

    predictions_by_id = {
        item["id"]: item for item in predictions
    }

    exact_correct = 0
    normalized_correct = 0
    total = 0

    print("\nSCIENTIFIC METADATA EXTRACTION EVALUATION")
    print("=" * 60)

    for truth in ground_truth:
        sample_id = truth["id"]
        prediction = predictions_by_id[sample_id]

        print(f"\n{sample_id}")
        print("-" * 60)

        for field in FIELDS:
            expected = truth[field]
            predicted = prediction[field]

            exact_match = expected == predicted
            normalized_match = normalize(expected) == normalize(predicted)

            total += 1

            if exact_match:
                exact_correct += 1

            if normalized_match:
                normalized_correct += 1

            status = "✓" if normalized_match else "✗"

            print(f"{status} {field}")
            print(f"    expected : {expected}")
            print(f"    predicted: {predicted}")

    exact_accuracy = exact_correct / total
    normalized_accuracy = normalized_correct / total

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    print(
        f"Exact Match Accuracy:      "
        f"{exact_correct}/{total} = {exact_accuracy:.1%}"
    )

    print(
        f"Normalized Match Accuracy: "
        f"{normalized_correct}/{total} = {normalized_accuracy:.1%}"
    )


if __name__ == "__main__":
    main()