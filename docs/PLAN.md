# Mission: Red Frontier — Facility Implementation Plan

Source of truth for gameplay: the Red Frontier rover design brief artifact (Hangar station table,
"if a part never matters on Mars, cut it from the Hangar").

## 1. Implementation plan (phases)

| Phase | Output | Status |
|---|---|---|
| 1 Inspection | assessment, this plan | done |
| 2 Greybox | `blender/RF_Facility_Blockout.blend`, `renders/blockout/` | done, awaiting review |
| 3 Modular kit | `build_modular_kit.py` → `blender/RF_Kit.blend`; greybox walls swapped for kit pieces | next |
| 4 Hangar near-final | materials, trims, lighting, decals, screen style, prop language — established in the Hangar only | |
| 5 Propagate | same system on Briefing, Mars Intel, Mission Control, corridors | |
| 6 Polish | decals, cables, signs, floor detail, screen placeholders, subtle wear | |
| 7 Game readiness | `validate_scene.py` + `export_gltf.py`, test import in Godot 4.7 | |

## 2. Folder structure (`D:\RedFrontier`)

```
scripts/      rf_lib.py (helpers) + one build script per phase; all rebuild from empty
blender/      RF_Facility_Blockout.blend, later RF_Kit.blend, RF_Facility.blend
assets/rover/ RF01_Rover.blend (LOCKED, linked) + source/rover-q.glb
renders/      <phase>/CAM_*.png
export/godot/ per-room .glb + kit .glb
docs/         this plan
textures/     decal sheets, trim sheets, screen placeholders (Phase 4+)
```

## 3. Collection structure

```
RF_FACILITY
  00_REFERENCE        linked rover instance, 1.75 m scale figures
  01_ARCH             Briefing / MarsIntelligence / Hangar / MissionControl / Corridor / Ceilings
  02_PROPS
  03_HERO             RoverPlatform, DigitalTwinDisplay, MarsTable, TerrainMapWall, LandingSites, MissionControlWall, LaunchConsole
  04_LIGHTS           LIGHTSET_Day_Operational, LIGHTSET_Launch_Mode (Phase 4)
  05_CAMERAS
  06_DECALS           mission path, zones, signs, hazard strips
  07_UI_PLACEHOLDERS  screen content planes and labels
  08_GAMEPLAY_MARKERS PLAYER_Start, TRIG_Room_*, INT_* interaction points
  99_DEBUG            plan-view labels
```
Both lists in the brief merged into one numbered tree. Objects tagged `rf_overhead`
(ceilings, trusses, gantry, light fixtures) and `rf_cutaway_hide` are toggled by the renderer.

## 4. Environment layout (metres, interior, +Y = north)

| Room | Footprint x / y | Height | Doors |
|---|---|---|---|
| Briefing | -4..4 / 0..10 | 4.0 | S entry (double), N exit at x 2.75 (orange-framed) |
| Corridor 01 | 1.25..4.25 / 10.25..15.75 | 3.2 | open ends |
| Mars Intelligence | -5..5 / 16..28 | 4.5 | S at x 2.75, N exit at x 0 |
| Corridor 02 | -1.5..1.5 / 28.25..32.75 | 3.2 | open ends, on the rover axis |
| Engineering Hangar | -9..9 / 33..55 | 10.0 | S entry 2.6 m on axis; W hangar door 8x7 m; E glass wall 8 m + door to MC |
| Mission Control | 9.25..24.25 / 41.75..53.75 | 5.0 | W = shared hangar wall (glass looks onto the rover) |

Walking: entry → launch console is about 85 m including the hangar loop; no stretch is longer
than 6 m without a screen, sign or hero object in view.

### Gameplay placement of every artifact decision (locked after the Phase 2 review)

| Where | Decision | Why there |
|---|---|---|
| Mars Intelligence | **Landing system** (standard / precision), then the **landing site** | precision landing decides which sites are reachable, so it has to come before site choice |
| Hangar entry | **Mission Configuration**: launch vehicle → payload limit (900 / 1,100 kg) and budget ($150M / $250M) | it sets the mass constraint for every station |
| Hangar SE | **SCIENCE**: 3 instrument slots + mission style | |
| Hangar SW | **POWER**: power + battery + thermal | |
| Hangar NW | **MOBILITY**: wheels + computer/AutoNav | |
| Hangar NE | **COMMS**: communications only | |
| Hangar N wall | **Digital Twin**: run the prediction, then iterate freely, then ACCEPT BUILD | |
| Mission Control | confirms the chosen launch vehicle; **ACCEPT RISK & LAUNCH** | it's only a confirmation, no new decision |

