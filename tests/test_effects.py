import numpy as np
import soundfile as sf

from engine import effects

SR = 24000


def _tone(seconds=0.5, amp=0.2):
    t = np.arange(int(SR * seconds)) / SR
    return (amp * np.sin(2 * np.pi * 220 * t)).astype(np.float32)


class TestBoost:
    def test_louder_and_within_ceiling(self):
        dry = _tone()
        wet = effects.boost(dry, SR)
        words = wet[: len(dry)]
        assert np.sqrt(np.mean(words**2)) > 1.5 * np.sqrt(np.mean(dry**2))
        assert np.max(np.abs(wet)) <= effects.BOOST_PEAK + 1e-6  # sounds clipped, never clips

    def test_keeps_an_echo_tail(self):
        dry = _tone()
        wet = effects.boost(dry, SR)
        assert len(wet) > len(dry) + SR // 4

    def test_mono_stays_mono_float32(self):
        wet = effects.boost(_tone(), SR)
        assert wet.ndim == 1
        assert wet.dtype == np.float32

    def test_stereo_stays_stereo(self):
        stereo = np.stack([_tone(), _tone()], axis=1)
        assert effects.boost(stereo, SR).shape[1] == 2

    def test_silence_does_not_crash(self):
        effects.boost(np.zeros(SR // 2, dtype=np.float32), SR)

    def test_boost_file_roundtrip(self, tmp_path):
        src, dst = tmp_path / "a.wav", tmp_path / "b.wav"
        sf.write(str(src), _tone(), SR)
        effects.boost_file(src, dst)
        data, sr = sf.read(str(dst), dtype="float32")
        assert sr == SR and len(data) > 0
