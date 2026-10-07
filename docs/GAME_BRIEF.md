# Mission: Red Frontier

This brief describes the complete game we are building. The implementation status near the end distinguishes the current playable prototype from the planned mission systems; it does not narrow the product vision.

## Current product direction

Red Frontier is a space mission-design game created for the Space Mission Design Game Challenge of NASA Space Apps Challenge 2026. The player starts in a mission facility, works backward from a science question, selects a landing site, configures a rover under constraints, evaluates the mission with a Digital Twin, accepts risk, launches, drives on Mars, and receives an outcome explanation.

The first playable milestone is smaller and concrete:

1. Traverse the six-room facility.
2. Inspect the mission briefing and landing-site information.
3. Enter the Engineering Hangar and view the rover on its turntable.
4. Configure the rover at the Hangar configuration console.
5. Lock the configuration and hand off to launch.

The Digital Twin, launch, Mars operations, and the scoring loop follow after this base loop is stable, in the order set by [the system design](SYSTEM_DESIGN.md#13-implementation-order).

## Facility route

| Order | Room               | Player purpose                                  |
| ----- | ------------------ | ----------------------------------------------- |
| 1     | Briefing           | Mission question, constraints, and objective    |
| 2     | Corridor 01        | Transition                                      |
| 3     | Mars Intelligence  | Landing-system and site selection               |
| 4     | Corridor 02        | Build-up to the rover reveal                    |
| 5     | Engineering Hangar | Rover configuration, stations, and Digital Twin |
| 6     | Mission Control    | Confirmation and `ACCEPT RISK & LAUNCH`         |

The room geometry is locked and streamed as a route. The Hangar is the main rover gameplay space.

## Rover decision

The detailed Perseverance model in `art/export/rover/perseverance/perseverance_rover.glb` is the canonical playable rover. It is exported through the existing `assets/rover/RF01_Rover.glb` runtime path so the Hangar manifest and room streaming continue to work.

## Recommended MVP scope

The architecture behind this scope is defined in [the system design](SYSTEM_DESIGN.md), and the numbers in [the rules](RULES.md).

- One shared facility route; no room loading screen.
- Three landing sites represented as data and UI before adding site-specific terrain.
- Rover choices for solar power, battery, shielding, communications, and three instruments, edited in the single Hangar configuration panel. Mobility choices are deferred.
- A constrained loadout with visible trade-offs in mass, power, science, and risk.
- One offline, deterministic, sol-by-sol mission simulation. The Digital Twin runs it against named stress scenarios (a nominal season, a real recorded dust storm, a degraded relay). The real mission runs it once.
- Mars operations as decisions: choose the order of the science targets (Ancient Delta, Crater, Ridge, Rock Field), then answer storm, power, and comms events. The Mars scene replays the simulation's log, and a 2D map view is the fallback.
- Dust storm decision as the first hazard.
- Outcome screen explaining the score and the consequences of the player's choices, built from simulation events and their data sources.

## Explicit cuts for the first milestone

Rocket cinematics, scientist NPCs, save games, tutorial content, real-time API hosting, live NASA data calls, AI or LLM features, a web build, and high-fidelity terrain are not part of the MVP. Arcade driving, landing-system choice, and launch vehicle or date choice are deferred. If arcade driving is added later, it may only send discrete commands, such as arriving at a target, to the simulation.

## Current implementation snapshot

### Playable foundation

- Six finished and streamed facility spaces with the approved visual language.
- Blender-to-GLB-to-Godot pipeline, shared materials, collision, and integrated-GPU presets.
- First- and third-person facility traversal with marker-based prompts.
- Briefing interaction and landing-site selection UI. The current site scores are explicitly marked prototype values, not NASA measurements.
- Hangar rover configuration UI with game-balance calculations for mass, budget, power, safety, and science.
- Canonical Perseverance-inspired rover integrated into the Hangar, with separate source and export QA.
- Mission-state hooks and a full facility route test through Mission Control.

### Planned game systems

- Source-backed terrain, landing, climate, dust, communications, and rover-performance data in the decisions that use them.
- A Digital Twin that stress-tests the build with the shared mission simulation against named scenarios, supports iteration, and explains the limiting subsystem.
- Mission readiness, launch confirmation, and the Earth–Mars signal delay from the baked light-time table. Launch vehicle and date choice are deferred.
- A Mars surface scene that replays the mission simulation: science targets, energy management, and event decisions.
- Dust-storm and communications events with meaningful player choices.
- A results and debrief loop that explains outcomes and compares decisions with real mission evidence, plus Replay.
- A packaged Windows build, and a performance retest on an updated driver or alternate renderer.
