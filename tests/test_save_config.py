import shutil

import pytest
import yaml

import core


def _setup(tmp_path):
    cfg_path = tmp_path / "models.yaml"
    shutil.copy(core.BASE_DIR / "models.yaml.example", cfg_path)
    isolated_cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    return cfg_path, isolated_cfg


def test_save_writes_and_backs_up(tmp_path, monkeypatch):
    cfg_path, isolated_cfg = _setup(tmp_path)
    monkeypatch.setattr(core, "BASE_DIR", tmp_path)
    monkeypatch.setattr(core, "cfg", isolated_cfg)
    status = core.save_cloud_config({
        "model": "new-model",
        "roles": ["executor"],
        "temperature": 0.8,
        "num_predict": 512,
    })
    assert status["model"] == "new-model"
    assert (tmp_path / "models.yaml.bak").exists()
    parsed = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert parsed["cloud"]["model"] == "new-model"
    assert parsed["cloud"]["roles"] == ["executor"]
    assert parsed["general"]["planner"]["model"] == "qwen2.5:7b"


def test_save_invalid_keeps_original(tmp_path, monkeypatch):
    cfg_path, isolated_cfg = _setup(tmp_path)
    monkeypatch.setattr(core, "BASE_DIR", tmp_path)
    monkeypatch.setattr(core, "cfg", isolated_cfg)
    before = cfg_path.read_text(encoding="utf-8")
    with pytest.raises(ValueError):
        core.save_cloud_config({"temperature": 9})
    assert cfg_path.read_text(encoding="utf-8") == before
