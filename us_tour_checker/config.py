import os
import json

def load_config(config_path='config.json'):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file '{config_path}' not found!")
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
