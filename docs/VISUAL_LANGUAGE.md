# Red Frontier — Facility Visual Language (established in the Engineering Hangar)

> **ALL SIX SPACES APPROVED AND LOCKED (2026-10-05):** Briefing, Corridor 01, Mars Intelligence, Corridor 02,
> Engineering Hangar, Mission Control. Facility phase COMPLETE (`docs/GAME_READINESS.md`). No redesign or new
> visual content.

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
- The rover must ship as `RF01_Rover.glb` (unquantized). Godot 4.7 cannot import `KHR_mesh_quantization`; the canonical source is the detailed Perseverance export in `art/`.
- Godot has no area lights. `RF_Hangar_lights.json` carries the light rig to rebuild in-engine.

**Performance on Intel UHD (Forward+, 1600×900):**

| Mode | FPS |
|---|---|
| With SSR + SSAO + 3 shadowed spots | 15–39 |
| Without them | 27–35 |

- **Integrated-GPU preset:** SSR off, shadows on the key light only.
- **Phase 7:** merge the per-decal materials into atlases to bring draw calls (450–720) down.

## Changes to the locked Hangar (2026-10-05, deliberate)
Two bugs found while building Mission Control. Both are fixed in code and re-verified (renders, re-export,
clean Godot import):

| Fix | Before | After |
|---|---|---|
| Cladding backer cut out at openings (`rf_kit.cladding`) | The near-black backer sheet covered every opening from inside: the glass wall to Mission Control, the Mission Control door, the south entry and the hangar door all read as black panels and blocked walking | Openings are open. The glass shows the lit control room, and the sectional hangar door now reads as a door |
| Column E4 left out (`build_hangar.build_structure`) | The 0.56 m column at y 52.8 stood in the Mission Control doorway (y 51.7–53.5), and the mission path ran through it | The door is clear and framed by its portal, the same treatment as the hangar-door span |

Nothing else in the Hangar changed: 118,154 → 118,116 triangles, with the same materials and lights.

# Mission Control (Phase 5): how the rules carry over
Built by `scripts/build_mission_control.py`. The room confirms upstream decisions and holds one action:
ACCEPT RISK & LAUNCH.

| Element | Hangar rule applied | Mission Control specific |
|---|---|---|
| Walls N / S / glass side | Same cladding: kick plate, warm-white lower band, trim rail with LED wash at 3.0 m, cool-grey upper zone | Grey panels close the band above the glass head; graphite reveal frames the glass |
| Front (east) wall | Same panel module | Rendered in graphite (`MAT_Wall_Media` ×3 variants) with one dark recess (y ±5.5 m, z 1.3–4.35 m) holding the displays, so the screens own the room |
| Floor | Path and orange discipline unchanged | Raised access floor, 0.6 m tiles (`T_Floor_Access_*`), mid-dark grey: the dim room |
| Ceiling | Dark | Flat acoustic `#4A4D52`, suspended linear fixtures over the desk runs (`MAT_Light_Diffuser_Dim`, emission 1.6) |
| Desks | Satin pedestals, graphite top, recessed kick | **No orange**: operator desks are not interactable. Two 16:9 monitors per position, all 16 sharing one atlas material (`T_Screen_MC_OpsAtlas`) |
| Launch console | Console language: kick, satin body, 18° graphite deck, orange LED strip | The only interactable in the room: orange strip, orange LED floor ring Ø2.5 m (stand here), orange button under a yellow/black hazard guard |
| Screens | Navy UI, cyan info, orange = selected / identity | Main wall 7.2 × 2.7 m (8:3) + GO/NO-GO and Readiness panels 1.3 × 2.7 m; Build sheet and Landing on the side walls. Each repeats a choice made upstream: vehicle, site, build |
| Labels | Service atlas, white Bahnschrift | Operator position plates (FLIGHT … MOBILITY) and EQ-11/12 appended to the same atlas; earlier cells unchanged |
| Hazard yellow | Hazard only | Wall beacons and the launch-button guard |

