# Rover integration record

## Asset comparison

| Property | `RF01_Rover` playable asset | Detailed Perseverance asset |
|---|---:|---:|
| Source | `assets/rover/source/rover-q.glb` | `art/source/rover/perseverance_detailed.blend` |
| Godot export | `assets/rover/RF01_Rover.glb` | `art/export/rover/perseverance/perseverance_rover.glb` |
| GLB size | 12,096,576 bytes | 2,189,724 bytes |
| Nodes | 78 | 27 |
| Meshes | 65 | 18 |
| Materials | 48 | 8 |
| Embedded images | 23 | 23 |
| Animations | 0 | 0 |
| Gameplay contract | Existing linked asset and Hangar manifest | No facility socket/configuration contract |
| Intended use | Canonical in-game rover | Visual fidelity/reference candidate |

The detailed asset has strong Perseverance-specific modeling and a smaller export, but replacing the facility asset immediately would remove the existing hierarchy and integration assumptions. The RF01 asset is therefore canonical for the playable base.

## Existing integration

The facility builder links `assets/rover/RF01_Rover.blend` into the Hangar as the read-only `REF_RF01_Rover` collection. The Hangar export excludes linked rover geometry and writes the rover separately into `godot/assets/RF01_Rover.glb`.

The generated manifest records:

- Asset: `RF01_Rover.glb`
- Godot position: `(-0.0164, 0.12, -42.8131)`
- Y rotation: approximately `-28` degrees
- Hangar footprint: `x=-9..9`, `z=-55..-33`

`godot/facility/facility_streamer.gd` treats the rover as a Hangar dependency. It loads and unloads the rover with the Hangar, and its warm-up path compiles the rover materials before traversal.

## Rebuild and verification

```powershell
blender -b --factory-startup --python scripts/build_rover_asset.py
blender -b assets/rover/RF01_Rover.blend --python scripts/export_rover_glb.py
blender -b blender/RF_Facility.blend --python scripts/export_gltf.py -- Hangar
python scripts/godot_sync.py
Godot --headless --path godot --script res://tests/inspect_hangar.gd
```

The standalone rover QA gates remain:

```powershell
node art/qa/verify_perseverance_export.cjs
node art/qa/verify_exports.cjs
```

These validate the detailed and legacy art deliverables independently; they do not imply that the detailed model is the current game asset.

## Replacement gate

The detailed asset may become canonical only after it has:

1. A documented transform and placement contract.
2. Equivalent named attachment points for station configuration.
3. A verified Hangar fit and visual inspection.
4. A Godot import and streaming pass.
5. A decision to update the facility source rather than silently diverge two rover definitions.

