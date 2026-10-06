# RF-01 Mission Systems Engineer: character workspace

The player avatar for the Earth/facility part of the game. This is a new, isolated workspace: nothing here
touches the locked facility (`blender/`, `scripts/`), the rover (`assets/rover/`, `art/source/rover/`) or Godot
gameplay (`godot/`).

| Path | Contents |
|---|---|
| `scripts/rf01_sdf.py` | Signed-distance sculpting kernel (numpy): primitives, smooth blends, sparse Surface Nets mesher, projection onto the field |
| `scripts/rf01_body.py` | Anatomy: A-pose skeleton plus about 290 anatomical forms (bone landmarks, muscle groups, fat pads, face features). Built for the left side and mirrored |
| `scripts/build_cp1_body.py` | Builds `source/RF01_Engineer_MASTER.blend` from the anatomy |
| `scripts/render_review.py` | Neutral review studio and renders (turntable, proportion sheet, head and hand close-ups) |
| `scripts/rf01_clothing.py` | CP2 garment fields: jacket, trousers, shoes (forms, construction displacements, openings) |
| `scripts/build_cp2_clothing.py` | Rebuilds only the CLOTHING collection in the master, plus an interpenetration audit |
| `scripts/gen_cp3_textures.py` | CP3 identity artwork (patch, chest/back marks, ID card, wrist UI) -> `textures/cp3/` |
| `scripts/rf01_identity.py` | CP3 identity objects seated on the garments (decals, patch, badge, wrist interface, hardware, piping) |
| `scripts/contact_sheet.py` | Tiles review renders into one sheet (system Python with Pillow) |
| `source/` | `.blend` files (the master, and a snapshot per checkpoint) |
| `renders/cp1_body/` | Checkpoint 1 review renders |

## What is in Git and what stays local
In Git:
- `scripts/`, this README and `textures/cp3/` (identity artwork)
- Four summary sheets under `renders/`
- The runtime character: `godot/assets/characters/rf01/RF01_Engineer.glb` and its textures

Kept on the workstation only (see `.gitignore`):
- `source/`: all `.blend` files (checkpoints, MASTER, GAME)
- `export/`: a working copy of the GLB
- `textures/game/`: bake outputs (they are embedded in the GLB)
- The individual review renders

## Conventions (match the facility and Godot)
- **Units and orientation:**
  - Blender metres, scale 1.0, Z up.
  - The origin is on the floor between the feet.
  - The character faces −Y (Blender front), and his left side is +X.
  - The glTF export converts to Godot's Y up. A −Y-facing model arrives facing Godot +Z.
- **Facing in Godot:** the Godot player (`godot/game/player/player.gd`) treats −Z as forward for its `Visual` node.
  When the character is integrated (only after visual approval), the GLB instance under `Visual` needs a 180° yaw.
  That is a transform on the visual child, not a change to the controller.
- **Placeholder this replaces:** a 1.75 m capsule (radius 0.3 m) with its feet at the CharacterBody3D origin, a camera
  pivot at 1.55 m and a third-person camera 3.2 m behind. The new character is 1.80 m tall and fits inside the
  existing collision capsule's radius, so there is no gameplay change.

## Rebuild
```
blender -b --factory-startup --python art/character/scripts/build_cp1_body.py
blender -b art/character/source/RF01_Engineer_MASTER.blend --python art/character/scripts/render_review.py -- art/character/renders/cp1_body --sheet --head --hands
```
`--quick --h 0.004` builds a fast look-dev mesh (surface nets only). `--region head|hand --h 0.00125` builds a
high-resolution patch for close review.

## Checkpoint 1: body and proportions (2026-10-06). APPROVED
**Files**
- **Master:** `source/RF01_Engineer_MASTER.blend`
- **Snapshot:** `source/RF01_Engineer_CP1_Body.blend`
- **Renders:** `renders/cp1_body/`
  - Sheets: `CP1_turntable_sheet.png`, `CP1_proportions_sheet.png`, `CP1_head_hands_sheet.png`
  - Individual frames
  - `measurements.json`

