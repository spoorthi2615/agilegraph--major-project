import networkx as nx
from src.graph.graph import AgileGraph

def save_graph(graph: AgileGraph, filepath: str):
    nx.write_graphml(graph.G, filepath)

def load_graph(filepath: str) -> AgileGraph:
    G = nx.read_graphml(filepath)
    ag = AgileGraph()
    ag.G = G
    return ag
