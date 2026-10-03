# Expert Validation

**Status: EXPERT LABELS PENDING**

## Overview
Phase 13 establishes the rigorous human-validation infrastructure for AgileGraph. 
A deterministically isolated held-out set of ~150-200 assets is prepared for multi-rater expert annotation.

## Infrastructure
- **Held-out Sampling (`IMPLEMENTED`)**: `sample_held_out_assets` reliably samples the non-training subset deterministically.
- **Expert Schema (`IMPLEMENTED`)**: Models `Expert`, `AssetForReview`, `ExpertLabel`, `ValidationSession`, and `ValidationDataset` support a `asset × expert → label` mapping without conflicts.
- **Aggregation Design (`IMPLEMENTED`)**: Enables consensus evaluation via methods like `MAJORITY_VOTE` without overriding original individual judgements.
- **Privacy Handling (`IMPLEMENTED`)**: Uses strictly pseudonymous `expert_id` handles. No PII is collected or stored.

## Research-Integrity Constraints
- No expert identity, rating, or consensus label may be fabricated.
- Synthetic testing ratings are strictly partitioned from the authentic production workflow (`TESTED`).
- Genuine expert annotation can now begin, but currently remains `PENDING`.
