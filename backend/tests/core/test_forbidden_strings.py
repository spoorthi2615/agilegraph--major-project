import os
from pathlib import Path

FORBIDDEN_STRINGS = [
    "PENDING_EXPERT_LABELS",
    "Neo4j",
    "CBOMkit",
]

EXCLUDED_DIR_NAMES = {
    ".git",
    "node_modules",
    "archive",
    ".pytest_cache",
    "__pycache__",
    "cache",
    "dist",
    "build",
    ".venv",
    "venv",
    ".idea",
    ".vscode",
}

EXCLUDED_EXTENSIONS = {
    ".pyc",
    ".png",
    ".jpg",
    ".jpeg",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".bin",
    ".pt",
    ".pth",
}


def test_forbidden_strings_eliminated_across_repository():
    """
    Asserts that forbidden out-of-scope strings (PENDING_EXPERT_LABELS, Neo4j, CBOMkit)
    do not exist in any active source code, documentation, or configuration file
    outside archived folders (e.g., docs/archive/).
    """
    repo_root = Path(__file__).resolve().parents[3]
    violations = []

    for root, dirs, files in os.walk(repo_root):
        # Filter out excluded directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIR_NAMES and not d.startswith(".")]

        rel_root = os.path.relpath(root, repo_root)
        if "docs" in Path(rel_root).parts and "archive" in Path(rel_root).parts:
            continue

        for file in files:
            file_path = Path(root) / file
            if file_path.name == "test_forbidden_strings.py":
                continue
            if file_path.suffix.lower() in EXCLUDED_EXTENSIONS:
                continue

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except Exception:
                continue

            for forbidden in FORBIDDEN_STRINGS:
                if forbidden.lower() in content.lower():
                    # Check if it is a false positive or actual violation
                    violations.append(f"{file_path.relative_to(repo_root)}: contains '{forbidden}'")

    assert not violations, (
        f"Found {len(violations)} forbidden string violations in active repository:\n"
        + "\n".join(violations)
    )
