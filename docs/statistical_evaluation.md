# Statistical Evaluation

**Status: EXPERIMENTAL RESULTS PENDING**

## Agreement Metrics
- **Weighted Cohen's Kappa**: `IMPLEMENTED`. Computes inter-rater reliability for ordinal labels (HIGH/MEDIUM/LOW).
- **Fleiss' Kappa**: `IMPLEMENTED`. Supports evaluation of agreement among multiple raters (≥4).
- **Macro-F1 / Precision / Recall**: `IMPLEMENTED`.

## Robustness
- **Missing Ratings**: Gracefully handled by isolating `UNKNOWN` or abstentions from kappa scoring.
- **Insufficient Data**: `IMPLEMENTED` strict exceptions when overlaps or raters do not meet mathematical minimums.

## Significance Testing
- Bootstrap confidence intervals and paired permutation testing are `IMPLEMENTED`.
- Evaluation on genuine human labels is `PENDING`.
- No claims of statistical significance will be manufactured before true labeled outcomes are recorded.
