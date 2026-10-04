import os
import sys
import json
import subprocess
import torch
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath('src'))
from src.dataset.models import CorpusManifest, CorpusProject, DataOrigin, ProjectStatus, SizeTier, Language, ScannerProvenance, GraphProvenance
from src.dataset.manager import DatasetManager
from src.scanners.python.scanner import scan_python_code
from src.scanners.java.scanner import scan_java_code
from src.scanners.go.scanner import scan_go_code
from src.scanners.dependencies.scanner import scan_manifest
from src.graph.graph import AgileGraph
from src.graph.builder import GraphBuilder
from src.graph.validation import validate_graph
from src.risk.factor_extractor import FactorExtractor
from src.risk.heuristic import calculate_heuristic_score
from src.risk.weights import HeuristicWeights
from src.risk.score import MissingDataPolicy
from src.ml.converter import convert_agilegraph_to_pyg
from src.ml.features import FeatureConfig
from src.ml.pipeline import set_seed

# The target repositories with pinned SHAs for reproducibility
REPOS = [
    {"id": "python_itsdangerous", "url": "https://github.com/pallets/itsdangerous", "sha": "672971d66a2ef9f85151e53283113f33d642dabd", "lang": Language.PYTHON, "size": SizeTier.SMALL},
    {"id": "python_bcrypt", "url": "https://github.com/pyca/bcrypt", "sha": "59b41aaa24c025d1cd231c37d2755b94184a3e67", "lang": Language.PYTHON, "size": SizeTier.SMALL},
    {"id": "python_cryptography", "url": "https://github.com/pyca/cryptography", "sha": "f0ba3000a365d44db153362e847c88339c9231f4", "lang": Language.PYTHON, "size": SizeTier.LARGE},
    {"id": "java_java_jwt", "url": "https://github.com/auth0/java-jwt", "sha": "29f252b2d6fea74df6576803d5fce5f6d6799cf3", "lang": Language.JAVA, "size": SizeTier.SMALL},
    {"id": "java_jjwt", "url": "https://github.com/jwtk/jjwt", "sha": "fb71496164c71442d08adec4571d9616ed5e1b8d", "lang": Language.JAVA, "size": SizeTier.LARGE},
    {"id": "go_jwt", "url": "https://github.com/golang-jwt/jwt", "sha": "73c870b18e68b6e654b2b03f485aa3c9fab32cea", "lang": Language.GO, "size": SizeTier.SMALL},
    {"id": "go_jwt_go", "url": "https://github.com/dgrijalva/jwt-go", "sha": "9742bd7fca1c67ba2eb793750f56ee3094d1b04f", "lang": Language.GO, "size": SizeTier.SMALL},
    {"id": "go_crypto", "url": "https://github.com/golang/crypto", "sha": "b39ff6d641ecc5bb4b241737cb0c6b646f3e12a9", "lang": Language.GO, "size": SizeTier.LARGE}
]

CORPUS_DIR = "dataset/corpus"
ARTIFACTS_DIR = "dataset/artifacts"

def run_cmd(cmd, cwd=None):
    res = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Command failed: {cmd}\n{res.stderr}")
    return res.stdout.strip()

def clone_and_get_sha(repo):
    repo_dir = os.path.join(CORPUS_DIR, repo["id"])
    if not os.path.exists(repo_dir):
        print(f"Cloning {repo['url']}...")
        run_cmd(f"git clone {repo['url']} {repo['id']}", cwd=CORPUS_DIR)
    
    # Checkout the pinned SHA
    pinned_sha = repo.get("sha")
    if pinned_sha:
        run_cmd(f"git checkout {pinned_sha}", cwd=repo_dir)
        
    sha = run_cmd("git rev-parse HEAD", cwd=repo_dir)
    return sha, repo_dir

def scan_files(repo_id, repo_dir, lang):
    findings = []
    ext = {Language.PYTHON: ".py", Language.JAVA: ".java", Language.GO: ".go"}[lang]
    scan_fn = {
        Language.PYTHON: scan_python_code,
        Language.JAVA: scan_java_code,
        Language.GO: scan_go_code
    }[lang]
    
    # 1. Source code scanning
    for root, _, files in os.walk(repo_dir):
        for file in files:
            if file.endswith(ext):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, repo_dir).replace("\\", "/")
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        code = f.read()
                    f_findings = scan_fn(repo_id, rel_path, code)
                    findings.extend(f_findings)
                except Exception as e:
                    pass # Ignore read errors
    
    # 2. Dependency scanning
    manifests = ["requirements.txt", "pom.xml", "build.gradle", "go.mod"]
    for m in manifests:
        m_path = os.path.join(repo_dir, m)
        if os.path.exists(m_path):
            try:
                with open(m_path, "r", encoding="utf-8") as f:
                    content = f.read()
                df = scan_manifest(repo_id, m, content)
                findings.extend(df)
            except:
                pass
                
    return findings

