import re


def get_us_states_map():
    """
    Returns a mapping of US state abbreviations and full names for fallback matching.

    Returns:
        dict: Map of state abbreviations to full names, and full names to abbreviations
    """
    state_abbr_to_name = {
        'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
        'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
        'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
        'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
        'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
        'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
        'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
        'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
        'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
        'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
        'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
        'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
        'WI': 'Wisconsin', 'WY': 'Wyoming',
        'DC': 'District of Columbia',
    }

    state_name_to_abbr = {v.upper(): k for k, v in state_abbr_to_name.items()}

    return {
        'abbr_to_name': state_abbr_to_name,
        'name_to_abbr': state_name_to_abbr,
        'all_abbrs': set(state_abbr_to_name.keys()),
        'all_names': set(state_abbr_to_name.values()),
    }


def is_us_location_by_postal_code(address_text):
    """
    Detect if an address is in the US by looking for the US postal code format:
    State abbreviation (2 capital letters) followed by 5-digit ZIP code.
    Falls back to checking for US state names/abbreviations if no postal code found.

    Examples:
    - "New York, NY 10001" → True
    - "Los Angeles, CA 90210" → True
    - "New York, NY" → True (fallback: state abbreviation)
    - "1 Pl. Saint-Nazaire, 11000 Carcassonne" → False (European address)

    Args:
        address_text (str): The full address string

    Returns:
        bool: True if the address is identified as a US location
    """
    # Primary: state abbreviation + ZIP code pattern, e.g. "NY 10001" or "CA 90210-1234"
    us_pattern = r'[,\s]([A-Z]{2})\s+\d{5}(?:-\d{4})?'
    match = re.search(us_pattern, address_text)
    if match:
        return True

    # Fallback: check for state abbreviations or full state names
    states_map = get_us_states_map()
    address_upper = address_text.upper()

    for abbr in states_map['all_abbrs']:
        if re.search(rf'\b{abbr}\b', address_upper):
            return True

    for name in states_map['all_names']:
        if re.search(rf'\b{name.upper()}\b', address_upper):
            return True

    return False


def apply_filtering(events, filtering_config):
    """
    Filter a list of events according to the filtering configuration.

    Args:
        events (list): List of event dicts
        filtering_config (dict): The 'filtering' section from config

    Returns:
        list: Filtered list of events
    """
    if not filtering_config.get('enabled', False):
        return events

    filter_type = filtering_config.get('type', '')

    if filter_type == 'us_only':
        filtered = [e for e in events if is_us_location_by_postal_code(e.get('address', ''))]
        return filtered

    # Unknown filter type — return all events unchanged
    return events
