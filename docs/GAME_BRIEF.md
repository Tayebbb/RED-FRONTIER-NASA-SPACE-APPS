# Mission: Red Frontier

## Current product direction

Red Frontier is a NASA Space Apps mission-design game. The player starts in a NASA-style facility, works backward from a science question, selects a landing site, configures a rover under constraints, evaluates the mission with a Digital Twin, accepts risk, launches, drives on Mars, and receives an outcome explanation.

The first playable milestone is smaller and concrete:

1. Traverse the six-room facility.
2. Inspect the mission briefing and landing-site information.
3. Enter the Engineering Hangar and view the rover on its turntable.
4. Configure the rover through station interactions.
5. Lock the configuration and hand off to launch.

Mars driving, the full Digital Twin, and the final scoring loop follow after this base loop is stable.

## Facility route

| Order | Room | Player purpose |
|---|---|---|
| 1 | Briefing | Mission question, constraints, and objective |
| 2 | Corridor 01 | Transition |
| 3 | Mars Intelligence | Landing-system and site selection |
| 4 | Corridor 02 | Build-up to the rover reveal |
| 5 | Engineering Hangar | Rover configuration, stations, and Digital Twin |
| 6 | Mission Control | Confirmation and `ACCEPT RISK & LAUNCH` |

The room geometry is locked and streamed as a route. The Hangar is the main rover gameplay space.

## Rover decision

The detailed Perseverance model in `art/export/rover/perseverance/perseverance_rover.glb` is the canonical playable rover. It is exported through the existing `assets/rover/RF01_Rover.glb` runtime path so the Hangar manifest and room streaming continue to work.

## Recommended MVP scope

- One shared facility route; no room loading screen.
- Three landing sites represented as data and UI before adding site-specific terrain.
- Rover choices for power, battery, shielding, communications, mobility, and payload.
- A constrained loadout with visible trade-offs in mass, power, science, and risk.
- Offline Digital Twin evaluation before adding a server.
- Arcade Mars driving with two science locations and return-to-base.
- Dust storm decision as the first hazard.
- Outcome screen explaining the score and the consequences of the player's choices.

## Explicit cuts for the first milestone

Rocket cinematics, scientist NPCs, solar and thermal hazard systems, save games, tutorial content, real-time API hosting, and high-fidelity terrain are not required to prove the facility-to-Hangar game base.

## Current status

### Complete

- Six facility spaces and their locked visual language.
- Blender-to-GLB-to-Godot export pipeline.
- Shared materials and textures.
- Adjacent-room streaming.
- Canonical RF01 rover placed on the Engineering Hangar turntable.
- Hangar rover manifest and Godot streamer dependency.
- Rover and facility QA scripts.

### Remaining

- Player controller and interaction prompts.
- Persistent mission state and station configuration.
- Landing-site selection UI.
- Digital Twin evaluation.
- Launch lock and scene handoff.
- Mars scene, driving, hazard, scoring, and outcome flow.
- Performance retest on an updated driver or alternate renderer.
