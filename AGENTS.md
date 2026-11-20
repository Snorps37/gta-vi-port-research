# Project NATIVE

- Work in this repository. Use the self-authored Python fixture for harness experiments.
- Before editing, call Concord `start_work` from the project or assigned worktree and claim the exact files. Resolve overlaps first.
- Use `inspect_work` to read the task and `transfer_work` for a handoff. From a clean commit, run `python harness.py` and attach `python harness.py --handoff RUN_ID` to Concord. Record the commit, changed files and test results with `finish_work`.
- Use a separate Git worktree for a second editing agent. The reviewer works from the producer's commit.
- Treat model reports as review evidence and test exit codes as test evidence.
- Use Sonnet for the first review of Codex work and Codex for the first review of Claude work. Escalate a focused unresolved question to Opus only after collecting the local evidence.
