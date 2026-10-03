# Mobility Realism Review

## Scope and Result

Read-only visual comparison for the existing fictional modular low-poly rover. No Blender scene, model, export, or source files were edited. Only this report and two reference photos were added under `art/qa/`.

Reviewed the assembled base, all six named wheel placements (`SM_Wheel_FL`, `SM_Wheel_FR`, `SM_Wheel_ML`, `SM_Wheel_MR`, `SM_Wheel_RL`, `SM_Wheel_RR`), `SM_Chassis`, `SM_Arm_Bogie_L`, `SM_Arm_Bogie_R`, `Wheel_Standard`, and `Wheel_Reinforced`.

**Overall:** The chassis silhouette and modular, low-poly character are coherent. The main realism gap is that the wheel treads and the load-bearing suspension articulation read as generic shapes rather than rover mobility hardware. These are visual recommendations, not a 1:1 Curiosity/Perseverance replica specification.

## Evidence Reviewed

1. Existing [mobility sheet](mobility_before.png): assembled rover, chassis, left/right bogie arms, and both wheel variants. The assembled view reads as six-wheel, but occlusion and scale prevent identifying each wheel name or checking hidden attachments.
2. NASA/JPL, [Break in Raised Tread on Curiosity Wheel](https://science.nasa.gov/photojournal/break-in-raised-tread-on-curiosity-wheel/), PIA21486. Downloaded photo: [PIA21486_Curiosity_Wheel_Grouser.jpg](references/PIA21486_Curiosity_Wheel_Grouser.jpg). Direct image URL: https://images-assets.nasa.gov/image/PIA21486/PIA21486~orig.jpg. Credit: NASA/JPL-Caltech/MSSS. The March 19, 2017 MAHLI close-up shows substantial angled, zig-zag raised grousers; the caption describes Curiosity's aluminum wheels as about 50 cm in diameter and 40 cm wide and reports damage to two grousers.
3. NASA/JPL, [Installation of Curiosity's Wheels and Suspension](https://science.nasa.gov/photojournal/installation-of-curiositys-wheels-and-suspension/), PIA13234. Downloaded photo: [PIA13234_Curiosity_Wheels_Suspension.jpg](references/PIA13234_Curiosity_Wheels_Suspension.jpg). Direct image URL: https://images-assets.nasa.gov/image/PIA13234/PIA13234~orig.jpg. Credit: NASA/JPL-Caltech. The June 29, 2010 cleanroom photograph shows the mobility subsystem and discrete mechanical connections during installation; it is assembly context, not a finished-flight detail drawing.
4. NASA's [Perseverance Rover Components](https://science.nasa.gov/mission/mars-2020-perseverance/rover-components/) page was used for text context only: 52.5 cm wheel diameter, 48 machined grousers, and the rocker-bogie/differential relationship. The supplied 0.525 m target matches that Perseverance diameter. These facts are not attributed to the Curiosity photos.

## Findings and Fixes

### P1 — Suspension connectivity and load path

- `SM_Arm_Bogie_L`: The sheet shows a long, thin, straight beam with a small bracket; the front-to-chassis rocker path and rocker-to-bogie joint do not read clearly. Add a faceted chassis-side pivot mount, a distinct rocker pivot, and a visible secondary link branching toward the middle/rear wheel carriers. Keep the existing arm object name and overall reach.
- `SM_Arm_Bogie_R`: Same issue and same fix, mirrored coherently. The joint locations should be visually aligned with the left side and with the wheel carriers.
- `SM_Chassis`: The boxy deck, perimeter chamfers, inset orange access panel, louvers, and fasteners read clearly at sheet scale. The chassis-to-rocker mounts and differential/pivot area are not legible in the assembled view. Add compact external pivot plates/bearing collars where the suspension meets the chassis; expose the underside skid in a presentation view rather than changing the envelope to make it visible.
- Assembled base: Make the sequence chassis mount → rocker → bogie branch → wheel carrier traceable on both sides. Favor a small number of larger, readable low-poly joints over extra tiny bolts or surface clutter.

### P1 — Wheel tread profile

- `Wheel_Standard`: The sheet shows broad straight rectangular crosswise tread blocks. Replace or reshape them into raised angled/zig-zag grouser bands that wrap the circumference, with consistent spacing and a visible chevron direction. Retain the 0.525 m diameter and axle-centered origin.
- `Wheel_Reinforced`: Fine parallel circumferential lines dominate, with no strong raised chevrons. Add a clearly raised chevron grouser profile as well; distinguish the reinforced option with slightly broader/deeper lugs, a restrained shoulder rib, or a reinforced sidewall/hub guard. Keep the two options visibly related, not separate wheel families.
- `SM_Wheel_FL`, `SM_Wheel_FR`, `SM_Wheel_ML`, `SM_Wheel_MR`, `SM_Wheel_RL`, `SM_Wheel_RR`: The assembled view is consistent with one shared visual wheel treatment, but it does not resolve the individual names or hidden hubs. Apply the selected wheel variant consistently to all six placements. If corner steering hardware is depicted, use small steering-knuckle collars on the four corner carriers and simpler fixed carriers on the middle pair; keep this subtle and do not move the axle origins.
- Use a muted machined-metal read for the exposed wheel/grousers and hub against a darker tire or recess treatment. Curiosity's aluminum construction is reference context, not a requirement that overrides the fictional rover's established material identity.

### P2 — Hub and wheel-side construction

- Both wheel variants: Keep the existing faceted hub plate and bolt treatment, but add a simple inset hub ring/shoulder so the center reads as a mechanical attachment rather than a flat cap. The reference photo supports a strong hub-to-wheel transition; it does not establish the exact internal spoke pattern, so avoid elaborate or asserted spoke geometry without another source.
- Preserve the two variants' common tire diameter and axle interface. Do not use overall scaling or a moved origin to communicate reinforcement.

### P3 — Chassis detail restraint

- `SM_Chassis`: The existing side access panel, louvers, chamfer, fasteners, and documented belly skid already provide useful authored detail. Prioritize the missing suspension mounts over adding more panels, labels, or bolts. A few short, protected harness runs at visible chassis-to-arm interfaces may improve functional readability, but remain secondary and close to the structure.

## Constraints to Preserve

The handoff reports base bounds of 2.700 × 3.000 × 2.1985 m, 5,232 base triangles, 0.525 m wheel diameter, six 404-triangle base wheels, 160 triangles per bogie, unit scales, axle-centered origins, and all nine sockets parented to the chassis. Preserve the bounds, names, sockets, scales, and origins. The strict triangle headroom is 8,000 − 5,232 = 2,768 triangles for all base changes combined. Treat that as a ceiling, not a target; prefer replacing tread geometry and adding only readable pivot forms. Re-run the numeric audit after any future edits.

## Multi-Agent Synthesis

Three independent, read-only assessments were requested for wheel construction, bogie connectivity, and chassis/assembled readability. All agreed on the priorities: visible multi-joint suspension load paths first, raised chevron grousers on both wheel options second, and chassis interface details rather than extra body decoration. One assessment suggested open spokes and another suggested harness runs; both are lower-confidence optional details because the supplied photos do not verify the exact fictional wheel internals or cable routing. The chassis assessment treated the PIA13234 image as assembly context, not as a final configuration reference.

## Not Verifiable From This Sheet

- Whether each of the six `SM_Wheel_*` objects is individually attached, named, oriented, or built with separate mesh data; the view and handoff summary do not show per-object transforms/topology.
- Actual pivot axes, articulation range, steering/drive motor geometry, clearances, or mechanical behavior.
- The hidden underside, exact belly-skid shape, interior wheel construction, or the geometry/material of occluded surfaces.
- Exact Curiosity/Perseverance tread counts, grouser dimensions, or how a fictional Reinforced option should differ. The current sheet supports visual guidance only; dimensions beyond the explicit rover constraints are not being inferred.

## Image Inspection Count

Exactly **3 image inspections**: `mobility_before.png` (1), PIA21486 wheel photo (2), PIA13234 suspension installation photo (3). No additional image was opened or requested.

## Final Verification — Corrected Sheet

Read-only check of `mobility_after.png` against the cited NASA wheel-tread and suspension-assembly evidence. This final pass inspected exactly **1 image**; the earlier three-image count above records the prior review, and those images were not reopened.

- **Result:** No material visual defect requiring repair is evident at sheet scale. The chassis-to-side-pivot-to-rocker path and the rocker/bogie branching are now traceable on both arm variants. Wheel carriers meet the visible tread bodies, and no clear arm-to-chassis break or frame penetration is apparent. The silhouettes remain coherent for a fictional, low-poly modular rover; exact Curiosity/Perseverance identity is not required.
- **Wheels:** `Wheel_Standard` and `Wheel_Reinforced` both read as raised angled/chevron-like grouser treatments; the reinforced option appears slightly more substantial while remaining in the same family. Visible assembled placements use a consistent wheel treatment. The isolated sheet does not let me map each of the six `SM_Wheel_*` names to an individual tire with certainty, so placement names/scales passing is taken from the supplied numeric audit rather than claimed from this image.
- **Accepted simplification / visibility limits:** Faceted box chassis, simplified pin joints and axle/hub caps, sparse articulation detail, and close visual similarity between wheel variants are acceptable at this style and resolution. Socket/body intersections, hidden attachments, articulation axes, clearances, and the obscured wheel placement cannot be fully verified from this isolated sheet.
- **Measurements:** Current supplied audit passes: base 2.700 × 3.000 × 2.1985 m, 7,804 triangles (196 below the 8,000 limit), 0.525 m wheels, requested names present, and scales pass. These current figures supersede the earlier baseline values recorded above.
