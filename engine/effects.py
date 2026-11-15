"""Post-synthesis audio effects. Boost: the one-phrase meme mode.

Boost makes a finished line sound like a blown-out mic without actually
being painfully loud: pitched down a touch, bass boosted, saturated so it
crunches like a clipping mic, then a long echo and a big reverb. The output
is levelled to a fixed loudness and its peaks never reach full scale, so the
crunch is the effect's, not the listener's speakers'. It runs on the
converted wav, so the voice itself is untouched and no model work repeats.
pedalboard (Spotify) supplies the effects; it imports lazily so the module
stays importable without it.
"""

from pathlib import Path

# Seconds of silence appended so the echo and reverb tails ring out instead
# of being cut off at the end of the words.
BOOST_TAIL_S = 1.6
# Semitones the boosted line drops (a small shift; the voice stays recognisable).
BOOST_PITCH = -1.0
# Loudness of the words after boosting (RMS, full scale = 1.0). A typical
# plain line sits near 0.15, so this is roughly +6 dB.
BOOST_RMS = 0.3
# Output peaks stay below this: it sounds clipped but never really clips.
BOOST_PEAK = 0.85


def _boost_board():
    from pedalboard import (
        Clipping,
        Delay,
        Distortion,
        Gain,
        LowShelfFilter,
        Pedalboard,
        PitchShift,
        Reverb,
    )

    return Pedalboard([
        PitchShift(semitones=BOOST_PITCH),
        LowShelfFilter(cutoff_frequency_hz=160, gain_db=9.0, q=0.7),  # bass boost
        Distortion(drive_db=22.0),  # tanh saturation: the clipping-mic crunch
        Clipping(threshold_db=-4.0),  # a little hard edge on top
        Gain(gain_db=-12.0),  # back down before the echo and room
        Delay(delay_seconds=0.22, feedback=0.4, mix=0.3),  # echo
        Reverb(room_size=0.88, damping=0.35, wet_level=0.42, dry_level=0.8, width=1.0),
    ])


def boost(data, sr: int):
    """Return the boosted copy of mono or multichannel float32 audio."""
    import numpy as np

    audio = np.asarray(data, dtype=np.float32)
    mono = audio.ndim == 1
    if mono:
        audio = audio[:, None]
    voiced = len(audio)
    tail = np.zeros((int(BOOST_TAIL_S * sr), audio.shape[1]), dtype=np.float32)
    audio = np.concatenate([audio, tail])
    # pedalboard takes (channels, samples)
    out = _boost_board()(audio.T.copy(), sr).T
    # Level the words (not the tail) to BOOST_RMS, then keep peaks under BOOST_PEAK.
    rms = float(np.sqrt(np.mean(out[:voiced] ** 2)))
    if rms > 1e-6:
        out = out * (BOOST_RMS / rms)
    peak = float(np.max(np.abs(out)))
    if peak > BOOST_PEAK:
        out = out * (BOOST_PEAK / peak)
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
