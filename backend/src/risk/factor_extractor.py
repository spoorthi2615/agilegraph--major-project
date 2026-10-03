from src.risk.factors import RiskFactors, FactorValue
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
        best_crypto_weakness = FactorValue(value=None, source="algorithm unknown", confidence=0.0)
        
        if algorithm is not None:
            # If explicitly provided, just evaluate that one
            best_crypto_weakness = extract_crypto_weakness(algorithm)
        else:
            # Traverse CONTAINS edges to find ALL crypto_usage nodes and take the maximum risk
            out_edges = self.graph.G.out_edges(node_id, data=True)
            for _, target, edge_data in out_edges:
                if edge_data.get("relationship") == "CONTAINS":
                    target_data = self.graph.G.nodes.get(target, {})
                    if target_data and target_data.get("category") == "crypto_usage":
                        target_algo = target_data.get("algorithm")
                        key_size = target_data.get("key_size")
                        if target_algo:
                            weakness = extract_crypto_weakness(target_algo, key_size=key_size)
                            # Keep the highest risk score
                            if weakness.value is not None:
                                if best_crypto_weakness.value is None or weakness.value > best_crypto_weakness.value:
                                    best_crypto_weakness = weakness
                                    
        return RiskFactors(
            data_sensitivity=extract_data_sensitivity(metadata),
            asset_criticality=extract_asset_criticality(metadata),
            internet_exposure=extract_internet_exposure(metadata),
            crypto_weakness=best_crypto_weakness,
            cve_risk=extract_cve_risk(cve_info),
            library_centrality=calculate_in_degree_centrality(self.graph, node_id),
            migration_difficulty=extract_migration_difficulty(migration_inputs)
        )
