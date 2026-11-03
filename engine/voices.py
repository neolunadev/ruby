"""Voice options: the Kokoro female catalogue, the tunable settings schema,
voice blending and presets.

Pure module: no torch, onnx or numpy at import time, so the app, the bot and
the hardware-free tests can all import it. The design and the reasoning for
every range and default live in docs/designs/voice-options.md.
"""

from collections import OrderedDict

# Every female voice pack in voices-v1.0.bin (the file app/setup_wizard.py
# downloads from kokoro-onnx's model-files-v1.0 release). The prefix encodes
# language and gender: a=American, b=British, e=Spanish, f=French, h=Hindi,
# i=Italian, j=Japanese, p=Brazilian Portuguese, z=Mandarin; f=female.
# "grade" is upstream Kokoro's own training-data quality grade (VOICES.md),
# a rough guide to how clean the pack sounds. Text is always phonemized as
# American English, so non-English packs speak English with their accent and
# character flavouring the result. "character" is a first impression to be
# confirmed by ear through the Miku model, not a measured property.
FEMALE_VOICES = OrderedDict(
    [
        ("af_heart", {"label": "Heart", "accent": "American", "grade": "A", "character": "warm, natural, the default"}),
        ("af_bella", {"label": "Bella", "accent": "American", "grade": "A-", "character": "bright, expressive, energetic"}),
        ("af_nicole", {"label": "Nicole", "accent": "American", "grade": "B-", "character": "soft, breathy, close-mic whisper"}),
        ("af_aoede", {"label": "Aoede", "accent": "American", "grade": "C+", "character": "smooth, even, slightly low"}),
        ("af_kore", {"label": "Kore", "accent": "American", "grade": "C+", "character": "clear, confident"}),
        ("af_sarah", {"label": "Sarah", "accent": "American", "grade": "C+", "character": "calm, mature, steady"}),
        ("af_nova", {"label": "Nova", "accent": "American", "grade": "C", "character": "crisp, assistant-like"}),
        ("af_alloy", {"label": "Alloy", "accent": "American", "grade": "C", "character": "neutral, flat"}),
        ("af_sky", {"label": "Sky", "accent": "American", "grade": "C-", "character": "light, airy, youthful"}),
        ("af_jessica", {"label": "Jessica", "accent": "American", "grade": "D", "character": "casual, uneven"}),
        ("af_river", {"label": "River", "accent": "American", "grade": "D", "character": "relaxed, uneven"}),
        ("bf_emma", {"label": "Emma", "accent": "British", "grade": "B-", "character": "polished, gentle"}),
        ("bf_isabella", {"label": "Isabella", "accent": "British", "grade": "C", "character": "warm, rounded"}),
        ("bf_alice", {"label": "Alice", "accent": "British", "grade": "D", "character": "clipped, formal"}),
        ("bf_lily", {"label": "Lily", "accent": "British", "grade": "D", "character": "soft, quiet"}),
        ("jf_alpha", {"label": "Alpha", "accent": "Japanese", "grade": "C+", "character": "clear, bright"}),
        ("jf_gongitsune", {"label": "Gongitsune", "accent": "Japanese", "grade": "C", "character": "storyteller, gentle"}),
        ("jf_nezumi", {"label": "Nezumi", "accent": "Japanese", "grade": "C-", "character": "storyteller, light"}),
        ("jf_tebukuro", {"label": "Tebukuro", "accent": "Japanese", "grade": "C", "character": "storyteller, soft"}),
        ("zf_xiaobei", {"label": "Xiaobei", "accent": "Mandarin", "grade": "D", "character": "not yet heard through Miku"}),
        ("zf_xiaoni", {"label": "Xiaoni", "accent": "Mandarin", "grade": "D", "character": "not yet heard through Miku"}),
        ("zf_xiaoxiao", {"label": "Xiaoxiao", "accent": "Mandarin", "grade": "D", "character": "not yet heard through Miku"}),
        ("zf_xiaoyi", {"label": "Xiaoyi", "accent": "Mandarin", "grade": "D", "character": "not yet heard through Miku"}),
        ("ef_dora", {"label": "Dora", "accent": "Spanish", "grade": "C", "character": "not yet heard through Miku"}),
        ("ff_siwis", {"label": "Siwis", "accent": "French", "grade": "B-", "character": "clear, soft"}),
        ("hf_alpha", {"label": "Alpha", "accent": "Hindi", "grade": "C", "character": "not yet heard through Miku"}),
        ("hf_beta", {"label": "Beta", "accent": "Hindi", "grade": "C", "character": "not yet heard through Miku"}),
        ("if_sara", {"label": "Sara", "accent": "Italian", "grade": "C", "character": "not yet heard through Miku"}),
        ("pf_dora", {"label": "Dora", "accent": "Brazilian Portuguese", "grade": "C", "character": "not yet heard through Miku"}),
    ]
)

