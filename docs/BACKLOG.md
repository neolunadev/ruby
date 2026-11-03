# Backlog

Ideas and follow-ups that are not scheduled yet. Newest section first.

## Voice options (left out of v0.6.0)

From `docs/designs/voice-options.md`.

- **Measure preset costs on the RTX 2070 target.** Run `scripts/preset_demo.py` there
  and put real Kokoro and RVC times in the design doc; the numbers in it now are
  estimates from the code.
- **Characterise the untested packs.** The Mandarin, Spanish, Hindi, Italian and
  Portuguese packs are listed as "not yet heard through Miku". Listen, write a
  character note, and drop any that sound broken through English phonemes.
- **Autotune toggle.** The vendored RVC code already has `f0_autotune` and
  `f0_autotune_strength` (snaps pitch to notes, very Vocaloid). Cheap to run; needs a
  listening pass to pick a strength.
- **Auto transpose.** The vendored `proposed_pitch` option picks the transpose from
  the base voice's median pitch, which would make every catalogue voice land in
  Miku's register without hand-tuning pitch per voice.
- **More f0 methods.** Only RMVPE ships in the slim build. fcpe is about as fast and
  sometimes smoother; it needs its model vendored and added to the setup download.
  Crepe is too slow for live use.
- **Filter radius / RMVPE voicing threshold.** Hardcoded to 0.03 in
  `engine/rvc/infer/pipeline.py`. Exposing it means plumbing a parameter through the
  vendored code; only worth it if a voice shows dropped or extra voiced frames.
- **Blends of three or more voices.** The maths generalises (weights summing to 1);
  the UI does not. Could be a "voice recipe" text field in Advanced.
- **Save your own presets.** Name the current settings and add them to the preset list
  (stored in `config.json`).
- **Discord commands for the new knobs.** `/voice` already lists the new presets.
  There is no `/blend` or `/likeness`, and Discord changes are not saved to
  `config.json` (that was true before this change too).
- **Noise clean-up.** `clean_audio` in the vendored converter needs the `noisereduce`
  package; probably not needed with a TTS source.
- **Other RVC voice models.** The model picker is fixed to `models/voice_models/Miku`;
  supporting several models is a separate feature (and a licensing question per model).
- **Language-aware phonemization.** Non-English packs read English with American
  phonemes. Passing a matching `lang` to Kokoro belongs to the text path, which is
  being reworked for the fidelity bug; revisit after that lands.
