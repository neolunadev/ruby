# Backlog

Ideas and follow-ups that are not scheduled yet. Newest section first.

## Text and delivery (asked 2026-11-15, after boost mode shipped)

Luke's asks from the 0.7.0 session. The first four share one foundation, splitting a
message into sentences, so they get one spec (EGM) before code.

- **Per-sentence rendering with early start.** Split long messages into sentences,
  synthesize them one at a time, and start speaking once enough is rendered that the
  rest will be ready before playback reaches it (Luke: "start at about 80%"; the real
  rule is "remaining render time < remaining audio time"). Then the 500-character cap
  can rise to Discord's 2000.
- **Punctuation effects, per sentence.** A sentence ending in `~`, `!` or `?` gets its
  own delivery effect (for example `~` sing-song lilt, `!` louder and brighter, `?`
  rising pitch). Commas and full stops should give real pauses. Exact effects are a
  Desk pick.
- **Drawn-out syllables.** "i think you liiiiike meeeee" should hold the vowel, not
  spell or skip it. Likely route: collapse the run to the dictionary word, phonemize,
  then repeat or stretch the stressed vowel.
- **Laughs and interjections.** 0.7.0 fixes the phonemes ("haha" stressed on the
  wrong "ha", "hihi" ending in "high"). If laughs still sound flat by ear, try
  breathier phonemes or short recorded-style takes. Must not change how "yeah"
  sounds now (Luke likes it).
- **Misspellings and jokes.** "cummunity" comes out like "community": espeak does
  give it a different first vowel (kʌm, not kəm), but the syllable is unstressed so
  the difference blurs. Options: a user pronunciation list in Settings ("write it as /
  say it as"), or stressing a word whose spelling differs from the dictionary word.
- **Sing mode.** RVC already has `f0_autotune` (see the Autotune toggle below);
  singing needs a melody: snap to a scale for an autotune feel, or take a simple
  note line. Needs a design pass.
- **Japanese text.** Lines with Japanese characters (日本語) should be spoken in
  Japanese. Kokoro has Japanese voices (jf_*) and misaki has a Japanese G2P; this
  needs script detection per sentence and a Japanese voice, so it rides on the
  per-sentence split.
- **A preset built from real use.** Luke's user runs Heart, speed 0.70 to 0.80,
  pitch +7 to +9, likeness 1.0, loudness 0.5, consonant protection slider at 0.50.
  Build a named preset around that and improve it by ear.
- **Short words.** A lone "no" can come out as "sendeno". Candidate fixes are on the
  0.7.0 ear-check page (cut the quiet lead-in before RVC, or protection on).
- **Boost tuning.** Boost (0.7.0) has one fixed chain in `engine/effects.py`; add an
  intensity slider if Luke wants it, and a `/say boost:true` option for Discord.

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
