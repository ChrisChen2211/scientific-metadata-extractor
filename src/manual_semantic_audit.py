"""Create, validate, and summarize a human semantic-audit worksheet.

This script never calls an LLM. A human reviewer must assign every semantic label.
"""

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from real_schema import REAL_METADATA_FIELDS


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SAMPLES = PROJECT_ROOT / "data" / "real" / "samples.json"
DEFAULT_GROUND_TRUTH = PROJECT_ROOT / "data" / "real" / "ground_truth.json"
DEFAULT_PREDICTIONS = PROJECT_ROOT / "outputs" / "real_predictions.json"
DEFAULT_AUDIT = PROJECT_ROOT / "data" / "real" / "manual_semantic_audit.json"
DEFAULT_RESULTS = PROJECT_ROOT / "outputs" / "manual_semantic_audit_results.json"
DEFAULT_REPORT = PROJECT_ROOT / "outputs" / "manual_semantic_audit.md"

UNREVIEWED = "Unreviewed"
SEMANTIC_LABELS = ["Correct", "Partially correct", "Incorrect", "Unsupported"]
ALL_LABELS = [UNREVIEWED, *SEMANTIC_LABELS]

RUBRIC = {
    "Correct": (
        "The prediction preserves all scientifically important information represented by "
        "the reference. Abbreviations, paraphrases, and additional excerpt-supported detail "
        "are allowed."
    ),
    "Partially correct": (
        "The core metadata is correct, but the prediction omits or changes some important "
        "information."
    ),
    "Incorrect": "The core scientific meaning is inconsistent with the stored excerpt.",
    "Unsupported": "The prediction contains information that the stored excerpt cannot support.",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with temporary_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    temporary_path.replace(path)


def prediction_list(payload: Any) -> Tuple[List[Dict[str, Any]], Any]:
    if isinstance(payload, list):
        return payload, None
    if isinstance(payload, dict) and isinstance(payload.get("predictions"), list):
        return payload["predictions"], payload.get("model")
    raise ValueError("Predictions must be a list or an object containing a predictions list.")


def build_template(
    samples: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    predictions_payload: Any,
) -> Dict[str, Any]:
    predictions, model = prediction_list(predictions_payload)
    samples_by_id = {item["id"]: item for item in samples}
    predictions_by_id = {item["id"]: item for item in predictions}

    sample_sources = []
    items = []
    for truth in ground_truth:
        sample_id = truth["id"]
        sample = samples_by_id[sample_id]
        prediction = predictions_by_id[sample_id]
        sample_sources.append(
            {
                "id": sample_id,
                "paper_title": sample["paper_title"],
                "source_url": sample["source_url"],
                "section": sample.get("section"),
                "excerpt": sample["excerpt"],
            }
        )
        for field in REAL_METADATA_FIELDS:
            items.append(
                {
                    "sample_id": sample_id,
                    "field": field,
                    "ground_truth": truth.get(field),
                    "prediction": prediction.get(field),
                    "label": UNREVIEWED,
                    "schema_ambiguity": False,
                    "rationale": None,
                }
            )

    return {
        "audit_name": "Manual semantic audit of real-paper metadata extraction",
        "audit_status": "not_started",
        "auditor": None,
        "audit_date": None,
        "audit_method": "independent human semantic audit; no LLM judge",
        "model": model,
        "unit_of_analysis": "one prediction field",
        "instructions": [
            "This worksheet must be completed by a human reviewer; do not use an LLM judge.",
            "Judge each prediction only against the stored excerpt, not outside knowledge.",
            "Choose exactly one semantic label and write a concise evidence-based rationale.",
            "Set schema_ambiguity to true when the field definition or reference annotation admits more than one reasonable interpretation.",
            "Do not edit predictions or ground truth to improve scores.",
        ],
        "rubric": RUBRIC,
        "sample_sources": sample_sources,
        "items": items,
    }


def validate_audit(audit: Dict[str, Any]) -> Tuple[Counter, List[str]]:
    errors = []
    items = audit.get("items")
    if not isinstance(items, list):
        return Counter(), ["items must be a list"]

    expected_count = len(audit.get("sample_sources", [])) * len(REAL_METADATA_FIELDS)
    if len(items) != expected_count:
        errors.append(f"expected {expected_count} items, found {len(items)}")

    seen = set()
    counts: Counter = Counter()
    for index, item in enumerate(items):
        key = (item.get("sample_id"), item.get("field"))
        if key in seen:
            errors.append(f"duplicate item: {key}")
        seen.add(key)

        if item.get("field") not in REAL_METADATA_FIELDS:
            errors.append(f"item {index} has unknown field: {item.get('field')}")

        label = item.get("label")
        if label not in ALL_LABELS:
            errors.append(f"item {index} has invalid label: {label}")
        else:
            counts[label] += 1

        if not isinstance(item.get("schema_ambiguity"), bool):
            errors.append(f"item {index} schema_ambiguity must be true or false")

        if label != UNREVIEWED and not str(item.get("rationale") or "").strip():
            errors.append(f"item {index} requires a rationale after review")

    return counts, errors


def initialize(args: argparse.Namespace) -> int:
    if args.audit.exists():
        existing = load_json(args.audit)
        reviewed = sum(
            item.get("label") != UNREVIEWED for item in existing.get("items", [])
        )
        if reviewed:
            raise RuntimeError(
                f"Refusing to overwrite {args.audit}: {reviewed} reviewed labels exist."
            )

    audit = build_template(
        load_json(args.samples),
        load_json(args.ground_truth),
        load_json(args.predictions),
    )
    save_json(args.audit, audit)
    print(f"Created human audit worksheet with {len(audit['items'])} unreviewed items:")
    print(args.audit)
    return 0


def validate(args: argparse.Namespace) -> int:
    audit = load_json(args.audit)
    counts, errors = validate_audit(audit)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    reviewed = sum(counts[label] for label in SEMANTIC_LABELS)
    print(f"Audit schema valid. Reviewed {reviewed}/{sum(counts.values())} fields.")
    for label in ALL_LABELS:
        print(f"  {label}: {counts[label]}")
    return 0


def write_markdown(path: Path, audit: Dict[str, Any], result: Dict[str, Any]) -> None:
    lines = [
        "# Manual Semantic Audit",
        "",
        f"Method: {audit['audit_method']}.",
        "",
        f"- Auditor: {audit['auditor']}",
        f"- Audit date: {audit['audit_date']}",
        f"- Model: {audit.get('model')}",
        f"- Fields reviewed: {result['total_fields']}",
        "",
        "## Results",
        "",
        "| Label | Count | Percentage |",
        "|---|---:|---:|",
    ]
    for label in SEMANTIC_LABELS:
        lines.append(
            f"| {label} | {result['counts'][label]} | "
            f"{result['percentages'][label]:.1%} |"
        )
    lines.append(
        f"| Correct or partially correct | "
        f"{result['correct_or_partially_correct_count']} | "
        f"{result['correct_or_partially_correct_rate']:.1%} |"
    )

    lines.extend(["", "## Schema ambiguities", ""])
    ambiguous = [item for item in audit["items"] if item["schema_ambiguity"]]
    if ambiguous:
        for item in ambiguous:
            lines.extend(
                [
                    f"### {item['sample_id']} — {item['field']}",
                    "",
                    f"- Ground truth: `{item['ground_truth']}`",
                    f"- Prediction: `{item['prediction']}`",
                    f"- Label: {item['label']}",
                    f"- Rationale: {item['rationale']}",
                    "",
                ]
            )
    else:
        lines.append("No schema ambiguities were marked by the reviewer.")

    lines.extend(
        [
            "",
            "## Limitations",
            "",
            "This review covers five excerpts and 35 fields. Its recorded method is shown above; it is not an independent domain-expert validation or an inter-annotator agreement study.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def summarize(args: argparse.Namespace) -> int:
    audit = load_json(args.audit)
    counts, errors = validate_audit(audit)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    if counts[UNREVIEWED]:
        print(
            f"Audit incomplete: {counts[UNREVIEWED]} of {sum(counts.values())} "
            "fields remain Unreviewed."
        )
        return 2
    if not str(audit.get("auditor") or "").strip() or not str(
        audit.get("audit_date") or ""
    ).strip():
        print("Audit incomplete: set auditor and audit_date before summarizing.")
        return 2

    total = sum(counts.values())
    result = {
        "audit_name": audit["audit_name"],
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "auditor": audit["auditor"],
        "audit_date": audit["audit_date"],
        "model": audit.get("model"),
        "total_fields": total,
        "counts": {label: counts[label] for label in SEMANTIC_LABELS},
        "percentages": {
            label: counts[label] / total for label in SEMANTIC_LABELS
        },
        "correct_or_partially_correct_count": (
            counts["Correct"] + counts["Partially correct"]
        ),
        "correct_or_partially_correct_rate": (
            counts["Correct"] + counts["Partially correct"]
        ) / total,
        "schema_ambiguity_count": sum(
            item["schema_ambiguity"] for item in audit["items"]
        ),
        "method": audit["audit_method"],
    }
    save_json(args.results, result)
    write_markdown(args.report, audit, result)
    print(f"Saved manual-audit results to {args.results}")
    print(f"Saved manual-audit report to {args.report}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("init", "validate", "summarize"))
    parser.add_argument("--samples", type=Path, default=DEFAULT_SAMPLES)
    parser.add_argument("--ground-truth", type=Path, default=DEFAULT_GROUND_TRUTH)
    parser.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "init":
        return initialize(args)
    if args.command == "validate":
        return validate(args)
    return summarize(args)


if __name__ == "__main__":
    raise SystemExit(main())
