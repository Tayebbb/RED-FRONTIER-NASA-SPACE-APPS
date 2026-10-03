# Red Frontier — Facility Visual Language (established in the Engineering Hangar)

> **STATUS: LOCKED (2026-10-03).** The Hangar passed its final polish pass, the 4-camera review, and a clean
> Godot 4.7 import. Change these rules only by a deliberate decision, not while building other rooms.

These are the rules the other rooms inherit in Phase 5. Every value below is in code:
`scripts/rf_materials.py`, `scripts/rf_kit.py` and `scripts/build_hangar.py`.

## Walls
| Zone | Height | Finish |
|---|---|---|
| Kick plate | 0–0.2 m | graphite `#2C2F34` |
| Lower band | 0.2–3.0 m | warm off-white satin panels `#E4E1DA`, 1.1 m modules, 2 rows, 14 mm reveals over a near-black backer |
| Trim rail | 3.0 m | graphite rail 0.13 m, warm LED wash on its underside |
| Upper zone | 3.13 m to ceiling | cool grey `#8C9197` panels, 2.2 m modules; deliberately darker so the eye stays at human height |

Columns: graphite, 0.56 m, on base plates with anchor bolts, with a white stencil ID (H1–H5) at 2.6 m.

## Floor
- **Main floor:** sealed epoxy concrete, light grey, roughness 0.30–0.38 (soft reflections). Saw-cut joints sit on the 4.4 m column grid.
- **Work zones:** dark rubber mats under each station.
- **Cable trenches:** flush slotted-steel grates with graphite edge angles, running from each station to its turntable port. They tie the stations physically to the rover.

## Ceiling
- **Structure:** dark profiled roof deck with graphite Warren trusses on the column grid.
- **Lighting:** linear high-bay fixtures with warm diffusers, 4 rows × 3.
- **Crane:** a graphite box-girder crane. Yellow appears only on the hook block, the end-truck stripes and the hazard bands.

## Consoles and stations
- **Console:**
  - A recessed black kick.
  - A satin light body.
  - A graphite deck tilted 18° toward the operator, with the screen set into it.
  - A front **orange LED strip**: orange-lit means interactable.
  - Two small status LEDs (cyan / amber).
- **Station bay:**
  - Two slim graphite posts and a header plate with the white station name.
  - A one-line list of the decisions it covers.
  - A small orange identity tab and a warm downlight onto the hardware.
- **Station identity:** the hardware the station configures is visible above console height.

  | Station | Hardware |
  |---|---|
  | POWER | battery cells + radiator fins |
  | SCIENCE | rack with 3 lit payload slots |
  | MOBILITY | real-size spare wheel on a stand + AutoNav screen |
  | COMMS | dish mast + signal screen |

## Screens
- **Frame:** chamfered graphite bezel with a ledge.
- **Surface:** matte anti-glare finish (no light hotspots).
- **UI:** navy `#08111F` background with a faint grid, cyan `#74B6FF` information, white values.
  - **Orange marks only the selected option and the screen's identity tab.**
- **Digital Twin:** shows line art of the actual rover model.

## Colour discipline
- **Orange `#C2501C`:**
  - The mission path.
  - Step badges 01–06.
  - Interact strips.
  - Station tabs.
  - The turntable light line.
  - Selected UI.

  It is never used on walls or structure.
- **Yellow `#E3A928`:** hazard only (door jambs, crane, stanchions, turntable safety ring).
- **Cyan:** information and status only.

## Decals
- **Typeface:** Bahnschrift (DIN family) SemiBold, white on graphite or floor.
- **Floor graphics:**
  - "RF-01 WORK BAY".
  - Numbered step badges.
  - The turntable degree ring (ticks every 5°, labels every 30°).
  - Wheel-alignment brackets taken from the real rover's contact patches.
- **Insignia:** Red Frontier mark (Mars disc + horizon + chevron) on the Digital Twin header.

## Lighting (LIGHTSET_Day_Operational) — final, measured
| Light | Purpose | Settings |
|---|---|---|
| High-bay ×12 | general, warm white | area lights, 400 W, full spread |
| Hero key | modelling light on the rover | 740 W, **60° beam** |
| Hero fill | soft cool fill | 300 W, 70° beam |
| Hero rim | separates the rover from the bright Digital Twin wall | 520 W, 85° beam |
| Station downlights | warm, from each bay header | 78 W each |
| Fixture diffusers / trim-rail LED | perimeter wall wash | emission 9 |

Hero lights use a **narrow beam (spread)** so the light stays on the rover instead of washing the walls.

Measured against the approved pre-polish render (CAM_Hangar_Entrance, 1600 px):

| Measure | Result |
|---|---|
| Upper walls | −13% / −17% |
| Lower walls | −11% |
| Rover-to-background contrast | 1.30 → 1.48 |
| Rover clipping | 1.8% of the rover area (small speculars on the white mast top) |

Rule: never raise the hero lights to gain separation. Darken the room instead; the near-white rover
paint clips fast.

AgX view transform, Medium High Contrast look. Mission Control adds LIGHTSET_Launch_Mode.

## Surface variation (polish pass)
- **Wall panels:**
  - Three hashed finish variants per zone (roughness 0.50–0.72, ±1% tone).
  - The lower protective row is a darker matte `#C9C5BD`.
- **Floor wear:** a very light wear decal (alpha ≤0.2, roughness 0.62) under each work position, and cart scuffs. Never dirt.
- **Service labels:** one atlas, one material.
  - Port IDs P1–P6, plus a LIVE CONNECTOR caution beside every port that has a trench.
  - Hatch labels and the turntable load limit.
  - ESD ground point, QC stickers, EQ cabinet IDs, crane SWL, torque tag.

## Godot 4.7 import (verified)
| Check | Result |
|---|---|
| Import | 0 errors, 0 warnings |
| Content | 215 meshes, 118,154 triangles, 74 materials, 43 textures |
| Missing normals / UVs / textures | none |
| Size | 18.5 × 10.6 × 22.5 m (true scale) |
| Emissive strengths | carried over exactly (KHR_materials_emissive_strength) |
| Transparency | 37 decal/glass materials alpha-blended |
| Gameplay markers | cameras, interaction points and room trigger arrive as nodes |

**Known requirements:**
- The rover must ship as `RF01_Rover.glb` (unquantized). Godot 4.7 cannot import `KHR_mesh_quantization` (`rover-q.glb`).
- Godot has no area lights. `RF_Hangar_lights.json` carries the light rig to rebuild in-engine.

**Performance on Intel UHD (Forward+, 1600×900):**

| Mode | FPS |
|---|---|
| With SSR + SSAO + 3 shadowed spots | 15–39 |
| Without them | 27–35 |

- **Integrated-GPU preset:** SSR off, shadows on the key light only.
- **Phase 7:** merge the per-decal materials into atlases to bring draw calls (450–720) down.
