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
CODEX_REVIEW = [
    "codex", "--ask-for-approval", "never", "exec", "--ignore-user-config",
    "--sandbox", "read-only", "--ephemeral", "--color", "never", "-",
]
CLAUDE_REVIEW = [
    "claude", "-p", "--restricted", "--strict-mcp-config", "--tools", "",
    "--no-session-persistence", "--max-turns", "1",
]
REVIEWS = {
    "codex": CODEX_REVIEW,
    "claude": [*CLAUDE_REVIEW, "--model", "sonnet"],
    "opus": [*CLAUDE_REVIEW, "--model", "opus"],
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
            if command[0] == "claude":
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


def clean_revision():
    """Return a revision only when the worktree is clean."""
    try:
        status = subprocess.check_output(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=ROOT, stderr=subprocess.DEVNULL, text=True, timeout=10,
        )
        if not status:
            return subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, stderr=subprocess.DEVNULL,
                text=True, timeout=10,
            ).strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def handoff(db, run_id):
    receipt = db.execute(
        "SELECT revision FROM receipts WHERE run_id = ?", (run_id,),
    ).fetchone()
    if not receipt or not receipt[0]:
        print("Handoff needs a recorded clean commit. Rerun from a clean worktree.", file=sys.stderr)
        return 1
    rows = dict(db.execute("SELECT step, status FROM steps WHERE run_id = ?", (run_id,)))
    print(f"Commit {receipt[0]}\nHarness run {run_id}")
    for step in ("tests", *REVIEWS):
        print(f"{step}: {rows.get(step, 'not requested')}")
    print(f"Evidence: python harness.py --show {run_id} (local worktree)")
    return 0 if rows.get("tests") == "passed" else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--review", choices=("codex", "claude", "both"))
    options.add_argument("--escalate", metavar="QUESTION")
    options.add_argument("--show", metavar="RUN_ID")
    options.add_argument("--handoff", metavar="RUN_ID")
    args = parser.parse_args()
    if args.escalate is not None and not args.escalate.strip():
        parser.error("--escalate needs a focused question")
    review = "opus" if args.escalate is not None else args.review

    STATE.mkdir(exist_ok=True)
    with closing(sqlite3.connect(STATE / "runs.sqlite3")) as db:
        db.execute(
            """CREATE TABLE IF NOT EXISTS steps (
                run_id TEXT, step TEXT, status TEXT, exit_code INTEGER, output TEXT,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (run_id, step)
            )"""
        )
        db.execute("CREATE TABLE IF NOT EXISTS receipts (run_id TEXT PRIMARY KEY, revision TEXT)")
        if args.handoff:
            return handoff(db, args.handoff)
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
        revision = clean_revision()
        test = [sys.executable, "-m", "unittest", "discover", "-s", "fixture", "-t", ".", "-v"]
        passed = run_step(db, run_id, "tests", test, timeout=15)
        if revision and clean_revision() == revision:
            with db:
                db.execute("INSERT INTO receipts VALUES (?, ?)", (run_id, revision))
        if not passed or review is None:
            return 0 if passed else 1

        prompt = (
            "Review only the self-authored Python fixture included below. No tools are needed. "
            "Check correctness for the documented inputs and identify one useful missing test, "
            "if any. Reply in at most five lines. Do not change files.\n"
        )
        if args.escalate:
            prompt += f"Focus the review on this unresolved question: {args.escalate}\n"
        for path in SOURCE:
            if revision:
                source = subprocess.check_output(
                    ["git", "show", f"{revision}:{path}"], cwd=ROOT, encoding="utf-8", timeout=10,
                )
            else:
                source = (ROOT / path).read_text(encoding="utf-8")
            prompt += f"\n--- {path} ---\n{source}"
        reviewers = ("codex", "claude") if review == "both" else (review,)
        results = [
            run_step(db, run_id, reviewer, REVIEWS[reviewer], timeout=90, prompt=prompt)
            for reviewer in reviewers
        ]
        return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
