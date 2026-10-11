#!/usr/bin/env python3
"""Map whisper word timestamps (narration/words.json) onto the script's words.

Writes src/timings.json: per scene, its duration, every script word with a
start time, and every sentence with a start and end time.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def norm(word):
    return re.sub(r"[^a-z0-9]", "", word.lower())


def align(script_words, heard):
    times = [None] * len(script_words)
    j = 0
    misses = 0  # consecutive script words not heard; widens the window so "0.6.0"
    for i, word in enumerate(script_words):  # read as five words cannot stall the match
        target = norm(word)
        for k in range(j, min(j + 5 + 4 * misses, len(heard))):
            h = norm(heard[k]["w"])
            if h and (h == target or h.startswith(target) or target.startswith(h)):
                times[i] = heard[k]["s"]
                j = k + 1
                misses = 0
                break
        else:
            misses += 1
    known = [(i, t) for i, t in enumerate(times) if t is not None]
    for i in range(len(times)):
        if times[i] is None:
            before = [p for p in known if p[0] < i]
            after = [p for p in known if p[0] > i]
            if before and after:
                (i0, t0), (i1, t1) = before[-1], after[0]
                times[i] = t0 + (t1 - t0) * (i - i0) / (i1 - i0)
            else:
                times[i] = (before[-1][1] + 0.3) if before else (after[0][1] if after else 0.0)
    return times, len(known)


def main():
    scenes = json.loads((ROOT / "narration/scenes.json").read_text())
    durations = json.loads((ROOT / "src/durations.json").read_text())
    heard_all = json.loads((ROOT / "narration/words.json").read_text())
    timings = {}
    for scene in scenes:
        sid = scene["id"]
        words = scene["text"].split()
        times, matched = align(words, heard_all[sid])
        sentences, current = [], []
        for word, t in zip(words, times):
            current.append((word, t))
            if re.search(r"[.?!]$", word):
                sentences.append(current)
                current = []
        if current:
            sentences.append(current)
        rows = [{"text": " ".join(w for w, _ in s), "start": round(s[0][1], 3)} for s in sentences]
        for a, b in zip(rows, rows[1:] + [{"start": durations[sid]}]):
            a["end"] = round(b["start"], 3)
        timings[sid] = {
            "duration": durations[sid],
            "words": [{"w": w, "s": round(t, 3)} for w, t in zip(words, times)],
            "sentences": rows,
        }
        print(f"{sid}: matched {matched}/{len(words)} words")
    (ROOT / "src/timings.json").write_text(json.dumps(timings, indent=1) + "\n")


if __name__ == "__main__":
    main()
