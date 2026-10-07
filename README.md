# RED FRONTIER

### A Space Mission Design Game by Team AUSThir | NASA Space Apps Challenge 2026

Build a rover around a science question, choose where it lands, then find out whether the mission can survive Mars.

<p align="center">
  <img src="renders/hangar_LOCKED/01_Entrance.png" alt="The Red Frontier Engineering Hangar and Perseverance-inspired rover" width="100%">
</p>

**Red Frontier** is a space mission-design game about making connected engineering and science decisions under uncertainty. Its first mission is to plan and operate a rover expedition to Mars, from the science briefing through site selection, rover design, simulation, launch, surface operations, and a final explanation of the outcome.

> This is an independent student project created for the Space Mission Design Game Challenge of NASA Space Apps Challenge 2026. It is not a NASA product and is not endorsed by NASA.

## The Mission

The player starts with a science objective, not a prebuilt rover. Every later decision should serve that objective and respond to Mars conditions.

1. **Understand the mission.** Read the science question, constraints, and success criteria in the Briefing room.
2. **Choose a landing strategy.** Compare landing systems and candidate sites using terrain, science value, sunlight, and risk. The current site-selection values are prototypes; source-backed values are part of the planned data integration.
3. **Engineer the rover.** Select solar power, battery, shielding, communications, and three science instruments. Trade mass, budget, power demand, capability, and risk. A mobility category is planned for later.
4. **Test the design.** Run the Digital Twin: the same mission simulation the real mission uses, tested against named scenarios (a normal season, a real recorded dust storm, a degraded relay). Use the results to revise the rover before committing.
5. **Accept the risk and launch.** Review mission readiness, including the real Earth–Mars signal delay for the mission date, and make the launch decision.
6. **Operate on Mars.** Choose which science targets to visit and in what order, then make the calls when dust, low power, or communications problems arrive: preserve the rover or press on.
7. **Learn from the outcome.** See what the rover achieved, which decisions mattered, and how the result compares with real mission evidence.

The game is being built in stages. The complete mission above is the project goal; the current playable build is a facility-and-rover-configuration prototype. Planned systems are described as plans, not as completed gameplay.

## Visual Tour

<table>
  <tr>
    <td><img src="renders/briefing_review/CAM_Briefing_Hero.png" alt="Mission briefing room" width="100%"></td>
    <td><img src="renders/mars_intel_review/CAM_MarsIntel_Hero.png" alt="Mars Intelligence and landing-site table" width="100%"></td>
  </tr>
  <tr>
    <td><img src="renders/hangar_LOCKED/03_Rover.png" alt="Rover in the Engineering Hangar" width="100%"></td>
    <td><img src="renders/mission_control_review/CAM_MissionControl_Hero.png" alt="Mission Control launch console" width="100%"></td>
  </tr>
</table>

## Gameplay Recordings

- [Watch the first-person facility and mission flow](renders/demo/Red_Frontier_Gameplay_FPP.mp4)
- [Watch the third-person facility and mission flow](renders/demo/Red_Frontier_Gameplay.mp4)

Both recordings show the current prototype, not the complete planned Mars-driving game.

## What Is Playable Now

- Six connected 3D facility spaces, streamed as the player walks: Briefing, Corridor 01, Mars Intelligence, Corridor 02, Engineering Hangar, and Mission Control.
- First- or third-person facility traversal, interaction prompts, briefing flow, and landing-site selection.
- A rover configuration panel with live mass, budget, power, safety, and science trade-offs.
- A reference-guided, Perseverance-inspired rover displayed in the Engineering Hangar.
- Automated gameplay coverage for the facility route, mission interactions, and rover-build rules.

Landing-site scores and rover configuration values are game prototypes. They are not NASA measurements or engineering specifications. The Digital Twin, launch, Mars operations, scoring, and results loop remain planned: the current build ends after the rover configuration is accepted.

## How It Is Built

Red Frontier is a single-player, offline Godot game. It needs no server, network connection, or AI service.

- **Rules** are pure functions with headless tests ([rules](docs/RULES.md)).
- **One deterministic, sol-by-sol mission simulation** (planned) drives the Digital Twin, the Mars mission, and the debrief. The same setup and seed always produce the same outcome.
- **Content** is JSON in the repository. Real-world values are prepared offline from NASA and partner data, and each one carries its source.
- **The 3D facility and Mars scenes** present the results. They never decide them.

The [system design](docs/SYSTEM_DESIGN.md) is the authoritative architecture and implementation plan.

## Project Structure

