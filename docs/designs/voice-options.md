# Voice options: female voices, blending, sliders and presets

Status: built in `feat/voice-options` (v0.6.0). Asked for by Luke on 2026-11-03:
"more options for female voices to use, more settings and sliders, while keeping it
easy and quick to process".

## Goals

- More base voices to choose from, all female, plus a two-voice blend.
- The RVC knobs that change how Miku sounds, as sliders, out of the way by default.
- A short list of named presets, so most people never touch a slider.
- A quick Preview so a change can be heard without speaking into the call.
- The default path stays exactly as fast as before: same voice pack, same RVC
  call, no extra work per message.
- Moving a slider never reloads a model.

## How the voice is made

Text goes to Kokoro (kokoro-onnx, local, GPU), which speaks it in a base voice. That
audio goes through RVC with the Miku model, which keeps the timing, words and
intonation of the base voice and replaces the timbre with Miku's. So the base voice
mostly shapes **prosody, pacing and accent**, and RVC shapes **timbre**. A female base
voice is used because RVC has less pitch distance to cover, which sounds cleaner.

Warm latency on an RTX 3060 Ti is about 1.1 s per message: Kokoro about 0.2 s and
RVC about 0.8 s. RVC cost grows roughly with the length of the audio.

## 1. The female voice catalogue

The repo pins Kokoro's `voices-v1.0.bin` (kokoro-onnx release `model-files-v1.0`,
downloaded by `app/setup_wizard.py`). It holds 54 voice packs; 29 are female. All 29
are in the picker, grouped by accent. The id prefix is language plus gender
(`af` = American female, `bf` = British female, and so on).

"Grade" is upstream Kokoro's own grade for the quality and amount of training data
behind each pack (from Kokoro-82M `VOICES.md`). A higher grade usually means cleaner
audio and steadier prosody. "Character" is a first impression to confirm by ear
through the Miku model; the RVC stage changes a lot, so the base voice character
shows mostly in rhythm, energy and breathiness.

Text is always phonemized as American English (that is the text path, and it is not
touched here). Non-English packs therefore speak English words with their own
accent and rhythm, which is often charming and sometimes odd. That is why the
"Japanese accent" preset blends a Japanese pack with an American one rather than
using it alone.

| Id | Name | Accent | Grade | Character |
|---|---|---|---|---|
| af_heart | Heart | American | A | warm, natural; the default |
| af_bella | Bella | American | A- | bright, expressive, energetic |
| af_nicole | Nicole | American | B- | soft, breathy, close-mic whisper |
| af_aoede | Aoede | American | C+ | smooth, even, slightly low |
| af_kore | Kore | American | C+ | clear, confident |
| af_sarah | Sarah | American | C+ | calm, mature, steady |
| af_nova | Nova | American | C | crisp, assistant-like |
| af_alloy | Alloy | American | C | neutral, flat |
| af_sky | Sky | American | C- | light, airy, youthful |
| af_jessica | Jessica | American | D | casual, uneven |
| af_river | River | American | D | relaxed, uneven |
| bf_emma | Emma | British | B- | polished, gentle |
| bf_isabella | Isabella | British | C | warm, rounded |
| bf_alice | Alice | British | D | clipped, formal |
| bf_lily | Lily | British | D | soft, quiet |
| jf_alpha | Alpha | Japanese | C+ | clear, bright |
| jf_gongitsune | Gongitsune | Japanese | C | storyteller, gentle |
| jf_nezumi | Nezumi | Japanese | C- | storyteller, light |
| jf_tebukuro | Tebukuro | Japanese | C | storyteller, soft |
| zf_xiaobei | Xiaobei | Mandarin | D | not yet heard through Miku |
| zf_xiaoni | Xiaoni | Mandarin | D | not yet heard through Miku |
| zf_xiaoxiao | Xiaoxiao | Mandarin | D | not yet heard through Miku |
| zf_xiaoyi | Xiaoyi | Mandarin | D | not yet heard through Miku |
| ef_dora | Dora | Spanish | C | not yet heard through Miku |
| ff_siwis | Siwis | French | B- | clear, soft |
| hf_alpha | Alpha | Hindi | C | not yet heard through Miku |
| hf_beta | Beta | Hindi | C | not yet heard through Miku |
| if_sara | Sara | Italian | C | not yet heard through Miku |
| pf_dora | Dora | Brazilian Portuguese | C | not yet heard through Miku |

