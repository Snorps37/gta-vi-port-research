"""Test the fixture and optionally request independent reviews."""

import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parent
STATE = ROOT / ".native"
SOURCE = ("fixture/units.py", "fixture/test_units.py")
REVIEWS = {
    "codex": [
        "codex", "--ask-for-approval", "never", "exec", "--ignore-user-config",
        "--sandbox", "read-only", "--ephemeral", "--color", "never", "-",
    ],
    "claude": [
        "claude", "-p", "--model", "sonnet", "--restricted", "--strict-mcp-config",
        "--tools", "", "--no-session-persistence", "--max-turns", "1",
    ],
}
PROVIDER_ENV = (
    "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX", "CLAUDE_CODE_USE_FOUNDRY",
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "CODEX_API_KEY",
)


def run_step(db, run_id, name, command, timeout, prompt=""):
    with db:
        db.execute(
            "INSERT INTO steps (run_id, step, status) VALUES (?, ?, 'running')",
            (run_id, name),
        )
    status, code = "failed", None
    try:
        env = os.environ.copy()
        if prompt:
            for key in PROVIDER_ENV:
                env.pop(key, None)
            if name == "claude":
                env.pop("CLAUDECODE", None)
        result = subprocess.run(
            command, cwd=ROOT, input=prompt, capture_output=True, timeout=timeout,
            encoding="utf-8", errors="replace", env=env,
        )
        code = result.returncode
        status = "passed" if code == 0 and (not prompt or result.stdout.strip()) else "failed"
        output = result.stdout + result.stderr
    except subprocess.TimeoutExpired as error:
        status = "timed_out"
        output = (error.stdout or b"").decode("utf-8", "replace")
        output += (error.stderr or b"").decode("utf-8", "replace")
        output += f"\nTimeout after {timeout} seconds."
    except OSError as error:
        output = str(error)
    with db:
        db.execute(
            """UPDATE steps SET status = ?, exit_code = ?, output = ?
               WHERE run_id = ? AND step = ?""",
            (status, code, output, run_id, name),
        )
    print(f"{run_id}  {name}: {status}", flush=True)
    if name == "tests" or status != "passed":
        print(output.strip(), flush=True)
    return status == "passed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--review", choices=(*REVIEWS, "both"))
    options.add_argument("--show", metavar="RUN_ID")
    args = parser.parse_args()

    STATE.mkdir(exist_ok=True)
    with closing(sqlite3.connect(STATE / "runs.sqlite3")) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS steps (
                run_id TEXT, step TEXT, status TEXT, exit_code INTEGER, output TEXT,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (run_id, step)
            )"""
        )
        if args.show:
            rows = db.execute(
                "SELECT step, status, exit_code, output FROM steps WHERE run_id = ? ORDER BY rowid",
                (args.show,),
            ).fetchall()
            if not rows:
                parser.error(f"unknown run ID: {args.show}")
            for step, status, code, output in rows:
                print(f"{step}: {status} (exit {code})\n{output or ''}")
            return 0

        run_id = uuid.uuid4().hex[:12]
        test = [sys.executable, "-m", "unittest", "-v", "fixture.test_units"]
        if not run_step(db, run_id, "tests", test, timeout=15):
            return 1
        if args.review is None:
            return 0

        prompt = (
            "Review only the self-authored Python fixture included below. No tools are needed. "
            "Check correctness for the documented inputs and identify one useful missing test, "
            "if any. Reply in at most five lines. Do not change files.\n"
        )
        for path in SOURCE:
            prompt += f"\n--- {path} ---\n{(ROOT / path).read_text(encoding='utf-8')}"
        reviewers = REVIEWS if args.review == "both" else [args.review]
        results = [
            run_step(db, run_id, reviewer, REVIEWS[reviewer], timeout=90, prompt=prompt)
            for reviewer in reviewers
        ]
        return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
