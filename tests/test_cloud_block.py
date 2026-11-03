import pytest
import yaml

import core

SAMPLE = """general:
  planner:
    model: qwen2.5:7b
search:
  api_key: ""
cloud:
  enabled: false
  api_key: ""
  roles: [planner]
memory:
  topk: 4
"""


def test_replace_only_cloud():
    new_cloud = {
        "enabled": False, "provider": "deepseek",
        "base_url": "https://x", "api_key": "k",
        "model": "m", "roles": ["executor"],
        "temperature": 0.3, "num_predict": 1024,
    }
    out = core._replace_cloud_block(SAMPLE, new_cloud)
    parsed = yaml.safe_load(out)
    assert parsed["cloud"]["roles"] == ["executor"]
    assert parsed["cloud"]["api_key"] == "k"
    assert parsed["general"]["planner"]["model"] == "qwen2.5:7b"
    assert parsed["memory"]["topk"] == 4
    assert parsed["search"]["api_key"] == ""


def test_missing_cloud_raises():
    with pytest.raises(ValueError):
        core._replace_cloud_block("general:\n  a: 1\n", {})
