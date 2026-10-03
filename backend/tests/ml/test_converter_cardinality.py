import torch
from src.graph.graph import AgileGraph
from src.ml.converter import convert_agilegraph_to_pyg
from src.ml.features import FeatureConfig

def test_converter_preserves_cardinality():
    ag = AgileGraph()
    
    # Add multiple nodes of same type
    for i in range(5):
        ag.G.add_node(f"file_{i}", category="file", properties={"language": "python"})
        
    for i in range(3):
        ag.G.add_node(f"lib_{i}", category="library", properties={"name": f"lib{i}"})
        
    for i in range(2):
        ag.G.add_node(f"crypto_{i}", category="crypto_usage", properties={})

    # Convert
    config = FeatureConfig(include_base_risk=False)
    pyg_data = convert_agilegraph_to_pyg(ag, config)

    # Validate cardinality
    assert "file" in pyg_data.node_types
    assert pyg_data["file"].x.size(0) == 5
    
    assert "library" in pyg_data.node_types
    assert pyg_data["library"].x.size(0) == 3
    
    assert "crypto_usage" in pyg_data.node_types
    assert pyg_data["crypto_usage"].x.size(0) == 2
    
    total_pyg_nodes = sum(pyg_data[nt].x.size(0) for nt in pyg_data.node_types)
    assert total_pyg_nodes == ag.G.number_of_nodes()
