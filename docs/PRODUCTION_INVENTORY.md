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
- The mission simulation and the Digital Twin stress test. The current mission-state fields and test stand-ins are hooks, not a working simulator.
- Launch readiness, the launch decision, and the scene handoff. Launch vehicle and date choice are deferred.
- Mars operations: science targets, event decisions, dust and communications hazards, and a replay scene. Arcade driving is deferred.
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

The authoritative order and reasoning are in [the system design](SYSTEM_DESIGN.md#13-implementation-order). In summary:

1. Keep [the rules](RULES.md) and their tests in sync; move the formula constants into a `rules.json` content file.
2. Simplify mission state: store facts, derive the phase and objective, and remove the stored copies of derived numbers.
3. Package a Windows build that ships the lighting caches, and test it on a clean machine.
4. Build the deterministic mission simulation with golden-run tests.
5. Add the Digital Twin stress test, scoring, the results screen, and Replay.
6. Add the launch console, with the signal delay from the baked light-time table.
7. Replace prototype values with sourced data (sites, storm scenarios, an MMRTG power option) and record each source.
8. Build the Mars replay scene: the 2D fallback first, then 3D.
9. Improve Hangar lighting and draw-call performance, and add debug fast travel for demos.
