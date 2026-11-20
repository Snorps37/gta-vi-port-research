# Project NATIVE

Project NATIVE is a local test project for Codex, Claude Code, and Concord. The Python fixture converts a frame count into milliseconds. The harness uses only the Python standard library.

## Public research demo

The JavaScript launcher calls the Python fixture on Windows. The REA pilot records which dependencies a static reviewer recovered and which call needed a runtime check. The research plan tracks the steps from a synthetic manifest to a repeatable PC playability test. [Experiment, reproduction commands, and milestones](research/rea.md)

![Elapsed time for 30 frames at four frame rates, computed by the fixture](docs/frame-timing.png)

## Run the harness

```powershell
cd D:\gta6\ProjectNative
python harness.py
python harness.py --review claude
python harness.py --show RUN_ID
python harness.py --handoff RUN_ID
```

Run `python harness.py` for local tests. When you request a review, the harness runs the tests first and calls the reviewer only if they pass. Use `--review codex` for an independent Codex review, `--review claude` for a Sonnet review, or `--review both` to run both in sequence. To ask Opus one unresolved technical question, run the harness separately with `--escalate "Your question"`.

Each provider call has a 90-second timeout. If your Claude session has expired, renew it with `claude auth login`. The harness removes common API key and provider environment variables from the child process and does not automatically switch to paid API access. Each provider manages subscription quotas and any extra usage enabled on your account.

Pass the run ID printed in the terminal to `--show` to see test output, model responses, and process status. Runs are stored locally in `.native/runs.sqlite3`. An interrupted run can remain marked `running`. Each retry gets a new ID. A successful model command means the harness received a response. Evaluate its findings separately.

For a run from a clean working tree, `--handoff` reports the commit SHA and the status of each step. Add this summary to the Concord task. The SQLite database stays local, so reviewers in another worktree rerun the tests at the same commit. If an older run has no recorded commit, rerun the tests from a clean working tree.

## Codex, Claude Code, and Concord

| Role | When to use it | Expected output |
| --- | --- | --- |
| Codex | Implement small changes, write tests, and integrate reviewed work | Commit, test result, and any open question for the reviewer |
| Claude Code / Sonnet | Give a Codex change its first independent review | Finding with the file and input needed to reproduce it |
| Codex CLI | Review a Sonnet change or provide a second opinion while Sonnet is unavailable | Concise review and a suggested test for a coverage gap |
| Claude Code / Opus | Resolve conflicting reviews or a difficult technical decision | Reasoned answer to one question and a way to verify it |
| Concord | Coordinate file ownership, check for overlaps, track status, and hand off work | Task record with the commit and test evidence |

1. The implementing agent claims the files with `start_work`. A second agent editing concurrently uses a separate worktree and claims its own files.
2. The implementing agent commits the change, runs the tests from the clean working tree, and adds the `--handoff RUN_ID` summary to Concord. If the reviewer is connected, hand over the task with `transfer_work`.
3. The reviewer reads the commit and acceptance criteria with `inspect_work` and records findings in Concord. CLI reviews cover the fixture source. Codex runs in read-only mode, and Claude runs with tools disabled.
4. Fix failing tests locally first. If access or quota limits prevent a model call, record the failure and continue with local tests. Switching providers or escalating to Opus requires an explicit call.

## Local Claude Code plugin and Concord workspace

From the project directory, install OpenAI's official Codex plugin with local scope.

```powershell
claude plugin marketplace add openai/codex-plugin-cc --scope local
claude plugin install codex@openai-codex --scope local
```

Start Claude Code from the project root. Run `/codex:setup` to check the local Codex session. To review a Claude change, run the tests on the feature branch, then run `/codex:review --base main`. Keep the automatic review gate disabled.

The Git repository root is the Concord workspace for NATIVE tasks. If you start a session from the parent directory or a separate worktree, run `concord -C <project-root> status` to get the workspace ID and pass it as `workspace_id` in Concord calls. Claude Code and Codex should see the same NATIVE task when opened from the same project directory.

## Plan for the incoming download

| Timing | Owner | Work and acceptance criteria |
| --- | --- | --- |
| While the download is in progress | Codex | Run `python harness.py` from a clean commit. Once the fixture tests pass, record the run ID and commit in Concord. |
| First 15 minutes after completion | Codex | Check the client's completion status for the selected files and identify any skipped files. List file paths and sizes locally. Record whether the executable exists at the path specified in the manifest. |
| Next 15?60 minutes | Codex | Identify any missing or inconsistent files. If torrent piece verification is needed, measure its duration separately because it depends on disk speed. Piece verification checks the data against the torrent metadata. Verifying publisher provenance requires an independent signature or trusted reference. |
| First development iteration | Codex and Sonnet | Create two sample manifests in the test project. Point one at an existing file and the other at a missing file. Add an automated test showing that the checker accepts the first and reports the missing path for the second. If Sonnet is available, have it review the commit independently. |
| Decision and handoff | Codex | If the executable is missing, mark runtime testing of the package as blocked. If it exists, assess the target platform, provenance, and authorized test environment. Record the inventory and test results separately in either case. |

Keep the raw package and local inventory on the download machine. Use the shared Git repository for project-authored tools, synthetic fixtures, and reproducible tests.
