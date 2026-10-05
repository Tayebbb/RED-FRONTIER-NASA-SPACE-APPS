# Rover integration record

## Asset comparison

| Property | `RF01_Rover` playable asset | Detailed Perseverance asset |
|---|---:|---:|
| Source | `art/export/rover/perseverance/perseverance_rover.glb` | `art/source/rover/perseverance_detailed.blend` |
| Godot export | `assets/rover/RF01_Rover.glb` | `art/export/rover/perseverance/perseverance_rover.glb` |
| GLB size | 12,096,576 bytes | 2,189,724 bytes |
| Nodes | 78 | 27 |
| Meshes | 65 | 18 |
| Materials | 48 | 8 |
| Embedded images | 23 | 23 |
| Animations | 0 | 0 |
| Gameplay contract | Existing linked asset and Hangar manifest | Wrapped through the existing RF01 asset path |
| Intended use | Legacy comparison | Canonical in-game rover source |

The detailed asset has the intended Perseverance-specific modeling. It is now wrapped and exported through the existing RF01 asset path, preserving the facility hierarchy and Hangar streaming assumptions while making the art model canonical.

## Existing integration

The facility builder links `assets/rover/RF01_Rover.blend` into the Hangar as the read-only `REF_RF01_Rover` collection. The Hangar export excludes linked rover geometry and writes the rover separately into `godot/assets/RF01_Rover.glb`.

The generated manifest records:

- Asset: `RF01_Rover.glb`
- Godot position: `(0.0, 0.12, -42.7424)`
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

The detailed export gate validates the canonical source model; the legacy gate validates the preserved modular archive.

## Canonical asset contract

The detailed asset is canonical. Future changes must preserve:

1. The documented transform and placement contract.
2. The `assets/rover/RF01_Rover.glb` runtime path.
3. Verified Hangar fit and visual inspection.
4. A Godot import and streaming pass.
5. Explicit compatibility between any future configuration system and the detailed model's static sockets.
