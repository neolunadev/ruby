# Handoff: neolunamiku, 2026-10-05

## Where things stand

- `main` is at v0.2.0 plus quick phrases, the Discord input switch, a startup option, and setup and CI hardening (PR #7). See `git log` and `CHANGELOG.md`.
- Draft [PR #9](https://github.com/neolunadev/neolunamiku/pull/9) (`wip/installer-progress-window`) replaces the console bootstrap with a progress window. Its one recorded failure (empty exit code at the venv step) came from a test harness run in a temp folder, so it may not be an installer bug. It needs a clean-machine test before merging.

## Next steps, in order

0. Rebrand the project to Ruby (see the pending note at the top of `CLAUDE.md`). The repo is now `neolunadev/ruby`.
1. Voice fidelity milestone: fixed in 0.5.1 (`fix/voice-fidelity`). Cause: kokoro-onnx fed Kokoro raw espeak-ng phonemes, splitting diphthongs into two vowel tokens, so "I'm" was spoken "I am". The text itself was never changed on any input path. Remaining: confirm by ear on the GPU PC with `scripts\smoke_test.py`; if "love you" still gains a leading "I", it is a short-utterance onset sound from Kokoro or RVC, not a text change.
2. Voice quality: RVC and Kokoro tuning.

## Gotchas

- Hard-won engine and audio gotchas live in `claude.md`; read them before touching `engine/`.