**Object structure**
- **Collection `RF01_Character`**
  - `RF01_Character_ROOT` (empty at the origin; also stores the A-pose joint positions as `joint_*` properties)
  - **BODY:** `RF01_Body`, `RF01_Eyes`
  - **CLOTHING, ACCESSORIES, RIG:** empty, ready for later checkpoints
- **Not saved in the file:** the review studio (backdrop, ruler, lights, cameras) is built only at render time.

**Measured (A-pose)**

| Measure | Value |
|---|---|
| Stature | 1.80 m |
| Head height | 0.239 m (7.54 heads) |
| Head breadth | 153 mm |
| Eye height | 1.683 m |
| Chin height | 1.563 m |
| Chest (breadth × depth) | 314 × 212 mm |
| Waist breadth | 273 mm |
| Hip breadth | 365 mm |
| Joint heights | shoulder 1.44 m, hip 0.925 m, knee 0.505 m, ankle 0.084 m |
| Upper arm / forearm | 0.318 m / 0.258 m |
| Foot length | 0.279 m |

**Geometry**

| Object | Geometry |
|---|---|
| `RF01_Body` | 658,136 quads (about 1.32 M triangles); one closed, genus-0 surface |
| `RF01_Eyes` | 2 × UV-sphere eyeballs (2,980 vertices) with a corneal bulge |

**Approach**
- **Pose and stance:** a skeleton in A-pose: arms 45° below horizontal, elbows 12° bent, feet toed out 7°.
- **Forms:** anatomical primitives blended as signed distance fields. The face was checked against standard
  adult-male profile and cross-section landmarks; most deviations are within about 5 mm.
- **Meshing:**
  - Sparse Naive Surface Nets at 2 mm.
  - Laplacian relax, then Newton projection back onto the field.

**Limitations (to fix at later checkpoints)**
- **Not yet production topology.** This is a sculpt-stage mesh.
  - Designed quad retopology (loops for the mouth, eyes, shoulders, elbows, knees, fingers) and UVs come before
    rigging.
  - QuadriFlow could not be used: Blender 5.2 rejects every voxel-remeshed input as non-manifold, even a remeshed
    Suzanne.
- **Face is basic anatomy only.** Lips read slightly heavy and forward in 3/4 view, and brow and lid
  transitions are soft. Checkpoint 4 refines it.
- **Hands:** the thumb is a little short and stubby.
- **Review-only items:**
  - The dark briefs are a face-material mask with a stepped edge.
  - The clay material is for form review only.
- **No hair, eyebrows, teeth or skin material yet** (checkpoints 4 and 5).

**Approval note (2026-10-06):** proportions, height, scale and silhouette are approved. Carried forward to the
face/hands checkpoint (no further work on the bare body until then):
- lips slightly heavy/forward
- brow/lid transitions need refinement
- thumb slightly short/stubby
- face and hands not final

Production retopology, UVs, rig, textures and hair are deliberately not started.

## Checkpoint 2: clothing blockout (2026-10-06). APPROVED
**Files**
- **Master:** `source/RF01_Engineer_MASTER.blend`
- **Snapshot:** `source/RF01_Engineer_CP2_ClothingBlockout.blend`
- **Renders:** `renders/cp2_clothing/`
- **Rebuild:**
  ```
  blender -b art/character/source/RF01_Engineer_MASTER.blend --python art/character/scripts/build_cp2_clothing.py
  ```

**Objects** (collection `CLOTHING`, parented to `RF01_Character_ROOT`; separate from `RF01_Body`, which is untouched)

| Object | Form | Base quads | Triangles with thickness |
|---|---|---|---|
| `RF01_Jacket` | Hip-length technical jacket: stand collar, centre zip placket, front/back yoke, set-in sleeves with cuff bands, side panels, back princess seams, two flapped chest pockets, side welt pockets, hem band. 3.5 mm thick (Solidify) | 180,338 | 723,612 |
| `RF01_Trousers` | Straight, slightly tapered technical trousers: waistband with loops, fly, slant front pockets, back yoke and flat back pockets, side seams and inseams, articulated knee darts. 2.8 mm thick | 147,451 | 591,728 |
| `RF01_Shoes` | Mid-height engineering shoe (collar about 12.5 cm): 28/19 mm sole with toe spring, toe box, heel counter, lacing panel, mudguard line. Solid | 84,420 | 168,840 |

