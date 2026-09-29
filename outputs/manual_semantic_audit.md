# Manual Semantic Audit

Method: Human semantic audit by Chris Chen; an AI-prepared comparison worksheet and draft rationales were individually reviewed and approved by the auditor.

- Auditor: Chris Chen
- Audit date: 2026-09-29
- Model: gpt-5.6-luna
- Fields reviewed: 35

## Results

| Label | Count | Percentage |
|---|---:|---:|
| Correct | 34 | 97.1% |
| Partially correct | 1 | 2.9% |
| Incorrect | 0 | 0.0% |
| Unsupported | 0 | 0.0% |
| Correct or partially correct | 35 | 100.0% |

## Schema ambiguities

### real_004 — biospecimen

- Ground truth: `subcutaneous abdominal adipose tissue biopsy`
- Prediction: `Adipose tissue biopsy (5–7 g) lateral to the umbilicus`
- Label: Correct
- Rationale: The prediction accurately reports the excerpt's adipose tissue biopsy, mass, and location. The reference adds 'subcutaneous abdominal,' which is not directly stated in the model's stored excerpt, so the reference annotation itself is broader than the excerpt evidence.


## Limitations

This review covers five excerpts and 35 fields. Its recorded method is shown above; it is not an independent domain-expert validation or an inter-annotator agreement study.
