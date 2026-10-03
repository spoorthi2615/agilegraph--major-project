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
        return RiskFactors(
            data_sensitivity=extract_data_sensitivity(metadata),
            asset_criticality=extract_asset_criticality(metadata),
            internet_exposure=extract_internet_exposure(metadata),
            crypto_weakness=extract_crypto_weakness(algorithm),
            cve_risk=extract_cve_risk(cve_info),
            library_centrality=calculate_in_degree_centrality(self.graph, node_id),
            migration_difficulty=extract_migration_difficulty(migration_inputs)
        )
