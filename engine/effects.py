"""Post-synthesis audio effects. Boost: the one-phrase meme mode.

Boost turns a finished line into a blown-out mic: bass boost, heavy gain into
a hard clip (the sound of a mic clipping), then a long echo and a big reverb.
It runs on the converted wav, so the voice itself is untouched and no model
work repeats. pedalboard (Spotify) supplies the effects; it imports lazily so
the module stays importable without it.
"""

from pathlib import Path

# Seconds of silence appended so the echo and reverb tails ring out instead
# of being cut off at the end of the words.
BOOST_TAIL_S = 1.6
# Final peak level. Everything is driven into this ceiling on purpose.
BOOST_CEILING = 0.99
# How far past the ceiling the normalised mix is pushed before the final clip.
BOOST_DRIVE = 2.2


def _boost_board():
    from pedalboard import (
        Clipping,
        Delay,
        Gain,
        LowShelfFilter,
        Pedalboard,
        Reverb,
    )

    return Pedalboard([
        LowShelfFilter(cutoff_frequency_hz=180, gain_db=12.0, q=0.7),  # bass boost
        Gain(gain_db=24.0),  # drive it hot
        Clipping(threshold_db=-6.0),  # hard digital clip: the blown-mic crunch
        Delay(delay_seconds=0.22, feedback=0.45, mix=0.35),  # echo
        Reverb(room_size=0.9, damping=0.3, wet_level=0.5, dry_level=0.8, width=1.0),
    ])


def boost(data, sr: int):
    """Return the boosted copy of mono or multichannel float32 audio."""
    import numpy as np

    audio = np.asarray(data, dtype=np.float32)
    mono = audio.ndim == 1
    if mono:
        audio = audio[:, None]
    tail = np.zeros((int(BOOST_TAIL_S * sr), audio.shape[1]), dtype=np.float32)
    audio = np.concatenate([audio, tail])
    # pedalboard takes (channels, samples)
    out = _boost_board()(audio.T.copy(), sr).T
    peak = float(np.max(np.abs(out))) or 1.0
    # Normalise, then overdrive past the ceiling so the whole line sits clipped.
    out = np.clip(out * (BOOST_CEILING / peak) * BOOST_DRIVE, -BOOST_CEILING, BOOST_CEILING)
    # Trim trailing near-silence left over from the tail.
    loud = np.nonzero(np.max(np.abs(out), axis=1) > 1e-3)[0]
    if loud.size:
        out = out[: loud[-1] + 1]
    out = out.astype(np.float32)
    return out[:, 0] if mono else out


def boost_file(src: Path, dst: Path) -> Path:
    """Write the boosted version of a wav file to dst."""
    import soundfile as sf

    data, sr = sf.read(str(src), dtype="float32")
    sf.write(str(dst), boost(data, sr), sr)
    return dst
