"""
Storage handlers for saving property data.
"""
import json
import csv
import os
from typing import List
from property_model import Property


class PropertyStorage:
    """Handles saving property data to various formats."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def save_to_json(self, properties: List[Property], filename: str = "properties.json"):
        """Save properties to JSON file."""
        filepath = os.path.join(self.output_dir, filename)
        data = [prop.to_dict() for prop in properties]
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(properties)} properties to {filepath}")
    
    def save_to_csv(self, properties: List[Property], filename: str = "properties.csv"):
        """Save properties to CSV file."""
        filepath = os.path.join(self.output_dir, filename)
        
        if not properties:
            return
        
        fieldnames = list(properties[0].to_dict().keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for prop in properties:
                writer.writerow(prop.to_dict())
        
        print(f"Saved {len(properties)} properties to {filepath}")