**Folds** (medium only): inner elbows, blousing above the cuffs, under-arm compression, armpit drape, shoulder, crotch,
back of the knees, hem break over the shoes.

**Method**
- **Forms:** each garment is a signed-distance field on the CP1 skeleton: garment forms UNION (the layer underneath
  offset by its clearance). Layering inside to out: body, shoes, trousers, jacket.
  - Clearances: trousers 10 mm, jacket 12 mm over the body and 8 mm over the trousers, shoes 6 mm.
- **Construction:** panels, seams and folds are displacement layers that follow the surface.
- **Openings and thickness:** the openings are clip planes. The clipped caps are deleted and the edges are snapped
  onto the hem, cuff and collar lines; Solidify adds thickness inward.
- **Meshing:** surface nets (3 mm garments, 2 mm shoes), relaxed and projected back onto the field.

**Interpenetration audit (A-pose, from the build)**
- 0 jacket inner-surface vertices inside the body or the trousers; 0 body vertices through the jacket.
- 0 trouser inner-surface vertices inside the body (none within 2 mm); 0 body vertices through the trousers.
- 8 trouser inner-surface vertices touch the shoe collar at the hem break (hidden under the hem).
- 0 foot vertices outside the shoes below the collar opening.

**Known issues / not done**
- Sculpt-stage meshes (no retopology or UVs). Garment polycounts are blockout-level and will drop with retopology.
- The audit covers the A-pose only. Deformation clearance (armpits, crotch, knees in motion) is checked at the rig
  checkpoint.
- No materials beyond review clay, no branding, patches, badge or accessory (checkpoint 3).

**Approval note (2026-10-06):** silhouette and fit approved. Carried forward, not reasons to redo CP2: the jacket
feels intentionally plain, the trousers are simple, the footwear could be more technical, and the clothing has no
identity yet (all addressed in CP3).

## Checkpoint 3: hero design and Red Frontier identity (2026-10-06). APPROVED, LOCKED
**Files**
- **Master:** `source/RF01_Engineer_MASTER.blend`
- **Snapshot:** `source/RF01_Engineer_CP3_HeroDesign.blend`
- **Renders:** `renders/cp3_hero/`
- **Rebuild:**
  ```
  python art/character/scripts/gen_cp3_textures.py
  blender -b art/character/source/RF01_Engineer_MASTER.blend --python art/character/scripts/build_cp2_clothing.py -- --stage 3
  ```

**Principle:** the CP2 garments are the foundation. Stage 3 appends layers; no CP2 shape or layer changes, and
`--stage 2` still rebuilds CP2 exactly.

**Silhouette check against CP2.** Distance of every CP3 garment vertex from the approved CP2 surface:

| Garment | Median | Maximum | Where the maximum is |
|---|---|---|---|
| Jacket | 0 mm | 1.6 mm | added detail heights |
| Trousers | 0 mm | 1.8 mm | added detail heights |
| Shoes | 0 mm | 3.5 mm | 0.005 % of vertices, at the toe-cap overlay |

**Construction added (subtle displacement layers)**
- **Jacket:**
  - Body-side yoke seam with an orange piping cord, front and back.
  - Reinforced elbow panels with stitch line.
  - Cuff tabs with snaps.
  - Bound collar edge.
  - Orange pull tab on the left chest pocket.
- **Trousers:**
  - Articulated knee panels.
  - One flat zipped utility pocket on the left outer thigh (not cargo).
- **Shoes:**
  - Toe-cap overlay.
  - Side saddle overlays.
  - Tonal rubber mudguard.
  - Two-tone sole (grey midsole, black outsole).

**Colour blocking.** Per-vertex region distances drive the shader threshold, so panel edges are crisp and follow
the seams. Palette from the facility visual language:

