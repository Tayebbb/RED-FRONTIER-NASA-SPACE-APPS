# Red Frontier facility: game readiness (final, 2026-10-05)

| Area | Status |
|---|---|
| Facility art / asset pipeline | **COMPLETE**: six spaces locked (Briefing, Corridor 01, Mars Intelligence, Corridor 02, Engineering Hangar, Mission Control) |
| Blender → GLB → Godot pipeline | **VERIFIED** |
| Room streaming | **IMPLEMENTED** |
| Shared material/texture system | **IMPLEMENTED** |
| Integrated-GPU optimization | **IMPLEMENTED** |
| Runtime stability | **ACCEPTABLE FOR DEVELOPMENT**, with a known Intel UHD device-loss caveat (below) |

Test machine: Intel UHD Graphics on driver 31.0.101.4032 (Dec 2022), 7.7 GB shared system RAM, Godot 4.7
Forward+, 1600×900, integrated-GPU preset. Raw reports: `docs/traversal_reports.json`.

## Results

| Check | Result |
|---|---|
| Blender validation (`validate_scene.py`) | 0 errors, 0 warnings (590 objects) |
| Godot import (`godot_sync.py`, 4 passes) | 0 errors, 0 warnings |
| Shared library (`tools/verify_shared.gd`) | 0 problems; 877 surfaces → 119 shared materials, 75 shared textures, all GPU-compressed |
| Texture deduplication | each texture loaded once; before, up to 5 uncompressed copies (one per room) |
| Room streaming | at most 3 spaces resident (current + neighbours); load/unload sequence correct in every run |
| Peak GPU memory | **2,631 MB → 1,031–1,063 MB** (Hangar neighbourhood); about 300–380 MB elsewhere |
| Peak RAM (engine static) | 122–123 MB |
| Missing / non-shared materials during traversal | 0 / 0 |
| Visual match | every approved camera within ±1.5 brightness levels of the pre-streaming screenshots (Hangar entrance +5.6) |

**Performance:** traversal Briefing → Mission Control, final configuration.

| Space | FPS (min–max, avg) | Draw calls avg / max |
|---|---|---|
| Briefing | 20–45, avg 33 | 67 / 109 |
| Corridor 01 | 31–52, avg 41 | 109 / 120 |
| Mars Intelligence | 24–46, avg 31 | 76 / 127 |
| Corridor 02 | 14–48, avg 36 | 387 / 1,109 |
| Hangar | 11–21, avg 17 | 260 / 1,260 |
| Mission Control | 19–30, avg 24 | 85 / 196 |

Whole walk: average 23–25 fps. Load hitch: one frame of 70–145 ms at each room transition, the worst being the
Hangar arriving (its VoxelGI upload).

## How it works

- **Exports:**
  - Room GLBs carry geometry and material names only.
  - `RF_MaterialLibrary.glb` carries every material and texture once.
  - `godot_sync.py` builds `godot/shared/` and maps each room's materials to it.
- **Streaming** (`facility/facility_streamer.gd`):
  - Background-thread loading of each room with its rover and GI cache.
  - Staged entry and exit, a few nodes per frame, with GI and probe in their own frames.
  - Occluders on every solid wall.
  - Door impostors keep the two forward sightlines into rooms that aren't resident yet.
- **Lighting:**

  | Space | GI | Lights |
  |---|---|---|
  | Hangar | VoxelGI 256, unchanged | dynamic |
  | Mission Control | VoxelGI 64 | dynamic (Launch Mode) |
  | Mars Intelligence, Briefing | VoxelGI 64 | lights baked static |
  | Corridors | none | line light |

  - Room light scales (Briefing ×1.6, Mars Intelligence ×1.6, Mission Control ×1.3) replace light that leaked
    through walls when every room was resident, so the approved look is kept.
  - The reflection atlas is capped at 8 slots: a single probe was allocating 556 MB under Godot's default of 64.
- **Presets** (`facility/quality_presets.gd`):
  - High and Laptop are unchanged.
  - Integrated GPU is chosen automatically on an integrated GPU. It turns off SSR and SSAO, restrains bloom, keeps
    one shadowed light on a 2048 atlas, and uses very-low soft-shadow filtering.
  - Global render settings are applied once, never per room load.
- **Visual fixes in this pass (the two permitted):**
  - Mars Intelligence ellipses: 24 mm wide, emission 2.8.
  - Mission Control launch console: key light 85 W aimed at the console front, and the screen material made
    emit-only.

## Known runtime caveat: open issue

**Symptom:** occasional Vulkan device loss. Godot reports "Vulkan device was lost" (driver timeout/reset), the last
breadcrumb is `BLIT_PASS`, and the process exits.

**When:**
- Only seen during repeated automated traversal (`Godot --path godot -- traverse`) on the machine above.
- Final configuration: **1 crash in 10 runs** (40 s in, standing in the Hangar, no streaming event nearby).
- With the shader warm-up enabled: 5 crashes in about 27 runs.
- Seen at start-up, at room loads and in steady state.
- Asset imports, geometry and materials are unaffected, and the 120-step streaming stress tool
  (`tools/stream_stress.gd`) did not reproduce it.

**Tried, without fully resolving it:**
- Half-resolution GI off.
- Global render settings no longer re-applied on every room load.
- Shader/material warm-up made opt-in (`-- warmup`). Its effect on the crash rate was not measurable.
- Ruled out: creating or freeing GI volumes, and impostors (stress-tested without a crash).

**Next step:** update the Intel graphics driver (the installed one is from Dec 2022), then re-run 10 traversals.
If it persists, test on a second GPU, and try Godot's Compatibility renderer or D3D12 for Intel UHD.

## Current integration status

The Engineering Hangar already contains the canonical playable rover through the generated `RF_Hangar_lights.json` manifest:

- Asset: `RF01_Rover.glb`
- Position: `(0.0, 0.12, -42.7424)` in Godot coordinates
- Rotation: approximately `-28` degrees around Y
- Lifecycle: loaded and unloaded with the Hangar by `facility_streamer.gd`

The detailed Perseverance build under `art/` is now the canonical rover source and is exported through the existing `RF01_Rover.glb` runtime path. See `docs/ROVER_INTEGRATION.md` for the source and placement contract.

## Lighting caches on a fresh checkout

The VoxelGI caches (`godot/assets/*_voxelgi.res`) are gitignored, and `scripts/godot_sync.py` deletes them on every
sync so they never go stale. The first windowed visit to each room bakes its cache on the main thread and saves it,
which is a one-time pause, longest in the Hangar. The Hangar cache is about 35 MB; the other three are about 1.5 MB each.
Headless runs skip GI.

For a release, sync, then bake all four caches in a windowed run, then export. An exported build cannot write `res://`,
so the caches must be inside the export (see [system design §11](SYSTEM_DESIGN.md#11-reliability)).

## Next recommended work

The gameplay base (traversal, prompts, mission state, landing site, and rover configuration) is now built. Remaining work
follows the [system design implementation order](SYSTEM_DESIGN.md#13-implementation-order). The facility-specific items are:

1. A Windows export preset that ships the lighting caches, tested on a clean machine.
2. A driver update and a re-test of the caveat above; also try `--rendering-driver d3d12`.
3. Hangar: compare VoxelGI 128 or 64 against the approved cameras, and merge per-decal materials into atlases. It's the
   slowest room (11–21 fps) and the main load-hitch source. A smaller GI grid also shrinks its cache.
4. Measure the same traversal on a dedicated GPU (only Intel UHD has been measured).
