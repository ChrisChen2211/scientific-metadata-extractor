# Scientific Metadata Extractor

This repository is a small research prototype for evaluating whether an LLM can extract structured study metadata from scientific-paper excerpts. It is **not a validated scientific system** and its outputs must not be used for clinical, regulatory, or evidence-synthesis decisions without expert review.

## Research question

How accurately can a cost-efficient language model extract a fixed metadata schema from short biomedical and proteomics paper excerpts while abstaining (`null`) when an excerpt does not support a field?

## Motivation

Scientific study descriptions are often distributed across prose, making them difficult to compare automatically. Structured extraction may reduce manual effort, but an evaluation must distinguish lexical disagreement, semantic disagreement, and genuinely unsupported claims. This project therefore keeps the input excerpt, manually verified ground truth, raw prediction, deterministic metrics, automated lexical analysis, and human semantic audit separate.

## Pipeline

```text
Scientific paper excerpts
        |
        v
Structured LLM extraction
        |
        v
JSON predictions
        |
        +--------> Ground truth
        |              |
        v              v
   Deterministic metrics
         |          |
         v          v
 Lexical analysis   Human semantic audit
```

The real-data extractor uses the OpenAI Responses API with Pydantic structured output. The prompt explicitly limits the model to the stored excerpt, forbids outside knowledge and unsupported inference, and requires `null` when evidence is unavailable. The default model is `gpt-5.6-luna`, selected as a cost-sensitive model for this bounded extraction task. Override it with `--model` or `OPENAI_EXTRACTION_MODEL`.

## Metadata schema

Every real-paper prediction contains:

- `study_design`
- `population`
- `sample_size`
- `intervention_or_exposure`
- `biospecimen`
- `measurement_method`
- `duration_or_timepoints`

All fields except `sample_size` are nullable strings; `sample_size` is a nullable integer. Ground-truth values describe only facts explicitly present in each stored excerpt, not facts found elsewhere in the full paper.

## Datasets

### Synthetic development set

The original three-example experiment is preserved in [`data/samples.json`](data/samples.json) and [`data/ground_truth.json`](data/ground_truth.json). Its original schema and scripts remain available through `src/extractor.py` and `src/evaluator.py`.

### Real-paper evaluation set

[`data/real/samples.json`](data/real/samples.json) contains five short, manually selected excerpts from open-access PubMed Central papers. [`data/real/ground_truth.json`](data/real/ground_truth.json) contains excerpt-bounded annotations. Two of the 35 reference fields are deliberately `null` because the corresponding excerpts do not explicitly support a value.

Papers used:

