import pytest
import torch
from src.graph.graph import AgileGraph
from src.graph.schema import GraphNode
from src.ml.features import FeatureConfig
from src.ml.converter import convert_agilegraph_to_pyg

def test_graph_conversion():
    ag = AgileGraph()
    # Add Nodes
    # Using specific node types from schema
    n1 = GraphNode(id="file1", category="file", properties={"expert_label": {"class_idx": 1}})
    n2 = GraphNode(id="lib1", category="library", properties={"risk_factors": {"cve_risk": 1.0}})
    ag.add_node(n1)
    ag.add_node(n2)
    # Add Edge
    ag.G.add_edge("file1", "lib1", relationship="IMPORTS")
    
    config = FeatureConfig(include_base_risk=False)
    pyg_data = convert_agilegraph_to_pyg(ag, config)
    
    assert "file" in pyg_data.node_types
    assert "library" in pyg_data.node_types
    
    # Check features and labels
    assert pyg_data["file"].x.shape == (1, 14)
    assert pyg_data["file"].y[0].item() == 1
    assert pyg_data["file"].label_sources[0] == "EXPERT"
    
    assert pyg_data["library"].x[0][4].item() == 1.0 # cve_risk is index 4
    assert pyg_data["library"].y[0].item() == -1 # UNKNOWN
    
    # Check edges
    edge_type = ("file", "IMPORTS", "library")
    assert edge_type in pyg_data.edge_types
    assert pyg_data[edge_type].edge_index.shape == (2, 1)
