from app.bridge import parse_id_list


class TestParseIdList:
    def test_keeps_digit_entries_only(self):
        assert parse_id_list("123, 456x, 789 ,") == ["123", "789"]

    def test_empty_string(self):
        assert parse_id_list("") == []


import pytest  # noqa: E402

from app import config  # noqa: E402
from app.bridge import JsApi  # noqa: E402
from engine import pipeline  # noqa: E402


class FakeLoop:
    def __init__(self):
        self.submitted = []

    def submit(self, coro):
        self.submitted.append(coro)
        coro.close()


class FakePlayer:
    device = None
    monitor_device = None


@pytest.fixture
def api():
    saved = dict(pipeline.SETTINGS)
    saves = []
    cfg = dict(config.DEFAULTS)
    a = JsApi(FakeLoop(), FakePlayer(), cfg, lambda c: saves.append(dict(c)))
    a.saves = saves
    yield a
    pipeline.SETTINGS.clear()
    pipeline.SETTINGS.update(saved)


class TestVoiceSettings:
    def test_slider_updates_engine_and_saves(self, api):
        assert api.set_setting("index_rate", 0.7) == {"ok": True}
        assert pipeline.SETTINGS["index_rate"] == 0.7
        assert api.saves[-1]["index_rate"] == 0.7

    def test_slider_is_clamped(self, api):
        api.set_setting("protect_rate", 3)
        assert pipeline.SETTINGS["protect_rate"] == 0.5
        assert api._cfg["protect_rate"] == 0.5

    def test_slider_rejects_text(self, api):
        assert api.set_setting("rms_mix", "loud")["ok"] is False

    def test_voice_picker_switches_to_local_engine(self, api):
        api.set_setting("preset", "Miku (cloud backup)")
        assert api.set_setting("voice", "bf_emma") == {"ok": True}
        assert pipeline.SETTINGS["engine"] == "kokoro"
        assert api._cfg["engine"] == "kokoro"
        assert api._cfg["voice"] == "bf_emma"

    def test_unknown_or_male_voice_rejected(self, api):
        assert api.set_setting("voice", "am_adam")["ok"] is False
        assert api.set_setting("blend_voice", "am_adam")["ok"] is False

    def test_blend_voice_clears(self, api):
        api.set_setting("blend_voice", "af_sky")
        assert pipeline.SETTINGS["blend_voice"] == "af_sky"
        api.set_setting("blend_voice", "")
        assert pipeline.SETTINGS["blend_voice"] is None
        assert api._cfg["blend_voice"] is None

    def test_preset_writes_all_voice_fields(self, api):
        api.set_setting("speed", 1.4)
        api.set_setting("preset", "Miku (bright)")
        assert api._cfg["blend_voice"] == "af_sky"
        assert api._cfg["n_semitones"] == 11
        assert api._cfg["speed"] == 1.4  # presets keep the user's pace
        assert pipeline.SETTINGS["blend"] == 0.35

    def test_state_reports_custom_after_slider(self, api):
        api._version = lambda: "test"
        assert api.get_state()["preset_match"] == "Miku"
        api.set_setting("index_rate", 0.9)
        state = api.get_state()
        assert state["preset_match"] is None
        assert len(state["voices"]) == 29
        assert state["schema"]["blend"]["max"] == 1.0

    def test_preview_runs_once_at_a_time(self, api):
        assert api.preview() == {"ok": True}
        assert api.preview()["ok"] is False
        assert len(api._loop.submitted) == 1
