# GATv2 Model Architecture

## Status
`MODEL INFRASTRUCTURE: IMPLEMENTED + TESTED`
`REAL TRAINING: PENDING CORPUS/LABELS`
`EXPERIMENTAL RESULTS: NOT AVAILABLE`

## Architecture Design
The AgileGraph model utilizes a Heterogeneous Graph Attention Network (GATv2) built with PyTorch Geometric (`torch_geometric`). The `create_hetero_gatv2` function dynamically wraps a homogenous GATv2 using PyG's `to_hetero` transformation, enabling message passing across all 6 specific node categories and typed edges.

## Graph Conversion
The deterministic `convert_agilegraph_to_pyg` interface safely bridges the operational NetworkX `AgileGraph` into a PyG `HeteroData` tensor structure. It preserves:
- Node types and Edge types
- Node identities (via the `node_ids` manifest)
- Feature tensor extraction
- Label provenance (`label_sources`)

## Evaluation and Explainability Hooks
Interfaces are prepared for future empirical validation, including Macro-F1 scoring, confusion matrices, class-wise precision/recall, and GNNExplainer hooks for node/edge/feature attention importance. 

**Note: No expert data currently exists. Do not assume or fabricate training capabilities until Phase 9 actualizes the real dataset.**
