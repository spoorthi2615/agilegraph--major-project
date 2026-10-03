from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode, GraphEdge
from src.scanners.common.models import FindingRecord
from src.scanners.dependencies.models import DependencyRecord
from src.scanners.common.enums import AssetType
from src.scanners.common.normalization import normalize_to_node

class GraphBuilder:
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
            # Enrich existing node
            lib_node.properties.update(properties)
            self.graph.add_node(lib_node) # will update in NetworkX graph wrapper if we set properties, but let's re-add
            
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
            # If it's a file node itself, it might override the stub, which is fine
            # If it's a library node, we don't add the line-specific finding node, we only add the canonical library node later
            if node.id != file_node_id or node.category != AssetType.FILE.value:
                if record.asset_type != AssetType.LIBRARY:
                    self.graph.add_node(node)
                
            # Create Edges based on Implementation Decisions from docs/graph_schema.md
            if record.asset_type == AssetType.CRYPTO_USAGE and file_node_id:
                # File --CONTAINS--> CryptoUsage
                self.graph.add_edge(GraphEdge(
                    source_id=file_node_id,
                    target_id=node.id,
                    relationship="CONTAINS"
                ))
                
                # CryptoUsage --CALLS--> Library (if library is known)
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
                    
            elif record.asset_type == AssetType.LIBRARY and file_node_id:
                # File --IMPORTS--> Library
                # Use a specific ID for library to avoid collision with file lines
                lib_node_id = f"{record.repository}:library:{record.library}"
                
                # We normalize_to_node created an ID for the import statement. 
                # Let's map it to the actual library node.
                lib_node = GraphNode(id=lib_node_id, category=AssetType.LIBRARY.value, properties={"library": record.library})
                self.graph.add_node(lib_node)
                
                self.graph.add_edge(GraphEdge(
                    source_id=file_node_id,
                    target_id=lib_node_id,
                    relationship="IMPORTS"
                ))
