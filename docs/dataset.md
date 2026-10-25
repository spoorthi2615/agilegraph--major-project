# AgileGraph Dataset & Corpus Construction

## Corpus Status
**CORPUS INFRASTRUCTURE: IMPLEMENTED**
**CANONICAL BENCHMARK CORPUS: ACQUIRED & PINNED**

AgileGraph evaluates against 8 pinned open-source benchmark repositories spanning Python, Java, and Go, totaling 4,558 committed source files and 1,458 evaluated file nodes. Every repository is pinned to an immutable commit SHA and archived locally with verified provenance.

## Dataset Schema
The corpus relies on strong Pydantic typing to preserve provenance:
- `CorpusManifest`: The unified tracker for all acquired projects (`benchmark_manifest.json`).
- `CorpusProject`: Represents a single repository snapshot with an immutable commit SHA. Tracks the transition from `PLANNED` -> `ACQUIRED` -> `SCANNED` -> `GRAPH_BUILT` -> `RISK_SCORED` -> `READY_FOR_MODELING`.
- `DatasetArtifact` & `DatasetMetadata`: A frozen dataset snapshot representing a specific project-level split.

## Provenance
Every `READY_FOR_MODELING` project must provide:
- `checkout_timestamp`
- `commit_sha`
- `ScannerProvenance` (scanner tools version)
- `GraphProvenance` (graph and heuristic versions)

Data Origins are strictly classified into `PUBLIC_OPEN_SOURCE`, `SYNTHETIC`, `USER_AUTHORIZED`, or `UNKNOWN`.

## Benchmark Repositories
The 8 canonical benchmark repositories are:
1. `python_itsdangerous` (commit `672971d`, 50 files)
2. `python_bcrypt` (commit `59b41aa`, 23 files)
3. `python_cryptography` (commit `f0ba300`, 3,072 files)
4. `java_java_jwt` (commit `9b626e9`, 134 files)
5. `java_jjwt` (commit `ef7d934`, 733 files)
6. `go_jwt` (commit `99580d4`, 77 files)
7. `go_jwt_go` (commit `2e8df31`, 51 files)
8. `go_crypto` (commit `ebd54e8`, 418 files)
