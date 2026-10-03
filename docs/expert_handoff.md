# Expert Validation Handoff Package

**Status: EXPERT LABELS PENDING**
**Protocol Status: PENDING FINALIZATION**

This package prepares the environment for genuine expert annotations. Do not populate this with synthetic data or fake expert identities. 

## Contents
1. **Annotation Protocol**: Defined in `docs/annotation_protocol.md`. This MUST reach `FINALIZED` status before empirical evaluation begins.
2. **Validation Sampling Configuration**: 150-200 held-out assets strictly separated from the 5 project training split via `src/ml/sampling.py`.
3. **Asset Manifest Template**: (Generated dynamically by Phase 14 validation generation script once protocol is finalized).
4. **Annotation Schema**: Strictly requires `asset_id`, `expert_id`, `label`, `timestamp`, `dataset_version`, and `annotation_protocol_version`.
5. **Expert Instructions**: Read `docs/annotation_protocol.md`. Evaluate asset risk using domain expertise. Use `UNKNOWN` if an asset cannot be reasonably assessed. Do NOT use the heuristic score as a crutch; it is an initial estimate, not ground truth.
6. **Pseudonymous Expert-ID Mechanism**: You will be assigned a non-PII identifier (e.g., `expert_01`). 
7. **Import Format**: A JSON list of annotation dictionaries conforming to the schema above.
8. **Validation Checks**: The strict importer (`src/ml/import_annotations.py`) will automatically reject unknown assets, unknown raters, malformed data, or submissions prior to protocol finalization.

## Next Steps
When the protocol is finalized and genuine experts are identified, run the dataset generation script to produce the target asset list. Distribute the assets, collect the annotations in JSON, and use the importer to construct the validation dataset.
