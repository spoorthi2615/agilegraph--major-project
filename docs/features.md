# Feature Schema and Targets

## Node Features
The feature extraction layer strictly parses the 7 context factors defined in the Asset-Context phase. Missing factors are explicitly padded to `0.0`. 
Feature tensor dimensions default to 7. 

## Target Labels & Weak Supervision
The `extract_target_label` explicitly identifies the provenance of the label (`EXPERT`, `HEURISTIC`, `SYNTHETIC`, `UNKNOWN`). 
- **The heuristic score is a weak-supervision signal, NOT ground truth.**
- The training pipeline will refuse execution (`MissingLabelsError`) if invoked on a dataset devoid of explicitly identified labels.

## Synthetic Fixtures
Tiny deterministic synthetic graphs (`SYNTHETIC_TEST_DATA`) exist exclusively in `tests/ml/` to validate model forward-passes, tensor shapes, and bounds checking. They are NOT real security assessments.
