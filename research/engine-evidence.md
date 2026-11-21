# What can we infer about the GTA VI engine?

The strongest evidence comes from following one reference across two layers. A pipeline referencing the same shader as another pipeline proves code reuse. A replay entry whose display keys occur in a second UI resource supports a catalog-to-UI relationship. Neither observation explains the CPU code that chooses the pipeline or starts the mission.

## Where the code is

| Layer | What we examined locally | What would answer the next question |
|---|---|---|
| Main CPU program | Launch metadata, file inventory and a static raw-container search. The declared program has not been recovered. | Trusted matching source, executable or supported reference trace. This is the gap for the main loop, scheduling and gameplay control flow. |
| Native support libraries | Read-only x64 disassembly over every file-backed executable section of the supplied support DLLs. Import slots were joined to direct call/jump operands and one graphics call site was independently checked with DUMPBIN. | A reference run to establish which paths actually execute, under what inputs and in what order. |
| GPU programs | Decoded cache boundaries, shader ranges, code hashes and per-pipeline shader references. The coverage explorer distinguishes graphics and compute and shows reuse. | Stage-specific binding semantics, a known input and an authenticated reference output to assess a desktop translation. |
| Data and possible scripts | Parsed structured records and UI catalogs, checked cross-archive identity candidates, and tested their boundaries. A gameplay VM and its entry point remain unverified. | A documented instruction encoding, a matching runtime and a repeatable state transition. |

An x64 decoder can turn data embedded in a code section into plausible instructions. Unwind-described ranges, a second disassembler and an import-table join make a particular interpretation stronger. A DLL dependency alone cannot establish the game engine's call order, thread model or memory budget.

## How a frame might fit together

Package configuration identifies the program. Typed data refers to resources; world placements refer to scene objects; a graphics pipeline binds programs and resources; a media event can refer to an audio or video stream. This describes the interfaces a compatible implementation would have to satisfy. The precise streaming scheduler, simulation order, animation selection, render-pass order and service behavior remain open. The [Xbox-to-PC diagrams](xbox-to-pc.md) explain the general platform model. The [data-type report](data-types.md) records the limits of each comparison. Rockstar describes the shipped console title's performance target in its [platform overview](https://www.rockstargames.com/newswire/article/89834o94713o21/pre-load-grand-theft-auto-vi-now).

## Build a local media browser

The [library builder](../tools/media_library.py) creates one offline HTML file. It indexes existing local media and reads your own inventories. Each inventory supplies paths relative to the media root paired with it. The generated HTML contains local paths and belongs with private research outputs.

| Option | Input | Required columns |
|---|---|---|
| `--videos INDEX ROOT` | CSV | `file, archive, width, height, duration_seconds` |
| `--music INDEX ROOT` | TSV | `file, channels, rate, duration_seconds`; optional `name` |
| `--candidates INDEX ROOT` | TSV | Same audio columns; items are labeled unidentified |

Supply at least one input. From the repository root in PowerShell:

~~~powershell
python tools/media_library.py .native/library.html --videos $videoInventory $videoRoot --music $musicInventory $musicRoot
~~~

Open the generated file, search by title or source, filter by media type and select an entry. Browser codec support varies; each selection also provides a direct local-file link. Previously converted files are reused. The builder has no network dependency.
