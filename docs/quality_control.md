# Quality Control Checkpoints

To ensure research correctness, methodology alignment, and strictly prevent the fabrication of results or capabilities, a mandatory quality-control checkpoint must be executed after every 5 completed phases. 

Development of new features MUST STOP at these checkpoints to perform a full audit against the AgileGraph synopsis.

## Mandatory Checkpoint Schedule

| Checkpoint | Phases | Status  | Tests | Issues | Resolved |
|------------|--------|---------|-------|--------|----------|
| QC-1       | 0–4    | PASSED  | 53/53 | 0      | YES      |
| QC-2       | 5–9    | PASSED  | 53/53 | 3      | YES      |
| QC-3       | 10–14  | PENDING |       |        |          |
| FINAL      | 15–16  | PENDING |       |        |          |

## Audit Verification Criteria

At each checkpoint, the following 10 areas must be verified:

1. **Synopsis compliance**: Does the implementation still match the project synopsis?
2. **No fabricated data**: No fake expert labels, fake CVEs, fake benchmark results, fake statistical significance, or invented real-world scan results.
3. **No misleading claims**: README matches actual functionality, documentation matches implementation, comments don't claim unsupported capabilities, limitations are explicitly documented.
4. **Reproducibility**: Fresh environment/install where practical, tests pass, deterministic components are reproducible, experiment configuration is recorded.
5. **Data provenance**: Every external dataset has a source, scanner findings retain evidence, expert labels are distinguishable from generated/weak labels, synthetic fixtures are clearly marked synthetic.
6. **ML integrity**: No train/test leakage, heuristic labels aren't accidentally treated as ground truth, leakage-ablation is actually implemented, baseline comparisons are fair.
7. **Security/ethics**: Active TLS scanning remains authorization-gated, no unauthorized scanning workflow, secrets aren't committed, credentials aren't hardcoded.
8. **Test coverage**: Existing tests still pass, new functionality has tests, integration tests cover the pipeline.
9. **Documentation**: Architecture reflects the real implementation, methodology reflects what was actually done, unresolved limitations are recorded.
10. **Research honesty**: Distinguish explicitly between IMPLEMENTED, TESTED, EXPERIMENTAL, PLANNED, and UNKNOWN. Never turn PLANNED into IMPLEMENTED in documentation.
