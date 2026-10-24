import os
import sys
import json
import time
import hashlib
import platform
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import scipy
from scipy import stats

from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge
from src.risk.factor_extractor import FactorExtractor
from src.risk.heuristic import calculate_heuristic_score
from src.risk.weights import HeuristicWeights
from src.risk.score import MissingDataPolicy
from src.ml.features import FeatureConfig, extract_node_features
from src.ml.split_validator import (
    PROTOCOL_A,
    SplitDefinition,
    validate_split_integrity,
    partition_assets_by_split
)
from src.ml.baselines import HeuristicBaseline, RuleBasedBaseline
from src.ml.experiment import RuleConfig, AblationRegime, LabelRegime
from src.ml.synthetic_dev_sandbox import SyntheticDevSandbox
from src.ml.gatv2 import create_hetero_gatv2
from src.ml.pipeline import TrainingPipeline, set_seed
from src.ml.evaluation import EvaluationMetrics
from src.ml.explainability import (
    explain_heuristic_decomposition,
    compute_gradient_feature_importance,
    estimate_risk_reduction
)
from torch_geometric.data import HeteroData
import torch_geometric.transforms as T


class ExperimentRunner:
    """
    Reproducible Experiment Runner for AgileGraph.
    
    Supports:
    1. --mode dev: Runs localized development smoke-tests inside isolated sandbox
       using quarantined synthetic annotations.
    2. --mode genuine: Strict research evaluation mode requiring verified
       GENUINE_HUMAN annotations and a finalized protocol. Fails closed if
       genuine annotations are missing or if synthetic data attempts to enter.
    """

    def __init__(
        self,
        mode: str = "dev",
        ablation: str = "ALL",
        seed: int = 42,
        epochs: int = 5,
        dataset_root: Optional[str] = None
    ):
        self.mode = mode.lower()
        if self.mode not in ("dev", "genuine"):
            raise ValueError(f"Invalid mode '{mode}'. Expected 'dev' or 'genuine'.")

        self.ablation = ablation.upper()
        valid_ablations = {"WITH_BASE_RISK", "WITHOUT_BASE_RISK", "STRUCTURE_ONLY", "ALL"}
        if self.ablation not in valid_ablations:
            raise ValueError(f"Invalid ablation '{ablation}'. Expected one of {valid_ablations}.")

        self.seed = seed
        self.epochs = epochs
        set_seed(seed)

        self.backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.dataset_dir = dataset_root or os.path.join(self.backend_dir, "dataset")
        self.package_path = os.path.join(self.dataset_dir, "annotation", "sample_annotation_package.json")
        self.template_path = os.path.join(self.dataset_dir, "annotation", "expert_submission_template.json")
        self.sandbox_dir = os.path.join(self.dataset_dir, "synthetic_dev_sandbox")
        os.makedirs(self.sandbox_dir, exist_ok=True)

    @staticmethod
    def compute_file_hash(path: str) -> str:
        """Computes SHA-256 hash of a file to verify immutability."""
        if not os.path.exists(path):
            return "FILE_NOT_FOUND"
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()

    def load_and_validate_benchmark(self) -> Dict[str, Any]:
        """
        Loads the canonical benchmark package and validates the 92/14/60 repository-disjoint split.
        """
        if not os.path.exists(self.package_path):
            raise FileNotFoundError(f"Canonical annotation package not found at: {self.package_path}")

        initial_package_hash = self.compute_file_hash(self.package_path)
        initial_template_hash = self.compute_file_hash(self.template_path)

        with open(self.package_path, "r", encoding="utf-8") as f:
            package_data = json.load(f)

        assets = package_data.get("assets", [])
        split_result = validate_split_integrity(assets, PROTOCOL_A)

        if not split_result["is_valid"]:
            error_msg = "; ".join(split_result["errors"])
            raise ValueError(f"Benchmark split validation failed: {error_msg}")

        partitions = partition_assets_by_split(assets, PROTOCOL_A)

        return {
            "package_data": package_data,
            "assets": assets,
            "split_result": split_result,
            "partitions": partitions,
            "package_hash": initial_package_hash,
            "template_hash": initial_template_hash
        }

    def construct_benchmark_graph(self, assets: List[Dict[str, Any]]) -> AgileGraph:
        """
        Builds the unified AgileGraph representing all 166 canonical benchmark assets
        and their associated observable cryptographic findings, dependency libraries,
        certificates, endpoints, and sensitive data findings.
        Computes 7 heuristic risk factors and base_risk for each file node.
        """
        ag = AgileGraph()

        # Weight vector for heuristic risk factors
        w = 1.0 / 7.0
        weights = HeuristicWeights(
            data_sensitivity=w, asset_criticality=w, internet_exposure=w,
            crypto_weakness=w, cve_risk=w, library_centrality=w, migration_difficulty=w
        )

        # 1. Populate all file nodes and observable findings
        for asset in assets:
            aid = asset["asset_id"]
            pid = asset.get("project_id", aid.split(":")[0] if ":" in aid else "unknown")
            rel_path = asset.get("relative_path", aid.split(":", 1)[1] if ":" in aid else aid)

            ag.add_node(GraphNode(
                id=aid,
                category="file",
                properties={
                    "project_id": pid,
                    "relative_path": rel_path,
                    "language": asset.get("language")
                }
            ))

            for idx, ev in enumerate(asset.get("observable_evidence", [])):
                ev_type = ev.get("type")
                if ev_type == "CRYPTO_USAGE":
                    nid = f"{aid}:crypto_{idx}"
                    ag.add_node(GraphNode(
                        id=nid,
                        category="crypto_usage",
                        properties={
                            "algorithm": ev.get("algorithm"),
                            "key_size": ev.get("key_size"),
                            "operation": ev.get("operation"),
                            "snippet": ev.get("snippet")
                        }
                    ))
                    ag.add_edge(GraphEdge(source_id=aid, target_id=nid, relationship="CONTAINS"))
                    ag.add_edge(GraphEdge(source_id=nid, target_id=aid, relationship="CONTAINED_BY"))

                elif ev_type == "DEPENDENCY_LIBRARY":
                    lib_name = ev.get("library")
                    nid = f"lib:{lib_name}"
                    if not ag.G.has_node(nid):
                        ag.add_node(GraphNode(
                            id=nid,
                            category="library",
                            properties={"library": lib_name, "version": ev.get("version")}
                        ))
                    ag.add_edge(GraphEdge(source_id=aid, target_id=nid, relationship="IMPORTS"))
                    ag.add_edge(GraphEdge(source_id=nid, target_id=aid, relationship="IMPORTED_BY"))

                elif ev_type == "CERTIFICATE":
                    nid = f"{aid}:cert_{idx}"
                    ag.add_node(GraphNode(
                        id=nid,
                        category="certificate",
                        properties={
                            "operation": ev.get("operation"),
                            "subject": ev.get("subject"),
                            "issuer": ev.get("issuer")
                        }
                    ))
                    ag.add_edge(GraphEdge(source_id=aid, target_id=nid, relationship="CONTAINS"))
                    ag.add_edge(GraphEdge(source_id=nid, target_id=aid, relationship="CONTAINED_BY"))

                elif ev_type == "ENDPOINT":
                    nid = f"{aid}:endpoint_{idx}"
                    ag.add_node(GraphNode(
                        id=nid,
                        category="endpoint",
                        properties={"exposure": ev.get("exposure", "UNKNOWN")}
                    ))
                    ag.add_edge(GraphEdge(source_id=aid, target_id=nid, relationship="EXPOSES"))
                    ag.add_edge(GraphEdge(source_id=nid, target_id=aid, relationship="EXPOSED_BY"))

                elif ev_type == "SENSITIVE_DATA":
                    nid = f"{aid}:sensitive_{idx}"
                    ag.add_node(GraphNode(
                        id=nid,
                        category="sensitive_data",
                        properties={"pattern": ev.get("pattern", "UNKNOWN")}
                    ))
                    ag.add_edge(GraphEdge(source_id=aid, target_id=nid, relationship="PROTECTS"))
                    ag.add_edge(GraphEdge(source_id=nid, target_id=aid, relationship="PROTECTED_BY"))

        # 2. Extract heuristic risk factors and compute base_risk
        extractor = FactorExtractor(ag)
        for asset in assets:
            aid = asset["asset_id"]
            factors = extractor.extract(aid, metadata={}, cve_info={}, migration_inputs={})
            score_res = calculate_heuristic_score(factors, weights, policy=MissingDataPolicy.RENORMALIZE)

            props = ag.G.nodes[aid].get("properties", {})
            props["risk_factors"] = {k: v["value"] for k, v in factors.model_dump().items()}
            props["base_risk"] = score_res.score if score_res.score is not None else 0.50
            props["heuristic_audit"] = score_res.model_dump()
            ag.G.nodes[aid]["properties"] = props

        return ag

    def evaluate_baselines_on_test_split(
        self,
        ag: AgileGraph,
        test_assets: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Runs HeuristicBaseline and RuleBasedBaseline
        strictly on the held-out test split (60 assets across go_crypto and java_jjwt).
        """
        test_ids = set(a["asset_id"] for a in test_assets)

        # 1. Heuristic Baseline
        h_baseline = HeuristicBaseline(ag)
        h_output = h_baseline.evaluate()
        test_h_scores = {aid: s for aid, s in h_output.scores.items() if aid in test_ids}

        # 2. Rule-Based Baseline
        r_config = RuleConfig(version="2.0", rules=["STATIC_ANALYSIS_CRYPTO_RULES"])
        r_baseline = RuleBasedBaseline(ag, r_config)
        r_output = r_baseline.evaluate()
        test_r_scores = {aid: s for aid, s in r_output.scores.items() if aid in test_ids}

        # 3. Comparative Statistics on Test Overlap
        overlap_ids = sorted(list(set(test_h_scores.keys()) & set(test_r_scores.keys())))
        if len(overlap_ids) >= 3:
            h_vec = np.array([test_h_scores[aid] for aid in overlap_ids], dtype=float)
            r_vec = np.array([test_r_scores[aid] for aid in overlap_ids], dtype=float)

            spearman_res = stats.spearmanr(h_vec, r_vec)
            spearman_rho = float(spearman_res.statistic) if not np.isnan(spearman_res.statistic) else 0.0
            spearman_p = float(spearman_res.pvalue) if not np.isnan(spearman_res.pvalue) else 1.0

            kendall_res = stats.kendalltau(h_vec, r_vec)
            kendall_tau = float(kendall_res.statistic) if not np.isnan(kendall_res.statistic) else 0.0
            kendall_p = float(kendall_res.pvalue) if not np.isnan(kendall_res.pvalue) else 1.0

            mean_diff = float(np.mean(h_vec - r_vec))
        else:
            spearman_rho, spearman_p = None, None
            kendall_tau, kendall_p = None, None
            mean_diff = None

        return {
            "test_asset_population": len(test_ids),
            "heuristic_evaluated_count": len(test_h_scores),
            "rule_based_evaluated_count": len(test_r_scores),
            "comparable_assets_count": len(overlap_ids),
            "spearman_rho": spearman_rho,
            "spearman_pvalue": spearman_p,
            "kendall_tau": kendall_tau,
            "kendall_pvalue": kendall_p,
            "mean_score_difference": mean_diff,
            "heuristic_scores_sample": {aid: round(test_h_scores[aid], 3) for aid in list(test_h_scores.keys())[:5]},
            "rule_scores_sample": {aid: round(test_r_scores[aid], 3) for aid in list(test_r_scores.keys())[:5]}
        }

    def build_pyg_data_for_ablation(
        self,
        ag: AgileGraph,
        consensus_labels: Dict[str, int],
        ablation_name: str,
        partitions: Dict[str, List[Dict[str, Any]]]
    ) -> HeteroData:
        """
        Converts AgileGraph to PyG HeteroData with exact ablation dimensions and masks.
        """
        if ablation_name == "WITH_BASE_RISK":
            cfg = FeatureConfig(include_base_risk=True, structure_only=False)
            expected_dim = 16
        elif ablation_name == "WITHOUT_BASE_RISK":
            cfg = FeatureConfig(include_base_risk=False, structure_only=False)
            expected_dim = 14
        elif ablation_name == "STRUCTURE_ONLY":
            cfg = FeatureConfig(include_base_risk=False, structure_only=True)
            expected_dim = 1
        else:
            raise ValueError(f"Unknown ablation: {ablation_name}")

        data = HeteroData()
        node_maps = {}
        initialized_categories = set()

        train_ids = set(a["asset_id"] for a in partitions["train"])
        val_ids = set(a["asset_id"] for a in partitions["val"])
        test_ids = set(a["asset_id"] for a in partitions["test"])

        for n_id, data_dict in ag.G.nodes(data=True):
            category = data_dict.get("category", "unknown_node")
            if category not in node_maps:
                node_maps[category] = {}
            current_idx = len(node_maps[category])
            node_maps[category][n_id] = current_idx

            if category not in initialized_categories:
                initialized_categories.add(category)
                data[category].x = []
                data[category].y = []
                data[category].node_ids = []
                data[category].train_mask = []
                data[category].val_mask = []
                data[category].test_mask = []

            props = data_dict.get("properties", data_dict)
            x_feat = extract_node_features(props, cfg)

            if category == "file":
                y_label = consensus_labels.get(n_id, -1)
                is_train = n_id in train_ids
                is_val = n_id in val_ids
                is_test = n_id in test_ids
            else:
                y_label = -1
                is_train, is_val, is_test = False, False, False

            data[category].x.append(x_feat)
            data[category].y.append(y_label)
            data[category].node_ids.append(n_id)
            data[category].train_mask.append(is_train)
            data[category].val_mask.append(is_val)
            data[category].test_mask.append(is_test)

        for category in node_maps.keys():
            if len(data[category].x) > 0:
                data[category].x = torch.stack(data[category].x)
                data[category].y = torch.tensor(data[category].y, dtype=torch.long)
                data[category].train_mask = torch.tensor(data[category].train_mask, dtype=torch.bool)
                data[category].val_mask = torch.tensor(data[category].val_mask, dtype=torch.bool)
                data[category].test_mask = torch.tensor(data[category].test_mask, dtype=torch.bool)

        edge_lists = {}
        for u, v, k, e_data in ag.G.edges(data=True, keys=True):
            u_cat = ag.G.nodes[u].get("category", "unknown_node")
            v_cat = ag.G.nodes[v].get("category", "unknown_node")
            edge_type = e_data.get("relationship", "unknown_edge")
            edge_triplet = (u_cat, edge_type, v_cat)

            if edge_triplet not in edge_lists:
                edge_lists[edge_triplet] = [[], []]

            edge_lists[edge_triplet][0].append(node_maps[u_cat][u])
            edge_lists[edge_triplet][1].append(node_maps[v_cat][v])

        for triplet, edge_index in edge_lists.items():
            data[triplet].edge_index = torch.tensor(edge_index, dtype=torch.long)

        data = T.ToUndirected()(data)

        # Verify exact dimension
        actual_dim = data["file"].x.shape[1]
        assert actual_dim == expected_dim, f"Ablation {ablation_name} expected {expected_dim} dims, got {actual_dim}"

        return data

    def run_ablation_smoke_test(
        self,
        ablation_name: str,
        pyg_data: HeteroData,
        hidden_dim: int = 32
    ) -> Dict[str, Any]:
        """
        Executes localized GATv2 training smoke-test on training split,
        evaluates on validation and held-out test split, and computes explainability saliency.
        """
        metadata = pyg_data.metadata()
        model = create_hetero_gatv2(metadata, hidden_channels=hidden_dim, out_channels=3, num_heads=2)
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        criterion = nn.CrossEntropyLoss()

        train_mask = pyg_data["file"].train_mask
        val_mask = pyg_data["file"].val_mask
        test_mask = pyg_data["file"].test_mask

        loss_history = []
        for ep in range(self.epochs):
            model.train()
            optimizer.zero_grad()
            out = model(pyg_data.x_dict, pyg_data.edge_index_dict)
            file_logits = out["file"][train_mask]
            file_targets = pyg_data["file"].y[train_mask]

            # Only compute loss on valid labeled training nodes
            valid_train = file_targets >= 0
            if valid_train.sum() > 0:
                loss = criterion(file_logits[valid_train], file_targets[valid_train])
                loss.backward()
                optimizer.step()
                loss_history.append(float(loss.item()))
            else:
                loss_history.append(0.0)

        # Checkpoint serialization
        checkpoint_name = f"dev_checkpoint_{ablation_name.lower()}.pt"
        checkpoint_path = os.path.join(self.sandbox_dir, checkpoint_name)
        torch.save({
            "model_state_dict": model.state_dict(),
            "ablation": ablation_name,
            "seed": self.seed,
            "provenance": "SYNTHETIC_DEVELOPMENT_ONLY"
        }, checkpoint_path)

        # Reload checkpoint to verify integrity
        loaded = torch.load(checkpoint_path, weights_only=False)
        model.load_state_dict(loaded["model_state_dict"])

        # Evaluation on test split
        model.eval()
        with torch.no_grad():
            eval_out = model(pyg_data.x_dict, pyg_data.edge_index_dict)
            test_logits = eval_out["file"][test_mask]
            test_preds = test_logits.argmax(dim=-1).numpy()
            test_targets = pyg_data["file"].y[test_mask].numpy()

        valid_test = test_targets >= 0
        y_true = test_targets[valid_test]
        y_pred = test_preds[valid_test]

        test_metrics = EvaluationMetrics.calculate_classification_metrics(y_true, y_pred)
        bootstrap_result = EvaluationMetrics.bootstrap_ci(y_true, y_pred, n_bootstraps=200)

        # Explainability saliency on first test node
        saliency_result = compute_gradient_feature_importance(
            model=model,
            pyg_data=pyg_data,
            target_node_category="file",
            target_node_idx=0
        )

        return {
            "ablation": ablation_name,
            "input_dimension": pyg_data["file"].x.shape[1],
            "epochs_trained": self.epochs,
            "initial_loss": float(loss_history[0]) if loss_history else 0.0,
            "final_loss": float(loss_history[-1]) if loss_history else 0.0,
            "checkpoint_path": checkpoint_path,
            "test_assets_evaluated": int(valid_test.sum()),
            "smoke_test_metrics": test_metrics,
            "bootstrap_ci": bootstrap_result.get("confidence_interval"),
            "saliency_status": saliency_result.get("status"),
            "saliency_method": saliency_result.get("method"),
            "loss_history": [round(l, 4) for l in loss_history]
        }

    def run(self) -> Dict[str, Any]:
        """
        Main execution workflow.
        """
        start_time = time.time()
        print("=" * 75)
        print("AGILEGRAPH — REPRODUCIBLE EXPERIMENT RUNNER")
        print("=" * 75)
        print(f"[CONFIG] Mode: {self.mode.upper()}")
        print(f"[CONFIG] Ablation: {self.ablation}")
        print(f"[CONFIG] Seed: {self.seed}")
        print(f"[CONFIG] Epochs: {self.epochs}")
        print(f"[CONFIG] Sandbox Dir: {self.sandbox_dir}")

        # Phase 1 & 2: Benchmark Load and Split Validation
        print("\n[STEP 1] Validating canonical benchmark and repository-disjoint split...")
        benchmark_info = self.load_and_validate_benchmark()
        assets = benchmark_info["assets"]
        split_res = benchmark_info["split_result"]
        partitions = benchmark_info["partitions"]

        print(f"  -> Total assets: {split_res['total_assets']} (Expected: 166)")
        print(f"  -> Train count: {split_res['actual_train_count']} (Expected: 92)")
        print(f"  -> Val count:   {split_res['actual_val_count']} (Expected: 14)")
        print(f"  -> Test count:  {split_res['actual_test_count']} (Expected: 60)")
        print(f"  -> Pairwise repository disjointness: VALIDATED")

        # Phase 3 Guardrail: Refuse genuine evaluation if genuine human labels missing
        if self.mode == "genuine":
            raise RuntimeError(
                "GENUINE RESEARCH EVALUATION REFUSED: Authentic expert labels have not been imported. "
                "Final research evaluation requires finalized GENUINE_HUMAN annotations. "
                "Use --mode dev for development experiments and mechanical verification."
            )

        # Construct AgileGraph for all 166 assets
        print("\n[STEP 2] Constructing benchmark AgileGraph for 166 assets...")
        ag = self.construct_benchmark_graph(assets)
        total_nodes = ag.G.number_of_nodes()
        total_edges = ag.G.number_of_edges()
        print(f"  -> Total graph nodes: {total_nodes}")
        print(f"  -> Total graph edges: {total_edges}")

        # Baseline Evaluation on Held-Out Test Split
        print("\n[STEP 3] Running Baselines on held-out test split (60 assets)...")
        baseline_results = self.evaluate_baselines_on_test_split(ag, partitions["test"])
        print(f"  -> Test assets evaluated: {baseline_results['test_asset_population']}")
        print(f"  -> Heuristic evaluated: {baseline_results['heuristic_evaluated_count']}")
        print(f"  -> Rule-based evaluated: {baseline_results['rule_based_evaluated_count']}")
        if baseline_results["spearman_rho"] is not None:
            print(f"  -> Spearman rho (Heuristic vs Rule): {baseline_results['spearman_rho']:.4f}")

        # Synthetic Development Sandbox Setup
        print("\n[STEP 4] Initializing isolated SyntheticDevSandbox...")
        sandbox = SyntheticDevSandbox(seed=self.seed)
        dataset_manifest = sandbox.generate_synthetic_development_dataset(assets, num_raters=4)
        consensus_labels = dataset_manifest["consensus_labels"]
        print(f"  -> Simulated consensus labels generated: {len(consensus_labels)}")
        print(f"  -> Provenance stamp: {dataset_manifest['provenance']}")

        # Ablations Selection
        if self.ablation == "ALL":
            ablations_to_run = ["WITH_BASE_RISK", "WITHOUT_BASE_RISK", "STRUCTURE_ONLY"]
        else:
            ablations_to_run = [self.ablation]

        # Exercise GATv2 training pipeline for each ablation
        print("\n[STEP 5] Exercising GATv2 training smoke-tests across ablations...")
        ablation_results = {}
        for abl_name in ablations_to_run:
            print(f"\n  [Ablation: {abl_name}]")
            pyg_data = self.build_pyg_data_for_ablation(ag, consensus_labels, abl_name, partitions)
            print(f"    -> Feature tensor shape: {pyg_data['file'].x.shape}")
            res = self.run_ablation_smoke_test(abl_name, pyg_data)
            print(f"    -> Loss reduction: {res['initial_loss']:.4f} -> {res['final_loss']:.4f}")
            print(f"    -> Checkpoint saved: {res['checkpoint_path']}")
            print(f"    -> Test smoke accuracy: {res['smoke_test_metrics']['accuracy']:.4f}")
            ablation_results[abl_name] = res

        # Verify integrity of canonical files
        current_pkg_hash = self.compute_file_hash(self.package_path)
        current_tpl_hash = self.compute_file_hash(self.template_path)
        assert current_pkg_hash == benchmark_info["package_hash"], "CANONICAL PACKAGE MUTATION DETECTED!"
        assert current_tpl_hash == benchmark_info["template_hash"], "CANONICAL TEMPLATE MUTATION DETECTED!"
        print("\n[STEP 6] Verified canonical package and template remain completely unchanged.")

        # Save Experiment Run Manifest
        elapsed = time.time() - start_time
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        manifest_data = {
            "is_synthetic_development_artifact": True,
            "valid_for_empirical_claims": False,
            "provenance": "SYNTHETIC_DEVELOPMENT_ONLY",
            "warning": "DO NOT USE FOR EMPIRICAL EVALUATION OR PUBLISHED RESEARCH CLAIMS.",
            "run_id": f"dev_run_{timestamp_str}",
            "execution_timestamp": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(elapsed, 2),
            "mode": self.mode,
            "ablation_mode": self.ablation,
            "seed": self.seed,
            "epochs": self.epochs,
            "software_environment": {
                "python": sys.version.split()[0],
                "platform": platform.platform(),
                "torch": torch.__version__,
                "numpy": np.__version__,
                "scipy": scipy.__version__
            },
            "split_validation": {
                "is_valid": split_res["is_valid"],
                "total_assets": split_res["total_assets"],
                "actual_train_count": split_res["actual_train_count"],
                "actual_val_count": split_res["actual_val_count"],
                "actual_test_count": split_res["actual_test_count"],
                "protocol": "PROTOCOL_A",
                "train_repos": PROTOCOL_A.train_repos,
                "val_repos": PROTOCOL_A.val_repos,
                "test_repos": PROTOCOL_A.test_repos
            },
            "split_asset_ids": {
                "train": [a["asset_id"] for a in partitions["train"]],
                "val": [a["asset_id"] for a in partitions["val"]],
                "test": [a["asset_id"] for a in partitions["test"]]
            },
            "baselines_on_test_split": baseline_results,
            "ablations": ablation_results,
            "integrity_checks": {
                "package_sha256": current_pkg_hash,
                "template_sha256": current_tpl_hash,
                "canonical_files_unmodified": True
            }
        }

        manifest_file = os.path.join(self.sandbox_dir, f"experiment_run_manifest_{timestamp_str}.json")
        latest_manifest = os.path.join(self.sandbox_dir, "latest_run_manifest.json")

        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        with open(latest_manifest, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        print(f"\n[STEP 7] Run manifest saved to: {latest_manifest}")

        # Generate Markdown Development Report
        report_path = os.path.join(self.sandbox_dir, "DEVELOPMENT_EXPERIMENT_REPORT.md")
        self.generate_development_report(manifest_data, report_path)
        print(f"[STEP 8] Development report generated at: {report_path}")

        print("\n" + "=" * 75)
        print("REPRODUCIBLE DEVELOPMENT RUN COMPLETED SUCCESSFULLY")
        print("=" * 75)

        return manifest_data

    def generate_development_report(self, manifest: Dict[str, Any], output_path: str):
        """
        Generates clearly labelled markdown development report separating
        software smoke-test mechanics from research results.
        """
        lines = [
            "# AgileGraph — Development Experiment Runner Report",
            "",
            "> [!WARNING]",
            "> **DEVELOPMENT SMOKE-TEST REPORT ONLY — NOT FOR RESEARCH CLAIMS**",
            "> This report was generated using synthetic annotations inside an isolated development sandbox.",
            "> All metrics, loss reductions, and evaluations herein verify software execution mechanics only.",
            "> **No empirical performance claims, F1 scores, or research conclusions may be drawn from this document.**",
            "",
            "## 1. Run Configuration & Software Provenance",
            f"- **Run ID**: `{manifest['run_id']}`",
            f"- **Execution Date**: {manifest['execution_timestamp']}",
            f"- **Execution Mode**: `{manifest['mode'].upper()}`",
            f"- **Ablation Mode**: `{manifest['ablation_mode']}`",
            f"- **Random Seed**: `{manifest['seed']}`",
            f"- **Training Epochs**: `{manifest['epochs']}`",
            f"- **Provenance Stamp**: `{manifest['provenance']}`",
            f"- **Python Version**: {manifest['software_environment']['python']}",
            f"- **PyTorch Version**: {manifest['software_environment']['torch']}",
            f"- **Operating System**: {manifest['software_environment']['platform']}",
            "",
            "## 2. Reconciled Benchmark Split Integrity (Protocol A)",
            "The repository-disjoint partition was strictly validated against canonical benchmark assets:",
            "",
            "| Split Partition | Repositories Included | Expected Count | Actual Count | Status |",
            "|---|---|---|---|---|",
            f"| **Training** | `python_cryptography`, `python_itsdangerous`, `go_jwt`, `java_java_jwt` | 92 | {manifest['split_validation']['actual_train_count']} | PASSED |",
            f"| **Validation** | `python_bcrypt`, `go_jwt_go` | 14 | {manifest['split_validation']['actual_val_count']} | PASSED |",
            f"| **Held-Out Test** | `go_crypto`, `java_jjwt` | 60 | {manifest['split_validation']['actual_test_count']} | PASSED |",
            f"| **Total Assets** | **8 Repositories** | **166** | **{manifest['split_validation']['total_assets']}** | **VERIFIED** |",
            "",
            "- **Pairwise Disjointness**: STRICT (Zero repo or asset leakage across splits).",
            "- **Canonical Package Immutability**: SHA-256 verified unchanged.",
            "- **Blank Submission Template Immutability**: SHA-256 verified unchanged.",
            "",
            "## 3. Baseline Evaluations on Consistent Test Population",
            "Evaluated strictly on the 60 held-out test assets (`go_crypto` and `java_jjwt`):",
            "",
            f"- **Test Assets Available**: {manifest['baselines_on_test_split']['test_asset_population']}",
            f"- **Heuristic Evaluated Assets**: {manifest['baselines_on_test_split']['heuristic_evaluated_count']}",
            f"- **Rule-Based Evaluated Assets**: {manifest['baselines_on_test_split']['rule_based_evaluated_count']}",
            f"- **Comparable Asset Overlap**: {manifest['baselines_on_test_split']['comparable_assets_count']}",
            f"- **Spearman Rank Correlation (Heuristic vs Rule)**: {manifest['baselines_on_test_split']['spearman_rho']:.4f}" if manifest['baselines_on_test_split']['spearman_rho'] is not None else "- **Spearman Rank Correlation**: N/A",
            "",
            "## 4. GATv2 Feature Ablations & Training Smoke-Test Mechanics",
            "Mechanical validation of forward/backward propagation, loss computation, and checkpoint persistence:",
            "",
            "| Ablation Scheme | Input Dim | Initial Loss | Final Loss | Test Accuracy (Simulated) | Checkpoint Status |",
            "|---|---|---|---|---|---|",
        ]

        for abl_name, res in manifest["ablations"].items():
            acc = res["smoke_test_metrics"].get("accuracy", 0.0)
            lines.append(
                f"| `{abl_name}` | {res['input_dimension']} | {res['initial_loss']:.4f} | "
                f"{res['final_loss']:.4f} | {acc:.4f} (smoke only) | Verified Saved & Loaded |"
            )

        lines.extend([
            "",
            "## 5. Research Evaluation Guardrail Checklist",
            "- [x] **Canonical Annotation Files Preserved**: `sample_annotation_package.json` and template untouched.",
            "- [x] **Isolated Sandbox Quarantine**: All checkpoints and manifests written strictly inside `synthetic_dev_sandbox/`.",
            "- [x] **Provenance Stamped**: All artifacts carry `is_synthetic_development_artifact: True`.",
            "- [x] **Held-Out Test Isolation**: Test split (60 assets) was excluded from all training and checkpoint selection.",
            "- [x] **Genuine Mode Refusal**: Pipeline refuses to proceed in genuine evaluation mode without verified human labels.",
            "",
            "## 6. Next Steps to Genuine Expert Evaluation",
            "When genuine expert annotations are collected:",
            "1. Receive filled expert submission JSON files matching `expert_submission_template.json`.",
            "2. Import via `AnnotationImporter` with `protocol_status='FINALIZED'`, `enforce_provenance=ProvenanceSource.GENUINE_HUMAN`.",
            "3. Verify Krippendorff's alpha agreement threshold ($\\alpha \\ge 0.667$).",
            "4. Adjudicate any unresolved ratings.",
            "5. Execute genuine evaluation using `--mode genuine`."
        ])

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
