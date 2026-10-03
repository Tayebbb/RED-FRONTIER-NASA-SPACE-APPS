# Rover Systems QA Review

## Scope and image budget

- Read-only visual review of `systems_before.png` and the two NASA/JPL reference photos listed below. No Blender scene, model, export, or source file was edited.
- Exact image inspection count: **3 images total** (1 systems sheet + 2 reference photos). No screenshots were captured. The two other files already present in `references/` were not opened.
- The review is of the visible geometry in the sheet, not a mesh/topology audit. Small details and hidden faces cannot be verified from this view.
- All suggested changes are optional procedural geometry/material refinements. Preserve the existing object names, origins, socket parenting, seven existing `MAT_*` Principled materials, low-poly budgets, and modular alternatives. Do not add image textures or import 3D assets.

## References

1. [Spirit, "Almost Like Being at Bonneville" (PIA05576)](https://photojournal.jpl.nasa.gov/catalog/PIA05576) — NASA/JPL. Local: `references/spirit-bonneville-PIA05576.jpg`. Direct image: https://images-assets.nasa.gov/image/PIA05576/PIA05576~large.jpg. The rover array is visible in the foreground of this stereo panorama, but the anaglyph and oblique crop limit cell-level comparison.
2. [Curiosity MMRTG fit-check photo (KSC-2011-6703)](https://photojournal.jpl.nasa.gov/catalog/KSC-2011-6703) — NASA/Cory Huston. Local: `references/curiosity-mmrtg-fit-check-KSC-2011-6703.jpg`. Direct image: https://images-assets.nasa.gov/image/KSC-2011-6703/KSC-2011-6703~large.jpg. This is useful for rear/underside installation context; the generator fins and communications antennas are not sharply resolved in this frame. The NASA archive description identifies the MMRTG cooling fins and their heat-rejection role.

## Component findings

### Solar_Light — Tweak

- **Observed:** framed, tilted blue panel on a substantial single support. Its proportions read as a solar module; the face uses a regular grid.
- **Photo comparison:** Spirit's array face is divided into repeated narrow photovoltaic strips/cells, though the anaglyph does not support an exact cell-count comparison.
- **Minimal refinement:** keep the panel outline and support; replace the coarse uniform grid with a few repeated dark cell bands and narrow separators, retain a thin perimeter frame, and add one simple hinge/pivot block at the support. Reuse existing dark-blue and frame materials.

### Solar_Large — Tweak

- **Observed:** two compact framed panel rectangles on a small central support; the visible active area reads smaller and more fragmented than the `Large` label suggests.
- **Photo comparison:** the Spirit reference supports a broad, deliberately segmented collecting surface, not a pair of unframed floating tiles. It does not establish the fictional rover's exact array size.
- **Minimal refinement:** preserve this alternative's two-panel silhouette and name, but enlarge their active faces within the existing envelope, align their frames, and add a narrow hinge/bridge and repeated PV cell bands. Keep seams as geometry/material boundaries, not textures.

### Battery_Standard — Tweak

- **Observed:** compact, closed rectangular housing with a colored top cover, lower mounting tray, and three dark rectangular side details.
- **Evidence limit:** neither selected reference exposes an analogous rover battery module. This is an engineering-readability review, not a claim that a real rover uses this layout.
- **Minimal refinement:** retain a sealed enclosure; add a shallow lid seam/gasket and small corner chamfers. Make the three side details read as a recessed connector panel with capped sockets, rather than holes into the battery. Use existing neutral housing and restrained accent materials.

### Battery_Extended — Tweak

- **Observed:** two adjacent enclosure volumes on one base, with the same colored lids and side details as the standard form.
- **Evidence limit:** fictional capacity alternative; no direct photo comparison is available.
- **Minimal refinement:** keep the two-volume capacity cue, but give both housings consistent lid seams, sealed faces, and a shared mounting rail. Add one small protected inter-module connector at the seam; do not expose cells or add ventilation holes to the sealed battery shell.

### Shield_Minimal — Inference / Tweak

- **Observed:** a single plain, upright rectangular plate with a narrow edge strip.
- **Evidence limit:** this and the other shields are fictional modular protection choices, not photo-backed replicas. No combat-armor interpretation is implied or needed.
- **Minimal refinement:** preserve the simple plate; add a small return flange and two or three low-profile stand-off/mount tabs so it reads as a replaceable dust/thermal guard. Keep the broad face plain and reuse the current dark/neutral metal materials.

### Shield_Standard — Inference / Tweak

- **Observed:** multiple perpendicular panels form a partial enclosure, with a contrasting inset panel on one side.
- **Evidence limit:** no selected reference establishes this enclosure's shape or protection purpose; these are design inferences for a fictional modular system.
- **Minimal refinement:** make the panel breaks and attachment seams legible, add a few shallow stiffening ribs or folded returns, and turn the inset into a flush service cover. Keep openings limited to plausible access/clearance locations and retain the existing understated palette.

### Shield_Heavy — Inference / Tweak

- **Observed:** deeper, box-like multi-panel guard with a large contrasting side insert and open upper volume.
- **Evidence limit:** fictional variant; do not present it as a real rover component or add weapon-like details.
- **Minimal refinement:** preserve the heavier enclosure and open clearance; add corner returns, a few visible fasteners, and a small louver/slot group only where heat-producing equipment needs airflow. Keep the insert flush and use the existing accent material sparingly. Do not seal a hot component behind a solid shell.

### Antenna_Std — Tweak; photo-unverified

- **Observed:** two very thin upright rods with conspicuous block-like orange end/base pieces.
- **Evidence limit:** the Curiosity fit-check frame does not resolve an antenna. The available photos do not directly validate this antenna's count or exact configuration.
- **Minimal refinement:** if the intended role is a UHF whip, retain the current number of rods if that is part of the design, but make each rod a consistent thin mast with a small feed/insulator at its base, a restrained tip/collar, and a compact mount. Reduce the visual weight of the orange blocks; use the existing accent only on the feed detail.

### Antenna_HighGain — Tweak; photo-unverified

- **Observed:** broad faceted dish on a short support, with a square-ended central element above the dish.
- **Evidence limit:** no clear high-gain dish is visible in the two selected photos. This recommendation is based on recognizable dish/feed geometry, not a direct dimensional match.
- **Minimal refinement:** preserve the low-poly dish and stand; give the reflector a shallow concave bowl and a thin raised rim, then replace the square cap with a compact feed horn at the focal point held by three sparse struts. Add a simple azimuth/elevation pivot at the support. Keep subdivisions low and avoid adding material slots.

### Power_Nuclear — Tweak; partial photo evidence

- **Observed:** a broad, flat colored top disk above a blocky base with radial vertical fins. It reads as a heat-producing module, but currently more like a capped pedestal than a compact RTG.
- **Photo comparison:** Curiosity's fit-check image supplies aft installation context but does not resolve the fin profile clearly. NASA's catalog description confirms cooling fins on the MMRTG and describes their role in rejecting excess heat; it does not establish this fictional unit's exact dimensions or placement.
- **Minimal refinement:** keep the existing part name and mounting footprint; reshape the cap/body into a short canister with end caps and a small axial mounting bracket. Turn the radial blocks into evenly spaced longitudinal fins with visible air gaps. If a protective shroud is desired, use a stand-off/perforated or louvered guard rather than enclosing the fins. Replace the broad saturated orange top with an existing neutral metal/dark material and reserve the current accent for a small end ring or heat-loop detail.

## Unverified / not inferred

- No selected photo directly validates either battery housing or any of the three fictional shields.
- Antenna count, exact UHF whip configuration, high-gain dish dimensions, and feed placement remain unverified by these photos.
- The Curiosity image is not a clean RTG close-up; fin shape recommendations above are grounded in the NASA archive description plus common heat-rejection geometry, not a fine visual read of that image.
- The Spirit reference is a stereo panorama, not a close orthographic view of the array. It supports repeated PV segmentation only at a broad level.
- This review does not verify hidden faces, mesh watertightness, exact triangle counts, socket alignment, material assignments, or runtime/export behavior.

## Final QA — 2026-10-03

- **Scope:** inspected exactly 2 images: `systems_after.png` and the single additional NASA/JPL reference below. No other screenshots or image references were inspected. No Blender scene, model, or exports were changed.
- **Scoring:** 1 = substantive correction recommended; 2 = acceptable stylized hardware with a targeted refinement/clearance check; 3 = acceptable as a fictional modular approximation.

### Individual verdicts

- **Solar_Light — 2:** Readable framed PV panel with a regular cell grid and support; stylization is acceptable. There is a plausible installed-configuration collision to check: the HG socket is at x=0.43, y=0.62, z=1 and the solar socket at x=0, y=0.66, z=1, while the panel mesh is reported at z=0.433 and HG feed at z=0.5. The separated-parts sheet cannot prove an intersection. Check the assembled bounds; if they overlap, add a rear outrigger under the solar module geometry while keeping both socket positions fixed.
- **Battery_Standard / Battery_Extended — 2:** Both read as sealed modular enclosures, and the extended option clearly signals added capacity. Orange lid plates and small tabs are visibly mounted on top, but lid seam/gasket and fixture alignment are not strongly legible; make the seam shallow and continuous and keep lid tabs aligned to the lid edge. Keep connector details as capped/recessed fittings, not shell penetrations. No selected photo provides a direct battery comparison.
- **Shield_Minimal / Shield_Standard / Shield_Heavy — 3:** All three read as intentional fictional protection options with increasing coverage. Their simplified plates and large inset are acceptable at this low-poly scale; exact shield function or geometry is not established by the references. If Heavy is installed near the RTG, preserve clear airflow around radiator surfaces rather than enclosing them.
- **Antenna_Std / Antenna_HighGain — 2:** The whip remains legible and the faceted dish, feed supports, and stand read as a high-gain antenna in the sheet. The central feed is blocky and the dish pivot is visually understated, but these are refinements rather than demonstrated functional defects. The added reference is not an antenna photo, so antenna count, feed geometry, and pivot layout remain photo-unverified.
- **Power_Nuclear — 1:** This is the clearest hardware-specific mismatch: the current part reads as a tall cylinder behind numerous narrow vertical blades and a broad flat top disk. PIA23306 instead shows a compact central MMRTG body with broad, segmented radiator panels, attachment hardware, and open heat-rejection surfaces. Replace the narrow radial-blade emphasis with a few broad segmented fin panels and visible air gaps; reduce the cap to a compact end flange while retaining the existing footprint. The exposed fins are not themselves a defect: they radiate excess heat. Do not add a solid shroud or place the Heavy shield so it blocks those surfaces. This is visual-design guidance, not a nuclear-safety assessment.

### Additional official reference

- NASA/JPL, **“Mars 2020’s MMRTG” (PIA23306)**, dated July 24, 2019. This is a pre-fueling/testing hardware photograph at Idaho National Laboratory, not an installed rover view. NASA’s description states that its fins radiate excess heat. Credit: NASA/JPL-Caltech. Catalog: https://science.nasa.gov/photojournal/mars-2020s-mmrtg/ . Direct original: https://images-assets.nasa.gov/image/PIA23306/PIA23306~orig.jpg . Local file: [references/nasa-mars2020-mmrtg-fins-PIA23306.jpg](references/nasa-mars2020-mmrtg-fins-PIA23306.jpg).

### Minimal repair priority

1. Verify solar-panel/HG-feed clearance in the assembled configuration; add a rear outrigger beneath the solar module only if the reported geometry intersects, without moving sockets.
2. Rework `Power_Nuclear` toward broad, segmented, unobstructed radiator panels; keep any nearby shield from occluding them.
3. Refine battery lid seams/fixture alignment and the high-gain feed/pivot only if another pass is already touching those parts. The existing stylized forms do not justify broader redesign.
