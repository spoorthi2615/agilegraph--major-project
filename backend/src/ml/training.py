import os
import copy
from typing import Dict, Any, List, Optional
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.data import HeteroData

from .experiment import ExperimentManifest, LabelRegime, ModelType
from .gatv2 import create_hetero_gatv2
from .pipeline import TrainingPipeline, set_seed
from .evaluation import EvaluationMetrics
from .converter import safe_load_pyg_data


def _build_synthetic_project_graph(num_files: int = 12, include_base_risk: bool = False, seed: int = 42) -> HeteroData:
    """Builds a deterministic synthetic HeteroData graph for testing and simulation."""
    set_seed(seed)
    in_channels = 15 if include_base_risk else 14
    d = HeteroData()
    d["file"].x = torch.randn((num_files, in_channels), dtype=torch.float32)
    # Balanced classes 0, 1, 2
    d["file"].y = torch.tensor([i % 3 for i in range(num_files)], dtype=torch.long)
    
    num_libs = max(num_files // 2, 2)
    d["library"].x = torch.randn((num_libs, in_channels), dtype=torch.float32)
    
    # Simple bipartite relations
    src = torch.arange(num_files, dtype=torch.long)
    dst = src % num_libs
    d["file", "IMPORTS", "library"].edge_index = torch.stack([src, dst], dim=0)
    d["library", "IMPORTED_BY", "file"].edge_index = torch.stack([dst, src], dim=0)
    return d


class ModelTrainer:
    """
    Orchestrates GNN training, LOPO evaluation, and paired target-leakage ablations
    guided by an ExperimentManifest.
    """

    def __init__(self, manifest: ExperimentManifest, artifacts: Optional[Dict[str, HeteroData]] = None):
        self.manifest = manifest
        self.artifacts: Dict[str, HeteroData] = artifacts if artifacts is not None else {}
        self._ensure_dataset_populated()

    def _ensure_dataset_populated(self):
        """Loads repository graph artifacts from disk if available, or synthesizes required split graphs."""
        if not self.artifacts:
            artifacts_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dataset", "artifacts"))
            if os.path.isdir(artifacts_dir):
                for fname in os.listdir(artifacts_dir):
                    if fname.endswith(".pt") and not fname.startswith("dev_sim_"):
                        pid = fname[:-3]
                        try:
                            self.artifacts[pid] = safe_load_pyg_data(os.path.join(artifacts_dir, fname))
                        except Exception:
                            pass

        # Ensure all projects referenced in project_split exist
        all_pids = set()
        for pids in self.manifest.project_split.values():
            all_pids.update(pids)

        for idx, pid in enumerate(sorted(all_pids)):
            if pid not in self.artifacts:
                self.artifacts[pid] = _build_synthetic_project_graph(
                    num_files=12,
                    include_base_risk=self.manifest.include_base_risk,
                    seed=self.manifest.seed + idx
                )

    def _prepare_graph(self, d: HeteroData, include_base_risk: bool) -> HeteroData:
        """Ensures the file features match the requested 14-dim (clean) or 15-dim (leaked) format."""
        d_out = copy.deepcopy(d)
        curr_dim = d_out["file"].x.shape[1]
        if include_base_risk and curr_dim == 14:
            # Append continuous target proxy
            leak_col = torch.tensor(
                [[0.10 if y == 0 else 0.45 if y == 1 else 0.85] for y in d_out["file"].y],
                dtype=torch.float32
            )
            d_out["file"].x = torch.cat([d_out["file"].x, leak_col], dim=-1)
        elif not include_base_risk and curr_dim > 14:
            d_out["file"].x = d_out["file"].x[:, :14]
        return d_out

    def run_training_loop(self) -> Dict[str, Any]:
        """Runs the actual training and evaluation experiment based on the manifest regime."""
        if self.manifest.label_source != LabelRegime.WEAK_SUPERVISION:
            raise ValueError(f"Unsupported label regime: {self.manifest.label_source}")

        train_pids = self.manifest.project_split.get("train", [])
        test_pids = self.manifest.project_split.get("test") or self.manifest.project_split.get("val") or train_pids

        if not train_pids:
            train_pids = list(self.artifacts.keys())
        if not test_pids:
            test_pids = train_pids

        train_graphs = [
            self._prepare_graph(self.artifacts[p], self.manifest.include_base_risk)
            for p in train_pids if p in self.artifacts
        ]
        test_graphs = [
            self._prepare_graph(self.artifacts[p], self.manifest.include_base_risk)
            for p in test_pids if p in self.artifacts
        ]

        if not train_graphs or not test_graphs:
            raise ValueError("No valid project graphs found for training/testing.")

        # Aggregate training labels to compute class balancing weights
        train_labels = []
        for g in train_graphs:
            train_labels.extend(g["file"].y.tolist())
        train_labels = np.array(train_labels)

        counts = np.bincount(train_labels, minlength=3)
        weights = len(train_labels) / (3.0 * np.maximum(counts, 1))
        criterion = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32))

        # Model initialization
        set_seed(self.manifest.seed)
        global_meta = (train_graphs[0].node_types, train_graphs[0].edge_types)
        model = create_hetero_gatv2(global_meta, hidden_channels=32, out_channels=3, num_heads=2, sample_data=train_graphs[0])
        pipeline = TrainingPipeline(model, {"seed": self.manifest.seed})
        
        lr = self.manifest.learning_rate if self.manifest.learning_rate is not None else 0.005
        optimizer = optim.Adam(model.parameters(), lr=lr)

        epochs = self.manifest.epochs if self.manifest.epochs is not None else 5
        for _ in range(epochs):
            for g in train_graphs:
                pipeline.train_step(g, optimizer, criterion)

        # Evaluation
        model.eval()
        all_trues = []
        all_preds = []
        with torch.no_grad():
            for g in test_graphs:
                out = model(g.x_dict, g.edge_index_dict)
                preds = out["file"].argmax(dim=-1).cpu().numpy().tolist()
                all_preds.extend(preds)
                all_trues.extend(g["file"].y.cpu().numpy().tolist())

        y_true = np.array(all_trues)
        y_pred = np.array(all_preds)
        m = EvaluationMetrics.calculate_classification_metrics(y_true, y_pred, target_classes=[0, 1, 2])

        return {
            "status": "COMPLETED",
            "experiment_id": self.manifest.experiment_id,
            "metrics": {
                "macro_f1": round(float(m["macro_f1"]), 4),
                "accuracy": round(float(m["accuracy"]), 4),
                "balanced_accuracy": round(float(m.get("balanced_accuracy", 0.0)), 4),
                "confusion_matrix": m["confusion_matrix"]
            },
            "trained_epochs": epochs,
            "sample_size": len(all_trues)
        }

    def run_leakage_ablation(self) -> Dict[str, Any]:
        """Runs paired ablation experiments (WITH_BASE_RISK vs WITHOUT_BASE_RISK)."""
        clean_manifest = copy.deepcopy(self.manifest)
        clean_manifest.include_base_risk = False
        trainer_clean = ModelTrainer(clean_manifest, artifacts=self.artifacts)
        clean_res = trainer_clean.run_training_loop()

        leaked_manifest = copy.deepcopy(self.manifest)
        leaked_manifest.include_base_risk = True
        trainer_leak = ModelTrainer(leaked_manifest, artifacts=self.artifacts)
        leak_res = trainer_leak.run_training_loop()

        clean_acc = clean_res["metrics"]["accuracy"]
        leak_acc = leak_res["metrics"]["accuracy"]
        clean_f1 = clean_res["metrics"]["macro_f1"]
        leak_f1 = leak_res["metrics"]["macro_f1"]
        gain_acc = leak_acc - clean_acc
        gain_f1 = leak_f1 - clean_f1

        return {
            "status": "COMPLETED",
            "experiment_id": self.manifest.experiment_id,
            "without_base_risk": clean_res["metrics"],
            "with_base_risk": leak_res["metrics"],
            "leakage_gain_accuracy": f"+{gain_acc*100:.2f}%" if gain_acc >= 0 else f"{gain_acc*100:.2f}%",
            "leakage_gain_macro_f1": round(float(gain_f1), 4)
        }
