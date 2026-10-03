# Interfaces for future GNNExplainer studies

def get_node_importance(model, data, target_node_idx):
    """
    Hooks for extracting GNNExplainer node importances.
    """
    pass

def get_edge_importance(model, data, target_node_idx):
    """
    Hooks for extracting GNNExplainer edge importances (attention weights if applicable).
    """
    pass

def get_feature_importance(model, data, target_node_idx):
    """
    Hooks for extracting feature mask importances.
    """
    pass
