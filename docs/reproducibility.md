# Reproducibility and Splits

## Snapshotting
AgileGraph relies on deterministic, reproducible infrastructure. Datasets are bound to specific `commit_sha` values rather than branch heads. Repositories must be locked to a specific commit during acquisition.

## Project-Level Split Strategy
To prevent trivial memorization and data leakage across the train/test sets, splits are performed strictly at the **repository (project) level**. 

A single repository will never have some files assigned to the training set and others assigned to the test set.

## Deterministic Seeding
Splits are generated using a deterministic random number generator controlled by a fixed `seed`. The resulting configuration is saved in the `DatasetArtifact` metadata, ensuring that anyone with the `manifest_id` and `seed` can exactly reproduce the split.

## Limitations
- We have not yet verified the statistical distribution of the 8-10 planned repositories. When the corpus is acquired, we may need to implement stratified splitting (by language or size) instead of purely uniform shuffling to ensure balanced classes.
