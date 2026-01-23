import os
import json
from datetime import datetime

def load_seen_dates(state_file='seen_dates.json'):
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            data = json.load(f)
            return data.get('dates', [])
    return []

def save_seen_dates(dates, state_file='seen_dates.json'):
    with open(state_file, 'w') as f:
        json.dump({'dates': dates, 'last_updated': datetime.now().isoformat()}, f)

def save_all_events(events, state_file='seen_dates.json'):
    data = {}
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            data = json.load(f)
    data['all_events'] = events
    data['last_scan'] = datetime.now().isoformat()
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
