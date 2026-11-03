import numpy as np
import pytest

from app import config
from engine import pipeline, voices


class TestCatalogue:
    def test_every_entry_is_a_female_pack(self):
        assert voices.FEMALE_VOICES
        for vid, meta in voices.FEMALE_VOICES.items():
            assert vid[1] == "f", vid
            assert meta["accent"] and meta["label"] and meta["grade"] and meta["character"]

    def test_covers_all_29_female_packs_of_voices_v1_0(self):
        # Listed from voices-v1.0.bin (kokoro-onnx model-files-v1.0).
        assert len(voices.FEMALE_VOICES) == 29
        assert sum(v.startswith("af_") for v in voices.FEMALE_VOICES) == 11
        assert sum(v.startswith("bf_") for v in voices.FEMALE_VOICES) == 4
        assert sum(v.startswith("jf_") for v in voices.FEMALE_VOICES) == 4

    def test_default_voice_is_first_and_in_catalogue(self):
        assert next(iter(voices.FEMALE_VOICES)) == voices.DEFAULT_VOICE == "af_heart"

    def test_catalogue_for_ui(self):
        items = voices.catalogue()
        assert items[0]["id"] == "af_heart"
        assert {"id", "label", "accent", "grade", "character"} <= set(items[0])


class TestSchema:
    @pytest.mark.parametrize("key", list(voices.SCHEMA))
    def test_default_inside_range(self, key):
        spec = voices.SCHEMA[key]
        assert spec["min"] <= spec["default"] <= spec["max"]
        assert spec["step"] > 0

    def test_defaults_keep_todays_fast_path(self):
        # Same numbers the pipeline shipped with before voice options.
        d = voices.VOICE_DEFAULTS
        assert d == {
            "engine": "kokoro",
            "voice": "af_heart",
            "blend_voice": None,
            "blend": 0.0,
            "n_semitones": 10,
            "index_rate": 0.5,
            "protect_rate": 0.33,
            "rms_mix": 1.0,  # 1.0 skips RVC's RMS pass entirely
        }
        assert voices.SCHEMA["speed"]["default"] == 1.1

    def test_speed_range_matches_kokoro_limits(self):
        assert voices.SCHEMA["speed"]["min"] == 0.5
        assert voices.SCHEMA["speed"]["max"] == 2.0

    def test_pipeline_and_config_share_the_defaults(self):
        for k, v in voices.VOICE_DEFAULTS.items():
            assert config.DEFAULTS[k] == v
        assert config.DEFAULTS["speed"] == voices.SCHEMA["speed"]["default"]
        assert config.DEFAULTS["preset"] == voices.DEFAULT_PRESET == "Miku"

    def test_clamp(self):
        assert voices.clamp("index_rate", 2) == 1.0
        assert voices.clamp("index_rate", -1) == 0.0
        assert voices.clamp("protect_rate", 0.9) == 0.5
        assert voices.clamp("speed", 3) == 2.0
        assert voices.clamp("n_semitones", 30) == 12
        assert voices.clamp("n_semitones", "4.6") == 5
        assert isinstance(voices.clamp("n_semitones", 4.0), int)
        assert voices.clamp("blend", float("nan")) == 0.0

    def test_clamp_rejects_non_numbers(self):
        with pytest.raises(ValueError):
            voices.clamp("blend", "loud")


class TestVoiceFields:
    def test_unknown_voice_falls_back(self):
        f = voices.voice_fields({"voice": "am_adam", "blend_voice": "zz_nope"})
        assert f["voice"] == "af_heart"
        assert f["blend_voice"] is None

    def test_edge_voice_kept_for_edge_engine(self):
        f = voices.voice_fields({"engine": "edge", "voice": "en-US-AnaNeural"})
        assert f["voice"] == "en-US-AnaNeural"

    def test_values_clamped(self):
        f = voices.voice_fields({"index_rate": 5, "rms_mix": -2, "blend": 3})
        assert (f["index_rate"], f["rms_mix"], f["blend"]) == (1.0, 0.0, 1.0)


class TestBlendWeights:
    def test_zero_blend_is_single_voice(self):
        assert voices.blend_weights("af_heart", "af_sky", 0) == [("af_heart", 1.0)]

    def test_no_second_voice_is_single_voice(self):
        assert voices.blend_weights("af_heart", None, 0.5) == [("af_heart", 1.0)]

    def test_same_voice_twice_is_single_voice(self):
        assert voices.blend_weights("af_heart", "af_heart", 0.5) == [("af_heart", 1.0)]

    def test_full_blend_is_second_voice(self):
        assert voices.blend_weights("af_heart", "af_sky", 1.0) == [("af_sky", 1.0)]

    @pytest.mark.parametrize("w", [0.05, 0.25, 0.35, 0.5, 0.95])
    def test_weights_sum_to_one(self, w):
        parts = voices.blend_weights("af_heart", "af_sky", w)
        assert [p[0] for p in parts] == ["af_heart", "af_sky"]
        assert sum(p[1] for p in parts) == pytest.approx(1.0)
        assert parts[1][1] == pytest.approx(w)


class FakePacks:
    def __init__(self):
        self.calls = 0
        rng = np.random.default_rng(0)
        self.packs = {v: rng.standard_normal((510, 1, 256)).astype(np.float32) for v in ("af_heart", "af_sky", "jf_alpha")}

    def get(self, name):
        self.calls += 1
        return self.packs[name]