| Colour | Used on |
|---|---|
| Warm off-white | Jacket base |
| Light grey | Elbow panels |
| Navy | Yoke front and back, side panels, cuff bands and tabs, zip tape, lining |
| Navy-charcoal | Trousers; knee panels a tone darker |
| Charcoal | Shoes |
| Orange `#C2501C` | Accents only: yoke piping, chest-pocket tab, zip pull, and inside the patch and badge |

**Identity objects** (collection ACCESSORIES unless noted; all separate geometry seated on the garments)

| Object | What it is |
|---|---|
| `RF01_ChestMark` | Left chest, embroidered on the navy yoke: insignia + RED FRONTIER + MISSION RF-01 (80 mm wide) |
| `RF01_BackMark` | Back yoke centre: insignia + RF-01 (62 mm). The third-person identifier |
| `RF01_MissionPatch` | Left upper arm, 78 mm round, 1.6 mm raised with a merrowed edge. Mars horizon, transfer trajectory, RF-01, ring text RED FRONTIER / MISSION SYSTEMS |
| `RF01_Badge` | CR80 facility ID card in a navy holder, clipped to the right chest pocket flap: RED FRONTIER PROGRAM, MISSION SYSTEMS ENGINEER, RF-01, ID MS-01, abstract portrait, no personal name. Rigid; the holder is pushed out until it clears the jacket by 1 mm |
| `RF01_WristInterface` | Slim strapped mission interface over the left sleeve: about 38 x 46 x 8 mm, matte screen with facility UI (cyan info, orange = selected) |
| `RF01_Hardware` (CLOTHING) | Zip slider with orange pull, cuff-tab snaps, thigh pocket zip pull |
| `RF01_JacketPiping` (CLOTHING) | The orange yoke piping cord |

**Branding:** fictional Red Frontier programme only. No NASA marks and no implied endorsement. The insignia is the
facility's own mark (Mars disc, horizon, chevron).

**Known issues / not done**
- Review-level PBR; final materials (fabric weave, embroidery relief, wear) come at checkpoint 5.
- The decals and patch have their own planar UVs (they are image decals). The garments themselves are still not UV
  unwrapped.
- The CP2 shoulder-cap step: the CP2 "yoke" step sits on the sleeve cap (an inverted half-space in the CP2 code). It
  stays as approved geometry; the CP3 yoke paint and seam use the body side.
- Face and hands are still unrefined (checkpoint 4).

## Game production (2026-10-06): time-constrained finish
The priority changed: a complete, good-looking, game-ready character instead of further cinematic refinement.

| Step | Script | Output |
|---|---|---|
| Face/hands cleanup, master update | `game_1_meshes.py` (+ `rf01_head_v4.py`) | `source/RF01_Engineer_MASTER.blend` (body now CP4, still 658k quads) |
| Bake sources + game meshes | `game_1_meshes.py` | `source/RF01_Engineer_GAME.blend` |
| Bakes (base colour + tangent normals) | `game_2_bake.py` | `textures/game/` |
| Rig, weights, Idle/Walk/Run | `game_3_rig.py` | `GAME.blend` |
| GLB export | `game_4_export.py` | `export/RF01_Engineer.glb`, `godot/assets/characters/rf01/RF01_Engineer.glb` |
| Fast review | `game_preview.py` | Eevee frames |

**Face and hands (single pass, `rf01_body.build(cp=4)`; CP1 to CP3 builds unchanged)**
- **Lips:** pulled back about 2 mm and wrapped tighter around the dental arch.
- **Face:** softer brow and lid transitions; nose tip and nostrils cleaned up.
- **Thumb and fingers:** a longer, slimmer thumb (the tip now reaches past the index knuckle); slightly waisted
  fingers; subtle tendons.
- **Asymmetry:** subtle (brow, lid, mouth corner, nose tip, cheek), applied as a coordinate warp.
- **Hair:** a modelled hair mass with a groove normal map.
- **Eyebrows, skin and eyes:** painted eyebrows and lip colour in the skin texture; clean-shaven; simple textured
  eyes.

