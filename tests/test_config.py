import json
import pytest

from us_tour_checker.config import load_config


def test_load_config_reads_json(tmp_path):
    config_data = {
        "site": {"name": "Example", "url": "https://example.com"},
        "notifications": {"email": {"subject_prefix": "Heads up", "subject_suffix": "Dates"}}
    }
    config_path = tmp_path / "custom_config.json"
    config_path.write_text(json.dumps(config_data), encoding="utf-8")

    loaded = load_config(str(config_path))

    assert loaded == config_data


def test_load_config_missing_file(tmp_path):
    missing_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_config(str(missing_path))