class TestStyleCache:
    def test_single_voice_resolves_to_name(self):
        packs = FakePacks()
        cache = voices.StyleCache(packs.get)
        assert cache.resolve("af_heart") == "af_heart"
        assert cache.resolve("af_heart", "af_sky", 0.0) == "af_heart"
        assert packs.calls == 0
        assert len(cache) == 0

    def test_blend_is_weighted_mix(self):
        packs = FakePacks()
        cache = voices.StyleCache(packs.get)
        style = cache.resolve("af_heart", "af_sky", 0.25)
        expected = packs.packs["af_heart"] * 0.75 + packs.packs["af_sky"] * 0.25
        assert style.shape == (510, 1, 256)
        assert style.dtype == np.float32
        np.testing.assert_allclose(style, expected, rtol=1e-6)

    def test_half_blend_is_midpoint(self):
        packs = FakePacks()
        style = voices.StyleCache(packs.get).resolve("af_heart", "jf_alpha", 0.5)
        np.testing.assert_allclose(style, (packs.packs["af_heart"] + packs.packs["jf_alpha"]) / 2, rtol=1e-6)

    def test_repeat_mix_is_cached(self):
        packs = FakePacks()
        cache = voices.StyleCache(packs.get)
        a = cache.resolve("af_heart", "af_sky", 0.4)
        calls = packs.calls
        b = cache.resolve("af_heart", "af_sky", 0.4)
        assert a is b
        assert packs.calls == calls

    def test_cache_is_bounded(self):
        packs = FakePacks()
        cache = voices.StyleCache(packs.get, max_entries=3)
        for w in (0.1, 0.2, 0.3, 0.4, 0.5):
            cache.resolve("af_heart", "af_sky", w)
        assert len(cache) == 3


class TestPresets:
    def test_first_preset_is_the_untouched_default(self):
        assert voices.PRESETS["Miku"] == voices.VOICE_DEFAULTS

    def test_all_presets_miku_labelled_and_valid(self):
        for name, p in voices.PRESETS.items():
            assert name.startswith("Miku")
            assert set(p) == set(voices.VOICE_DEFAULTS)
            assert voices.voice_fields(p) == p, name  # in range, known voices
            if p["engine"] == "kokoro":
                assert voices.is_female_voice(p["voice"])

    def test_presets_do_not_set_speed(self):
        assert all("speed" not in p for p in voices.PRESETS.values())

    def test_presets_are_distinct(self):
        seen = [tuple(sorted(p.items(), key=lambda kv: kv[0])) for p in voices.PRESETS.values()]
        assert len(set(seen)) == len(seen)

    def test_matching_preset(self):
        assert voices.matching_preset(dict(voices.PRESETS["Miku (bright)"])) == "Miku (bright)"
        assert voices.matching_preset({**voices.VOICE_DEFAULTS, "index_rate": 0.9}) is None

    def test_legacy_presets_keep_their_voice(self):
        assert voices.PRESETS["Miku (soft)"]["voice"] == "af_bella"
        assert voices.PRESETS["Miku (cloud backup)"]["engine"] == "edge"


class TestPipelineVoice:
    @pytest.fixture(autouse=True)
    def restore(self, monkeypatch):
        saved = dict(pipeline.SETTINGS)
        monkeypatch.setattr(pipeline, "_styles", None)
        yield
        pipeline.SETTINGS.clear()
        pipeline.SETTINGS.update(saved)

    def test_default_path_passes_the_pack_name(self, monkeypatch):
        packs = FakePacks()

        class FakeKokoro:
            get_voice_style = staticmethod(packs.get)

        monkeypatch.setattr(pipeline, "_get_kokoro", lambda: FakeKokoro())
        pipeline.apply_config(dict(config.DEFAULTS))
        assert pipeline._kokoro_voice() == "af_heart"

    def test_blend_passes_an_array(self, monkeypatch):
        packs = FakePacks()

        class FakeKokoro:
            get_voice_style = staticmethod(packs.get)

        monkeypatch.setattr(pipeline, "_get_kokoro", lambda: FakeKokoro())
        pipeline.SETTINGS.update(voice="af_heart", blend_voice="af_sky", blend=0.5)
        style = pipeline._kokoro_voice()
        assert isinstance(style, np.ndarray)

    def test_convert_passes_rvc_knobs(self, monkeypatch, tmp_path):
        seen = {}

        class FakeConverter:
            def convert_audio(self, **kw):
                seen.update(kw)

        monkeypatch.setattr(pipeline, "_get_converter", lambda: FakeConverter())
        monkeypatch.setattr(pipeline, "_get_rvc_files", lambda name: (tmp_path / "m.pth", None))
        pipeline.SETTINGS.update(n_semitones=11, index_rate=0.7, protect_rate=0.4, rms_mix=0.5)
        pipeline._convert_blocking(tmp_path / "in.wav", tmp_path / "out.wav")
        assert seen["pitch"] == 11
        assert seen["index_rate"] == 0.7
        assert seen["protect"] == 0.4
        assert seen["volume_envelope"] == 0.5
        assert seen["f0_method"] == "rmvpe"

    def test_apply_config_clamps_and_validates(self):
        pipeline.apply_config({**config.DEFAULTS, "speed": 9, "voice": "nope", "index_rate": 0.8})
        assert pipeline.SETTINGS["speed"] == 2.0
        assert pipeline.SETTINGS["voice"] == "af_heart"
        assert pipeline.SETTINGS["index_rate"] == 0.8
