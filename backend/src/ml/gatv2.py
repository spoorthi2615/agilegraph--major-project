import torch
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv, HeteroConv, Linear
import torch.nn as nn

class HeteroGATv2(nn.Module):
    def __init__(self, metadata, hidden_channels: int, out_channels: int, num_heads: int = 4):
        super().__init__()
        
        # Project all inputs to hidden_channels first
        self.proj = nn.ModuleDict()
        for node_type in metadata[0]:
            self.proj[node_type] = Linear(-1, hidden_channels)
            
        # Build HeteroConv layers manually
        conv1_dict = {}
        conv2_dict = {}
        for edge_type in metadata[1]:
            conv1_dict[edge_type] = GATv2Conv((-1, -1), hidden_channels, heads=num_heads, concat=False, add_self_loops=False)
            conv2_dict[edge_type] = GATv2Conv((-1, -1), hidden_channels, heads=num_heads, concat=False, add_self_loops=False)
            
        self.conv1 = HeteroConv(conv1_dict, aggr='sum')
        self.conv2 = HeteroConv(conv2_dict, aggr='sum')
        
        self.lin = nn.ModuleDict()
        for node_type in metadata[0]:
            self.lin[node_type] = Linear(-1, out_channels)

    def forward(self, x_dict, edge_index_dict):
        # 1. Project all nodes to hidden_channels so they have a valid representation
        h_dict = {key: F.elu(self.proj[key](x)) for key, x in x_dict.items()}
        
        # 2. First Conv Layer with residual fallback
        out1 = self.conv1(h_dict, edge_index_dict)
        for key in h_dict.keys():
            if key in out1:
                h_dict[key] = h_dict[key] + F.elu(out1[key])
                
        # 3. Second Conv Layer with residual fallback
        out2 = self.conv2(h_dict, edge_index_dict)
        for key in h_dict.keys():
            if key in out2:
                h_dict[key] = h_dict[key] + F.elu(out2[key])
                
        # 4. Final classification head
        out_dict = {key: self.lin[key](h) for key, h in h_dict.items()}
        return out_dict

def create_hetero_gatv2(metadata, hidden_channels: int = 64, out_channels: int = 3, num_heads: int = 4) -> nn.Module:
    """
    Creates a GATv2 model tailored for the heterogeneous AgileGraph metadata.
    Operates over the specific node categories and varying edge relationships.
    """
    return HeteroGATv2(metadata, hidden_channels, out_channels, num_heads)
