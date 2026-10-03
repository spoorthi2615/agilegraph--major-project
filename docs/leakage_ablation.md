# Leakage Ablation Experiment Interface

## The Requirement
A critical research requirement is verifying that the GATv2 model learns structural context, rather than trivially memorizing the heuristic `base_risk` label during weak supervision.

## Implementation Strategy
The `FeatureConfig` enforces a strict boolean `include_base_risk` toggle (defaulting to `False`). 

- When `True`: Feature dimension becomes 8. The `base_risk` is explicitly injected into the node features.
- When `False`: Feature dimension remains 7. The `base_risk` is strictly excluded.

This configurable toggle will drive the formal leakage-ablation study during the statistical evaluation phase.
