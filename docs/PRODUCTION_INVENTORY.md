# Red Frontier production inventory

This is the reduced working inventory. It replaces the long-form planning HTML as the implementation checklist.

## Art and assets

### Facility

- Six locked spaces: Briefing, Corridor 01, Mars Intelligence, Corridor 02, Engineering Hangar, Mission Control.
- Reusable room kit, shared material library, decals, lighting, camera markers, and interaction markers.
- Room exports: `RF_<Room>.glb`, light manifests, route data, and door impostors.

### Rover

- Canonical game asset: `assets/rover/RF01_Rover.glb`.
- Source asset: `assets/rover/source/rover-q.glb`.
- Detailed reference build: `art/export/rover/perseverance/perseverance_rover.glb`.
- Future configuration variants: power, battery, shielding, antenna, wheels, and instruments.

### Mars

- Landing zone and return marker.
- Two science locations for the first playable Mars loop.
- Compact terrain, landmarks, scan targets, rocks, dust, sky, and horizon.

## Godot systems

### Foundation

- Pinned Godot 4.7 project.
- Facility streamer with adjacent-room loading.
- Quality presets for High, Laptop, and integrated GPUs.
- Shared material and texture resources.

### Next implementation

- Player movement and camera.
- Interaction prompt and marker system.
- Mission state: selected site, selected parts, mass, power, battery, science, health, budget, and launch lock.
- Hangar station controller for power, battery, shielding, mobility, communications, payload, and Digital Twin.
- Route objectives and scene handoff.
- Landing-site and rover configuration UI.

### Later implementation

- Offline Digital Twin evaluator.
- Launch transition.
- Mars driving and scanner.
- Dust storm choice.
- Mission scoring, explanations, and endings.

## Verification checklist

- `scripts/validate_scene.py`
- `scripts/export_material_library.py`
- `scripts/export_gltf.py`
- `scripts/godot_sync.py`
- `godot/tools/verify_shared.gd`
- `godot/tests/inspect_hangar.gd`
- `godot/tools/stream_stress.gd`
- `node art/qa/verify_perseverance_export.cjs`
- `node art/qa/verify_exports.cjs`

## Delivery order

1. Keep the locked facility and canonical RF01 rover stable.
2. Add player traversal and interactions.
3. Add Hangar configuration and launch lock.
4. Add site selection and Digital Twin.
5. Add Mars gameplay and outcome scoring.
6. Optimize the Hangar and validate the release renderer.

