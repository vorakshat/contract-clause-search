import pytest

from clausesearch.config import DEFAULTS, config_hash, diff_configs, load_config, set_path


def test_baseline_config_loads_over_defaults():
    cfg = load_config("configs/baseline.yaml")
    assert cfg["name"] == "baseline" and cfg["chunking"]["chunk_size"] == 500
    assert cfg["eval"]["ks"] == DEFAULTS["eval"]["ks"]


def test_overrides_are_parsed_as_yaml():
    cfg = load_config("configs/baseline.yaml", ["chunking.chunk_size=300", "rerank.enabled=true"])
    assert cfg["chunking"]["chunk_size"] == 300 and cfg["rerank"]["enabled"] is True


def test_unknown_keys_and_bad_values_are_rejected(tmp_path):
    with pytest.raises(KeyError):
        load_config("configs/baseline.yaml", ["chunking.chunksize=300"])
    with pytest.raises(ValueError):
        load_config("configs/baseline.yaml", ["retrieval.method=magic"])
    with pytest.raises(ValueError):
        load_config("configs/baseline.yaml", ["chunking.overlap=500"])


def test_hash_and_diff():
    base = load_config("configs/baseline.yaml")
    changed = set_path(base, "chunking.overlap", 100)
    assert config_hash(base) != config_hash(changed)
    assert config_hash(base, ["retrieval"]) == config_hash(changed, ["retrieval"])
    assert diff_configs(base, changed) == {"chunking.overlap": (0, 100)}