- **Guided first pass** follows the artifact's design order: Config → Science → Power → Mobility → Comms → Digital Twin.
- **Why the corners changed:** the stations moved corners so that this order makes one clean loop on the floor (SE → SW → NW → NE → north wall).
- **After the Digital Twin** the player can go back to any station.

### Hangar work bay
- **Turntable:** Ø6.5 m with a 12 cm lip, on a flush steel bed.
- **On the turntable:**
  - A recessed orange light ring.
  - Three flush maintenance hatches.
  - Six power/data ports.
  - An amber safety ring.
- **Wheel alignment brackets:** generated from the real rover's six wheel contact patches.
- **The rover:**
  - It's linked, never scaled, and rotated −28° for a 3/4 view from the entry.
  - Its footprint centre is measured exactly onto the turntable centre: the farthest corner sits 2.21 m out, inside the 3.25 m radius.
- **Digital Twin wall:** 8×4 m, on the room's axis at the north wall.

**Rule: walking is never content.** The footprint is final. No side rooms, and no longer corridors.

## 5. Asset list (hero)
HERO_RoverPlatform · HERO_DigitalTwinDisplay · HERO_MarsTable · HERO_TerrainMapWall ·
HERO_LandingSite A/B/C · HERO_BriefingDisplay · HERO_MissionControlWall · HERO_LaunchConsole

## 6. Modular kit (Phase 3)
Architecture: MOD_Wall_2m/4m/8m, MOD_Wall_Window, MOD_GlassPanel, MOD_Corner_Inner/Outer,
MOD_Door_Single/Double, MOD_HangarDoor, MOD_Column, MOD_Beam, MOD_CeilingPanel, MOD_FloorPanel,
MOD_FloorGrate, MOD_Railing, MOD_Stairs_Short, MOD_Platform.
Technical: ControlConsole, StandingTerminal, WallScreen, LargeDisplay, EquipmentCabinet,
ServerRack, ToolCart, CableReel, Crate, Vent, Pipe, CableTray, HangingLight, CeilingLight,
WarningBeacon, SafetyBarrier. Furniture: Desk, Chair, MeetingTable, Workbench.
Rules: 2 m grid and 0.25 m wall thickness, origin at the bottom-centre, 1 cm bevel + weighted
normals, shared materials, linked duplicates for repeats (become instances in Godot).

## 7. Modeling priority
1. Hangar: platform, Digital Twin wall, stations, gantry, wall kit
2. Mission Control front wall + launch console
3. Mars table + terrain wall
4. Briefing display
5. Corridors (kit only)

## 8. Lighting strategy
- **Hangar:** large overhead area lights (key), soft wall bounce, a tight hero light cone on the
  rover, orange platform ring as the accent, and cyan only from the Digital Twin.
- **Mission Control:** dimmer and slightly warmer, with the screens as the main light.
- **Two light sets** as collections:
  - LIGHTSET_Day_Operational.
  - LIGHTSET_Launch_Mode: ambient −30%, screens up, amber beacons.
- **Godot:** bake-friendly, so the lights are mirrored as named empties for re-creation in Godot.

## 9. Material strategy
- **One shared library**, `build_materials.py`: MAT_Wall_White, MAT_Wall_Grey,
  MAT_Structural_Graphite, MAT_Structural_Navy, MAT_Floor_Rubber, MAT_Floor_Metal,
  MAT_Brushed_Metal, MAT_Painted_Metal, MAT_Glass, MAT_Screen_Dark, MAT_Screen_Emissive,
  MAT_Orange_Accent, MAT_Warning_Yellow, MAT_Black_Rubber, MAT_Ceiling_White.
- **Shading:** Principled BSDF only, satin roughness (0.45–0.7), and no node tricks that the
  glTF exporter drops. Detail comes from trim sheets and decals.
- **Colour budget:** 70% neutral light / 20% dark structure / ≤10% orange and functional accents.
- **Orange signals meaning:**
  - Orange floor line = mission path.
  - Orange-lit console = interactable.
  - Cyan = information.
  - Red = warning only.

## 10. Scripting strategy
- **Library:** `rf_lib.py` holds all helpers: boxes, panels, walls with openings, rooms,
  materials, text, floor markings, cameras, lights, markers.
- **One script per phase.** Each starts from an empty file, so reruns are safe.
- **Rover:** never imported into environment files, only linked.
- **Previews:** `render_previews.py <tag>` renders every CAM_* view for review.
- **Validation:** `validate_scene.py` checks names, transforms, scale, material slots,
  duplicates, hidden objects and modifiers before `export_gltf.py`.

```
blender -b --factory-startup --python scripts/build_rover_asset.py
blender -b --factory-startup --python scripts/build_blockout.py
blender -b blender/RF_Facility_Blockout.blend --python scripts/render_previews.py -- blockout
```
