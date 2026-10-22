# Skills Hub explainer video

A narrated explainer of Skills Hub for domain experts who also maintain their package,
built with [Remotion](https://www.remotion.dev). Not part of the skills-hub zip.

The narration audio (`public/audio/`) and renders (`out/`) are not committed. Run the
synthesis steps under "Change the script" to rebuild the audio before previewing or rendering.
The script follows the framing in the top-level README: Skills Hub is the framework, Google
Drive is the hub, and users get, sync, and contribute by asking their agent. About 6.7 minutes.

The running example is invented: Dana, a demand planner in a supply chain group, maintains a
`planning` package whose skills are `stock-readout`, `lead-times` and `weekly-brief`; Sam, Jun and
the others are her colleagues. No person, organization or dataset in the video is real.

```text
narration/scenes.json   the script: one narration paragraph per scene
narration/synth_all.py  ElevenLabs TTS per scene → public/audio/<id>.mp3, src/durations.json
narration/words.py      word timestamps with faster-whisper → narration/words.json
narration/align.py      maps timestamps onto the script → src/timings.json
narration/v1-src/       the first, cartoon-style version of the scenes (kept for reference)
src/kit.tsx             palette, type, timing hooks, panels (file tree, code, terminal), persona
src/scenesA.tsx         scenes 1–6: expert, agent and the Drive hub, layers, skill anatomy, Drive, quick start
src/scenesB.tsx         scenes 7–14: sync and the sync gate, publish, review, checks, release, feedback, boundaries, recap
src/Explainer.tsx       sequencing, captions, fades, audio
```

`Line` draws in stage coordinates (1920×1080). Put it directly under `Stage`, not inside a
positioned `Rise`, or it renders offset by the parent's position.

Every on-screen beat is keyed to a spoken phrase with `at("…")`, so visuals stay in sync with
the narration without hand-tuned frame numbers.

## Change the script

1. Edit the scene's text in `narration/scenes.json`, then delete `public/audio/<id>.mp3`
   **and** `public/audio/_chunks_<id>/` (the synth script caches by scene name).
2. `python3 narration/synth_all.py` (optional argument: an ElevenLabs voice ID), then
   `uv run --script narration/words.py` and `python3 narration/align.py`.
3. If a phrase used in `at("…")` no longer exists, rendering fails with `phrase not found`.
   `node scripts/stills.mjs 1` is the quickest way to surface that before a full render.

Numbers such as `0.6.0` are fine in the script: whisper hears them as several words, and
`align.py` widens its search window after a miss so the following words still match.

## Preview and render

```text
npm install
npm run studio                      # live preview
npm run render                      # out/explainer.mp4
node scripts/stills.mjs 12 95.5     # review stills at those seconds, in out/stills/
```
