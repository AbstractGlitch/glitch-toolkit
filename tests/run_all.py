"""Run every suite and report one number.

    python tests/run_all.py

Each suite is a script, not a test framework, and each is run as a subprocess so
that one crashing cannot take the others down with it. A suite that skips (exit
0 having printed "skip") is reported as skipped rather than passed, because a
green line that means "we did not look" is the exact failure the gate-check
practice exists to catch.
"""
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SUITES = ["test_cli.py", "test_ledger.py", "test_mcp_server.py"]

results = []
for name in SUITES:
    print("=" * 62)
    print(name)
    print("=" * 62)
    p = subprocess.run([sys.executable, str(HERE / name)], text=True, capture_output=True)
    sys.stdout.write(p.stdout)
    if p.stderr.strip():
        sys.stderr.write(p.stderr)
    skipped = p.returncode == 0 and "skip  " in p.stdout and " passed," not in p.stdout
    results.append((name, p.returncode, skipped))
    print("")

print("=" * 62)
failed = [n for n, code, skip in results if code != 0]
skipped = [n for n, code, skip in results if skip]
for name, code, skip in results:
    print("  {:<22} {}".format(name, "SKIPPED" if skip else ("ok" if code == 0 else "FAILED")))
if skipped:
    print("")
    print("  {} suite(s) skipped. That is not a pass.".format(len(skipped)))
    print("  For the server suite: pip install 'abstractglitch-toolkit[mcp]'")
print("")
sys.exit(1 if failed else 0)
