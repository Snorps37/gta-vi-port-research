# REA pilot and PC compatibility milestones

## What REA recovered

We gave REA 6.10.1 the two files in `research/timing-app`. The launcher delegates a timing calculation to the project's Python fixture. Could a reviewer recover the entry point, dependencies, and result from the JavaScript package?

| Question | REA observation | Independent check |
| --- | --- | --- |
| Where does execution begin? | The package entry resolves to `index.cjs`. REA also inferred an Electron main role from the package metadata. | The launcher runs under plain Node with no Electron dependency. The role inference overstates what the metadata establishes. |
| What does the launcher depend on? | The CommonJS module has two imports, `node:path` and `node:child_process`. Both appear as external references. | The two require statements match the graph. |
| Does the Python call succeed? | REA left the synchronous call target unresolved. | Running the launcher on Windows printed `500 ms` for 30 frames at 60 FPS. |

Use REA as an optional static inspection step when a project-owned artifact matches a supported format. Give the independent reviewer a specific claim and a way to falsify it. Keep execution and test evidence in the harness. The experiment covered JavaScript analysis only. [REA upstream](https://github.com/morluto/rea)

## Repeat the experiment

Use Python 3.9+ and a supported Node installation (tested with Node 24.22.1). From the repository root in PowerShell, run the launcher and analyze its directory. Acquire the pinned REA CLI from a separate directory. The report contains machine-local paths, so the example writes it under the ignored `.native` directory.

```powershell
node research/timing-app
$fixture = (Resolve-Path research/timing-app).Path
New-Item -ItemType Directory -Force .native | Out-Null
$report = Join-Path (Resolve-Path .native).Path 'rea-timing.json'
Push-Location ([System.IO.Path]::GetTempPath())
try {
    npx --yes rea-agents@6.10.1 analyze-javascript-application $fixture --json > $report
    if ($LASTEXITCODE -ne 0) { throw 'REA analysis failed' }
} finally {
    Pop-Location
}
$analysis = Get-Content -Raw $report | ConvertFrom-Json
$analysis.normalized_result.graph.nodes.observations.label | Sort-Object -Unique
```

## Porting precedents

| Project | What transfers to Project NATIVE | Where applicability ends |
| --- | --- | --- |
| [Unleashed Recompiled](https://github.com/hedge-dev/UnleashedRecomp) | A published PC port with distinct executable translation, graphics, and runtime work. Track acceptance for each separately. | The source platform was Xbox 360. A successful port there establishes feasibility for that title and platform. |
| [XenonRecomp](https://github.com/hedge-dev/XenonRecomp) | Its executable format and CPU assumptions show why identifying the target comes before choosing tools. | Its input is Xbox 360 PowerPC code. A console brand alone is insufficient to select this tool. |
| [Microsoft Xbox GDK samples](https://github.com/microsoft/Xbox-GDK-Samples) | Use a sample with a desktop target as a known-good comparison for a Windows toolchain and graphics setup. | Building an available desktop source target tests the development environment. Compatibility of a separately packaged title needs its own evidence. |

## Milestones and evidence

1. **Fixture preflight.** Accept a synthetic manifest with a present entry point and report the expected path for a missing one. Run both cases in the harness.
2. **Windows interaction.** Open an original scene, deliver keyboard input, verify the position changes, and exit cleanly. Keep a scripted smoke test alongside the interactive version.
3. **Desktop graphics baseline.** Build one public GDK sample that lists a desktop configuration. Record the toolchain, build command, adapter, first rendered frame, and clean exit. Reproduce on a second PC before claiming portability.
4. **Target feasibility.** Privately establish completion, provenance, entry point, platform, and availability of source or an authorized desktop build path. Record a blocker when any required input is missing. Keep package inventories, binaries, logs, screenshots, and extracted material from that investigation off the public remote.
5. **Playability.** For a target available for testing, define one short input sequence with an observable outcome. Require launch, rendering, responsive input, and a repeatable full session on Windows. Publish only evidence cleared for release. A fixture result supports only the fixture milestone.

Codex owns implementation and integration. A second agent can take an independent fixture or chart in a separate worktree. Sonnet reviews the producer's commit against the acceptance criteria. Concord records who owns each file, the commit tested, and the handoff.