def main():
    set_seed(42)
    os.makedirs(CORPUS_DIR, exist_ok=True)
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)
    
    projects = []
    report = {
        "projects_acquired": 0,
        "projects_rejected": 0,
        "languages": {},
        "size_tiers": {},
        "findings": 0,
        "graphs": 0,
        "failed_scans": 0,
        "details": []
    }
    

    for r in REPOS:
        try:
            sha, repo_dir = clone_and_get_sha(r)
            if not sha:
                report["projects_rejected"] += 1
                continue
                
            p = CorpusProject(
                project_id=r["id"],
                repository_url=r["url"],
                commit_sha=sha,
                language=r["lang"],
                size_tier=r["size"],
                origin=DataOrigin.PUBLIC_OPEN_SOURCE,
                status=ProjectStatus.ACQUIRED,
                checkout_timestamp=datetime.now(timezone.utc),
                scanner_provenance=ScannerProvenance(scanner_version="1.0", dependency_scan_version="1.0")
            )
            report["projects_acquired"] += 1
            report["languages"][r["lang"].value] = report["languages"].get(r["lang"].value, 0) + 1
            report["size_tiers"][r["size"].value] = report["size_tiers"].get(r["size"].value, 0) + 1
            
            # Scan
            findings = scan_files(p.project_id, repo_dir, p.language)
            p.status = ProjectStatus.SCANNED
            report["findings"] += len(findings)
            
            # Build Graph
            ag = AgileGraph()
            builder = GraphBuilder(ag)
            builder.build_from_normalized_records(findings)
            
            # Validate Graph
            errors = validate_graph(ag)
            if errors:
                raise Exception(f"Invalid graph: {errors}")
                
            p.status = ProjectStatus.GRAPH_BUILT
            p.graph_provenance = GraphProvenance(graph_version="1.0", risk_calculation_version="1.0")
            
            # Risk Scoring
            extractor = FactorExtractor(ag)
            for node, data in ag.G.nodes(data=True):
                if data.get("category") == "file":
                    props = data.get("properties", {})
                    factors = extractor.extract(node, props, {}, {})
                    # Convert factors to dict for properties
                    props = data.setdefault("properties", {})
                    props["risk_factors"] = {k: getattr(factors, k).value for k in factors.model_fields.keys() if getattr(factors, k).value is not None}
                    
                    # Heuristic score
                    w = 1.0 / 7.0
                    weights = HeuristicWeights(
                        data_sensitivity=w, asset_criticality=w, internet_exposure=w,
                        crypto_weakness=w, cve_risk=w, library_centrality=w, migration_difficulty=w
                    )
                    try:
                        result = calculate_heuristic_score(factors, weights, policy=MissingDataPolicy.RENORMALIZE)
                        props["base_risk"] = result.score
                        props["heuristic_audit"] = result.model_dump()
                    except ValueError:
                        pass # No valid factors
            
            p.status = ProjectStatus.RISK_SCORED
            
            # Convert to PyG
            config = FeatureConfig(include_base_risk=False)
            pyg_data = convert_agilegraph_to_pyg(ag, config)
            
            # Save artifact
            artifact_path = os.path.join(ARTIFACTS_DIR, f"{p.project_id}.pt")
            torch.save(pyg_data, artifact_path)
            
            p.status = ProjectStatus.READY_FOR_MODELING
            projects.append(p)
            report["graphs"] += 1
            report["details"].append({
                "id": p.project_id,
                "sha": p.commit_sha,
                "nodes": ag.G.number_of_nodes(),
                "edges": ag.G.number_of_edges(),
                "findings": len(findings)
            })
            
        except Exception as e:
            report["failed_scans"] += 1
            report["projects_rejected"] += 1
            print(f"Error on {r['id']}: {e}")
            
    # Manifest
    manifest = CorpusManifest(
        manifest_id="phase11_corpus",
        dataset_generation_version="1.0",
        projects=projects
    )
    
    with open(os.path.join(ARTIFACTS_DIR, "manifest.json"), "w") as f:
        f.write(manifest.model_dump_json(indent=2))
        
    # Stratified Split by Language (Prevent Language Confounding)
    train_ids = ["python_cryptography", "java_jjwt", "go_crypto"]
    val_ids = ["python_bcrypt", "java_java_jwt", "go_jwt"]
    test_ids = ["python_itsdangerous", "go_jwt_go"]
    
    report["splits"] = {
        "train": train_ids,
        "validation": val_ids,
        "test": test_ids
    }
    
    with open(os.path.join(ARTIFACTS_DIR, "report.json"), "w") as f:
        json.dump(report, f, indent=2)

    print("Phase 11 Corpus Generation Complete")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
