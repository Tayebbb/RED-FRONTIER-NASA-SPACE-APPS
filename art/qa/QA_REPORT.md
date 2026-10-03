# Rover Reference QA

## Result

Completed three specialist reviews, two visual review rounds, procedural corrections, static compatibility checks, and GLB validation. The finished asset remains a fictional modular low-poly rover. PASS applies to the tested static geometry/export scope, not exact NASA replica fidelity or physical engineering readiness.

Final scene: `art/source/rover/red_frontier_rover.blend`.
Original backup: `art/source/rover/red_frontier_rover_preqa.blend`.
Final visual evidence: [final_verification.png](final_verification.png).

## Component Coverage

| Components                           | Outcome                                                                           | Evidence limits                                                                |
| ------------------------------------ | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| SM_Chassis                           | Retained authored panels/skid; added suspension bearing mounts                    | NASA cleanroom mobility reference supports mechanical attachment cues          |
| SM_Arm_Bogie_L / R                   | Rebuilt connected rocker and bogie load paths, pivots and carriers                | Static meshes, not physically articulated suspension                           |
| SM_Wheel_FL / FR / ML / MR / RL / RR | Shared metal-wheel treatment, raised angled grousers and inset hubs               | All six numerically verified; 16 bands are a budget-driven simplification      |
| Wheel_Standard / Reinforced          | Common 0.525 m axle interface; wider reinforced variant and thicker grousers      | Not exact Curiosity or Perseverance tread counts                               |
| SM_Mast                              | Additional optical port and protective shade                                      | NASA test-bed mast reference; no exact internal hardware                       |
| Inst_Camera                          | Stereo optics retained; mounting fasteners added                                  | Generic camera, not a named flight unit                                        |
| Inst_Radar                           | Rear downward bowtie-like antenna; boom routed past solar support and guard       | NASA RIMFAX form/location reference; fictional mounting bracket                |
| Inst_Radiation                       | Rebuilt skyward detector window                                                   | RAD hardware photo plus NASA written skyward orientation                       |
| Inst_Soil                            | Raised articulated sampler support; final tip at ground Z=0                       | Physical access corrected, not a verified flight sampler design                |
| Inst_Spectrometer                    | Optical housing retained; outward/raised bracket clears Extended battery          | Generic spectrometer, not APXS or another specific replica                     |
| Inst_Weather                         | Exposed boom and separated sensor stack                                           | NASA MEDA reference supports exposed-sensor layout only                        |
| Solar_Light / Large                  | Thin frames, PV strips, hinge hardware; Large offset rearward for HG clearance    | NASA Spirit photo supports segmentation, not exact dimensions/cell count       |
| Battery_Standard / Extended          | Sealed-box styling and seams; Extended shifted forward for clearance              | Fictional alternatives; real battery internals not externally photo-verifiable |
| Shield_Minimal / Standard / Heavy    | Mount tabs; Standard/Heavy enclosure resized around modules                       | Fictional dust/thermal guards, not real flight shields or combat armor         |
| Antenna_Std                          | One rear whip with restrained insulator/feed and tip                              | Engineering inference; selected photos do not directly verify whip hardware    |
| Antenna_HighGain                     | Concave reflector, feed and three support struts; clear of both arrays            | Recognizable dish construction, not exact flight antenna/photo matching        |
| Power_Nuclear                        | Broad segmented heat-rejection fins, compact end flanges, forward stand-off mount | NASA MMRTG hardware photo; fictional scaled package, not thermal certification |

## Verification

- Base 7,804 triangles, under 8,000. Bounds 2.700 x 3.000 x 2.1985 m; mast top Z=2.20 m.
- Six base wheels retain 0.525 m diameter, axle-centered origins, unit scales.
- 28 meshes, 18 part variants, nine chassis-parented sockets. Camera and Light preserved.
- 110 compatible part-pair BVH surface checks: zero intersections after corrections. Mutually exclusive same-socket alternatives and wheel templates excluded.
- Soil contact tip: world Z=0; radiation window normal: +Z.
- Seven MAT\_\* materials, differentiated Principled finishes, no image textures.
- All 19 GLBs exported successfully. Executed `node art/qa/verify_exports.cjs`: PASS.
- Validator checked GLB headers/chunks, finite positions, valid triangle indices, base 10 meshes/nine sockets/7,804 triangles, one neutral-transform mesh node per part, no textures/cameras/animations.
- Part GLBs use socket-local coordinates. Base GLB carries the named attachment sockets. Runtime consumers must respect alternative-slot exclusivity.

## References and Image Budget

Nine official NASA/JPL photos are retained in `references/`; direct URLs and credits are recorded in [mobility_realism_review.md](mobility_realism_review.md), [science_review.md](science_review.md), and [systems_review.md](systems_review.md). This includes wheel/suspension, mast, RIMFAX, Spirit solar array, Curiosity MMRTG installation, MEDA, RAD, and Mars 2020 MMRTG hardware.

Images inspected: first driver viewport 1; first specialist round 9; driver pre-fix sheets 2; second specialist round 6; final driver sheet 1. **Total 19.** No further image inspection in this session.

## Limits

No claim of complete photorealism or 1:1 flight-hardware replication. Direct photo evidence does not cover every fictional option, hidden internals, or exact antenna/spectrometer details. No animation/physics, joint articulation, suspension differential, enclosure-containment, thermal analysis, structural analysis, or target-app runtime test was performed. BVH tests detect surface intersections, not all containment or insufficient-clearance cases.

The correction script is a one-time migration from the pre-QA backup; append-style details must not be applied twice. Earlier before/after sheets and specialist reports are historical evidence; the final sheet, final scene, and this report supersede pre-repair concerns.