# Tunable numeric settings: (min, max, step, default). The defaults are the
# values the pipeline shipped with before this module existed, so the
# default path is exactly as fast as before (one voice, no blend, no RMS mix).
SCHEMA = {
    "speed": {"min": 0.5, "max": 2.0, "step": 0.05, "default": 1.1},  # kokoro-onnx rejects outside 0.5..2.0
    "n_semitones": {"min": -12, "max": 12, "step": 1, "default": 10, "int": True},
    "blend": {"min": 0.0, "max": 1.0, "step": 0.05, "default": 0.0},
    "index_rate": {"min": 0.0, "max": 1.0, "step": 0.05, "default": 0.5},
    "protect_rate": {"min": 0.0, "max": 0.5, "step": 0.01, "default": 0.33},
    "rms_mix": {"min": 0.0, "max": 1.0, "step": 0.05, "default": 1.0},
}

DEFAULT_VOICE = "af_heart"

# The full set of fields a voice preset fixes. Speed is deliberately not one:
# it is the speaker's own pace and survives preset changes.
VOICE_DEFAULTS = {
    "engine": "kokoro",
    "voice": DEFAULT_VOICE,
    "blend_voice": None,
    "blend": SCHEMA["blend"]["default"],
    "n_semitones": SCHEMA["n_semitones"]["default"],
    "index_rate": SCHEMA["index_rate"]["default"],
    "protect_rate": SCHEMA["protect_rate"]["default"],
    "rms_mix": SCHEMA["rms_mix"]["default"],
}

# Every preset is Miku: they differ in the hidden base voice that feeds the
# Miku RVC model (prosody and accent) and the RVC knobs. None of them adds a
# slower code path except "Miku (steady)", whose RMS mix costs a few ms.
# Listed in UI order; the first one is the default.
_PRESET_DIFFS = OrderedDict(
    [
        ("Miku", {}),
        ("Miku (soft)", {"voice": "af_bella"}),
        ("Miku (bright)", {"voice": "af_heart", "blend_voice": "af_sky", "blend": 0.35, "n_semitones": 11}),
        ("Miku (gentle)", {"voice": "af_heart", "blend_voice": "af_nicole", "blend": 0.4, "protect_rate": 0.4}),
        ("Miku (calm)", {"voice": "af_sarah", "n_semitones": 9, "index_rate": 0.6}),
        ("Miku (British)", {"voice": "bf_emma"}),
        ("Miku (Japanese accent)", {"voice": "af_heart", "blend_voice": "jf_alpha", "blend": 0.5}),
        ("Miku (steady)", {"voice": "af_heart", "index_rate": 0.75, "rms_mix": 0.5}),
        ("Miku (cloud backup)", {"engine": "edge", "voice": "en-US-AnaNeural", "n_semitones": 2}),
        ("Miku (cloud backup 2)", {"engine": "edge", "voice": "en-US-JennyNeural", "n_semitones": 6}),
    ]
)
PRESETS = OrderedDict((name, {**VOICE_DEFAULTS, **diff}) for name, diff in _PRESET_DIFFS.items())
DEFAULT_PRESET = next(iter(PRESETS))