## Lighting: Mission Control
| Set | Lights | Materials |
|---|---|---|
| LIGHTSET_Day_Operational | 2 linear area lights 230 W over the desk runs, back line 120 W, launch key 85 W (45° spread) aimed at the console front, not its screen; warm `#FFE6CC` | Main wall 1.8, side panels 1.5, wall screens 1.4, monitors 1.2, fixtures 1.6 |
| LIGHTSET_Launch_Mode | Same rig at 70 % (key at 125 %), plus 2 amber beacon point lights | Screens ×1.35, fixtures 1.1, beacon lens 0.05 → 9 |

- **Switching:** `rf_lightsets.apply('Launch_Mode')` in Blender, `RF_LIGHTSET=Launch_Mode` for `render_cycles.py`,
  and **L** in the Godot viewer. `RF_MissionControl_lights.json` carries each light's set plus the per-set
  emission table.
- **Godot:** the Mission Control spots use `light_specular 0.15`, because a round spot highlight on the glass
  would read wrong for a linear fixture.
- **Performance** (Intel UHD, 1600×900, default preset):
  - Mission Control: 19–25 fps, 33–150 draw calls (873 when looking through the glass at the Hangar).
  - Loading Mission Control costs the Hangar about 1 fps.

# Mars Intelligence (Phase 5): how the rules carry over
Built by `scripts/build_mars_intelligence.py`. It holds two decisions in the order the brief locks:
LANDING SYSTEM at the console by the entrance, then LANDING SITE at the table.

| Element | Hangar rule applied | Mars Intelligence specific |
|---|---|---|
| Walls N / S / E | Same cladding as the Hangar | Site screens stay below the trim rail (top 2.86 m) |
| West wall | — | **Rule from Mission Control, now general:** a wall that carries a hero display becomes a graphite media wall with one dark recess |
| Floor | Sealed epoxy, 4.4 m joints | Joints aligned to the table edges |
| Ceiling | Dark acoustic, as in Mission Control | Suspended graphite **light halo** (4.6 × 3.0 m) frames the table and carries its light; linear lines over the aisles |
| Mars table (hero) | Satin body, recessed kick, graphite rim | Physical relief of Jezero: 161 × 97 vertex mesh displaced from `T_MarsTable_Height` (6 cm relief, about ×2 vertical exaggeration at 1 m = 22.5 km); crater, inflow channel, delta, boulder field at C |
| Landing ellipses + pins | Cyan = information | Ellipses follow the relief (precision size, 7.7 × 6.6 km). **A cyan, B orange (the selected site), C amber (needs precision landing)** — the same colours on the table, map wall, site screens and the Mission Control landing screen. 24 mm lines at emission 2.8 (readable across the room): lines, not status dots |
| Interactables | Orange-lit = interactable | Landing-system console strip, and the three site-pick strips on the table edge (one per site, at the INT_LandingSite markers) |
| Screens | Navy UI | Map wall 8.6 × 2.8 m (layer tabs, legend, sites); sites A/B/C along the walking path in the order the player meets them; atmosphere and season above the analyst desks (one atlas material); analyst monitors (one atlas material) |
| Desks | Mission Control `operator_desk`, single position | Four analyst desks with chairs |

All terrain imagery comes from one heightmap (`gen_textures.mars_height`), so the table, the map wall and
the site thumbnails always agree.

**Lighting** (Day_Operational only): table halo 190 W over 3.8 × 2.2 m, linear lines 170 W (path side) and
110 W (map side), console key 90 W at a 50° spread. Mars Intelligence has no Launch Mode.

**Godot:**
- **Occlusion culling is now on** for the whole facility. Every solid wall segment becomes a box occluder, so
  rooms behind walls are not drawn.
- Mars Intelligence draws 280–480 calls (800–950 before occlusion culling) and runs at 18–21 fps on Intel UHD.
- From Mars Intelligence the rover is visible through the north door, past Corridor 02: the intended sightline to the next room.

# Briefing (Phase 5): how the rules carry over
> **STATUS: APPROVED AND LOCKED (2026-10-05).** No more props, screens, furniture or lighting changes.

Built by `scripts/build_briefing.py`. This is the first room: the question, the constraints and the route.
No decision is made here.

