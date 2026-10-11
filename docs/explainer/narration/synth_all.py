#!/usr/bin/env python3
"""Synthesize one MP3 per scene with ElevenLabs and write their durations.

Uses the kb-to-podcast synth script, which finds the API key on its own.
Writes public/audio/<id>.mp3 and src/durations.json. Existing MP3s are kept;
delete one to re-render it.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNTH = Path.home() / ".claude/skills/kb-to-podcast/scripts/synth.py"
VOICE = sys.argv[1] if len(sys.argv) > 1 else "21m00Tcm4TlvDq8ikWAM"


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main():
    scenes = json.loads((ROOT / "narration/scenes.json").read_text())
    audio = ROOT / "public/audio"
    audio.mkdir(parents=True, exist_ok=True)
    work = ROOT / "narration/_txt"
    work.mkdir(exist_ok=True)
    durations = {}
    for scene in scenes:
        mp3 = audio / f"{scene['id']}.mp3"
        if not mp3.exists():
            txt = work / f"{scene['id']}.txt"
            txt.write_text(scene["text"] + "\n")
            subprocess.run(
                [sys.executable, str(SYNTH), "--in", str(txt), "--voice", VOICE,
                 "--format", "mp3_44100_128", "--stability", "0.55", "--style", "0.0",
                 "--out", str(mp3)],
                check=True,
            )
        durations[scene["id"]] = round(duration(mp3), 3)
        print(f"{scene['id']}: {durations[scene['id']]}s")
    (ROOT / "src").mkdir(exist_ok=True)
    (ROOT / "src/durations.json").write_text(json.dumps(durations, indent=2) + "\n")
    print(f"total: {sum(durations.values()):.1f}s")


if __name__ == "__main__":
    main()
