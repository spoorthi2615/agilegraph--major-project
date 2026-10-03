from src.risk.factors import RiskFactors
from src.risk.sensitivity import extract_data_sensitivity
from src.risk.criticality import extract_asset_criticality
from src.risk.exposure import extract_internet_exposure
from src.risk.algorithm_strength import extract_crypto_weakness
from src.risk.cve_risk import extract_cve_risk
from src.risk.centrality import calculate_in_degree_centrality
from src.risk.migration_difficulty import extract_migration_difficulty
from src.graph.graph import AgileGraph

class FactorExtractor:
    def __init__(self, graph: AgileGraph):
        self.graph = graph

    def extract(self, node_id: str, metadata: dict, cve_info: dict, migration_inputs: dict, algorithm: str = None) -> RiskFactors:
        """
        Extracts the seven heuristic risk factors without calculating the final risk score.
        """
        if algorithm is None:
            # Traverse CONTAINS edges to find crypto_usage nodes
            weakest_algo = None
            out_edges = self.graph.G.out_edges(node_id, data=True)
            for _, target, edge_data in out_edges:
                if edge_data.get("relationship") == "CONTAINS":
                    target_data = self.graph.G.nodes.get(target, {})
                    if target_data and target_data.get("category") == "crypto_usage":
                        target_algo = target_data.get("algorithm")
                        if target_algo:
                            # Simple logic: if we found an algorithm, use it.
                            # In a real system, we'd rank them by weakness, but for now we take the first found
                            # or try to find a known weak one.
                            if weakest_algo is None:
                                weakest_algo = target_algo
                            elif target_algo.lower() in ("md5", "sha1", "des", "rc4"):
                                weakest_algo = target_algo
                                
            if weakest_algo:
                algorithm = weakest_algo
                
        return RiskFactors(
            data_sensitivity=extract_data_sensitivity(metadata),
            asset_criticality=extract_asset_criticality(metadata),
            internet_exposure=extract_internet_exposure(metadata),
            crypto_weakness=extract_crypto_weakness(algorithm),
            cve_risk=extract_cve_risk(cve_info),
            library_centrality=calculate_in_degree_centrality(self.graph, node_id),
            migration_difficulty=extract_migration_difficulty(migration_inputs)
        )