| Element | Rule applied | Briefing specific |
|---|---|---|
| North wall | Hero-display wall = graphite media wall | Display 4.8 × 2.25 m (0.8 m narrower than the greybox, which ran into the exit portal); MISSION BRIEFING title on the dark band above |
| Exit to Mars Intelligence | Orange = the mission path | Graphite portal with an **orange LED reveal**, MARS INTELLIGENCE above it. The only orange on architecture anywhere, and it marks the way on |
| Program identity | White type only on graphite or the floor | E wall program board: graphite panel, insignia, RED FRONTIER PROGRAM, with its own 70 W wash |
| Mission table | Satin body, graphite top, orange strip = interactable | Standing height (0.94 m), flat display top: question, decisions, the rule, PROCEED TO MARS INTELLIGENCE |
| Screens | Navy UI, orange = selected / current | Main display: Mars globe with the Jezero target, objective, constraints, and the 4-step route with BRIEFING current. W wall: WHY JEZERO + TIMELINE (one atlas material) |
| Seats | Mission Control task chair | Six chairs in the greybox arc, each turned to face the display; central aisle on the path |

**Numbers that recur later:** payload 900 / 1,100 kg and budget $150M / $250M (Hangar Mission
Configuration), Jezero and the landing decisions (Mars Intelligence), the four-room route (every room).

**Lighting:** two linear lines at 130 W; the table light hits the table's front at 80 W (not the screen);
board wash 70 W.

**Godot:** 25–29 fps, 58–241 draw calls on Intel UHD.

**Key-light rule (from the Mission Control and Briefing reviews):** never aim a key light straight at a
horizontal screen. Screen materials take light as well as emitting it, so a direct key washes the UI out.
Light the console or table body instead.

# Corridors (Phase 5): connective, not hero
Built by `scripts/build_corridors.py`. The corridors use **no new kit pieces**: cladding, display frames, portals,
the linear light, existing decals, and one small texture cropped from the Mars table image.

| | Corridor 01: Briefing → Mars Intelligence | Corridor 02: Mars Intelligence → Engineering Hangar |
|---|---|---|
| Purpose | Mission context → planetary analysis | Anticipation before the rover reveal |
| Walls | Standard warm cladding both sides | Graphite (media) cladding both sides: dark framing, so the lit Hangar opens up ahead |
| Graphic | One Mars map strip (2.4 × 0.5 m), surface-mounted on the W panels | One RF-01 line-art graphic (1.8 × 0.9 m, the existing Digital Twin texture) set into a W-wall recess |
| Signage | MARS INTELLIGENCE over the far door (the single directional sign) | ENGINEERING HANGAR + RF-01 WORK BAY on the E wall, beside the route, never over it |
| Threshold | Graphite portals on the corridor side of both doors | Portal frame only at the Hangar door: nothing on the centre line or at the threshold |
| Light | One linear line, 80 W | One linear line, 55 W (darker than the rooms on either side) |
| Shared | Orange route line, trim rail + LED wash at 3.0 m, epoxy on the room joint grid, dark acoustic ceiling | |

- **Rover reveal (verified by ray cast):** the rover is in clear view from inside Mars Intelligence (y 26.8)
  through the whole of Corridor 02.
- **Recess rule:** cladding drops whole panels (1.4 m rows) wherever a recess overlaps. Recess only on graphite
  walls; on warm walls, surface-mount the display instead.

## Full facility in Godot (2026-10-05), superseded
> Superseded by the game-readiness pass: see `docs/GAME_READINESS.md` (streaming, shared materials, ~1 GB peak).

All six spaces load together: 18 cameras, 0 errors.

| Space | fps (Intel UHD, 1600×900) | Draw calls |
|---|---|---|
| Hangar | 8–16 | 95–769 |
| Mission Control | 10–22 | 33–672 |
| Mars Intelligence | 15–18 | 291–502 |
| Briefing | 21–24 | 64–268 |
| Corridor 01 | 28 | 412 |
| Corridor 02 | 19 | 542 |

**GPU memory is the limit on integrated graphics.**
- With a VoxelGI volume per space, the full facility ran out of device memory (`VkResult -2`). The corridors
  now have no GI volume of their own, and they read correctly without one.
- **Phase 7 must address this** before more content is added:
  - Shared textures are embedded once per GLB; the epoxy floor set is loaded five times.
  - Six VoxelGI volumes are resident at once.
  - Fix with one shared material/texture library on import, and stream rooms (load the current room and
    its neighbours only).
