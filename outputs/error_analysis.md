# Error Analysis: Real-Paper Evaluation

## Scope and method

This report is generated from deterministic comparisons. Exact and normalized metrics are observations. Error labels are rule-based interpretations and do not change either score. No LLM judge is used. A non-null prediction against a reference-null field is a disagreement requiring manual review, not automatic evidence of hallucination.

## Observations

- Exact mismatches: 27
- Normalized mismatches: 23
- Exact matches after normalization only: 4

### Category counts

- abbreviation/terminology difference: 12
- missing information: 0
- other content mismatch: 0
- overly broad extraction: 0
- overly specific extraction: 10
- reference-null disagreement (manual review required): 1
- semantically equivalent but lexically different: 4

### Mismatch details

#### real_001 — study_design

- Expected: `randomized crossover study`
- Predicted: `Randomized crossover study`
- Normalized match: True
- Heuristic category: semantically equivalent but lexically different

#### real_001 — population

- Expected: `healthy adults aged 18–35 with weekly running volume of 2–5 h and BMI < 30`
- Predicted: `Healthy adults aged 18–35 years with a weekly running volume of 2–5 h and BMI <30`
- Normalized match: False
- Heuristic category: overly specific extraction

#### real_001 — intervention_or_exposure

- Expected: `high-intensity interval exercise and moderate-intensity continuous exercise`
- Predicted: `High-intensity interval exercise (HIIE) and moderate-intensity continuous exercise (MICE) sessions`
- Normalized match: False
- Heuristic category: overly specific extraction

#### real_001 — biospecimen

- Expected: `peripheral blood mononuclear cells isolated from EDTA whole blood`
- Predicted: `Whole blood collected in EDTA tubes; peripheral blood mononuclear cells (PBMCs)`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

#### real_001 — duration_or_timepoints

- Expected: `baseline, immediately after exercise, and 1 h after exercise; at least 72 h between visits`
- Predicted: `Three visits (baseline testing, HIIE, MICE) with at least 72 h between visits; blood collected at baseline, immediately after exercise, and 1 h after exercise`
- Normalized match: False
- Heuristic category: overly specific extraction

#### real_002 — study_design

- Expected: `null`
- Predicted: `IMPOCT study; metformin-versus-placebo analysis in healthy participants`
- Normalized match: False
- Heuristic category: reference-null disagreement (manual review required)

#### real_002 — population

- Expected: `healthy participants without diabetes`
- Predicted: `Healthy participants without diabetes`
- Normalized match: True
- Heuristic category: semantically equivalent but lexically different

#### real_002 — intervention_or_exposure

- Expected: `metformin treatment`
- Predicted: `Metformin or placebo; metformin was titrated to a maximum dose of 1000 mg twice daily, taken during the final week`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

#### real_002 — biospecimen

- Expected: `blood`
- Predicted: `Blood`
- Normalized match: True
- Heuristic category: semantically equivalent but lexically different

#### real_002 — measurement_method

- Expected: `Olink panels`
- Predicted: `Protein levels measured using various Olink panels`
- Normalized match: False
- Heuristic category: overly specific extraction

#### real_002 — duration_or_timepoints

- Expected: `baseline and after 4 weeks of metformin treatment`
- Predicted: `Metformin treatment for 4 weeks; blood measurements at baseline and after 4 weeks`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

#### real_003 — study_design

- Expected: `acute exercise trial`
- Predicted: `Acute exercise study with repeated microdialysis sampling`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

#### real_003 — population

- Expected: `male participants`
- Predicted: `Six male participants`
- Normalized match: False
- Heuristic category: overly specific extraction

#### real_003 — intervention_or_exposure

- Expected: `one-legged knee extension exercise to exhaustion`
- Predicted: `One-legged knee extension exercise in the fed state, followed by recovery`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

#### real_003 — biospecimen

- Expected: `vastus lateralis muscle microdialysis samples`
- Predicted: `Microdialysis samples from the vastus lateralis muscle`
- Normalized match: False
- Heuristic category: overly specific extraction

#### real_003 — measurement_method

