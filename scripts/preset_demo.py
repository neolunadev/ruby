"""Render a line in each voice preset so you can listen and compare.

Usage:
  python scripts/preset_demo.py                     every preset, default line
  python scripts/preset_demo.py --preset "Miku (bright)"
  python scripts/preset_demo.py --preset "Miku (calm)" "your own line"
  python scripts/preset_demo.py --list

Each wav is copied to audio/presets/<preset>.wav (gitignored) and the
Kokoro and RVC timings are printed, so a preset that is slower than the
default shows up here. The first synthesis absorbs the model loads and is
not timed.
"""

import argparse
import asyncio
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engine import pipeline  # noqa: E402

DEFAULT_LINE = "Hey, it's me! Can you hear me okay? Let's start the next round."


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


async def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("text", nargs="?", default=DEFAULT_LINE)
    ap.add_argument("--preset", action="append", help="preset name (repeatable); default: all")
    ap.add_argument("--list", action="store_true", help="print the preset names and exit")
    args = ap.parse_args()

    if args.list:
        for name, p in pipeline.VOICE_PRESETS.items():
            print(f"{name:26} {p}")
        return
    names = args.preset or list(pipeline.VOICE_PRESETS)
    unknown = [n for n in names if n not in pipeline.VOICE_PRESETS]
    if unknown:
        sys.exit(f"Unknown preset(s): {unknown}. Try --list.")
    if not pipeline.model_available():
        sys.exit(f"No Miku model in {pipeline.MIKU_DIR}")

    out_dir = pipeline.AUDIO_DIR / "presets"
    out_dir.mkdir(parents=True, exist_ok=True)
    print("Warming up (model loads, not timed)...")
    await pipeline.warmup()

    for name in names:
        pipeline.apply_voice_preset(name)
        wav = await pipeline.synthesize(args.text)
        dest = out_dir / f"{_slug(name)}.wav"
        shutil.copyfile(wav, dest)
        t = pipeline.LAST_TIMING
        print(f"{name:26} tts {t['tts_ms']:>5} ms  rvc {t['rvc_ms']:>5} ms  total {t['total_ms']:>5} ms  -> {dest}")


if __name__ == "__main__":
    asyncio.run(main())
