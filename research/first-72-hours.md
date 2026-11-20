# The first 72 hours after an executable arrives

**Objective:** determine whether the matching program can initialize on this PC and, if it can, reach the most complete reproducible gameplay milestone the evidence supports. **72 hours is a decision window.** There is no demonstrated GTA VI desktop compatibility runtime in this project. An executable alone cannot support a defensible delivery date for a playable port.

## Before starting the clock

- Record the exact authorized program, data edition, build identity, source of each and available signature or catalog checks. Preserve them separately from scratch outputs.
- Record CPU, GPU, driver, OS, storage, SDK and tool versions. Reproduce the desktop sample, including its screenshot and a clean shutdown.
- Select one reference scene, input sequence and expected visible result on a supported target if available. Document which comparisons will be unavailable otherwise.
- Choose a route. A Windows executable needs its supported desktop deployment. Buildable source needs a Windows target and matching dependencies. An Xbox-only executable needs a compatible host. Without an executable or source, continue content research and leave the runtime milestones unstarted.

## Schedule and acceptance tests

| Hours | Owner and work | Acceptance evidence | If blocked |
|---|---|---|---|
| 0–4 | Integrator pairs content and program; Codex inventories static headers and dependencies; reviewer checks provenance separately. | Version match, architecture, target, executable entry, dependency inventory and supported host or build target recorded. | Isolate a mismatch. A missing host or desktop target is a route-level blocker. |
| 4–12 | Runtime owner establishes a supported reference launch. On desktop, test loader, allocation, jobs, files and clean exit in order. | Repeatable engine startup or a precise first failing operation, with expected ABI or service contract. | Avoid cascading stub fixes. Identify the first real missing contract and who can supply it. |
| 12–24 | Graphics owner tests desktop queue, fences, swap chain, compute dispatch and textured draw. Content owner resolves one known resource to validated bytes. | Correct reference buffer or pixels and reproducible cold-load/reload for the resource. Record whether each test ran in the game or in an isolated harness. | If no render backend, shader source or supported representation exists, scope it separately before promising a frame. |
| 24–36 | Integrator joins startup, resource loading and presentation. Reviewer distinguishes splash or clip playback from engine output. | Two independent launches present the same title-rendered scene or stop at the same documented boundary. | Capture the first divergent CPU or GPU operation and retain its input contract locally. |
| 36–48 | Gameplay owner adds input, simulation and a streaming transition. Audio/services owner checks sound, user state and failure paths. | Repeatable input changes world state; player can cross one boundary and return. | Record the missing behavior. A camera moving in a viewer does not establish gameplay. |
| 48–60 | Test owner exercises save/load, controller reconnect, repeated area traversal and process restart. | The same build restores the expected state after restart; no unknown dependencies are silently skipped. | Prioritize correctness defects before timing. |
| 60–72 | Performance owner repeats a fixed cold and warm route; independent reviewer reproduces the highest successful milestone. | Publish permissible methodology and a milestone statement with build, settings, duration, median/p95/p99 frame time and fraction over 33.33 ms. | If gameplay is unreachable, report the last reproducible stage, strongest blocker and smallest experiment that would change the decision. |

## Use AI credits where they can change the result

Concord records task ownership and file claims. Give Codex one implementation and its acceptance test. Give Claude a focused review question, public code, documented interfaces and expected behavior. Keep proprietary inputs, derived reports, logs and captures local. A local script can return pass/fail or work on an independently authored reproducer. Validate proposed changes with an actual test run before integrating them.

Parallelize static inspection, graphics baseline and content-reader work when their inputs are independent. Serialize changes to the loader and renderer once they share startup state. Escalate to a stronger model only with a narrowed question, observed failure and falsifiable prediction. If a trusted build, platform service, graphics specification or reference output is missing, record that dependency; spending additional inference time cannot provide it.

## End-of-window report

Record the route selected, last passing milestone, exact reproduction command, hardware and target, first failing operation, expected versus observed result, and the next piece of evidence needed. Distinguish these milestones in every report: static inspection → supported startup → game-rendered frame → controllable scene → repeatable gameplay → measured performance. Report the 30 FPS target only for the scene and settings actually tested.
