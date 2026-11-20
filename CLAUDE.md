@AGENTS.md

Use Sonnet for routine review. Read the commit and acceptance criteria in the Concord handoff, rerun the fixture tests in that worktree, and report the most important finding with a file and a reproducing input. Record the outcome in Concord.

Use Opus when an implementation decision remains unresolved after local verification. Give it one question, the relevant evidence and the options already tried. If a fix is assigned, claim its files before editing.

To get a Codex review of Claude's own commit, use the official OpenAI plugin's `/codex:review --base <base-ref>`. Request it once after tests pass and preserve the result in Concord.