| Path                      | Purpose                                                                      |
| ------------------------- | ---------------------------------------------------------------------------- |
| `godot/`                  | Playable Godot project, streamed facility, UI, and game systems              |
| `blender/` and `scripts/` | Facility source scenes, procedural builders, exports, and validation         |
| `assets/rover/`           | Rover wrapper and Godot runtime asset                                        |
| `art/`                    | Rover modeling work, exports, reference credits, and QA reports              |
| `docs/`                   | Game concept, roadmap, data strategy, visual language, and readiness reports |
| `renders/`                | Facility review images and gameplay recordings                               |

See the [documentation index](docs/README.md) for the design brief, data provenance, asset integration, and test evidence.

## Run the Prototype

### Requirements

- Godot 4.7
- Windows, macOS, or Linux with a Vulkan-capable GPU; integrated-GPU quality settings are selected automatically where supported.

Clone the repository, open the `godot/` folder in Godot, and run the project. From a terminal at the repository root:

```sh
godot --path godot
```

To start in first person:

```sh
godot --path godot -- fpp
```

**Controls:** WASD to move, Shift to run, mouse to look, E to interact, Esc to release the mouse (click to capture again). F3 toggles streaming diagnostics.

**First run:** the lighting (VoxelGI) caches are not stored in git. The first windowed visit to each room bakes and saves its cache, so expect a one-time pause, the longest in the Engineering Hangar. Later runs load the caches.

The standalone facility viewer is available with:

```sh
godot --path godot res://viewer/hangar_viewer.tscn
```

On Windows, `Open_Hangar_In_Godot.bat` is a convenience launcher. Set `GODOT_EXE` to a Godot 4.7 executable path if it is not on `PATH`.

## Verify

Run from the repository root:

```sh
godot --path godot -- gameplay_test full
godot --headless --path godot --script res://tests/rover_build_test.gd
node art/qa/verify_perseverance_export.cjs
node art/qa/verify_exports.cjs
```

The gameplay test traverses the full facility route and exercises the current mission UI. The Node.js export checks cover the detailed Perseverance-inspired model and the separate preserved hybrid baseline.

## Build the Facility Assets

The checked-in Godot project can be run without rebuilding the Blender source. To regenerate facility textures and assets, install Python with NumPy and Pillow, Blender, and Godot 4.7, then use the scripts under `scripts/`:

```sh
python -m pip install numpy Pillow
python scripts/gen_textures.py
blender -b --factory-startup --python scripts/build_facility.py
blender -b blender/RF_Facility.blend --python scripts/validate_scene.py
blender -b blender/RF_Facility.blend --python scripts/export_material_library.py
blender -b blender/RF_Facility.blend --python scripts/export_gltf.py -- Hangar
python scripts/godot_sync.py
```

Repeat the GLB export command for `Briefing`, `Corridor01`, `MarsIntel`, `Corridor02`, and `MissionControl` as needed. See [the facility plan](docs/PLAN.md) before rebuilding locked environments.

## Mars Data and Evidence

The design goal is to make consequential gameplay decisions traceable to planetary and mission data. The repository contains a research ledger and candidate sources for terrain, weather, dust storms, rover performance, and communications. Researching a dataset does not mean it is already integrated into the game.

- The game makes no live data calls. Source data is processed ahead of time into small files that ship with the game, so it works offline and every number can be checked.
- Current landing-site values are marked `PROTOTYPE` in [`landing_sites.json`](godot/game/data/landing_sites.json).
- The [data ledger](docs/DATA_LEDGER.md) separates the intended data-driven game from current prototype behavior and tracks source checks, licensing, and integration work.
- The [data-source register](docs/DATA_SOURCES.md) links NASA, JPL, USGS, ESA, and research sources.
- Rover model references, credits, and fidelity limits are documented in the [Perseverance build report](art/qa/PERSEVERANCE_BUILD_REPORT.md).

## Team AUSThir

- Md Tayeb Ibne Sayed
- Fairuz Anadi
- Samprity Haque
- Syed Mohammed Sazid Ullah
- Pantha Protick
- Md. Saidul Islam Shehab

## Credits and Licensing

NASA/JPL source material is credited in the relevant data and rover QA documents. NASA names and imagery do not imply endorsement; third-party media and datasets retain their own terms and are excluded from the project licenses unless explicitly stated otherwise.

- Original source code: [MIT License](LICENSE)
- Original art, models, documentation, and project media: [Creative Commons Attribution 4.0 International](LICENSE-ASSETS.md)
- Third-party sources and attribution notes: [docs/DATA_SOURCES.md](docs/DATA_SOURCES.md) and `art/qa/`

The rover is a visual approximation inspired by NASA's Perseverance, not an exact or engineering-certified replica. See its [build report](art/qa/PERSEVERANCE_BUILD_REPORT.md) for evidence and limitations.
