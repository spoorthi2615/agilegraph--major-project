from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge
from src.scanners.common.models import FindingRecord
from src.scanners.dependencies.models import DependencyRecord
from src.scanners.common.enums import AssetType
from src.scanners.common.normalization import normalize_to_node


class GraphBuilder:
    """
    Builds a typed property graph adhering strictly to the six-node ontology and
    legal edge relationships defined in Synopsis 5.3.
    """
    def __init__(self, graph: AgileGraph):
        self.graph = graph

    def build_from_normalized_records(self, records: list):
        for record in records:
            if isinstance(record, DependencyRecord):
                self._handle_dependency(record)
            elif isinstance(record, FindingRecord):
                self._handle_finding(record)
                
    def _handle_dependency(self, record: DependencyRecord):
        # We enrich an existing Library node or create a new one
        lib_node_id = f"{record.repository}:library:{record.package_name}"
        lib_node = self.graph.get_node(lib_node_id)
        
        properties = {
            "library": record.package_name,
            "version": record.version,
            "ecosystem": record.ecosystem,
            "crypto_relevance": record.crypto_relevance,
            "manifest_file": record.manifest_file
        }
        # Clean up Nones
        properties = {k: v for k, v in properties.items() if v is not None}
        
        if lib_node is None:
            lib_node = GraphNode(id=lib_node_id, category=AssetType.LIBRARY.value, properties=properties)
            self.graph.add_node(lib_node)
        else:
            lib_node.properties.update(properties)
            self.graph.add_node(lib_node)

        # Create manifest File node and link to Library with DEPENDS_ON (legal per schema)
        if record.manifest_file:
            manifest_file_id = f"{record.repository}:{record.manifest_file}"
            if self.graph.get_node(manifest_file_id) is None:
                manifest_node = GraphNode(
                    id=manifest_file_id,
                    category=AssetType.FILE.value,
                    properties={"repository": record.repository, "file": record.manifest_file, "language": record.language.value if record.language else None}
                )
                self.graph.add_node(manifest_node)
            self.graph.add_edge(GraphEdge(
                source_id=manifest_file_id,
                target_id=lib_node_id,
                relationship="DEPENDS_ON"
            ))
            
    def _handle_finding(self, record: FindingRecord):
        # Create primary node
        node = normalize_to_node(record)
        
        # Ensure File node exists if this record belongs to a file
        file_node_id = f"{record.repository}:{record.file}" if record.file else None
        if file_node_id and self.graph.get_node(file_node_id) is None:
            file_node = GraphNode(
                id=file_node_id,
                category=AssetType.FILE.value,
                properties={"repository": record.repository, "file": record.file, "language": record.language.value if record.language else None}
            )
            self.graph.add_node(file_node)

        # Add the primary node
        if node.id != file_node_id or node.category != AssetType.FILE.value:
            if record.asset_type != AssetType.LIBRARY:
                self.graph.add_node(node)
            
        # Create legal edges matching Synopsis 5.3:
        if record.asset_type == AssetType.CRYPTO_USAGE and file_node_id:
            # File --CONTAINS--> CryptoUsage
            self.graph.add_edge(GraphEdge(
                source_id=file_node_id,
                target_id=node.id,
                relationship="CONTAINS"
            ))
            
            # If library is declared with crypto call, link CryptoUsage --CALLS--> Library and File --IMPORTS--> Library
            if record.library:
                lib_node_id = f"{record.repository}:library:{record.library}"
                if self.graph.get_node(lib_node_id) is None:
                    lib_node = GraphNode(id=lib_node_id, category=AssetType.LIBRARY.value, properties={"library": record.library})
                    self.graph.add_node(lib_node)
                self.graph.add_edge(GraphEdge(
                    source_id=node.id,
                    target_id=lib_node_id,
                    relationship="CALLS"
                ))
                self.graph.add_edge(GraphEdge(
                    source_id=file_node_id,
                    target_id=lib_node_id,
                    relationship="IMPORTS"
                ))

            # Connect existing endpoints, certificates, and sensitive data in this file:
            for neighbor in list(self.graph.G.neighbors(file_node_id)):
                neighbor_data = self.graph.G.nodes.get(neighbor, {})
                cat = neighbor_data.get("category")
                if cat == AssetType.ENDPOINT.value:
                    # Endpoint --EXPOSES--> CryptoUsage
                    self.graph.add_edge(GraphEdge(
                        source_id=neighbor,
                        target_id=node.id,
                        relationship="EXPOSES"
                    ))
                elif cat == AssetType.CERTIFICATE.value:
                    # CryptoUsage --USES_CERT--> Certificate
                    self.graph.add_edge(GraphEdge(
                        source_id=node.id,
                        target_id=neighbor,
                        relationship="USES_CERT"
                    ))
                elif cat == AssetType.SENSITIVE_DATA.value:
                    # CryptoUsage --PROTECTS--> SensitiveData
                    self.graph.add_edge(GraphEdge(
                        source_id=node.id,
                        target_id=neighbor,
                        relationship="PROTECTS"
                    ))
                
        elif record.asset_type == AssetType.LIBRARY and file_node_id:
            # File --IMPORTS--> Library
            lib_node_id = f"{record.repository}:library:{record.library}"
            lib_node = GraphNode(id=lib_node_id, category=AssetType.LIBRARY.value, properties={"library": record.library})
            self.graph.add_node(lib_node)
            
            self.graph.add_edge(GraphEdge(
                source_id=file_node_id,
                target_id=lib_node_id,
                relationship="IMPORTS"
            ))

        elif record.asset_type == AssetType.CERTIFICATE and file_node_id:
            # File --CONTAINS--> Certificate
            self.graph.add_edge(GraphEdge(
                source_id=file_node_id,
                target_id=node.id,
                relationship="CONTAINS"
            ))
            # Connect any existing crypto_usage in this file: CryptoUsage --USES_CERT--> Certificate
            # Connect any existing endpoint in this file: Endpoint --USES_CERT--> Certificate
            for neighbor in list(self.graph.G.neighbors(file_node_id)):
                neighbor_data = self.graph.G.nodes.get(neighbor, {})
                cat = neighbor_data.get("category")
                if cat == AssetType.CRYPTO_USAGE.value:
                    self.graph.add_edge(GraphEdge(
                        source_id=neighbor,
                        target_id=node.id,
                        relationship="USES_CERT"
                    ))
                elif cat == AssetType.ENDPOINT.value:
                    self.graph.add_edge(GraphEdge(
                        source_id=neighbor,
                        target_id=node.id,
                        relationship="USES_CERT"
                    ))

        elif record.asset_type == AssetType.ENDPOINT and file_node_id:
            # File --CALLS--> Endpoint
            self.graph.add_edge(GraphEdge(
                source_id=file_node_id,
                target_id=node.id,
                relationship="CALLS"
            ))
            # Connect existing crypto usages in this file: Endpoint --EXPOSES--> CryptoUsage
            # Connect existing certificates in this file: Endpoint --USES_CERT--> Certificate
            for neighbor in list(self.graph.G.neighbors(file_node_id)):
                neighbor_data = self.graph.G.nodes.get(neighbor, {})
                cat = neighbor_data.get("category")
                if cat == AssetType.CRYPTO_USAGE.value:
                    self.graph.add_edge(GraphEdge(
                        source_id=node.id,
                        target_id=neighbor,
                        relationship="EXPOSES"
                    ))
                elif cat == AssetType.CERTIFICATE.value:
                    self.graph.add_edge(GraphEdge(
                        source_id=node.id,
                        target_id=neighbor,
                        relationship="USES_CERT"
                    ))

        elif record.asset_type == AssetType.SENSITIVE_DATA and file_node_id:
            # File --CONTAINS--> SensitiveData
            self.graph.add_edge(GraphEdge(
                source_id=file_node_id,
                target_id=node.id,
                relationship="CONTAINS"
            ))
            # If the file also contains crypto_usage: CryptoUsage --PROTECTS--> SensitiveData
            for neighbor in list(self.graph.G.neighbors(file_node_id)):
                neighbor_data = self.graph.G.nodes.get(neighbor, {})
                if neighbor_data.get("category") == AssetType.CRYPTO_USAGE.value:
                    self.graph.add_edge(GraphEdge(
                        source_id=neighbor,
                        target_id=node.id,
                        relationship="PROTECTS"
                    ))
