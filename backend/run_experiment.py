#!/usr/bin/env python3
"""
AgileGraph — Reproducible Experiment Runner CLI

Single documented command to execute development experiments, benchmark split validation,
baseline evaluations, and GATv2 training smoke-tests across feature ablations.

Usage:
    # Run full development experiment suite across all 3 ablations:
    python run_experiment.py --mode dev --ablation ALL --seed 42 --epochs 5

    # Run specific ablation:
    python run_experiment.py --mode dev --ablation WITH_BASE_RISK
    python run_experiment.py --mode dev --ablation WITHOUT_BASE_RISK
    python run_experiment.py --mode dev --ablation STRUCTURE_ONLY

    # Attempt genuine research evaluation (fails closed if authentic human labels missing):
    python run_experiment.py --mode genuine
"""

import sys
import os
import argparse

# Ensure backend root is on sys.path
backend_root = os.path.dirname(os.path.abspath(__file__))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from src.ml.experiment_runner import ExperimentRunner


def main():
    parser = argparse.ArgumentParser(
        description="AgileGraph Reproducible Experiment Runner & End-to-End Readiness",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["dev", "genuine"],
        default="dev",
        help="Experiment mode: 'dev' for isolated synthetic development smoke-test; "
             "'genuine' for final research evaluation with authentic human expert labels."
    )
    parser.add_argument(
        "--ablation",
        type=str,
        choices=["WITH_BASE_RISK", "WITHOUT_BASE_RISK", "STRUCTURE_ONLY", "ALL"],
        default="ALL",
        help="Feature ablation scheme to test (default: ALL)."
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic pseudo-random seed (default: 42)."
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=5,
        help="Number of training epochs for development smoke test (default: 5)."
    )

    args = parser.parse_args()

    try:
        runner = ExperimentRunner(
            mode=args.mode,
            ablation=args.ablation,
            seed=args.seed,
            epochs=args.epochs
        )
        runner.run()
        sys.exit(0)
    except Exception as e:
        print(f"\n[FATAL ERROR] Experiment execution terminated: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
