# GTA VI on Xbox | From game data to a PC frame

**Research question.** What would have to work for the Xbox Series version of Grand Theft Auto VI (GTA 6) to produce a playable frame on Windows? Rockstar lists Xbox Series X|S as a platform for the game. This independent Project NATIVE guide uses public platform documentation to explain the dependencies and provides a reproducible first experiment using an executable already on the reader's PC. It makes no claim that GTA VI has run on Windows through this project. [Rockstar's GTA VI product page](https://www.rockstargames.com/VI)

An Xbox Series game needs executable code, compatible platform services, game content and a graphics path for its target GPU. This walkthrough shows how those parts interact and how to investigate one of them on your own computer. The accompanying Python tool reads a Portable Executable (PE) image without launching it. The diagrams describe a typical GDK title at the level of public interfaces. Engine internals vary by title.

## 1. Inspect an executable already on your machine

From the repository root on Windows, run the following in PowerShell with Python 3 installed. The command prints JSON to the terminal. It opens the file read-only and makes no network requests.

~~~powershell
$program = Join-Path $env:WINDIR 'System32\notepad.exe'
python tools/inspect_pe.py $program
~~~

Read the fields in this order:

| Field | What to learn from it |
|---|---|
| `machine`, `pe_format` | The CPU architecture and optional-header layout determine how to interpret the image. An x64 result alone cannot establish Xbox or desktop compatibility. |
| `image_kind`, `entry_point_rva` | The DLL flag distinguishes a library image. The entry point is an address relative to the image base. Zero means no entry point is declared. |
| `subsystem_id`, `section_count` | The subsystem is a numeric PE classification. Sections map file bytes into the loaded image. |
| `ordinary_import_providers` | These are distinct module names referenced by the ordinary import descriptors. API-set names may resolve through the OS. The list says nothing about which function executes in a given scene. |
| `delay_import_directory_declared` | A true result flags additional metadata for follow-up. The tool does not enumerate delay-loaded names, runtime lookups or transitive dependencies. |

**Check it independently.** In a Visual Studio Developer PowerShell, run `dumpbin /headers $program` and `dumpbin /imports $program`. Compare machine type, the entry RVA, section count and ordinary provider names. Windows versions may ship different binaries. To inspect your own file, replace only the path. An error and exit code 1 mean the file could not be read using this parser's supported layout. It expects standard PE32/PE32+ images with a contiguous, file-backed ordinary import directory. [PE format specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format) · [DUMPBIN imports](https://learn.microsoft.com/en-us/cpp/build/reference/imports-dumpbin?view=msvc-170)

## 2. Follow Xbox startup

~~~mermaid
flowchart LR
    A["Installed package"] --> B["Game configuration"]
    B --> C["Target and executable selection"]
    C --> D["Platform loader"]
    E["OS and runtime libraries"] --> D
    D --> F["Game initialization"]
    F --> G["Engine requests content"]
    F --> H["Engine initializes graphics and input"]
~~~

The game configuration identifies eligible executables and target device families. The platform handles deployment and launch. The loader maps the program and resolves dependencies according to the target environment. Only then can the engine initialize its own allocator, thread scheduler, input and renderer. That distinction explains why changing a manifest entry or copying DLLs by name cannot establish a port. Two platforms can share a CPU instruction set while using different library contracts, graphics interfaces and packaging rules. [MicrosoftGame.config overview](https://learn.microsoft.com/en-us/gaming/gdk/docs/features/common/game-config/microsoftgameconfig-overview) · [Executable selection](https://learn.microsoft.com/en-us/gaming/gdk/docs/reference/system/microsoftgameconfig/elements/microsoftgameconfig-element-executable?view=gdk-2604)

## 3. Trace a resource from disk to the engine

~~~mermaid
flowchart LR
    A["Engine requests resource ID"] --> B["Package or archive index"]
    B --> C["Stored byte range"]
    C --> D["Read through authorized storage interface"]
    D --> E["Decode using the recorded format"]
    E --> F["Validate dimensions, counts and references"]
    F --> G["CPU object or GPU upload"]
~~~

1. Establish which layer owns the identifier. An installed package can contain an engine archive with a second index.
2. Validate each offset and length against the containing file. Record stored and decoded lengths separately.
3. Determine the transform from documented metadata. Compression needs the corresponding codec. Protected storage needs the supported runtime, entitlement or publisher-provided tooling. A failed decompression attempt establishes neither encryption nor its algorithm.
4. Validate the decoded object using its own structure. For a texture, check dimensions, pixel format, mip sizes and expected byte layout. For audio, check the stream table, channels and timing. For a mission catalog, distinguish an identifier from executable behavior. A file span, a model, and a placed instance are three different counting units.
5. Test a second resource using the same rule. Log where the process stopped if naming, decoding or runtime ownership remains unresolved. [Microsoft packaging during development](https://learn.microsoft.com/en-us/gaming/gdk/docs/features/common/packaging/packaging-packaging-during-development?view=gdk-2604)

## 4. Follow one rendered frame

~~~mermaid
flowchart LR
    I["Controller input"] --> S["Simulation step on CPU"]
    S --> L["Draw or dispatch commands"]
    A["Mesh and texture uploads"] --> R["Bound GPU resources"]
    R --> G["GPU executes commands"]
    P["Shaders and pipeline state"] --> G
    L --> Q["Command queue"]
    Q --> G
    G --> T["Render target"]
    T --> V["Present to display"]
~~~

The simulation chooses what happens this frame. The renderer supplies commands, resources, shaders and pipeline state. A root signature describes resource bindings. The CPU and GPU use synchronization to keep storage alive until commands finish. A PC port can reach a window while producing an empty frame if any of these contracts disagree. Test an offscreen clear and readback first, then a compute result, then a textured draw. Inspect the first incorrect draw in a desktop GPU capture before adding more scene content. [Direct3D 12 pipelines and shaders](https://learn.microsoft.com/windows/win32/direct3d12/pipelines-and-shaders-with-directx-12) · [Root signatures](https://learn.microsoft.com/en-us/windows/win32/direct3d12/root-signatures-overview) · [PIX GPU captures](https://learn.microsoft.com/en-us/windows/pix/gpu-captures/gpu-captures-overview)

## 5. Choose the porting route

| Available material | First useful step | Success you can demonstrate |
|---|---|---|
| Authorized source and matching content | Build the Windows GDK desktop target. Pair each platform-specific dependency with a supported implementation. | The desktop build initializes and opens a known resource. |
| A matching Windows executable | Confirm provenance, content version, service requirements and supported deployment. | The intended desktop program starts with matching content. |
| An Xbox executable alone | Inspect its architecture and imports. Establish whether an authorized host supports the binary, graphics and service contracts. | The original program reaches initialization on that host. Static inspection alone cannot establish that such a host exists. |
| Content alone | Inventory and validate readable structures through authorized interfaces. Identify what consumes them and which program or runtime is missing. | A resource can be interpreted and verified. A playable title still requires executable game behavior. |

For a source port, bring up one subsystem at a time. Each step has a small test that can isolate a failure. [Microsoft GDK desktop project configuration](https://learn.microsoft.com/en-us/gaming/gdk/docs/tools/tools-pc/visualstudio/gr-vs-templates?view=gdk-2604)

| Order | Subsystem | First repeatable check |
|---|---|---|
| 1 | CPU runtime, memory and jobs | Start and stop a fixed job graph. Check alignment, lifetime and deterministic output. |
| 2 | Files, mounts and streaming | Read one known object, evict it and reload it. Compare decoded size and content identity. |
| 3 | GPU, shaders and pipeline state | Compare compute output and rendered pixels with a known reference. |
| 4 | World, animation and physics | Load one scene, bind one skeleton, move one actor and cross a streaming boundary. |
| 5 | Audio and video | Verify timing, channel routing, pause, seek and scene transitions. |
| 6 | Input, saves and platform services | Disconnect and reconnect a controller, round-trip a save and exercise offline errors. |
| 7 | Gameplay and performance | Complete a repeatable interaction, then measure frame times over the same route with recorded resolution and settings. |

At 30 FPS a frame has about 33.33 ms. Report the percentage of frames above budget alongside average FPS and p95/p99 frame time. Distinguish a desktop sample, the first correct game frame and a controllable scene in every progress report. Each demonstrates a different piece of the port.