**Game mesh: 54,688 triangles in 11 meshes.** 53 bones (Godot SkeletonProfileHumanoid names).

| Mesh | Triangles | Notes |
|---|---|---|
| Skin | about 10.1k | head + neck + hands only; the hidden body is removed |
| Jacket | about 18k | thickness included |
| Trousers | about 13k | thickness included |
| Shoes | 5k | |
| Hair | about 3.6k | |
| Identity pieces | about 3.3k | chest mark, back mark, patch, badge, wrist unit |
| Eyes | about 0.6k | |

- **Textures:** 2K for skin, jacket and trousers; 1K for shoes and hair. Patch, badge and marks keep their own
  artwork; the decals use alpha clip.

**Rig and weights**
- Weights: inverse distance to the bone segments, gated per garment. The jacket ignores the legs, the trousers ignore
  the arms, the sleeves only follow arm bones within 10 cm, and fingers only within 4 cm.
- Hair, eyes, badge, marks, patch and wrist unit are bound rigidly to their bone.
- Automatic bone heat failed on the decimated proxy, which is why the distance-based solver is used.

**Animations** (in place, 24 fps, keyed procedurally)

| Clip | Length | Authored speed | Details |
|---|---|---|---|
| Idle | 3 s | 0 | breathing, weight shift, head drift |
| Walk | 0.75 s | 2.27 m/s | heel-to-toe feet, counter-rotation, opposite arm swing |
| Run | 0.667 s | 4.8 m/s | forward lean, flight phase, bent arms, loose fists |

Pelvis height is solved each frame so the planted foot meets the floor.

**Godot 4.7**
- **New files:**
  - `godot/game/player/rf01_visual.tscn`: the GLB instance turned 180 degrees about Y, so the model's −Y front
    faces the controller's −Z.
  - `godot/game/player/rf01_visual.gd`: visual-only script. It reads the CharacterBody3D velocity, picks
    Idle/Walk/Run (Run above the midpoint of GameConfig.WALK_SPEED and SPRINT_SPEED) and scales playback to speed.
- **`player.tscn`:** the placeholder Suit/Visor/Pack meshes under `Visual` were replaced by the RF01Visual instance.
  `player.gd`, collision, camera, interaction, MissionState and streaming are unchanged.
- **Verified:** clean import, and the gameplay acceptance test passes 87/87 (movement, wall collision, camera, room
  streaming, interactions, mission progression).

**Known limitations**
- Game meshes are decimated (triangulated), not hand-retopologised.
- The procedural clips are serviceable rather than motion-capture quality.
- Hands can brush the jacket hem at the extreme of the walk arm swing.
- The face is suited to gameplay and medium shots, not close-ups.
- The spawn point in the Briefing room is backlit, so the character reads dark there, as the capsule did.

## Final hair pass (2026-10-06): hair only
`scripts/game_5_hair.py` replaces GAME_Hair in `source/RF01_Engineer_GAME.blend`. Nothing else changed.

**Mass**
- Same short professional shape.
- Irregular, noise-broken hairline that thins out instead of ending in a ledge, wider at the front.
- Sides sit closer to the skull.
- Gentle large clumps and a lumpy top silhouette.
- The regular sine grooves are gone.

**Texture:** a strand pattern evaluated per pixel at bake time (stretched noise along a stored hair-direction
field), plus larger clumps and darker roots at the hairline. It is baked at 2K into colour and, through a bump, into
the normal map, then shipped at 1K.

**Material:** dark brown (not black), roughness 0.62, low specular.

**Cards:** tried, and dropped. On this procedural mass they read as stray strips or shards. The textured mass reads
better at gameplay and medium-shot distance.

**Cost:** 3,600 triangles and two 1K maps, the same as before. Character total: 54,690 triangles; GLB 13 MB.

**Verification:** gameplay test 87/87 after re-import. Review sheet: `renders/RF01_Hair_BEFORE_AFTER.png`.

**Limitation:** an extreme close-up still shows a thin edge at the front hairline.
