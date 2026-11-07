# Record of Research Terminology Corrections

**Date**: November 2026  
**Auditor**: Senior Applied Cryptography Researcher & ML Evaluation Specialist  
**Purpose**: Align all AgileGraph academic reports and documentation with precise scientific evaluation terminology, completely excising unsupported claims of "confirmatory" validation.

---

## 1. Canonical Terminology Standard

The following descriptions are now enforced across the entire repository:

1. **V1 Fixed**: `Original baseline point evaluation`
   - Evaluation with fixed universal thresholds ($0.30 / 0.60$) on the 160-asset consensus corpus.
2. **V1 LORO**: `Cross-validated calibrated-threshold baseline`
   - Evaluation of raw continuous scores under Leave-One-Repository-Out cross-validation, isolating the contribution of threshold calibration without graph propagation.
3. **V2 LORO**: `Cross-validated calibrated heuristic with graph weakness propagation`
   - Evaluation of threshold calibration combined with semantic graph weakness propagation ($\alpha = 0.55$) under Leave-One-Repository-Out cross-validation.
4. **Experiment 3**: `Post-hoc exploratory asymmetric-specific propagation ablation`
   - Offline research ablation restricting graph weakness propagation strictly to Shor-vulnerable asymmetric primitives, conceptualized after test-corpus error analysis.

---

## 2. Epistemological Distinctions Enforced

The documentation explicitly demarcates the following boundaries:

- **Internal Point Evaluation**: Evaluates fixed heuristic formulas directly against the corpus.
- **Internal Cross-Validation (LORO)**: Measures stability and prevents overfitting across held-out repositories within the benchmark corpus. **Cross-validation alone does not constitute proof of external generalization.**
- **Exploratory Method Development**: Denotes models where algorithmic rules or feature filters were informed by examining errors on the evaluation dataset.
- **Independent External Validation**: Formally designated as Future Work, requiring testing frozen models on external, independently curated repositories (e.g., Google Tink, Bouncy Castle).

---

## 3. Summary of Files Updated

| File | Changes Made |
| :--- | :--- |
| `FINAL_METRIC_RECONCILIATION.md` | Replaced "Confirmatory Baseline / Confirmatory Experimental" with "Internal Point Evaluation" and "Internal LORO Cross-Validation". Added explicit methodological caveat. |
| `FINAL_RESEARCH_HANDOVER.md` | Updated Section 2.2 comparison table headers and descriptions; rewritten Section 4 to explicitly distinguish Internal Cross-Validation, Exploratory Method Development, and External Validation. |
| `VIVA_PREPARATION.md` | Replaced "exploratory-to-confirmatory leakage" with "test-set-informed method development" and reinforced the canonical descriptions. |
| `docs/evaluation.md` | Standardized Section 9.3 comparison table to use V1 Fixed, V1 LORO, V2 LORO, and Experiment 3 canonical naming, with explicit notes on external generalization. |
| `docs/risk_formula.md` | Updated Section 11 to describe Candidate V3-Alpha as a "post-hoc exploratory asymmetric-specific propagation ablation". |
| `README.md` | Standardized Section 8 validation summary to explicitly contrast V1 Fixed, V1 LORO, V2 LORO, and Experiment 3. |

All numerical values, bootstrap confidence intervals, and confusion matrices were preserved with 100% fidelity.

