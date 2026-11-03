"""Per-user app settings persisted to config.json (gitignored)."""

import json
import logging
from pathlib import Path

from engine import voices

log = logging.getLogger(__name__)

DEFAULTS = {
    "hotkey": "ctrl+shift+m",
    "device": None,          # output device NAME (indices shift); None = system default
    "monitor_device": None,  # second sink to hear yourself; NAME or None = off
    "preset": voices.DEFAULT_PRESET,  # last preset picked; the fields below are the truth
    "speed": voices.SCHEMA["speed"]["default"],
    **voices.VOICE_DEFAULTS,  # engine, voice, blend_voice, blend, n_semitones, RVC knobs
    "mode": "mic",              # mic = virtual-mic sink, bot = server voice channel
    "allowed_dm_users": [],     # Discord user IDs allowed to speak via DM / user-app /say
    "say_posts_text": True,     # /say also posts the text visibly into the conversation
    "accept_discord_input": True,  # master switch for /say and DM input
    "start_with_windows": False,
    "quick_phrases": ["yes", "no", "one sec", "brb", "haha", "thanks"],
}


def load(path: Path) -> dict:
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return dict(DEFAULTS)
    if not isinstance(raw, dict):
        return dict(DEFAULTS)
    cfg = {k: raw.get(k, v) for k, v in DEFAULTS.items()}
    if "voice" not in raw and raw.get("preset") in voices.PRESETS:
        # Configs from before the voice options stored only the preset name
        # and a transpose; rebuild the voice fields from that preset so an
        # upgrade keeps the voice the user picked.
        cfg.update(voices.PRESETS[raw["preset"]])
        if "n_semitones" in raw:
            cfg["n_semitones"] = raw["n_semitones"]
    return cfg


def save(path: Path, cfg: dict) -> None:
    Path(path).write_text(json.dumps(cfg, indent=2), encoding="utf-8")
