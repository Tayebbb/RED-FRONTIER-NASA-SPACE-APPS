# Perseverance Detailed Build: Progress and Evidence

## Deliverables

- Separate working scene: `art/source/rover/perseverance_detailed.blend`.
- Assembled static GLB: `art/export/rover/perseverance/perseverance_rover.glb`.
- Export gate: `node art/qa/verify_perseverance_export.cjs`.
- Original hybrid scene, exports, and hybrid-only gate were not edited.

## Reference Sources

- NASA, [Perseverance Rover Components](https://science.nasa.gov/mission/mars-2020-perseverance/rover-components/). Specs used: 3.0 x 2.7 x 2.2 m body; aluminum 0.525 m wheels with 48 gently curved grousers and curved titanium spokes; 2.1 m, five-degree-of-freedom robotic arm; 0.64 m diameter x 0.66 m long aft MMRTG; 0.30 m hexagonal mid-aft port-side X-band high-gain antenna; deck-mounted UHF and X-band low-gain antennas.
- NASA/JPL-Caltech, [Perseverance Twin Drives Into the Mars Yard (PIA23966)](https://photojournal.jpl.nasa.gov/catalog/PIA23966). Local reference: `art/qa/references/nasa-perseverance-testbed-PIA23966.jpg`. Used for the overall rover silhouette, deck, wheel, suspension, and exposed-hardware character.
- NASA/JPL-Caltech, [The Tippy Top of Mars 2020 (PIA23316)](https://photojournal.jpl.nasa.gov/catalog/PIA23316). Local reference: `art/qa/references/nasa-perseverance-masthead-PIA23316.jpg`. Shows the large SuperCam aperture, two Mastcam-Z units, and outboard navigation cameras.
- NASA/JPL-Caltech, [Put a Bowtie on It! (PIA24206)](https://photojournal.jpl.nasa.gov/catalog/PIA24206). Local reference: `art/qa/references/nasa-perseverance-rimfax-PIA24206.jpg`. Supports the downward-facing underside RIMFAX antenna form and location.
- NASA/JPL-Caltech, [Mars 2020's MMRTG (PIA23306)](https://photojournal.jpl.nasa.gov/catalog/PIA23306). Local reference: `art/qa/references/nasa-mars2020-mmrtg-fins-PIA23306.jpg`. Supports an exposed, finned heat-rejection unit; this is a pre-installation hardware image, not a placement drawing.
- NASA/JPL-Caltech, [MEDA's Wind Sensor Springs Out (PIA24175)](https://photojournal.jpl.nasa.gov/catalog/PIA24175). Local reference: `art/qa/references/nasa-jpl-meda-wind-sensor-PIA24175.jpg`. Supports an exposed boom and compact sensor package, not exact dimensions or mounting coordinates.
- NASA/JPL-Caltech, [Robotic arm callout](https://science.nasa.gov/mission/mars-2020-perseverance/rover-components/). Local reference: `art/qa/references/nasa-perseverance-robotic-arm-callout.png`. Used for the long front arm and tool-turret arrangement.
- NASA/JPL-Caltech, [Curiosity and Perseverance wheel comparison](https://science.nasa.gov/mission/mars-2020-perseverance/rover-components/). Local reference: `art/qa/references/nasa-perseverance-wheel-comparison.jpg`. Supports the narrower Perseverance wheel and non-chevron tread treatment.

The references are used only for modeling guidance and source documentation. None is embedded as a rover surface texture or imported as a 3D asset.

## Modeled This Pass

- Forked the final hybrid scene into `perseverance_detailed.blend`; did not overwrite the hybrid.
- Replaced installed and spare wheel geometry with an aluminum barrel, 48 gently curved transverse grousers, open curved-spoke-style wheel faces, and machined hubs. All six remain 0.525 m diameter; modeled width is approximately 0.264 m.
- Reworked the mast face to show a large SuperCam aperture, two Mastcam-Z housings, and two outboard Navcam optics.
- Added an aft MMRTG approximation, three communications elements (0.30 m hexagonal HGA panel, UHF whip, low-gain unit), a static deployed robotic-arm pose and tool turret, an underside RIMFAX bowtie, a mast-side MEDA boom, and restrained external harness/fastener details.
- Replaced the broad rust chassis insert with ceramic white; differentiated satin aluminum, MLI-like gold, dark wheel metal, lens, and recess materials.
- Added smart UVs to all 36 scene meshes and packed 256 x 256 base-color maps for 11 material families. Eight flight materials also have packed roughness maps; seven have packed tangent normal maps. The maps are procedural, tileable surfaces with subtle variation, not photo-derived textures.
- Normalized the inherited frame in the new scene only. `SM_Chassis` is identity in world space, front is -Y, wheel centers are level at Z=0.264 m, wheel contact is Z=0.0015 m, and mast top remains Z=2.20 m.
- Legacy solar, battery, shield, and hybrid antenna/instrument options remain in the `.blend` as hidden templates and are excluded from the Perseverance GLB.

## Export Verification

Latest `node art/qa/verify_perseverance_export.cjs` result: PASS.

- GLB: 18 meshes, 56 primitives, 32,028 triangles, 23 embedded images.
- Every exported primitive has finite positions, normals, UVs, and valid triangle indices.
- Eight materials use base-color textures, seven use normal maps, and eight use metallic-roughness maps.
- Required chassis, mast, six wheels, robotic arm, MMRTG, antennas, RIMFAX, and MEDA nodes are present; non-flight alternatives are absent.
- No cameras, lights, or animations are exported.

The old `art/qa/verify_exports.cjs` remains specific to the hybrid and must not be changed to accept textures or a new triangle count.

## Fidelity Limits and Next Work

This is a reference-guided work in progress, not a verified 1:1 Perseverance replica. The chassis and rocker-bogie silhouettes still derive from the hybrid asset. Exact external panel geometry, instrument dimensions, antenna mechanisms, RTG fin segmentation/installation brackets, MEDA/RIMFAX dimensions, and cable routing are not established by the available photos. The robotic arm is a static pose, not a five-axis rig; its 1.96 m modeled reach and 25 mm ground clearance are visual approximations. Hidden internals, deployment motion, articulation, physical clearances, thermal behavior, and target-app rendering are unverified.

Next: refine the chassis/suspension and MMRTG from side/rear technical views; add remaining externally visible flight cameras/instruments only with source evidence; test clearances and arm-ground relationship; capture clean front/side/top/rear evidence; consider socket-local component exports after defining their transform contract.

Visual inspection ledger for this continuation: 17 images inspected, below the user's 20-image session cap.
