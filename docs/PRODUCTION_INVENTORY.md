# Red Frontier Production Inventory

This inventory covers the complete intended game and separates shipped foundation from planned gameplay. For the player-facing concept, see [the game brief](GAME_BRIEF.md).

## Complete Game Loop

1. Brief the player on a science objective and mission constraints.
2. Analyze Mars and select a landing system and site.
3. Configure a rover for the site, payload, power, mass, communications, and budget limits.
4. Run a Digital Twin, compare predicted outcomes, and iterate on the build.
5. Select a launch opportunity, review mission readiness, and accept the risk.
6. Drive on Mars, operate instruments, manage power and communications, and respond to hazards.
7. Return, score the mission, and explain how the player's decisions shaped the result.

## Implemented Foundation

### Facility and assets

- Six completed spaces: Briefing, Corridor 01, Mars Intelligence, Corridor 02, Engineering Hangar, and Mission Control.
- Blender builders and a validated Blender-to-GLB-to-Godot pipeline.
- Shared materials and textures, adjacent-room streaming, collision, route data, and GPU quality presets.
- Canonical runtime rover: `assets/rover/RF01_Rover.glb`, sourced from `art/export/rover/perseverance/perseverance_rover.glb`.
- First- and third-person traversal, interaction markers, prompts, and briefing flow.
- Landing-site selection and Hangar rover-configuration interfaces. Their current decision values are prototypes/game-balance values, not NASA measurements.
- Automated facility-route and rover-build checks.

### In progress / not yet implemented

- Source-backed site, climate, terrain, dust, communications, and rover-performance values in runtime systems.
- Digital Twin evaluator; current mission-state fields and test stand-ins are hooks, not a working simulator.
- Launch selection, date-driven mission timeline, launch decision, and scene handoff.
- Mars terrain and driving, instrument/science targets, return-to-base loop, and dust/communications hazards.
- Mission scoring, debrief, decision explanations, and comparison to real rover evidence.

## Verification

From the repository root:

```sh
godot --path godot -- gameplay_test full
godot --headless --path godot --script res://tests/rover_build_test.gd
node art/qa/verify_perseverance_export.cjs
node art/qa/verify_exports.cjs
```

Additional facility checks include `scripts/validate_scene.py`, `scripts/godot_sync.py`, `godot/tools/verify_shared.gd`, `godot/tests/inspect_hangar.gd`, and `godot/tools/stream_stress.gd`. Runtime performance and the Intel Vulkan caveat are documented in [game readiness](GAME_READINESS.md).

## Recommended Delivery Order

1. Integrate and cite approved source-backed planetary and rover data.
2. Implement and validate the Digital Twin against the rover-build model.
3. Complete mission setup, launch readiness, and the launch decision.
4. Build the Mars surface traversal and science-objective loop.
5. Add hazards, communications decisions, scoring, and the player debrief.
6. Validate performance and the complete end-to-end mission on supported hardware.
