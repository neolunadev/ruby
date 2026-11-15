# Changelog

## 0.7.2 - 2026-11-15

- Short lines are clear again: one- and two-word lines ("no", "haha", "hihi", "hee
  hee") use Kokoro's own pronunciation instead of the 0.5.1 mapping, which garbled
  them into other words. Longer lines and anything with a contraction ("I'm") keep
  the 0.5.1 fix. "yeah" and "cats" sound exactly as before.

## 0.7.1 - 2026-11-15

- Laughs are back to exactly how 0.6.0 said them. The 0.7.0 laugh change made
  "hihi" come out as other words; a better fix waits for a listening pass.

## 0.7.0 - 2026-11-15

- Boost mode: the 💥 Boost button beside Speak boosts the next line only (a touch
  lower, bass boosted, crunchy like a clipping mic without really clipping, big echo
  and reverb), then switches itself off. Ctrl+Enter
  speaks a line boosted, in the main box and the overlay. Boosted lines show 💥 in
  History and replay boosted.
- Updates now come only from full GitHub releases (never the main branch or a
  pre-release), and never offer an older version.
- Updates install only the packages that are missing instead of reinstalling every
  requirement, which could fail while the app was running. Missing packages are also
  installed at startup, so an update that failed halfway repairs itself.
- Laughs: "haha" is "ha ha" and "hihi" is "hee hee", each beat stressed like an
  English laugh (before, "haha" stressed the wrong "ha" and "hihi" ended in "high").
  Lines without a laugh are spoken exactly as before.
- Consonant protection slider now reads the right way round: further right protects
  more, shown as a percent (0.50 used to mean "off" at the far right). Saved settings
  keep their sound; a slider that was at the far right now shows 0% at the far left.
- Yellow notices where Windows administrator rights matter: installing VB-Cable, and
  the hotkey, which cannot reach apps running as administrator.

## 0.6.0 - 2026-11-03

- Voice options: pick any of Kokoro's 29 female voices (grouped by accent), blend two
  voices with a Mix slider, and choose from ten Miku presets (six new: bright, gentle,
  calm, British, Japanese accent, steady).
- Advanced section (collapsed by default) with Miku likeness, consonant protection
  and loudness sliders. Sliders never reload a model; blends are cached.
- Preview button: hear the current settings on your own speakers, not in the call.
- Voice settings are saved to `config.json`; older configs keep their voice.
- `scripts/preset_demo.py` renders a line in each preset with timings.
- Design: `docs/designs/voice-options.md`; follow-ups: `docs/BACKLOG.md`.

## 0.5.1 - 2026-11-03

- Voice fidelity: Kokoro now gets the phoneme set it was trained on (misaki), not raw
  espeak-ng output. Diphthongs were reaching it as two separate vowels, so "I'm" was
  spoken as two syllables ("I am") and short lines could pick up a stray leading sound.

## 0.5.0 — 2026-08-19

- Quick phrases: one-click common lines, editable in Settings.
- "Accept messages from Discord" switch - when off, `/say` and DMs answer "Mic is off"
  and nothing is spoken. Discord cannot tell an app whether you are in a DM call, so
  this switch is the control that exists.
- Start automatically when Windows starts (optional).
- Warns when synthesis falls back to the CPU, and writes a rotating log to `logs/`.
- Setup covers the virtual microphone, and the README explains the Discord audio
  settings that otherwise chop up synthesized speech.
- Discord-visible text carries no character branding.
- `bot.py` now shares the app's client, so the allowlist applies there too (196 -> 70 lines).
- CI also lints (ruff) and checks JavaScript syntax; uninstall removes downloaded models.

## 0.4.0 — 2026-08-19

- Renamed to neolunaruby. Voice presets are still named Miku.
- Windows installer (`neolunaruby-setup-<version>.exe`, about 2 MB): installs per-user,
  then the first launch installs Python, FFmpeg and dependencies by itself.
- First-run wizard downloads the voice models with per-file progress and takes an
  optional Discord bot token, so no terminal or manual file placement is needed.
- Updates work for installed copies too: a zip overlay replaces code only and never
  touches models, settings or the environment. Applying still needs your confirmation.

## 0.3.0 — 2026-08-19

- Slim build: RVC inference code vendored into `engine/rvc/`, ultimate-rvc and its
  app/training stack removed from dependencies. Environment shrinks 7.5 GB -> 5.6 GB
  (torch's CUDA runtime is the remaining floor). Only the rmvpe pitch method ships.
- requirements.txt is now the single, inference-only dependency file with documented
  post-install steps.
- MIT license, user-facing README, branch protection with required CI, PR-based flow.

## 0.2.0 — 2026-08-19

- Discord integration lives in the desktop app: `/say` works inside DM conversations
  (user-installable, auto-enabled install contexts), plain DMs to the bot are spoken,
  allowlist-gated, optional visible `🎤 text` transcript in the chat.
- Output mode toggle: virtual mic ⇄ server voice channel.
- One-click VB-Cable download/install; devices persist by name; WASAPI sample-rate
  auto-conversion (fixes silent playback); "Hear it too" monitor output.
- Hotkey recorder, system tray, UI restructured into Speak / History / Settings.
- Self-update from GitHub via the version chip; CI (pytest + compileall) on every push.

## 0.1.0 — 2026-08-19

- First working build: local kokoro→RVC Miku voice (~1.1s warm), Discord bot with
  `/say` `/join` `/leave` `/voice` `/pitch` `/speed`, desktop app shell with telemetry,
  history/replay, hotkey overlay, headless engine CLI.
