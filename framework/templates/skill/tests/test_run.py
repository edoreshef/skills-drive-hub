import subprocess
import sys
from pathlib import Path

script = Path(__file__).resolve().parents[1] / "scripts" / "run.py"
result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
if result.returncode != 0 or result.stdout.strip() != "SKILL-SCRIPT-RAN":
    raise SystemExit(1)
