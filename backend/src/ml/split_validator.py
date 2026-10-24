import json
from typing import Dict, List, Set, Any, Optional
from pydantic import BaseModel, Field


# Canonical 8 benchmark repositories
CANONICAL_BENCHMARK_REPOSITORIES = {
    "python_cryptography",
    "python_itsdangerous",
    "python_bcrypt",
    "go_jwt",
    "go_jwt_go",
    "go_crypto",
    "java_java_jwt",
    "java_jjwt",
}


class SplitDefinition(BaseModel):
    train_repos: List[str]
    val_repos: List[str]
    test_repos: List[str]
    expected_train_count: int
    expected_val_count: int
    expected_test_count: int


# Pinned Protocol A Configuration
# Exact asset totals derived from canonical sample_annotation_package.json (N = 166 total assets):
# Train: python_cryptography (50) + python_itsdangerous (7) + go_jwt (15) + java_java_jwt (20) = 92
# Val:   python_bcrypt (2) + go_jwt_go (12) = 14
# Test:  go_crypto (25) + java_jjwt (35) = 60
# Total: 92 + 14 + 60 = 166
PROTOCOL_A = SplitDefinition(
    train_repos=[
        "python_cryptography",
        "python_itsdangerous",
        "go_jwt",
        "java_java_jwt"
    ],
    val_repos=[
        "python_bcrypt",
        "go_jwt_go"
    ],
    test_repos=[
        "go_crypto",
        "java_jjwt"
    ],
    expected_train_count=92,
    expected_val_count=14,
    expected_test_count=60
)


def validate_repository_disjointness(split: SplitDefinition) -> Dict[str, Any]:
    """
    Formally verifies that training, validation, and test repository partitions
    are strictly pairwise disjoint, eliminating transductive leakage across codebases.
    """
    train_set = set(split.train_repos)
    val_set = set(split.val_repos)
    test_set = set(split.test_repos)

    train_val_overlap = train_set.intersection(val_set)
    train_test_overlap = train_set.intersection(test_set)
    val_test_overlap = val_set.intersection(test_set)

    is_disjoint = (len(train_val_overlap) == 0 and len(train_test_overlap) == 0 and len(val_test_overlap) == 0)

    all_split_repos = train_set.union(val_set).union(test_set)
    unknown_repos = all_split_repos.difference(CANONICAL_BENCHMARK_REPOSITORIES)

    return {
        "is_disjoint": is_disjoint,
        "has_unknown_repos": len(unknown_repos) > 0,
        "unknown_repos": sorted(list(unknown_repos)),
        "train_repos": sorted(list(train_set)),
        "val_repos": sorted(list(val_set)),
        "test_repos": sorted(list(test_set)),
        "train_val_overlap": sorted(list(train_val_overlap)),
        "train_test_overlap": sorted(list(train_test_overlap)),
        "val_test_overlap": sorted(list(val_test_overlap)),
    }


def partition_assets_by_split(
    assets: List[Dict[str, Any]],
    split: SplitDefinition
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Partitions asset dossiers according to repository membership.
    """
    train_set = set(split.train_repos)
    val_set = set(split.val_repos)
    test_set = set(split.test_repos)

    partitions = {"train": [], "val": [], "test": [], "unassigned": []}

    for a in assets:
        pid = a.get("project_id", a["asset_id"].split(":")[0] if ":" in a["asset_id"] else "")
        if pid in train_set:
            partitions["train"].append(a)
        elif pid in val_set:
            partitions["val"].append(a)
        elif pid in test_set:
            partitions["test"].append(a)
        else:
            partitions["unassigned"].append(a)

    return partitions


def validate_split_integrity(
    assets: List[Dict[str, Any]],
    split: SplitDefinition = PROTOCOL_A
) -> Dict[str, Any]:
    """
    Comprehensive, rigorous validation of benchmark split integrity:
    1. Rejects unknown repositories.
    2. Rejects duplicate asset IDs.
    3. Rejects missing repository IDs.
    4. Rejects unassigned assets.
    5. Confirms repository partitions are strictly pairwise disjoint.
    6. Verifies exact membership counts against expected values.
    """
    errors = []
    
    # 1. Check duplicate asset IDs
    asset_ids = [a.get("asset_id") for a in assets]
    if any(aid is None for aid in asset_ids):
        errors.append("Encountered asset with missing or null asset_id.")

    from collections import Counter
    id_counts = Counter(asset_ids)
    duplicates = [aid for aid, cnt in id_counts.items() if cnt > 1]
    if duplicates:
        errors.append(f"Duplicate asset IDs detected: {duplicates}")

    # 2. Check repository disjointness
    disjoint_check = validate_repository_disjointness(split)
    if not disjoint_check["is_disjoint"]:
        errors.append(
            f"Repository sets overlap! Train/Val: {disjoint_check['train_val_overlap']}, "
            f"Train/Test: {disjoint_check['train_test_overlap']}, Val/Test: {disjoint_check['val_test_overlap']}"
        )
    if disjoint_check["has_unknown_repos"]:
        errors.append(f"Split definition contains unknown repositories: {disjoint_check['unknown_repos']}")

    # 3. Partition assets
    partitions = partition_assets_by_split(assets, split)
    if partitions["unassigned"]:
        unassigned_ids = [a.get("asset_id") for a in partitions["unassigned"]]
        errors.append(f"Found {len(unassigned_ids)} unassigned assets not belonging to any split: {unassigned_ids[:5]}...")

    # 4. Count checks
    actual_train = len(partitions["train"])
    actual_val = len(partitions["val"])
    actual_test = len(partitions["test"])
    total_assets = len(assets)

    if actual_train != split.expected_train_count:
        errors.append(f"Train asset count mismatch: expected {split.expected_train_count}, got {actual_train}")
    if actual_val != split.expected_val_count:
        errors.append(f"Val asset count mismatch: expected {split.expected_val_count}, got {actual_val}")
    if actual_test != split.expected_test_count:
        errors.append(f"Test asset count mismatch: expected {split.expected_test_count}, got {actual_test}")

    # 5. Check repo-level counts
    repo_counts = {}
    for a in assets:
        pid = a.get("project_id", a["asset_id"].split(":")[0] if ":" in a["asset_id"] else "UNKNOWN")
        repo_counts[pid] = repo_counts.get(pid, 0) + 1

    unknown_asset_repos = set(repo_counts.keys()).difference(CANONICAL_BENCHMARK_REPOSITORIES)
    if unknown_asset_repos:
        errors.append(f"Assets belong to unapproved repositories: {unknown_asset_repos}")

    is_valid = len(errors) == 0

    return {
        "is_valid": is_valid,
        "total_assets": total_assets,
        "unique_asset_ids": len(id_counts),
        "actual_train_count": actual_train,
        "actual_val_count": actual_val,
        "actual_test_count": actual_test,
        "expected_train_count": split.expected_train_count,
        "expected_val_count": split.expected_val_count,
        "expected_test_count": split.expected_test_count,
        "repo_counts": repo_counts,
        "errors": errors
    }