1. Walzik D et al., “Acute exercise rewires the proteomic landscape of human immune cells,” *Nature Communications* (2026), [PMC12775541](https://pmc.ncbi.nlm.nih.gov/articles/PMC12775541/), DOI 10.1038/s41467-025-68101-9.
2. Connolly B et al., “The influence of metformin treatment on the circulating proteome,” *eBioMedicine* (2025), [PMC12301841](https://pmc.ncbi.nlm.nih.gov/articles/PMC12301841/), DOI 10.1016/j.ebiom.2025.105859.
3. Stocks B et al., “Temporal dynamics of the interstitial fluid proteome in human skeletal muscle following exhaustive exercise,” *Science Advances* (2025), [PMC11784852](https://pmc.ncbi.nlm.nih.gov/articles/PMC11784852/), DOI 10.1126/sciadv.adp8608.
4. Xie X et al., “Proteomics Analyses of Subcutaneous Adipocytes Reveal Novel Abnormalities in Human Insulin Resistance,” *Obesity* (2016), [PMC4926648](https://pmc.ncbi.nlm.nih.gov/articles/PMC4926648/), DOI 10.1002/oby.21528.
5. Robbins JM et al., “Plasma proteomic changes in response to exercise training are associated with cardiorespiratory fitness adaptations,” *JCI Insight* (2023), [PMC10132160](https://pmc.ncbi.nlm.nih.gov/articles/PMC10132160/), DOI 10.1172/jci.insight.165867.

## Evaluation methodology

`src/evaluate_real.py` reports:

1. Exact field match using Python value equality.
2. Normalized field match using Unicode NFKC normalization, case folding, punctuation-to-space conversion, and whitespace collapse.
3. Exact and normalized results for every field and sample.
4. Overall field-level and complete-sample results.
5. Reference-null behavior, including correct nulls and disagreements between null references and non-null predictions.

Normalization contains no paper-specific synonyms or hand-tuned aliases. Semantic judging is not included in the reported accuracy. The error-analysis labels use transparent lexical heuristics and remain separate from both metrics. A non-null prediction against a reference-null field is recorded as a disagreement requiring human review, not automatically as a hallucination.

## Manual semantic audit

[`data/real/manual_semantic_audit.json`](data/real/manual_semantic_audit.json) is a 35-item human semantic-review worksheet generated from the stored excerpts, references, and predictions. Chris Chen individually reviewed and approved every label and rationale. Codex prepared the comparison worksheet and draft rationales; the recorded decisions are the named auditor's judgments.

- **Correct:** preserves all scientifically important reference information; abbreviations, paraphrases, and additional excerpt-supported detail are allowed.
- **Partially correct:** preserves the core metadata but omits or changes important information.
- **Incorrect:** changes the core scientific meaning.
- **Unsupported:** contains information the stored excerpt cannot support.

The reviewer must add a rationale for every completed judgment and can separately mark `schema_ambiguity`. `src/manual_semantic_audit.py` validates completeness and produces a summary only after all 35 fields have been reviewed and the auditor and date are recorded. The audit file records both the human auditor and the use of an AI-prepared worksheet.

The `real_002` `study_design` item is marked `Correct` by the human auditor. Its reference is `null`, but the excerpt names the IMPOCT study and describes a metformin-versus-placebo analysis. Under the broad `study_design` field used here, the auditor accepted the prediction as a supported description. The automated evaluator still reports the deterministic reference-null disagreement, and the reference was not changed to improve the score.

## Results

The current working tree was evaluated on 2026-09-29 with `gpt-5.6-luna`:

| Metric | Result |
|---|---:|
| Exact field match | 8/35 (22.9%) |
| Normalized field match | 12/35 (34.3%) |
| Samples with all fields normalized-correct | 0/5 |
| Correct nulls | 1/2 (50.0%) |
| Non-null predictions on reference-null fields | 1 (manual review required) |
| Null predictions on supported-reference fields | 0 |

`sample_size` was the strongest field at 5/5 exact. Many otherwise plausible predictions contained additional excerpt-supported detail or paraphrased the reference, so deterministic string metrics remained intentionally strict. The 22.9% and 34.3% figures measure lexical agreement, not manually established semantic accuracy. These are results from one small run, not evidence of general scientific validity. A new API run may differ.

Machine-readable details are written to `outputs/evaluation_results.json`.

### Human semantic audit

The human-reviewed rubric produced the following separate result:

| Semantic label | Result |
|---|---:|
| Correct | 34/35 (97.1%) |
| Partially correct | 1/35 (2.9%) |
| Incorrect | 0/35 (0.0%) |
| Unsupported | 0/35 (0.0%) |
| Correct or partially correct | 35/35 (100.0%) |

One annotation/schema ambiguity was recorded: `real_004.biospecimen`, where the reference says “subcutaneous abdominal” although those words are not directly present in the model's stored excerpt. `real_003.intervention_or_exposure` was the only partially correct item because the prediction omitted the “to exhaustion” endpoint. These are single-reviewer judgments and remain subjective despite the explicit rubric.

## Error analysis

`outputs/error_analysis.md` is generated automatically and separates observations from interpretations. In the recorded run it reported:

- 27 exact mismatches and 23 normalized mismatches;
- 4 formatting/case differences that matched after normalization;
- 10 overly specific extractions under the token-subset heuristic;
- 12 abbreviation or terminology differences;
- 1 non-null prediction for a reference-null field, requiring manual adjudication;
- no overly broad extractions and no missing supported values.

The category labels are heuristics, not semantic ground truth. In particular, “abbreviation/terminology difference” indicates lexical overlap or string similarity and still requires manual review. The ten token-subset labels must not be presented as ten confirmed “overly specific errors.”

## Limitations

- Five excerpts and 35 fields are too small for reliable generalization or statistical claims.
- Excerpts are selected from biomedical, proteomics, metabolism, and exercise studies and are not representative of all scientific literature.
- Ground truth is manually derived and bounded to selected sentences; it does not summarize each full paper.
- Exact and normalized matching penalize valid paraphrases.
- The lexical error categories can misclassify nuanced semantic differences.
- Only two reference fields are null, so null-reference behavior is especially uncertain.
- The semantic audit has one named reviewer and no inter-annotator agreement measurement; the worksheet and draft rationales were prepared with AI assistance before human verification.
- Model aliases and model behavior can change; API availability and outputs depend on the caller's account and run date.
- No inter-annotator agreement, external validation set, or clinical validation is provided.

## Reproducibility and setup

Python 3.9 or newer is required. Dependencies are pinned in `requirements.txt`. The project expects `OPENAI_API_KEY` in a local `.env`; `.env` is ignored and must never be committed or printed.

```bash
cd /path/to/scientific-metadata-extractor
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Edit .env locally and add a newly created OPENAI_API_KEY.
```

Run the real-paper pipeline end to end:

```bash
python src/extract_real.py
python src/evaluate_real.py
python src/manual_semantic_audit.py validate
python -m unittest discover -s tests -v
python -m json.tool data/real/samples.json >/dev/null
python -m json.tool data/real/ground_truth.json >/dev/null
python -m json.tool outputs/real_predictions.json >/dev/null
python -m json.tool outputs/evaluation_results.json >/dev/null
```

Generated files:

- `outputs/real_predictions.json`: model ID, response IDs, statuses, and structured predictions.
- `outputs/evaluation_results.json`: metric policy, aggregate and per-field metrics, null-reference behavior, and sample-level comparisons.
- `outputs/error_analysis.md`: mismatch details and cautious rule-based interpretations.
- `data/real/manual_semantic_audit.json`: completed human-reviewed worksheet containing all 35 labels, rationales, and ambiguity flags.
- `outputs/manual_semantic_audit_results.json` and `outputs/manual_semantic_audit.md`: semantic-review summary and report.

To validate or regenerate the semantic summary, run:

```bash
python src/manual_semantic_audit.py validate
python src/manual_semantic_audit.py summarize
```

`summarize` exits without publishing results while any item remains `Unreviewed`. For an independent human audit, initialize a fresh worksheet, have the reviewer complete it without seeing these labels if possible, and record that reviewer and method explicitly.

The extractor writes an atomic checkpoint after every sample and records API errors per sample. Use `--fail-fast` to stop at the first API error. To rerun with another available model:

```bash
python src/extract_real.py --model MODEL_ID
python src/evaluate_real.py
```

The original synthetic experiment can still be run independently:

```bash
python src/extractor.py
python src/evaluator.py
```

## Repository hygiene

`.env`, `.venv`, `.idea`, raw prediction files, and temporary output files are ignored. The shareable deterministic artifacts `outputs/evaluation_results.json` and `outputs/error_analysis.md` are not ignored, so reviewers can inspect the experiment without receiving credentials or raw API response identifiers. Before sharing an archive, verify its contents explicitly rather than relying on `.gitignore`, because ignore rules do not control arbitrary ZIP creation.