The catalogue lives in `engine/voices.py` (`FEMALE_VOICES`). Male packs are left out
on purpose: the ask was female voices, and a male base voice needs a much larger
transpose, which sounds worse through the Miku model.

Processing cost: **none**. Every pack has the same shape, `voices-v1.0.bin` is loaded
once at startup, and switching packs only changes which array Kokoro reads.

### Voice blending

Each pack is a style array of shape (510, 1, 256), one 256-value style vector per
possible phoneme count. kokoro-onnx's `create(voice=...)` takes either a pack name or
such an array, so a blend is a weighted sum of two packs:

```text
style = (1 - w) * pack_A + w * pack_B        w = Mix slider, 0..1
```

The weights always sum to 1, which keeps the style vector in the range the model was
trained on. Rules (`voices.blend_weights`):

- `w = 0`, no second voice, or the same voice twice: just pack A, passed **by name**,
  exactly the call Kokoro got before this feature.
- `w = 1`: just pack B, by name.
- otherwise: the weighted array.

Range 0 to 1 in steps of 0.05, default 0 (off). Processing cost: one weighted sum of
about 130k floats (microseconds), done **once per distinct mix** and kept in a small
cache (`voices.StyleCache`, last 32 mixes), so dragging the slider back and forth never
recomputes a mix it has seen and never touches the disk. Kokoro's own inference time
does not change with a blend.

Only two voices are blended in the UI. Three or more is a one-line generalisation of
the maths but makes the UI harder; it is in the backlog.

## 2. Kokoro speed

| Control | Range | Default | Cost |
|---|---|---|---|
| Speed | 0.5 to 2.0, step 0.05 | 1.1 | Free in Kokoro. Faster speech is shorter audio, so RVC gets **faster** (about proportional to length); slower speech makes RVC slower. |

The range is kokoro-onnx's own limit (it rejects anything outside 0.5 to 2.0). Speed is
the speaker's own pace, so presets do not change it.

## 3. RVC knobs

The vendored RVC code (`engine/rvc/`) is a slim build of ultimate-rvc / Applio
inference. The converter stays resident (`engine/pipeline.py`); every knob below is a
plain argument to `convert_audio`, so changing one never reloads the Miku model, the
embedder, RMVPE or the faiss index.

| Knob | UI label | Range | Default | What it does | Cost |
|---|---|---|---|---|---|
| Pitch shift (`n_semitones`) | Pitch | -12 to +12 semitones, step 1 | +10 | Transposes the base voice into Miku's register. | None: it scales the f0 curve. |
| Index rate (`index_rate`) | Miku likeness (Advanced) | 0 to 1, step 0.05 | 0.5 | How much of each frame's features is replaced by the nearest Miku training features from the faiss index. Higher is more Miku-like timbre but can slur words; lower keeps more of the base voice and is clearer. | Same for any value above 0 (one faiss search per message). At exactly 0 the search is skipped, a small saving. |
| Protect (`protect_rate`) | Consonant protection (Advanced) | 0 to 0.5, step 0.01 | 0.33 | Keeps unvoiced sounds (s, t, breaths) closer to the base voice so they do not turn into tonal artifacts. Lower protects more. 0.5 turns protection off. | Negligible: one extra feature copy and blend below 0.5; none at 0.5. |
| RMS mix (`rms_mix`, RVC `volume_envelope`) | Loudness (Advanced) | 0 to 1, step 0.05 | 1.0 | Mixes the base voice's loudness envelope into the output. 1.0 keeps the RVC output's own loudness (off); lower follows Kokoro's loudness, which evens out volume swings. | 1.0 skips the step entirely. Below 1.0, two RMS envelopes and an interpolation: a few milliseconds per message (estimate). |
| Filter radius | not exposed | n/a | n/a | In classic RVC, a median filter over the pitch curve, used only by the "harvest" f0 method. This slim build has only RMVPE, and the vendored code passes the name `filter_radius` to RMVPE as its voicing threshold, hardcoded to 0.03. Exposing it means changing vendored code for a control that rarely helps. | n/a |
| f0 method | not exposed | rmvpe only | rmvpe | The pitch tracker. The slim build removed crepe, fcpe and harvest; only RMVPE ships (it is also the fastest good one on GPU). | Crepe would cost about 2x to 5x more RVC time; fcpe is about as fast as RMVPE but needs its model vendored and downloaded. |

