import torch
import random
import numpy as np

def set_seed(seed: int):
    """
    Ensures deterministic training initialization.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

class MissingLabelsError(Exception):
    pass

class TrainingPipeline:
    def __init__(self, model: torch.nn.Module, config: dict):
        self.model = model
        self.config = config
        set_seed(config.get("seed", 42))
        
    def validate_data_for_training(self, hetero_data):
        """
        Scans data to ensure we have actual labels before training.
        Refuses to train if no expert (or heuristic, if explicitly allowed) labels are present.
        """
        has_labels = False
        
        # Check all node categories for valid labels (y >= 0)
        for node_type in hetero_data.node_types:
            if hasattr(hetero_data[node_type], 'y'):
                valid_labels = (hetero_data[node_type].y >= 0).sum().item()
                if valid_labels > 0:
                    has_labels = True
                    break
                    
        if not has_labels:
            raise MissingLabelsError("Training refused: No labeled data found in the dataset.")
            
    def train_step(self, hetero_data, optimizer, criterion):
        self.model.train()
        optimizer.zero_grad()
        
        out = self.model(hetero_data.x_dict, hetero_data.edge_index_dict)
        
        loss = 0.0
        # Calculate loss over labeled nodes
        for node_type in hetero_data.node_types:
            if hasattr(hetero_data[node_type], 'y') and node_type in out:
                mask = hetero_data[node_type].y >= 0
                if mask.sum() > 0:
                    loss += criterion(out[node_type][mask], hetero_data[node_type].y[mask])
                    
        if isinstance(loss, float) and loss == 0.0:
            return 0.0 # No labeled nodes
            
        loss.backward()
        optimizer.step()
        return loss.item()

    def save_checkpoint(self, path: str):
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'config': self.config
        }, path)
        
    def load_checkpoint(self, path: str):
        checkpoint = torch.load(path)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.config = checkpoint['config']
