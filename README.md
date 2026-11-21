# GTA VI Port Research

A field guide and read-only Python toolkit for researchers investigating Grand Theft Auto VI on Xbox Series X|S. Use it to inventory a local package, inspect an executable's dependencies, and test where compressed archive records begin and end. The [data-type report](research/data-types.md) maps those records to research questions about the world, characters, missions, and media.

## Run your first inspection

From the repository root, with Python 3.9 or later:

```powershell
python tools/inventory.py tools --sha256
```

This reads the tools in your checkout and prints one JSON object per file with `path`, `bytes`, and `sha256`. Replace `tools` with the path to your own local package to produce the same inventory for that directory. Omit `--sha256` for a quick listing that reads file metadata. [Inventory source](tools/inventory.py)

## Data map at a glance

| If you are looking at… | What to trace | Open this file |
|---|---|---|
| Package configuration (`.xml`, `.config`) | Target device family → declared executable → file actually present. Record an absent entry before investigating launch. | [Package, code and storage](research/data-types.md#package-code-and-storage) |
| Executables and libraries (`.exe`, `.dll`) | PE header → machine type and entry RVA → ordinary import providers. A provider name narrows the dependency search; call behavior still needs a runtime test. | [PE inspector](tools/inspect_pe.py) · [Xbox launch diagram](research/xbox-to-pc.md#2-follow-xbox-startup) |
| Archives and streaming containers (`.rpf`, `.ttpf`) | Directory row → predicted stored range → independently verified end → resource type. For a streaming index, check each boundary against the containing file before assigning asset names. | [Compressed-stream reader](fixture/rpf.py) · [Directory probe](fixture/directory_probe.py) · [Storage research status](research/data-types.md#package-code-and-storage) |
| World, interiors, props and vehicles | Placement → archetype → drawable → material and texture. Count placements and distinct models separately: a street can contain many instances of one prop. | [World and movement report](research/data-types.md#rendering-world-and-movement) |
| Shaders and pipeline states | Pipeline → referenced shader → bindings → draw or compute output. Several pipelines can reuse one shader. | [Rendering report](research/data-types.md#rendering-world-and-movement) · [Rendered-frame diagram](research/xbox-to-pc.md#4-follow-one-rendered-frame) |
| Characters, clothing and animation | Spawn or schedule → character identity → model and rig → wearable slot or animation clip. A schedule ID alone cannot identify a unique NPC. | [Character and clothing report](research/data-types.md#characters-stories-and-media) · [Animation](research/data-types.md#rendering-world-and-movement) |
| Missions, scripts and choices | Replay ID → typed reference → executable event → observed state change. A branch needs a condition and distinct reachable outcomes. | [Story and script report](research/data-types.md#characters-stories-and-media) |
| Movies, music and dialogue | Video container → frame index and audio tracks; audio event → bank → stream. A title or scene assignment needs an independent link to that media. | [Media inspection workflow](research/handbook.md#a-repeatable-media-check) · [Media research status](research/data-types.md#characters-stories-and-media) |

The linked Python files are runnable tools. The reports document methods, public GTA V references, what Project NATIVE has demonstrated, and the evidence still needed. Build-specific inventories and extracted media stay local.

## Inspect a Windows executable

```powershell
python tools/inspect_pe.py "$env:WINDIR\System32\notepad.exe"
```

This reads the installed binary without launching it. Look at `machine`, `entry_point_rva`, and `ordinary_import_providers`. A declared delay-import directory is flagged separately. Compare the result with Microsoft's DUMPBIN using the [executable walkthrough](research/xbox-to-pc.md#1-inspect-an-executable-already-on-your-machine).

## Verify a compressed-stream boundary

Try the checks immediately with `python -m unittest fixture.test_rpf fixture.test_directory_probe -v`. On your own archive, start with an offset predicted by a directory row or supplied by the packer. The probes take an offset as input; they do not discover the archive's directory.

With a local archive and a candidate **16-byte-aligned stored offset**, choose the probe that matches your hypothesis. Substitute your own file and offsets.

```text
python -m fixture.rpf FILE OFFSET
python -m fixture.rpf FILE OFFSET --paged
python -m fixture.directory_probe FILE TABLE_START TABLE_END --base 0 --unit 1 --stride 8
```

- **Adjacent streams:** the first command checks two zlib checksums and their alignment padding, then prints both half-open stored ranges.
- **Paged resource:** the second follows full 64 KiB decoded pages through a short final page. It reports stored span, decoded size, and page count.
- **Directory hypothesis:** the third reads candidate offset/length pairs from consecutive rows before inspecting their payloads. Both predictions must agree with independently measured stream ends. The base, unit, and stride shown are hypotheses to test against the candidate layout.

A passing checksum identifies an intact stream. To identify the asset inside it, parse the decoded structure and cross-check an independent name, index, or typed reference. [Stream tests](fixture/test_rpf.py) · [Directory tests](fixture/test_directory_probe.py)

## What runs on PC today?

The public tools perform static inspection. The desktop GDK sample has rendered a Direct3D 12 frame; a GTA VI gameplay frame on Windows remains unverified. Start with the [desktop build and capture](demo/gdk/README.md) for the graphics result, the [research handbook](research/handbook.md) for the full tool directory, or the [executable intake playbook](research/first-72-hours.md) for the porting milestones. Run `python harness.py` to verify the repository tests.

Project NATIVE is independent of Rockstar Games, Take-Two Interactive, and Microsoft. Contributions should contain original tools, diagrams, or links to public documentation. Keep game files, extracted assets, keys, download links, and private inventories off GitHub.
