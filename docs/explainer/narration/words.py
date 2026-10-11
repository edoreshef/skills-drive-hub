# /// script
# dependencies = ["faster-whisper"]
# ///
"""Word-level timestamps for each scene MP3 with faster-whisper. Writes narration/words.json."""
import json
from pathlib import Path
from faster_whisper import WhisperModel

ROOT = Path(__file__).resolve().parents[1]
scenes = json.loads((ROOT / "narration/scenes.json").read_text())
model = WhisperModel("small.en", device="cpu", compute_type="int8")
out = {}
for scene in scenes:
    segments, _ = model.transcribe(str(ROOT / "public/audio" / f"{scene['id']}.mp3"), word_timestamps=True)
    out[scene["id"]] = [{"w": w.word.strip(), "s": round(w.start, 3), "e": round(w.end, 3)} for seg in segments for w in seg.words]
    print(scene["id"], len(out[scene["id"]]))
(ROOT / "narration/words.json").write_text(json.dumps(out) + "\n")
