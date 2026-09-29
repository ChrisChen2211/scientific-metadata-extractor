"""Evaluate real-paper predictions and generate deterministic error analysis."""

import argparse
import json
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from real_schema import REAL_METADATA_FIELDS


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GROUND_TRUTH = PROJECT_ROOT / "data" / "real" / "ground_truth.json"
DEFAULT_PREDICTIONS = PROJECT_ROOT / "outputs" / "real_predictions.json"
DEFAULT_RESULTS = PROJECT_ROOT / "outputs" / "evaluation_results.json"
DEFAULT_REPORT = PROJECT_ROOT / "outputs" / "error_analysis.md"

ERROR_CATEGORIES = [
    "semantically equivalent but lexically different",
    "missing information",
    "reference-null disagreement (manual review required)",
    "overly broad extraction",
    "overly specific extraction",
    "abbreviation/terminology difference",
    "other content mismatch",
]


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def normalize(value: Any) -> Any:
    """Apply only generic case, Unicode, punctuation, and whitespace normalization."""
    if value is None or isinstance(value, (int, float, bool)):
        return value
    text = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    text = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def token_set(value: Any) -> Set[str]:
    normalized = normalize(value)
    if normalized is None:
        return set()
    return set(str(normalized).split())


def classify_mismatch(expected: Any, predicted: Any) -> List[str]:
    """Assign transparent heuristic labels; these labels never change metric scores."""
    if expected == predicted:
        return []
    if normalize(expected) == normalize(predicted):
        return ["semantically equivalent but lexically different"]
    if expected is not None and predicted is None:
        return ["missing information"]
    if expected is None and predicted is not None:
        return ["reference-null disagreement (manual review required)"]

    expected_tokens = token_set(expected)
    predicted_tokens = token_set(predicted)
    if predicted_tokens and predicted_tokens < expected_tokens:
        return ["overly broad extraction"]
    if expected_tokens and expected_tokens < predicted_tokens:
        return ["overly specific extraction"]

    expected_text = str(normalize(expected))
    predicted_text = str(normalize(predicted))
    similarity = SequenceMatcher(None, expected_text, predicted_text).ratio()
    if similarity >= 0.55 or expected_tokens.intersection(predicted_tokens):
        return ["abbreviation/terminology difference"]
    return ["other content mismatch"]


def safe_ratio(numerator: int, denominator: int) -> Optional[float]:
    return numerator / denominator if denominator else None


def load_predictions(path: Path) -> Dict[str, Any]:
    payload = load_json(path)
    if isinstance(payload, list):
        return {"model": None, "predictions": payload}
    if not isinstance(payload, dict) or not isinstance(payload.get("predictions"), list):
        raise ValueError(f"Unexpected predictions format in {path}")
    return payload


