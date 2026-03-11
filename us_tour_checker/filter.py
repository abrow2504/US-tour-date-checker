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
    Falls back to checking for a state abbreviation in standard US address format
    (", NY" — comma-separated), which avoids false positives from European addresses
    that contain matching 2-letter sequences (e.g. "Milano MI, Italie" or French "de").

    Examples:
    - "New York, NY 10001" → True  (primary: state abbr + ZIP)
    - "Los Angeles, CA 90210" → True
    - "Nashville, TN" → True  (fallback: ", TN" comma-format)
    - "Viale dell'Innovazione, Milano MI, Italie" → False
    - "1 Pl. Saint-Nazaire, 11000 Carcassonne" → False

    Args:
        address_text (str): The full address string

    Returns:
        bool: True if the address is identified as a US location
    """
    # Primary: state abbreviation + ZIP code, e.g. "NY 10001" or "CA 90210-1234"
    us_zip_pattern = r'[,\s]([A-Z]{2})\s+\d{5}(?:-\d{4})?'
    if re.search(us_zip_pattern, address_text):
        return True

    # Fallback: state abbreviation in standard US address comma-format ", NY"
    # Requires a comma before the abbreviation to avoid matching abbreviations
    # embedded in European city/country names.
    states_map = get_us_states_map()
    for abbr in states_map['all_abbrs']:
        if re.search(rf',\s*{abbr}\b', address_text.upper()):
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