- Expected: `nanoflow high-performance liquid chromatography coupled to Q Exactive H-FX mass spectrometry`
- Predicted: `Easy nanoflow high-performance liquid chromatography coupled to a Q Exactive H-FX mass spectrometer`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

#### real_003 — duration_or_timepoints

- Expected: `before and during exercise, and 22–30 min and 160–180 min after exercise`
- Predicted: `180-min recovery period; samples collected before exercise (−30 to −5 min), during exercise (1 to 8 min and 11 to 18 min), and during early (22 to 30 min after exercise) and late (160 to 180 min after exercise) recovery`
- Normalized match: False
- Heuristic category: overly specific extraction

#### real_004 — study_design

- Expected: `comparison of insulin-resistant and insulin-sensitive groups`
- Predicted: `Observational comparison of insulin-resistant and insulin-sensitive groups defined by euglycemic clamp`
- Normalized match: False
- Heuristic category: overly specific extraction

#### real_004 — population

- Expected: `healthy non-diabetic adults aged 21–70 with BMI 20–35 kg/m2`
- Predicted: `Healthy non-diabetic adults aged 21–70 years with BMI 20–35 kg/m²; 8 men and 15 women`
- Normalized match: False
- Heuristic category: overly specific extraction

#### real_004 — intervention_or_exposure

- Expected: `insulin-resistant versus insulin-sensitive status`
- Predicted: `Insulin resistance versus insulin sensitivity, classified using predefined euglycemic clamp criteria`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

#### real_004 — biospecimen

- Expected: `subcutaneous abdominal adipose tissue biopsy`
- Predicted: `Adipose tissue biopsy (5–7 g) lateral to the umbilicus`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

#### real_004 — measurement_method

- Expected: `one-dimensional gel electrophoresis followed by HPLC-ESI-MS/MS using a hybrid linear ion trap–Fourier Transform Ion Cyclotron Resonance mass spectrometer`
- Predicted: `One-dimensional gel electrophoresis followed by HPLC-ESI-MS/MS using a hybrid linear ion trap–Fourier Transform Ion Cyclotron Resonance mass spectrometer`
- Normalized match: True
- Heuristic category: semantically equivalent but lexically different

#### real_005 — population

- Expected: `healthy sedentary individuals aged 17–65 from families of European and African descent`
- Predicted: `Healthy, sedentary individuals from families of European and African descent; 38% African ancestry; age range 17–65 years; free from cardiometabolic disease`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

#### real_005 — intervention_or_exposure

- Expected: `supervised endurance exercise 3 times per week, progressing from 30 to 50 min/session and 55% to 75% VO2max`
- Predicted: `Supervised endurance exercise 3 times per week for 20 weeks; 30 to 50 minutes per session; intensity increased from heart rate associated with 55% VO2max to that associated with 75% VO2max`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

#### real_005 — biospecimen

- Expected: `plasma`
- Predicted: `Plasma samples`
- Normalized match: False
- Heuristic category: overly specific extraction

#### real_005 — measurement_method

- Expected: `approximately 5000-plex SOMAscan aptamer-based proteomics`
- Predicted: `Approximately 5000-plex SOMAscan platform using aptamer reagents and a multistep capture, release, and recapture enrichment process to measure plasma proteins`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

#### real_005 — duration_or_timepoints

- Expected: `20 weeks; before training and at least 24 hours after the last session`
- Predicted: `20 weeks; plasma collected at rest before the program and again at least 24 hours after the last session`
- Normalized match: False
- Heuristic category: abbreviation/terminology difference

## Interpretations

The labels above are conservative lexical heuristics. “Overly broad” means the prediction's normalized token set is a strict subset of the reference; “overly specific” means the reverse. “Abbreviation/terminology difference” indicates partial lexical overlap or moderate string similarity, not proven semantic equivalence. A reference-null disagreement may reflect unsupported content, annotation ambiguity, or an underspecified schema. Manual review is required before drawing research conclusions from these labels.

## Limitations

This analysis covers five excerpts and 35 fields. Ground truth is bounded to the stored excerpts, so it does not represent every fact in the full papers. Deterministic normalization cannot recognize all paraphrases, and the heuristic categories can overlap conceptually even though this report assigns one primary label per mismatch.