def evaluate(ground_truth: List[Dict[str, Any]], prediction_run: Dict[str, Any]) -> Dict[str, Any]:
    predictions = prediction_run["predictions"]
    predictions_by_id = {item["id"]: item for item in predictions}

    exact_correct = 0
    normalized_correct = 0
    total = 0
    sample_results: List[Dict[str, Any]] = []
    field_counts = {
        field: {"exact_correct": 0, "normalized_correct": 0, "total": 0}
        for field in REAL_METADATA_FIELDS
    }
    categories: Counter = Counter({name: 0 for name in ERROR_CATEGORIES})
    null_counts = {
        "reference_null": 0,
        "correct_null": 0,
        "non_null_on_reference_null": 0,
        "reference_supported": 0,
        "non_null_on_reference_supported": 0,
        "null_on_reference_supported": 0,
    }

    for truth in ground_truth:
        sample_id = truth["id"]
        prediction = predictions_by_id.get(sample_id)
        extraction_status = "missing"
        if prediction is not None:
            extraction_status = prediction.get("status", "success")

        field_results = []
        sample_exact = True
        sample_normalized = True
        for field in REAL_METADATA_FIELDS:
            expected = truth.get(field)
            predicted = prediction.get(field) if prediction is not None else None
            exact_match = expected == predicted
            normalized_match = normalize(expected) == normalize(predicted)
            mismatch_categories = classify_mismatch(expected, predicted)

            total += 1
            field_counts[field]["total"] += 1
            if exact_match:
                exact_correct += 1
                field_counts[field]["exact_correct"] += 1
            else:
                sample_exact = False
            if normalized_match:
                normalized_correct += 1
                field_counts[field]["normalized_correct"] += 1
            else:
                sample_normalized = False
            categories.update(mismatch_categories)

            if expected is None:
                null_counts["reference_null"] += 1
                if predicted is None:
                    null_counts["correct_null"] += 1
                else:
                    null_counts["non_null_on_reference_null"] += 1
            else:
                null_counts["reference_supported"] += 1
                if predicted is None:
                    null_counts["null_on_reference_supported"] += 1
                else:
                    null_counts["non_null_on_reference_supported"] += 1

            field_results.append(
                {
                    "field": field,
                    "expected": expected,
                    "predicted": predicted,
                    "exact_match": exact_match,
                    "normalized_match": normalized_match,
                    "error_categories": mismatch_categories,
                }
            )

        sample_results.append(
            {
                "id": sample_id,
                "extraction_status": extraction_status,
                "all_fields_exact": sample_exact,
                "all_fields_normalized": sample_normalized,
                "fields": field_results,
            }
        )

    per_field = {}
    for field, counts in field_counts.items():
        per_field[field] = {
            **counts,
            "exact_accuracy": safe_ratio(counts["exact_correct"], counts["total"]),
            "normalized_accuracy": safe_ratio(
                counts["normalized_correct"], counts["total"]
            ),
        }

    null_performance = {
        **null_counts,
        "correct_null_rate": safe_ratio(
            null_counts["correct_null"], null_counts["reference_null"]
        ),
        "supported_reference_coverage": safe_ratio(
            null_counts["non_null_on_reference_supported"],
            null_counts["reference_supported"],
        ),
    }

    return {
        "dataset": "real scientific-paper excerpts",
        "model": prediction_run.get("model"),
        "metric_policy": {
            "exact": "Python value equality; strings must match character-for-character.",
            "normalized": (
                "Unicode NFKC, case folding, punctuation-to-space, whitespace collapse; "
                "no dataset-specific aliases or semantic judging."
            ),
            "error_categories": (
                "Deterministic heuristics for analysis only; categories do not alter scores."
            ),
        },
        "overall": {
            "total_fields": total,
            "exact_correct": exact_correct,
            "exact_accuracy": safe_ratio(exact_correct, total),
            "normalized_correct": normalized_correct,
            "normalized_accuracy": safe_ratio(normalized_correct, total),
            "samples_all_fields_exact": sum(
                item["all_fields_exact"] for item in sample_results
            ),
            "samples_all_fields_normalized": sum(
                item["all_fields_normalized"] for item in sample_results
            ),
            "total_samples": len(sample_results),
        },
        "per_field": per_field,
        "null_reference_behavior": null_performance,
        "error_category_counts": dict(sorted(categories.items())),
        "samples": sample_results,
    }


def format_percent(value: Optional[float]) -> str:
    return "n/a" if value is None else f"{value:.1%}"


def print_summary(results: Dict[str, Any]) -> None:
    overall = results["overall"]
    print("\nREAL-PAPER METADATA EXTRACTION EVALUATION")
    print("=" * 64)
    print(
        f"Exact Match Accuracy:      {overall['exact_correct']}/"
        f"{overall['total_fields']} = {format_percent(overall['exact_accuracy'])}"
    )
    print(
        f"Normalized Match Accuracy: {overall['normalized_correct']}/"
        f"{overall['total_fields']} = {format_percent(overall['normalized_accuracy'])}"
    )
    print(
        "Complete samples (normalized): "
        f"{overall['samples_all_fields_normalized']}/{overall['total_samples']}"
    )

    print("\nPer-field results")
    print("-" * 64)
    for field, metrics in results["per_field"].items():
        print(
            f"{field:26} exact {metrics['exact_correct']}/{metrics['total']} "
            f"({format_percent(metrics['exact_accuracy'])}), normalized "
            f"{metrics['normalized_correct']}/{metrics['total']} "
            f"({format_percent(metrics['normalized_accuracy'])})"
        )

    nulls = results["null_reference_behavior"]
    print("\nNull-reference behavior")
    print("-" * 64)
    print(
        f"Correct nulls: {nulls['correct_null']}/{nulls['reference_null']} "
        f"({format_percent(nulls['correct_null_rate'])})"
    )
    print(
        "Non-null predictions on reference-null fields: "
        f"{nulls['non_null_on_reference_null']}"
    )
    print(
        "Null predictions on supported-reference fields: "
        f"{nulls['null_on_reference_supported']}"
    )


