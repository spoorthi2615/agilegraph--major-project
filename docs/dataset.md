# AgileGraph Dataset & Corpus Construction

## Corpus Status
**CORPUS INFRASTRUCTURE: IMPLEMENTED**
**ACTUAL CORPUS: PENDING**

Currently, the pipeline supports ingesting, validating, and snapshotting repositories, but the physical 8-10 target public repositories have not yet been acquired and processed. 

## Dataset Schema
The corpus relies on strong Pydantic typing to preserve provenance:
- `CorpusManifest`: The unified tracker for all acquired projects.
- `CorpusProject`: Represents a single repository snapshot with an immutable commit SHA. Tracks the transition from `PLANNED` -> `ACQUIRED` -> `SCANNED` -> `GRAPH_BUILT` -> `RISK_SCORED` -> `READY_FOR_MODELING`.
- `DatasetArtifact` & `DatasetMetadata`: A frozen dataset snapshot representing a specific project-level split.

## Provenance
Every `READY_FOR_MODELING` project must provide:
- `checkout_timestamp`
- `commit_sha`
- `ScannerProvenance` (scanner tools version)
- `GraphProvenance` (graph and heuristic versions)

Data Origins are strictly classified into `PUBLIC_OPEN_SOURCE`, `SYNTHETIC`, `USER_AUTHORIZED`, or `UNKNOWN`.

## Synthetic-Data Separation
Synthetic fixtures are labeled with `SYNTHETIC` origin and require explicit `SYNTHETIC_TEST_DATA` metadata. The split mechanism strictly prevents combining synthetic fixtures with real-world repositories during modeling.
