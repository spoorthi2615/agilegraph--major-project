from src.risk.factors import RiskFactors, FactorValue
from src.risk.sensitivity import extract_data_sensitivity
from src.risk.criticality import extract_asset_criticality
from src.risk.exposure import extract_internet_exposure
from src.risk.algorithm_strength import extract_crypto_weakness
from src.risk.cve_risk import extract_cve_risk
from src.risk.centrality import calculate_in_degree_centrality, calculate_library_centrality_for_file
from src.risk.migration_difficulty import extract_migration_difficulty
from src.graph.graph import AgileGraph

class FactorExtractor:
    def __init__(self, graph: AgileGraph):
        self.graph = graph

    def extract(self, node_id: str, metadata: dict, cve_info: dict, migration_inputs: dict, algorithm: str = None) -> RiskFactors:
        """
        Extracts the seven heuristic risk factors without calculating the final risk score.
        """
        best_crypto_weakness = FactorValue(value=None, source="algorithm unknown", confidence=0.0)
        
        # Traverse graph edges to discover connected assets for this file
        connected_endpoints = []
        connected_sensitive_data = []
        connected_libraries = []
        connected_certificates = []
        crypto_usage_count = 0

        out_edges = self.graph.G.out_edges(node_id, data=True)
        for _, target, edge_data in out_edges:
            rel = edge_data.get("relationship")
            target_data = self.graph.G.nodes.get(target, {})
            cat = target_data.get("category")
            if cat == "endpoint" or rel in ("EXPOSES", "CALLS"):
                connected_endpoints.append(target_data)
            elif cat == "sensitive_data" or rel == "PROTECTS":
                connected_sensitive_data.append(target_data)
            elif cat == "library" or rel in ("IMPORTS", "DEPENDS_ON"):
                connected_libraries.append((target, target_data))
            elif cat == "certificate" or rel in ("CONTAINS", "USES_CERT"):
                if cat == "certificate":
                    connected_certificates.append(target_data)

        if algorithm is not None:
            # If explicitly provided, just evaluate that one
            best_crypto_weakness = extract_crypto_weakness(algorithm)
        else:
            # Traverse CONTAINS edges to find ALL crypto_usage nodes and take the maximum risk
            unrated_algos = []
            rated_findings = []
            for _, target, edge_data in out_edges:
                if edge_data.get("relationship") == "CONTAINS":
                    target_data = self.graph.G.nodes.get(target, {})
                    if target_data and target_data.get("category") == "crypto_usage":
                        crypto_usage_count += 1
                        target_algo = target_data.get("algorithm")
                        key_size = target_data.get("key_size")
                        if target_algo:
                            weakness = extract_crypto_weakness(target_algo, key_size=key_size)
                            if weakness.value is not None:
                                rated_findings.append((weakness, target_algo))
                            else:
                                unrated_algos.append(target_algo)

            if rated_findings:
                best_weakness, _ = max(rated_findings, key=lambda x: x[0].value)
                if unrated_algos:
                    unrated_str = ", ".join(sorted(set(unrated_algos)))
                    best_crypto_weakness = FactorValue(
                        value=best_weakness.value,
                        source=f"{best_weakness.source} [unrated crypto also detected: {unrated_str}]",
                        confidence=round(min(best_weakness.confidence, 0.65), 2)
                    )
                else:
                    best_crypto_weakness = best_weakness
            elif unrated_algos:
                unrated_str = ", ".join(sorted(set(unrated_algos)))
                best_crypto_weakness = FactorValue(
                    value=None,
                    source=f"unrecognized algorithm(s) ({unrated_str})",
                    confidence=0.0
                )

        # Data-backed CVE enrichment from connected libraries if not explicitly provided
        active_cve_info = cve_info
        if not active_cve_info and connected_libraries:
            from src.scanners.dependencies.cve import enrich_cves
            all_cves = []
            provider_failed = False
            for item in connected_libraries:
                lib = item[1] if isinstance(item, tuple) else item
                props = lib.get("properties", lib) if isinstance(lib, dict) else getattr(lib, "properties", {})
                pkg_name = props.get("library")
                eco = props.get("ecosystem", (metadata or {}).get("language", "python"))
                ver = props.get("version")
                if pkg_name:
                    res = enrich_cves(pkg_name, eco, ver)
                    if res.get("status") == "success":
                        all_cves.extend(res.get("cves", []))
                    elif res.get("status") == "unavailable":
                        provider_failed = True
            if all_cves:
                active_cve_info = {"status": "success", "cves": all_cves}
            elif provider_failed:
                active_cve_info = {"status": "unavailable"}
            else:
                active_cve_info = {"status": "success", "cves": []}

        # Data-backed migration inputs from graph structure if not explicitly provided
        active_migration_inputs = migration_inputs
        if not active_migration_inputs:
            # Only count code_change if there are crypto usages that were assessed or recognized
            effective_crypto_count = crypto_usage_count if best_crypto_weakness.value is not None else 0
            total_elements = effective_crypto_count + len(connected_libraries) + len(connected_certificates) + len(connected_endpoints)
            if total_elements > 0:
                active_migration_inputs = {
                    "code_change": effective_crypto_count,
                    "dependency_change": len(connected_libraries),
                    "certificate_change": len(connected_certificates),
                    "infrastructure_change": len(connected_endpoints)
                }

        # Robust file path extraction from metadata or node attributes
        meta = dict(metadata) if metadata else {}
        file_path = meta.get("file")
        if not file_path and node_id in self.graph.G:
            file_path = self.graph.G.nodes[node_id].get("file")
        if not file_path and ":" in node_id:
            candidate = node_id.split(":", 1)[1]
            if any(candidate.endswith(ext) for ext in (".py", ".java", ".go", ".txt", ".xml", ".gradle")):
                file_path = candidate
        if file_path and "file" not in meta:
            meta["file"] = file_path

        in_deg = self.graph.G.in_degree(node_id) if node_id in self.graph.G else 0

        # If node itself is a library, calculate its direct centrality; otherwise aggregate connected libraries for file
        node_cat = self.graph.G.nodes.get(node_id, {}).get("category")
        if node_cat == "library":
            lib_centrality = calculate_in_degree_centrality(self.graph, node_id)
        else:
            lib_centrality = calculate_library_centrality_for_file(self.graph, node_id, connected_libraries)

        return RiskFactors(
            data_sensitivity=extract_data_sensitivity(meta, connected_sensitive_data),
            asset_criticality=extract_asset_criticality(meta, file_path=file_path, in_degree=in_deg),
            internet_exposure=extract_internet_exposure(meta, connected_endpoints),
            crypto_weakness=best_crypto_weakness,
            cve_risk=extract_cve_risk(active_cve_info),
            library_centrality=lib_centrality,
            migration_difficulty=extract_migration_difficulty(active_migration_inputs)
        )
