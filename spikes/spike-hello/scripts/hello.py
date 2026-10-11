# /// script
# requires-python = ">=3.9"
# dependencies = ["tabulate>=0.9"]
# ///
import platform
import sys

try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

rows = [
    ["python", sys.version.split()[0]],
    ["executable", sys.executable],
    ["platform", platform.platform()],
    ["tabulate", "available" if tabulate else "MISSING"],
]

print("SPIKE-HELLO-SCRIPT-RAN")
if tabulate:
    print(tabulate(rows, headers=["key", "value"]))
else:
    for key, value in rows:
        print(f"{key}: {value}")
