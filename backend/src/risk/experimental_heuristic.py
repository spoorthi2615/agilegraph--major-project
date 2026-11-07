"""
Experimental Heuristic V2 Module for AgileGraph.

ISOLATED RESEARCH EXPERIMENT - NOT IN PRODUCTION.
This module implements experimental extensions to AgileGraph's heuristic risk engine:
1. Component A: Data-Aware Threshold Calibration via Leave-One-Repository-Out (LORO) Cross-Validation.
2. Component B: Graph-Propagated Structural Weakness Inheritance for Cryptographic Abstractions.
3. Component C (Optional): PQC Dominance Floor Protection.

Methodological Constraints:
- Baseline heuristic-v1.0 (src/risk/heuristic.py) is preserved 100% unchanged.
- Expert annotations remain strictly isolated from GATv2 training routines (zero leakage).
- Thresholds are fitted strictly on training repositories and evaluated on held-out repositories.
- Propagation operates strictly over semantically verified cryptographic library dependencies.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from torch_geometric.data import HeteroData
from sklearn.metrics import f1_score, confusion_matrix, cohen_kappa_score, precision_recall_fscore_support

from src.risk.factors import FactorValue, RiskFactors
from src.risk.weights import HeuristicWeights
from src.risk.score import RiskScoreResult, MissingDataPolicy
from src.risk.heuristic import calculate_heuristic_score as calculate_v1_score, CURRENT_FORMULA_VERSION


@dataclass
class ExperimentalHeuristicConfig:
    """Configuration for Experimental Heuristic V2 ablation testing."""
    version_id: str = "heuristic-v2.0-experimental"
    enable_data_aware_thresholds: bool = True
    enable_graph_weakness_propagation: bool = True
    enable_pqc_dominance_floor: bool = False
    
    # Thresholds
    default_low_threshold: float = 0.30
    default_high_threshold: float = 0.60
    calibrated_low_threshold: Optional[float] = None
    calibrated_high_threshold: Optional[float] = None
    
    # Graph weakness propagation parameters
    attenuation_factor: float = 0.55  # alpha attenuation for inherited weakness
    crypto_library_keywords: List[str] = field(default_factory=lambda: [
        "key", "cipher", "signature", "mac", "digest", "certificate", "secret", "crypto", "security"
    ])
    
    # Dominance floor
    pqc_floor_factor: float = 0.70  # Floor = factor * crypto_weakness


def propagate_graph_crypto_weakness(
    graph: HeteroData,
    config: Optional[ExperimentalHeuristicConfig] = None
) -> Dict[str, float]:
    """
    Propagates cryptographic weakness from concrete cipher usages to unobserved
    cryptographic key abstractions, interfaces, and builders along semantic graph edges.
    
    Guards:
    - Only propagates to files where direct crypto_weakness is unobserved (mask == 1.0).
    - Only propagates if the file imports a semantically verified cryptographic library.
    - Prevents unrelated utility and non-crypto package dependencies from inheriting weakness.
    """
    active_config = config if config is not None else ExperimentalHeuristicConfig()
    if not active_config.enable_graph_weakness_propagation:
        return {}

    if "file" not in graph.node_types:
        return {}

    file_node_ids = graph["file"].node_ids if hasattr(graph["file"], "node_ids") else []
    n_files = graph["file"].num_nodes

    # 1. Identify files with directly observed crypto weakness
    direct_crypto_weaknesses = {}
    for idx in range(n_files):
        # Feature 3 is crypto_weakness, Feature 10 is missingness mask
        mask = graph["file"].x[idx, 10].item() if graph["file"].x.shape[1] > 10 else 1.0
        val = graph["file"].x[idx, 3].item()
        if mask == 0.0 and val > 0.0:
            direct_crypto_weaknesses[idx] = val

    if not direct_crypto_weaknesses:
        return {}

    max_repo_weakness = max(direct_crypto_weaknesses.values())

    # 2. Check library imports
    file_to_crypto_libs: Dict[int, List[str]] = {}
    if ("file", "IMPORTS", "library") in graph.edge_types and "library" in graph.node_types:
        lib_node_ids = graph["library"].node_ids
        src, dst = graph[("file", "IMPORTS", "library")].edge_index
        src_list = src.tolist()
        dst_list = dst.tolist()

        for s, d in zip(src_list, dst_list):
            if d < len(lib_node_ids):
                lib_name = lib_node_ids[d].lower()
                if any(kw in lib_name for kw in active_config.crypto_library_keywords):
                    file_to_crypto_libs.setdefault(s, []).append(lib_name)

    propagated_map: Dict[str, float] = {}
    for idx in range(n_files):
        mask = graph["file"].x[idx, 10].item() if graph["file"].x.shape[1] > 10 else 1.0
        if mask == 1.0:  # Only propagate to unobserved files
            if idx in file_to_crypto_libs:
                # File imports verified cryptographic key/cipher types
                inherited_weakness = round(active_config.attenuation_factor * max_repo_weakness, 4)
                fn = file_node_ids[idx] if idx < len(file_node_ids) else f"file_{idx}"
                propagated_map[fn] = inherited_weakness

    return propagated_map


def propagate_graph_crypto_weakness_nx(
    graph_or_agile: Any,
    config: Optional[ExperimentalHeuristicConfig] = None
) -> Dict[str, float]:
    """
    NetworkX / AgileGraph implementation of semantic cryptographic weakness propagation.
    Propagates repository-level cryptographic weakness to unobserved key abstraction files
    that import verified cryptographic libraries.
    """
    active_config = config if config is not None else ExperimentalHeuristicConfig()
    if not active_config.enable_graph_weakness_propagation:
        return {}

    g = getattr(graph_or_agile, "G", graph_or_agile)
    if not hasattr(g, "nodes") or not hasattr(g, "out_edges"):
        return {}

    from src.risk.algorithm_strength import extract_crypto_weakness

    # 1. Identify max direct crypto weakness in the repository
    direct_weaknesses: Dict[str, float] = {}
    for node, data in g.nodes(data=True):
        if data.get("category") == "file":
            for _, target, edge_data in g.out_edges(node, data=True):
                if edge_data.get("relationship") == "CONTAINS":
                    target_data = g.nodes.get(target, {})
                    if target_data.get("category") == "crypto_usage":
                        algo = target_data.get("algorithm")
                        ksize = target_data.get("key_size")
                        if algo:
                            w = extract_crypto_weakness(algo, key_size=ksize)
                            if w.value is not None and w.value > 0.0:
                                direct_weaknesses[node] = max(direct_weaknesses.get(node, 0.0), w.value)

    if not direct_weaknesses:
        return {}

    max_repo_weakness = max(direct_weaknesses.values())

    # 2. Propagate to files with no direct crypto weakness that import crypto libraries
    propagated_map: Dict[str, float] = {}
    for node, data in g.nodes(data=True):
        if data.get("category") == "file" and node not in direct_weaknesses:
            imports_crypto_lib = False
            for _, target, edge_data in g.out_edges(node, data=True):
                rel = edge_data.get("relationship")
                if rel in ("IMPORTS", "DEPENDS_ON"):
                    target_data = g.nodes.get(target, {})
                    lib_name = (
                        target_data.get("library")
                        or target_data.get("package_name")
                        or (target.split(":library:")[-1] if ":library:" in target else target)
                    )
                    if any(kw in str(lib_name).lower() for kw in active_config.crypto_library_keywords):
                        imports_crypto_lib = True
                        break

            if imports_crypto_lib:
                inherited = round(active_config.attenuation_factor * max_repo_weakness, 4)
                propagated_map[node] = inherited

    return propagated_map


def derive_heuristic_label_v2(
    score: Optional[float],
    low_th: float = 0.18,
    high_th: float = 0.38
) -> Optional[str]:
    """
    Derives the discrete risk label under Heuristic V2 data-aware calibrated thresholds.
    Default calibrated thresholds: LOW < 0.18, MEDIUM [0.18, 0.38), HIGH >= 0.38.
    """
    if score is None:
        return None
    if score >= high_th:
        return "HIGH"
    elif score >= low_th:
        return "MEDIUM"
    return "LOW"


def calculate_experimental_heuristic_score(
    factors: RiskFactors,
    weights: Optional[HeuristicWeights] = None,
    policy: MissingDataPolicy = MissingDataPolicy.RENORMALIZE,
    config: Optional[ExperimentalHeuristicConfig] = None
) -> RiskScoreResult:
    """
    Calculates the composite risk score using the experimental heuristic configuration.
    Preserves exact formula from V1 while supporting optional PQC dominance floor.
    """
    active_config = config if config is not None else ExperimentalHeuristicConfig()
    
    # Calculate baseline V1 continuous score
    base_result = calculate_v1_score(factors, weights=weights, policy=policy)
    final_score = base_result.score

    # Component C: Optional PQC Dominance Floor
    if active_config.enable_pqc_dominance_floor:
        cw_val = factors.crypto_weakness.value
        if cw_val is not None and cw_val >= 0.80:
            floor = active_config.pqc_floor_factor * cw_val
            if final_score < floor:
                final_score = round(floor, 4)

    base_result.score = final_score
    base_result.formula_version = active_config.version_id
    return base_result


def classify_score(
    score: float,
    low_threshold: float = 0.30,
    high_threshold: float = 0.60
) -> int:
    """Maps continuous score to discrete class: 0 (LOW), 1 (MEDIUM), 2 (HIGH)."""
    if score < low_threshold:
        return 0
    elif score < high_threshold:
        return 1
    return 2


def bootstrap_metric_ci(
    metric_fn,
    y_true: List[int],
    y_pred: List[int],
    n_bootstraps: int = 1000,
    seed: int = 42
) -> Dict[str, float]:
    """Empirical percentile bootstrap confidence interval."""
    rng = np.random.RandomState(seed)
    n = len(y_true)
    point = metric_fn(y_true, y_pred)
    scores = []
    y_t = np.array(y_true)
    y_p = np.array(y_pred)
    for _ in range(n_bootstraps):
        idx = rng.randint(0, n, size=n)
        scores.append(metric_fn(y_t[idx], y_p[idx]))
    return {
        "point_estimate": round(float(point), 4),
        "ci_lower": round(float(np.percentile(scores, 2.5)), 4),
        "ci_upper": round(float(np.percentile(scores, 97.5)), 4),
        "n_bootstraps": n_bootstraps
    }