The sliders that people reach for (Speed, Pitch) stay visible on the Speak tab, as
before. The three that need a trained ear (likeness, protection, loudness) sit in an
**Advanced** section that is collapsed every time the app opens.

## 4. Presets

All presets are Miku (user-visible voice labels say Miku). A preset fixes every voice
field (engine, voice, blend, pitch and the three RVC knobs) so there are no leftovers
from the last preset; speed is left alone. Each is a diff from the default, defined in
`engine/voices.py`:

| Preset | Base voice | Changes from default | Extra cost |
|---|---|---|---|
| Miku | af_heart | none (the default, unchanged) | none |
| Miku (soft) | af_bella | voice | none |
| Miku (bright) | af_heart + 35% af_sky | blend, pitch +11 | none (blend cached) |
| Miku (gentle) | af_heart + 40% af_nicole | blend, protect 0.40 | none |
| Miku (calm) | af_sarah | voice, pitch +9, likeness 0.60 | none |
| Miku (British) | bf_emma | voice | none |
| Miku (Japanese accent) | af_heart + 50% jf_alpha | blend | none |
| Miku (steady) | af_heart | likeness 0.75, loudness 0.50 | a few ms (RMS mix) |
| Miku (cloud backup) | edge-tts AnaNeural | cloud engine, pitch +2 | about +1 s, needs internet |
| Miku (cloud backup 2) | edge-tts JennyNeural | cloud engine, pitch +6 | about +1 s, needs internet |

The names of the four older presets are unchanged, so Discord's `/voice` and existing
configs keep working. When the current settings match no preset, the picker shows
"Custom", and **Reset to preset** goes back to the last preset picked.

## 5. App behaviour

- **Speak tab**: Preset with a Preview button; Voice (the catalogue, grouped by accent,
  with a one-line hint for the selected voice); Mix with (a second voice or nothing);
  Mix slider (disabled until a second voice is chosen); Speed; Pitch; then the
  collapsed Advanced section. Same toolkit and style as the rest of the app (plain
  HTML, CSS variables, `pywebview.api` calls).
- **Preview** speaks "Hi! This is how I sound right now." with the current settings,
  plays it on the monitor device (or the default speakers when no monitor is set),
  never into the virtual mic or a voice channel, and keeps it out of the history. One
  preview at a time. It goes through the same GPU lock as normal messages.
- **Saving**: every control saves on release through the existing `set_setting` into
  `config.json`. New keys: `engine`, `voice`, `blend_voice`, `blend`, `index_rate`,
  `protect_rate`, `rms_mix`. Values are clamped to the ranges above, and unknown
  voices fall back to af_heart, so a hand-edited config cannot stop the voice.
- **Upgrades**: a config from before this change holds only a preset name and a pitch;
  on load the voice fields are rebuilt from that preset, so the voice does not change.
- **No reloads**: Kokoro, its voice packs, the RVC model, the embedder, RMVPE and the
  faiss index are all loaded once; sliders only change numbers that the next synthesis
  reads.
- `bot.py` loads the same saved settings as the app.

## 6. Speed guarantee

With the default preset the Kokoro call receives the pack name `"af_heart"` and the
RVC call receives the same arguments as before (`volume_envelope=1.0` skips the RMS
step). The test suite pins these defaults (`tests/test_voices.py`). The only presets
with a per-message cost above zero are "steady" (a few ms) and the cloud backups.

Measured costs on real hardware are not in this document: the GPU models cannot run
in the build environment. `scripts/preset_demo.py` prints Kokoro and RVC times for
each preset on Luke's PC.

## Not in scope

See `docs/BACKLOG.md` for what was left out and why.
