import pytest

import core


def test_valid_full_update():
    out = core._validate_cloud_updates({
        "provider": " deepseek ",
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "roles": ["executor", "executor", "planner"],
        "temperature": "0.5",
        "num_predict": "2048",
    })
    assert out["provider"] == "deepseek"
    assert out["temperature"] == 0.5
    assert out["num_predict"] == 2048
    assert out["roles"] == ["executor", "planner"]


def test_non_dict_raises():
    with pytest.raises(ValueError):
        core._validate_cloud_updates("not a dict")


def test_bad_role_raises():
    with pytest.raises(ValueError):
        core._validate_cloud_updates({"roles": ["executor", "hacker"]})


def test_temperature_range():
    with pytest.raises(ValueError):
        core._validate_cloud_updates({"temperature": 3.0})
    with pytest.raises(ValueError):
        core._validate_cloud_updates({"temperature": "abc"})


def test_num_predict_range():
    with pytest.raises(ValueError):
        core._validate_cloud_updates({"num_predict": 0})
    with pytest.raises(ValueError):
        core._validate_cloud_updates({"num_predict": "abc"})


def test_unknown_fields_ignored():
    out = core._validate_cloud_updates({"enabled": True, "model": "m"})
    assert "enabled" not in out
    assert out["model"] == "m"
