import os
import json
from typing import Dict, Any, List
from src.ml.expert_validation import ValidationDataset

class AnnotationImporter:
    def __init__(self, expected_asset_ids: List[str], expected_expert_ids: List[str], dataset_version: str):
        self.expected_asset_ids = set(expected_asset_ids)
        self.expected_expert_ids = set(expected_expert_ids)
        self.dataset_version = dataset_version

    def import_annotations(self, filepath: str, protocol_status: str) -> Dict[str, Any]:
        """
        Imports genuine expert annotations strictly validating constraints.
        """
        if protocol_status != "FINALIZED":
            return {
                "status": "REJECTED",
                "message": f"Cannot import annotations while protocol is {protocol_status}."
            }
            
        if not os.path.exists(filepath):
            return {
                "status": "REJECTED",
                "message": "File not found."
            }

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return {"status": "REJECTED", "message": "Invalid JSON format."}

        # Simplified schema check for handoff
        imported = 0
        seen = set()
        
        # Validations
        for record in data.get("labels", []):
            asset_id = record.get("asset_id")
            expert_id = record.get("expert_id")
            label = record.get("label")
            ts = record.get("timestamp")
            dv = record.get("dataset_version")
            
            if asset_id not in self.expected_asset_ids:
                return {"status": "REJECTED", "message": f"Unknown asset ID: {asset_id}"}
                
            if expert_id not in self.expected_expert_ids:
                return {"status": "REJECTED", "message": f"Unknown expert ID: {expert_id}"}
                
            if label not in ["HIGH", "MEDIUM", "LOW", "UNKNOWN"]:
                return {"status": "REJECTED", "message": f"Invalid label: {label}"}
                
            if not ts:
                return {"status": "REJECTED", "message": "Malformed timestamp."}
                
            if dv != self.dataset_version:
                return {"status": "REJECTED", "message": "Inconsistent dataset version."}
                
            pair = (asset_id, expert_id)
            if pair in seen:
                return {"status": "REJECTED", "message": "Duplicate rating for same asset by same expert."}
            seen.add(pair)
            
            imported += 1
            
        return {
            "status": "SUCCESS",
            "imported_count": imported
        }
