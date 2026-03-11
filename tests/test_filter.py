import pytest
from us_tour_checker.filter import is_us_location_by_postal_code, apply_filtering


# --- is_us_location_by_postal_code ---

@pytest.mark.parametrize("address", [
    "New York, NY 10001",           # state abbr + ZIP
    "Los Angeles, CA 90210",        # state abbr + ZIP
    "Los Angeles, CA 90210-1234",   # state abbr + ZIP+4
    "Nashville, TN",                # comma-format fallback
    "Austin, TX",                   # comma-format fallback
    "Chicago, IL 60601",            # state abbr + ZIP
    "Washington, DC 20001",         # DC included
])
def test_is_us_location_returns_true_for_us_addresses(address):
    assert is_us_location_by_postal_code(address) is True


@pytest.mark.parametrize("address", [
    "Viale dell'Innovazione, 2022, 20126 Milano MI, Italie",  # Italian MI province
    "Rue de l'Enseignement 81, 1000 Bruxelles, Belgique",     # French "de"
    "1 Pl. Saint-Nazaire, 11000 Carcassonne",                 # French ZIP only
    "Tempodrom, Berlin",                                       # German city
    "Zénith de Paris, Paris",                                  # French city
    "Reims, France",                                           # French city
    "Zürich, Schweiz",                                         # Swiss city
])
def test_is_us_location_returns_false_for_non_us_addresses(address):
    assert is_us_location_by_postal_code(address) is False


# --- apply_filtering ---

EVENTS = [
    {"date": "2026-05-01", "city": "Nashville", "venue": "Ryman", "address": "Nashville, TN 37201", "link": ""},
    {"date": "2026-05-10", "city": "Berlin", "venue": "Tempodrom", "address": "Tempodrom, Berlin", "link": ""},
    {"date": "2026-05-15", "city": "Chicago", "venue": "United Center", "address": "Chicago, IL 60612", "link": ""},
    {"date": "2026-06-01", "city": "Paris", "venue": "Zénith", "address": "Zénith de Paris, Paris", "link": ""},
]


def test_apply_filtering_us_only_returns_only_us_events():
    config = {"enabled": True, "type": "us_only"}
    result = apply_filtering(EVENTS, config)
    cities = [e["city"] for e in result]
    assert "Nashville" in cities
    assert "Chicago" in cities
    assert "Berlin" not in cities
    assert "Paris" not in cities


def test_apply_filtering_disabled_returns_all_events():
    config = {"enabled": False, "type": "us_only"}
    result = apply_filtering(EVENTS, config)
    assert result == EVENTS


def test_apply_filtering_empty_config_returns_all_events():
    result = apply_filtering(EVENTS, {})
    assert result == EVENTS


def test_apply_filtering_unknown_type_returns_all_events():
    config = {"enabled": True, "type": "eu_only"}
    result = apply_filtering(EVENTS, config)
    assert result == EVENTS