def markdown_value(value: Any) -> str:
    if value is None:
        return "`null`"
    return "`" + str(value).replace("`", "\\`") + "`"


def write_error_report(path: Path, results: Dict[str, Any]) -> None:
    mismatches = [
        (sample["id"], field)
        for sample in results["samples"]
        for field in sample["fields"]
        if not field["exact_match"]
    ]
    normalized_mismatches = [item for item in mismatches if not item[1]["normalized_match"]]
    category_counts = results["error_category_counts"]

    lines = [
        "# Error Analysis: Real-Paper Evaluation",
        "",
        "## Scope and method",
        "",
            (
                "This report is generated from deterministic comparisons. Exact and normalized "
                "metrics are observations. Error labels are rule-based interpretations and do "
                "not change either score. No LLM judge is used. A non-null prediction against "
                "a reference-null field is a disagreement requiring manual review, not automatic "
                "evidence of hallucination."
        ),
        "",
        "## Observations",
        "",
        f"- Exact mismatches: {len(mismatches)}",
        f"- Normalized mismatches: {len(normalized_mismatches)}",
        (
            "- Exact matches after normalization only: "
            f"{len(mismatches) - len(normalized_mismatches)}"
        ),
        "",
        "### Category counts",
        "",
    ]
    if category_counts:
        lines.extend(f"- {name}: {count}" for name, count in category_counts.items())
    else:
        lines.append("- No mismatches were observed.")

    lines.extend(["", "### Mismatch details", ""])
    if not mismatches:
        lines.append("No exact mismatches were observed.")
    else:
        for sample_id, field in mismatches:
            categories = ", ".join(field["error_categories"])
            lines.extend(
                [
                    f"#### {sample_id} — {field['field']}",
                    "",
                    f"- Expected: {markdown_value(field['expected'])}",
                    f"- Predicted: {markdown_value(field['predicted'])}",
                    f"- Normalized match: {field['normalized_match']}",
                    f"- Heuristic category: {categories}",
                    "",
                ]
            )

    lines.extend(
        [
            "## Interpretations",
            "",
            (
                "The labels above are conservative lexical heuristics. “Overly broad” means "
                "the prediction's normalized token set is a strict subset of the reference; "
                "“overly specific” means the reverse. “Abbreviation/terminology difference” "
                "indicates partial lexical overlap or moderate string similarity, not proven "
                "semantic equivalence. A reference-null disagreement may reflect unsupported "
                "content, annotation ambiguity, or an underspecified schema. Manual review is "
                "required before drawing research conclusions from these labels."
            ),
            "",
            "## Limitations",
            "",
            (
                "This analysis covers five excerpts and 35 fields. Ground truth is bounded "
                "to the stored excerpts, so it does not represent every fact in the full "
                "papers. Deterministic normalization cannot recognize all paraphrases, and "
                "the heuristic categories can overlap conceptually even though this report "
                "assigns one primary label per mismatch."
            ),
            "",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ground-truth", type=Path, default=DEFAULT_GROUND_TRUTH)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--error-report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ground_truth = load_json(args.ground_truth)
    prediction_run = load_predictions(args.predictions)
    results = evaluate(ground_truth, prediction_run)
    save_json(args.results, results)
    write_error_report(args.error_report, results)
    print_summary(results)
    print(f"\nSaved machine-readable results to {args.results}")
    print(f"Saved error analysis to {args.error_report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
