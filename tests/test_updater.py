import pytest

from app import updater


class TestVersions:
    @pytest.mark.parametrize("remote,local,newer", [
        ("v0.7.0", "0.6.0", True),
        ("v0.5.0", "0.6.0", False),  # an older "latest" release never downgrades
        ("v0.6.0", "0.6.0", False),
        ("v0.10.0", "0.9.3", True),
        ("v1.0.0", "dev", True),
        ("garbage", "0.6.0", False),
    ])
    def test_is_newer(self, remote, local, newer):
        assert updater.is_newer(remote, local) is newer

    def test_tag_zip_url_points_at_the_tag(self):
        assert updater.tag_zip_url("v0.7.0").endswith("/zip/refs/tags/v0.7.0")


class TestCheck:
    def test_reports_latest_release(self, monkeypatch):
        monkeypatch.setattr(updater, "latest_release", lambda: "v9.0.0")
        info = updater.check()
        assert info["behind"] == 1 and info["latest"] == "v9.0.0"

    def test_apply_skips_when_not_newer(self, monkeypatch):
        monkeypatch.setattr(updater, "latest_release", lambda: "v0.0.1")
        monkeypatch.setattr(updater, "_apply_zip_overlay", lambda tag: pytest.fail("overlaid"))
        monkeypatch.setattr(updater, "_git", lambda *a, **k: pytest.fail("git ran"))
        updater.apply()


class TestRequirements:
    def test_names_strip_extras_pins_and_comments(self):
        text = "# header\ndiscord.py[voice]\ntorch==2.7.1\nlibrosa   # comment\n\n-r other.txt\n"
        assert updater.requirement_names(text) == ["discord.py", "torch", "librosa"]

    def test_missing_only_lists_uninstalled(self):
        assert updater.missing_requirements("pytest\nsurely-not-installed-pkg-xyz\n") == [
            "surely-not-installed-pkg-xyz"
        ]