def clamp(key: str, value) -> float | int:
    """Coerce a slider value into its schema range (ints stay ints)."""
    spec = SCHEMA[key]
    v = float(value)
    if v != v:  # NaN
        v = spec["default"]
    v = min(spec["max"], max(spec["min"], v))
    return int(round(v)) if spec.get("int") else round(v, 4)


def is_female_voice(voice) -> bool:
    return voice in FEMALE_VOICES


def voice_fields(cfg: dict) -> dict:
    """The preset-controlled fields of a settings dict, validated and clamped.

    Unknown voices fall back to the default pack so a hand-edited config can
    never stop the engine from speaking.
    """
    out = {k: cfg.get(k, d) for k, d in VOICE_DEFAULTS.items()}
    if out["engine"] not in ("kokoro", "edge"):
        out["engine"] = "kokoro"
    if out["engine"] == "kokoro" and not is_female_voice(out["voice"]):
        out["voice"] = DEFAULT_VOICE
    if not is_female_voice(out["blend_voice"]):
        out["blend_voice"] = None
    for key in ("blend", "n_semitones", "index_rate", "protect_rate", "rms_mix"):
        out[key] = clamp(key, out[key])
    return out


def matching_preset(cfg: dict) -> str | None:
    """Name of the preset the current voice fields equal, or None (custom)."""
    current = voice_fields(cfg)
    for name, preset in PRESETS.items():
        if voice_fields(preset) == current:
            return name
    return None


def blend_weights(voice: str, blend_voice: str | None, blend: float) -> list[tuple[str, float]]:
    """The packs to mix and their weights, which always sum to 1.

    blend is the share of the second voice: 0 = only the first voice,
    1 = only the second. A single entry means no mixing is needed.
    """
    w = clamp("blend", blend)
    if not blend_voice or blend_voice == voice or w <= 0:
        return [(voice, 1.0)]
    if w >= 1:
        return [(blend_voice, 1.0)]
    return [(voice, round(1 - w, 4)), (blend_voice, w)]


class StyleCache:
    """Resolves (voice, blend_voice, blend) to what kokoro.create(voice=...) takes.

    A single pack resolves to its name, so the default path hands Kokoro the
    same string it always did. A blend resolves to a weighted sum of the
    packs' style arrays, computed once per distinct mix and kept, so moving
    the slider back and forth never recomputes a seen mix and nothing is
    ever reloaded from disk.
    """

    def __init__(self, get_style, max_entries: int = 32) -> None:
        self._get_style = get_style  # name -> ndarray, e.g. Kokoro.get_voice_style
        self._max = max_entries
        self._cache: OrderedDict = OrderedDict()

    def resolve(self, voice: str, blend_voice: str | None = None, blend: float = 0.0):
        parts = blend_weights(voice, blend_voice, blend)
        if len(parts) == 1:
            return parts[0][0]
        key = tuple(parts)
        hit = self._cache.get(key)
        if hit is not None:
            self._cache.move_to_end(key)
            return hit
        (a, wa), (b, wb) = parts
        style = self._get_style(a) * wa + self._get_style(b) * wb
        style = style.astype(self._get_style(a).dtype, copy=False)
        self._cache[key] = style
        if len(self._cache) > self._max:
            self._cache.popitem(last=False)
        return style

    def __len__(self) -> int:
        return len(self._cache)


def catalogue() -> list[dict]:
    """The female catalogue as plain dicts for the UI."""
    return [{"id": vid, **meta} for vid, meta in FEMALE_VOICES.items()]


def schema() -> dict:
    return {k: dict(v) for k, v in SCHEMA.items()}
