"""Extract structured metadata from the real-paper excerpt dataset."""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from real_schema import REAL_METADATA_FIELDS, RealScientificMetadata


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "data" / "real" / "samples.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "outputs" / "real_predictions.json"
DEFAULT_MODEL = "gpt-5.6-luna"

SYSTEM_PROMPT = """You are a scientific metadata extraction system.
Use only the scientific-paper excerpt supplied by the user.
Do not use outside knowledge, even if you recognize the paper.
Do not infer or guess unsupported information.
Return null for every field that is not explicitly supported by the excerpt.
Keep supported text concise and preserve important quantities, units, and timepoints.
For sample_size, return the number of participants in the described analysis, not a screened or excluded count.
"""


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


def extract_metadata(client: OpenAI, excerpt: str, model: str) -> Dict[str, Any]:
    response = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": "Extract metadata from this excerpt only:\n\n" + excerpt,
            },
        ],
        text_format=RealScientificMetadata,
    )

    if response.output_parsed is None:
        raise RuntimeError("The API response did not contain parsed structured output.")

    return {
        "response_id": response.id,
        **response.output_parsed.model_dump(),
    }


def build_error_prediction(sample_id: str, exc: Exception) -> Dict[str, Any]:
    """Represent an API failure without exposing credentials or fabricating values."""
    message = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED_API_KEY]", str(exc))
    return {
        "id": sample_id,
        "status": "error",
        "error_type": type(exc).__name__,
        "error_message": message[:500],
        **{field: None for field in REAL_METADATA_FIELDS},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_EXTRACTION_MODEL", DEFAULT_MODEL),
        help="OpenAI model ID (default: %(default)s)",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on the first API error instead of recording it and continuing.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(PROJECT_ROOT / ".env")

    samples = load_json(args.input)
    if not isinstance(samples, list):
        raise ValueError(f"Expected a JSON list in {args.input}")

    client = OpenAI()
    predictions: List[Dict[str, Any]] = []
    run_payload: Dict[str, Any] = {
        "dataset": "real scientific-paper excerpts",
        "model": args.model,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input_file": str(args.input.relative_to(PROJECT_ROOT)),
        "predictions": predictions,
    }

    for index, sample in enumerate(samples, start=1):
        sample_id = sample["id"]
        print(f"[{index}/{len(samples)}] Extracting {sample_id}...", flush=True)
        try:
            extracted = extract_metadata(client, sample["excerpt"], args.model)
            prediction = {"id": sample_id, "status": "success", **extracted}
            predictions.append(prediction)
            save_json(args.output, run_payload)
        except Exception as exc:  # API/validation failures are recorded per sample.
            if args.fail_fast:
                raise
            prediction = build_error_prediction(sample_id, exc)
            predictions.append(prediction)
            save_json(args.output, run_payload)
            print(
                f"  ERROR {sample_id}: {prediction['error_type']}: "
                f"{prediction['error_message']}",
                file=sys.stderr,
            )

    success_count = sum(item["status"] == "success" for item in predictions)
    print(f"Saved {len(predictions)} predictions to {args.output}")
    print(f"Successful API responses: {success_count}/{len(predictions)}")
    return 0 if success_count == len(predictions) else 1


if __name__ == "__main__":
    raise SystemExit(main())
