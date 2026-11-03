import json

from app import config


class TestLoad:
    def test_missing_file_returns_defaults(self, tmp_path):
        assert config.load(tmp_path / "nope.json") == config.DEFAULTS

    def test_corrupt_file_returns_defaults(self, tmp_path):
        p = tmp_path / "config.json"
        p.write_text("{not json")
        assert config.load(p) == config.DEFAULTS

    def test_merges_over_defaults_and_drops_unknown(self, tmp_path):
        p = tmp_path / "config.json"
        p.write_text(json.dumps({"hotkey": "f8", "junk": 1}))
        cfg = config.load(p)
        assert cfg["hotkey"] == "f8"
        assert "junk" not in cfg
        assert cfg["speed"] == config.DEFAULTS["speed"]


class TestSave:
    def test_roundtrip(self, tmp_path):
        p = tmp_path / "config.json"
        cfg = dict(config.DEFAULTS, hotkey="f9")
        config.save(p, cfg)
        assert config.load(p) == cfg


class TestVoiceOptions:
    def test_defaults_include_voice_fields(self):
        for key in ("voice", "blend_voice", "blend", "index_rate", "protect_rate", "rms_mix"):
            assert key in config.DEFAULTS

    def test_old_config_keeps_its_preset_voice(self, tmp_path):
        p = tmp_path / "config.json"
        p.write_text(json.dumps({"preset": "Miku (soft)", "n_semitones": 8, "speed": 1.3}))
        cfg = config.load(p)
        assert cfg["voice"] == "af_bella"
        assert cfg["n_semitones"] == 8
        assert cfg["speed"] == 1.3

    def test_old_cloud_config_keeps_edge_engine(self, tmp_path):
        p = tmp_path / "config.json"
        p.write_text(json.dumps({"preset": "Miku (cloud backup)"}))
        cfg = config.load(p)
        assert cfg["engine"] == "edge"
        assert cfg["voice"] == "en-US-AnaNeural"

    def test_new_config_is_not_overridden_by_preset(self, tmp_path):
        p = tmp_path / "config.json"
        p.write_text(json.dumps({"preset": "Miku (soft)", "voice": "bf_emma", "blend": 0.3}))
        cfg = config.load(p)
        assert cfg["voice"] == "bf_emma"
        assert cfg["blend"] == 0.3

    def test_non_object_json_returns_defaults(self, tmp_path):
        p = tmp_path / "config.json"
        p.write_text("[1, 2]")
        assert config.load(p) == config.DEFAULTS
