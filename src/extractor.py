import json
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()
client = OpenAI()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_FILE = PROJECT_ROOT / "data" / "samples.json"
OUTPUT_FILE = PROJECT_ROOT / "outputs" / "predictions.json"


# --------------------------------------------------
# Metadata schema
# --------------------------------------------------

class ScientificMetadata(BaseModel):
    sample_type: Optional[str]
    sample_size: Optional[int]
    experimental_method: Optional[str]
    intervention: Optional[str]
    duration: Optional[str]


# --------------------------------------------------
# LLM extraction
# --------------------------------------------------

def extract_metadata(text: str) -> ScientificMetadata:
    response = client.responses.parse(
        model="gpt-5-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are a scientific metadata extraction system. "
                    "Extract only information explicitly stated in the text. "
                    "Do not infer or invent missing information. "
                    "If a field is not stated, return null."
                ),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        text_format=ScientificMetadata,
    )

    return response.output_parsed


# --------------------------------------------------
# Main pipeline
# --------------------------------------------------

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as file:
        samples = json.load(file)

    predictions = []

    for sample in samples:
        print(f"Processing {sample['id']}...")

        metadata = extract_metadata(sample["text"])

        result = {
            "id": sample["id"],
            **metadata.model_dump(),
        }

        predictions.append(result)

        print(json.dumps(result, indent=2))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(predictions, file, indent=2, ensure_ascii=False)

    print(f"\nSaved predictions to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()