# Red Frontier System Design

_Status: **authoritative** for gameplay architecture from 2026-10-08. Where another document disagrees about how the game is built, this document wins. Rule numbers and formulas live in [RULES.md](RULES.md); art and environment decisions stay in [PLAN.md](PLAN.md) and [VISUAL_LANGUAGE.md](VISUAL_LANGUAGE.md)._

This design comes from a full audit of the repository on 2026-10-08. Each claim is tagged with where it comes from:

- **[R]** observed in the repository.
- **[V]** verified against an external primary or official source.
- **[I]** engineering inference, to be measured.
- **[D]** design decision.

## 1. Verdict

Red Frontier is a **single-player, offline Godot 4.7 game**. There is no backend, no network access, no LLM, no save system and no randomness anywhere in the runtime [R]. That is the right shape for the product, and it stays that way.

- **Strong today:** the six-room streamed facility, the shared material pipeline, and a pure, tested build evaluator (`game/data/rover_build.gd`).
- **Missing today:** everything after **ACCEPT BUILD**. The Digital Twin, launch, Mars, scoring, results and replay exist only as `MissionState` fields and comments [R]. The playable loop dead-ends at the "Run the Digital Twin" objective.

The plan is to finish the loop with the fewest moving parts possible:

> **One pure, deterministic, sol-by-sol mission simulation.** The Digital Twin runs it against named stress scenarios. The real mission runs it once. The Mars scene and results screen only present its log.

## 2. Requirements

Red Frontier is the team's entry for the **Space Mission Design Game Challenge** (NASA Space Apps Challenge 2026, 14–15 November 2026). These requirements come from the team's design. They must be checked against the official challenge statement when it is published on 28 October 2026 (§16).

### Functional (the complete game loop)

1. Briefing.
2. Lock a landing site.
3. Configure RF-01 within limits.
4. Run the Digital Twin and iterate.
5. Accept risk and launch.
6. Run Mars operations: choose targets and answer event decisions.
7. Read a results debrief that explains causes.
8. Replay.

### Non-functional

| Requirement | Target | Why |
|---|---|---|
| Works offline | 100% of gameplay | Judges and venues have unreliable networks |
| Reproducible outcome | Same setup, decisions and seed give a byte-identical result | Fairness, testing, explainable debrief |
| Traceable numbers | Every real-world value has a source row; game-balance values are labelled | Educational credibility ([DATA_LEDGER.md](DATA_LEDGER.md)) |
| Full loop length | About 10–12 minutes for a first-time player [D] | Judging slot |
| Facility frame rate | ≥30 fps on the Laptop preset with a dedicated GPU; ≥20 fps on the Integrated preset (Hangar today: 11–21 fps on Intel UHD [R]) | Playable demo |
| Simulation cost [I] | One mission run under 5 ms; one Twin assessment under 50 ms | Must feel instant; measure once built |
| Failure mode | Degrade visibly and keep running; never block the loop | Live demo |

### Size estimates [I]

| Item | Size |
|---|---|
| Gameplay content JSON | Under 1 MB |
| Optional Mars heightmap | 16 MB or less |
| Simulation state per run | About 100 sols × about 10 fields, a few KB |

There is no server traffic to estimate. The heaviest runtime resources are the facility's GPU memory (about 1 GB peak in the Hangar neighbourhood [R]) and the 35 MB Hangar VoxelGI cache [R].

## 3. Architecture

A modular monolith inside the one Godot project. Dependencies point downward only.

```
 ┌─────────────── content (JSON, read-only at runtime, baked offline with provenance) ──────────────┐
 │ rover_parts · rules · landing_sites · scenarios · science_targets · light_time · sources        │
 └──────────────────────────────────────────┬────────────────────────────────────────────────────────┘
                                            │ read
 ┌──────────────── core logic (pure GDScript: static / RefCounted, no Nodes, headless tests) ───────┐
 │ RoverBuild.evaluate()   MissionSim.run()   Twin.assess()   Scoring.score()                        │
 └──────────────────────────────────────────▲────────────────────────────────────────────────────────┘
                                            │ called by (never calls up)
              Mission (autoload): RunSetup + decisions, validated transitions, signals
                                            ▲ signals / intent calls
 ┌──────────────────────────────────────────┴────────────────────────────────────────────────────────┐
 │ presentation: facility (streamer, collision, interactions) · player · HUD · panels ·               │
 │               MarsReplay scene · Results screen                                                     │
 └─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Component contracts

| Component | Why it exists | Owns | Must not own | Talks to |
|---|---|---|---|---|
| Content JSON + loaders (`game/data/*.gd`) | Every number in one place with its source | Parts, sites, rules constants, scenarios, targets, light-time, source rows | Logic, mutable state | Core (read-only) |
| `RoverBuild` | One implementation of build rules | Validation, mass, cost, power, safety, build science, engineering | UI, stored state | Content |
| `MissionSim` | Consequences must be reproducible and testable | The outcome of a mission from `(setup, decisions, scenario, seed)` | Nodes, frame time, physics, rendering, RNG it did not create | Content, `RoverBuild` |
| `Twin` | Lets the player test before committing | A stress-test report: outcome per named scenario and the limiting subsystem | Its own physics; it only calls `MissionSim` | `MissionSim` |
| `Scoring` | Turns outcomes into a score and an explanation | Mission scores and an ordered cause list with source ids | Mechanics, presentation | Simulation result, content |
| `Mission` (autoload; today `MissionState`) | One authority for a run | Run facts and the validated transitions between them | Formulas, UI nodes, derived numbers | Core; emits signals |
| Facility (`facility/`, `game/world`, `game/interaction`) | The explorable mission centre | Streaming, collision, prompts | Game rules | `Mission` signals, interaction handlers |
| Panels and HUD (`game/ui`) | Player decisions and feedback | View state and working copies (an unsaved build) | Formulas, authoritative state | `Mission` intents, core for previews |
| `MarsReplay` scene | Shows the mission | Animation, camera, event prompts | Outcomes; it plays the log and never decides | `Mission` (result + decisions) |
| Results screen | Debrief | Layout | Score math | `Scoring` output |

### What is deliberately absent

There is no server, API, database, account system, LLM, web build, event bus, entity component system, plugin system or live NASA call at runtime. See §12.

## 4. State model and source of truth

Store **facts**. Derive everything else.

| State | Owner | Mutated by | Kind | Persisted | Notes |
|---|---|---|---|---|---|
| Content tables | `content/*.json` | Build-time scripts only | Static | In the repo | Validated on load; on failure, show a visible error plus a bundled default |
| `briefing_done` | `Mission` | `complete_briefing()` | **Authoritative** | Optional | |
| `site_id` | `Mission` | `lock_site(id)`; refused if unknown or already locked | **Authoritative** | Optional | |
| `build` (part ids) | `Mission` | `accept_build(b)`; refused if invalid or after launch | **Authoritative** | Optional | |
| `twin_signature` | `Mission` | `record_twin(signature)` | **Authoritative** | Optional | Marks which build the player tested |
| `launch` (date, seed) | `Mission` | `launch()`; only when the Twin is current | **Authoritative** | Optional | The seed defaults from the mission date (§7) |
| `ops_decisions` | `Mission` | `decide(sol, choice)` | **Authoritative** | Optional | A list of `(sol, choice)` pairs plus the target order |
| Build stats | `RoverBuild.evaluate(build, site)` | None (pure) | Derived | No | Never stored. Today `MissionState.mass/power/budget` are stored copies and must go. |
| Twin report | `Twin.assess(setup)` | None | Derived | No | Cached in memory by build signature |
| Mission result | `MissionSim.run(...)` | None | Derived | No | Recomputed from facts |
| Score and explanation | `Scoring.score(...)` | None | Derived | No | |
| Phase and objective | `Mission.phase()` | None | **Derived** from facts | No | Replaces the stored `mission_phase`, `current_objective` and five booleans |
| UI and render state | Each panel or scene | Itself | View | No | |

**Phase derivation** (first unmet step): `BRIEFING → LANDING_SITE → ROVER_CONFIG → DIGITAL_TWIN` (when `twin_signature != signature(build)`) `→ LAUNCH → MARS → RESULT`. The objective text is a lookup on the phase. Because the phase is derived, a stale Twin result or an out-of-sync flag can't happen.

**Persistence:** none is required. If it's added, save only the authoritative rows to `user://last_run.json` and recompute the rest. Save games stay out of scope.

## 5. Data flow

```
Player input ─▶ Panel (working copy) ─▶ RoverBuild.evaluate() for live preview
            ─▶ Mission.accept_build(build) ─▶ validate (RoverBuild) ─┬─ refused: panel shows problems
                                                                     └─ accepted: fact stored, signal emitted
Digital Twin console ─▶ Twin.assess(setup) ─▶ MissionSim.run(setup, policy, scenario_k) for each stress scenario
                     ─▶ report shown ─▶ Mission.record_twin(signature)
Launch console ─▶ Mission.launch() (requires a current Twin) ─▶ change scene to MarsReplay
MarsReplay ─▶ MissionSim.run(setup, decisions, scenario_from_seed) ─▶ log
           ─▶ animate until the next decision event ─▶ Mission.decide(sol, choice) ─▶ re-run from sol 0 ─▶ continue
End ─▶ Scoring.score(setup, result) ─▶ Results screen ─▶ Replay = Mission.reset() + facility scene
```

Re-running from sol 0 after each decision costs microseconds [I]. It removes the need for snapshots or partial-state bookkeeping, and it guarantees the replayed log matches the final result.

## 6. Simulation design

The rules and constants for the simulation go in [RULES.md §4](RULES.md#4-mission-simulation-planned). This section fixes the structure.

- **Time step:** one sol. A mission lasts a fixed number of sols, taken from the rules.
- **Inputs:** RunSetup `(site, build, mission_date, seed)`, the ordered science targets, the decision list, and the scenario.
- **Per-sol state:** battery (Wh), rover health, dust opacity (tau), position along the target route, science gathered, data buffered and data returned, and an event log.
- **Data already in the repo that the simulation consumes [R]:**
  - Instrument `site` tags (`ancient_delta`, `crater`, `ridge`, `rock_field`) define the four **science targets**. An instrument earns full science only at its matching target. That's what the "Useful at …" text in the build UI promises.
  - `passive_science`, used by the weather sensor and radiation detector.
  - `storm_damage`, used by the radiation detector.
  - Battery `capacity`.
  - Antenna `reliability` and `draw`.
  - Site `solar` and `terrain_risk`.
- **Player agency on Mars:**
  - Choose and order targets before the first drive.
  - Answer event decisions such as a storm warning ("hibernate" or "press on") or low battery ("rest" or "drive").
  - Each decision is a discrete `(sol, choice)` pair. Continuous driving doesn't affect the outcome.
- **Outcomes:** returned with science, partial (stranded but data returned), or lost. Each comes with the sol and the cause.
- **Calibration:** solar and dust behaviour is calibrated against sourced cases. Examples are Opportunity's 2018 storm energy collapse and InSight's dust loss. Their sources are in [DATA_LEDGER.md](DATA_LEDGER.md). The calibration constants are game-balance values and are labelled that way.

### Digital Twin = stress test (no Monte Carlo)

`Twin.assess` runs the same simulation with a default operations policy against a short, fixed list of **named scenarios**:

1. **Nominal season** at the chosen site.
2. **Real storm:** a recorded dust event, such as the 2018 global storm that ended Opportunity.
3. **Relay degraded:** one fewer relay orbiter.

It reports the outcome per scenario and the first limiting subsystem (power, thermal, comms, terrain, radiation). The existing `*_risk` fields become categorical LOW / MEDIUM / HIGH values derived from these margins.

This was chosen over a Monte Carlo percentage because a named result ("you survive a normal season but die on sol 14 of a 2018-class storm") is easier to understand, ties directly to real events, needs no randomness, and tests deterministically.

## 7. Determinism

- A single `RandomNumberGenerator` is created inside `MissionSim.run()` from the seed and passed down explicitly. Nothing else in core logic may use randomness.
- No `delta`, wall-clock time, frame count, physics or node state may enter the simulation.
- Iterate arrays in a defined order, and never iterate dictionary keys for logic that affects the outcome.
- **Seed:** derived from the mission date by default, so the same mission always gets the same Mars. An override (`-- seed N`) is available for testing. The seed and scenario name appear on the results screen.
- **Tests:** headless golden runs, in the same pattern as `tests/rover_build_test.gd`. A fixed input must produce a fixed outcome and log hash.

## 8. Content and external data

**Policy [D]:** no network access at runtime. Each external source is processed offline by a script into a small JSON or image file in the repo, with a source row. The Data Ledger's "target data pipeline" already describes this [R].

| Source | Use in game | Runtime form | Status |
|---|---|---|---|
| Landing-site values | Site science, solar, terrain | `landing_sites.json` with a source per value | Prototype values today [R]; replace with sourced values |
| JPL Horizons | Earth–Mars light time for the mission date | `light_time.json` (Appendix A of the Data Ledger) | Use the baked table. [V] The Horizons API documents 500 and 503 availability responses, so live use would be a demo risk. |
| Mars Dust Activity Database (CC BY 4.0) | Storm scenarios per site | `scenarios.json` | Planned |
| Opportunity and InSight power records | Calibrate dust and solar | Constants in `rules.json` with source ids | Planned; prefer NASA primary pages over secondary articles |
| Relay orbiter capacity | Comms scenario | Constants with source ids | MAVEN excluded. [V] Contact was lost on 2025-12-06, and it was declared unrecoverable in June 2026. |
| MMRTG fact sheet | Optional nuclear power part | One part row in `rover_parts.json` | Recommended addition. The Perseverance-inspired rover really uses an MMRTG, so a solar-only part sheet is a fidelity gap. |
| Perseverance waypoints | Results comparison ("median drive 46 m") | Snapshot statistics | Undocumented feed: snapshot it, never fetch it live |
| MOLA / HiRISE terrain | Optional Mars replay heightmap | One cropped heightmap, 16 MB or less | Deferred; a stylized terrain is acceptable |
| Mars Climate Database | Possible per-site climate | Summary values only, if used | Deferred: free for science, permission terms per LMD |
| Curiosity weather feed, Mars Trek tiles | Flavour | — | Not planned for runtime (feed lags; tiles need the network) |

## 9. AI

**No AI or LLM component at runtime [D].** Each candidate role was checked:

- **Mechanics, scoring, validity, physics and scientific facts** must be deterministic and sourced. A model can't be authoritative for any of them.
- **The debrief and explanations** come from simulation events and source rows. That makes them more accurate than generated text, works offline, and is instant.
- **Characters or dialogue** were already cut from the first milestone ([GAME_BRIEF.md](GAME_BRIEF.md)).

If a future version adds generated text, it must be optional, cosmetic, cached, and fed only by `Scoring` output. It must never write game state.

## 10. Rendering and performance

| Item | Decision |
|---|---|
| Renderer | **Keep Forward+.** [V] VoxelGI is Forward+-only, and Godot's Web export uses the Compatibility renderer only, so the approved look can't run in a browser. |
| Room streaming, staged loading, shared materials, impostors, presets | Keep as built [R] |
| Hangar | Measure VoxelGI 128 and 64 against the approved cameras. Atlas the per-decal materials (the room peaks at 1,260 draw calls [R]). A smaller GI grid also shrinks the 35 MB cache and the 70–145 ms load hitch. |
| Mars | Its own scene; the facility is unloaded first. Replay-style camera, one terrain mesh, no VoxelGI. A 2D map view of the same log is the low-end fallback. |
| Simulation | Never runs per frame. It runs once per decision. |
| Measurement | The existing `traverse` harness and `docs/traversal_reports.json`; change one variable at a time |

## 11. Reliability

| Risk | Evidence | Mitigation |
|---|---|---|
| Vulkan device loss on Intel UHD | About 1 in 10 automated traversals [R]; root cause unknown | Update the driver; try `--rendering-driver d3d12`; the Integrated preset; keep the recorded gameplay videos as the presentation fallback. [V] Public reports tie Intel device-loss errors to Forward+ and point to a driver change or Compatibility as workarounds; no engine fix is confirmed. |
| GI cache missing on a fresh checkout | Caches are gitignored and deleted by `godot_sync.py` on purpose; the first windowed visit bakes them on the main thread [R] | A release step bakes all four caches. The Windows export ships them. The README warns that a source run bakes once. Exported builds can't write `res://` [I], so the export must contain the caches. |
| No packaged build | No `export_presets.cfg` [R] | Add a Windows export preset and test on a machine that has never run the project |
| Walking at low frame rate during a demo | Hangar at 11–21 fps [R] | A debug-only fast-travel menu that jumps between interaction points |
| Corrupt or missing content | Loaders log `push_error` and return empty data [R] | Keep validation, show a visible in-game error, and fall back to the bundled default |
| Invalid transitions | `Mission` intent methods validate; the phase is derived | Covered by tests |
| Network or AI outage | None used | Not applicable |

## 12. Decisions

| Decision | Items |
|---|---|
| **KEEP** | Godot 4.7 Forward+; `RoverBuild.evaluate` and its tests; JSON content with validating loaders; `FacilityStreamer`, `FacilityCollision`, `InteractionManager`, `QualityPresets`; build `signature()` for Twin staleness; the offline-first stance; the Blender → GLB → `godot_sync.py` pipeline; the single configuration panel |
| **SIMPLIFY** | `MissionState` → `Mission`: store facts and derive phase and objective; replace the generic `set_value()` with intent methods |
| **RESTRUCTURE** | Move the constants inside `evaluate()` (12, 7, 0.6, 0.8, 0.5, 1.8, 46, 45, 35, 20, 0.55, 0.45) into `rules.json`; move live Mars state out of the autoload into the simulation result |
| **REMOVE** | Stored copies `mass`, `power`, `budget`; stored Mars fields (`battery`, `rover_health`, `science`, `data_integrity`); `GameConfig.RULE_CANDIDATES`; runtime plans for the Curiosity feed and Trek tiles |
| **REPLACE** | Monte Carlo Twin idea → named stress scenarios; free-driving outcome → discrete operations decisions |
| **ADD** | [RULES.md](RULES.md); `MissionSim`, `Twin`, `Scoring`; Digital Twin and launch console interactions; MarsReplay and Results scenes; Replay; baked data files with source rows; a Windows export and release checklist; debug fast travel |
| **DEFER** | Arcade driving (if built, it may only issue discrete "arrived at target" commands); landing-system choice (standard or precision); launch vehicle and date choice; a dedicated MOBILITY category; HiRISE terrain; Mars Climate Database values; save games; moving large media out of git |

**Hangar stations [D]:** the single configuration panel stays the one place to edit the build, because it shows every trade-off at once. Optionally, the SCIENCE, POWER and COMMS stations open the same panel focused on their category. MOBILITY has no parts and stays decor until a mobility category exists. The older station-by-station flow in [PLAN.md §4](PLAN.md) describes the environment's design intent, not gameplay to build.

## 13. Implementation order

| # | Work | Why first |
|---|---|---|
| 1 | Keep [RULES.md](RULES.md) current; move constants to `rules.json`, with the existing tests unchanged and passing | The specification and its tests must agree before the rules grow |
| 2 | `MissionState` → facts plus derived phase; drop stored copies; update `gameplay_smoke.gd` | Removes duplicated truth before more systems read it |
| 3 | Windows export preset, GI-cache release step, clean-machine test | Highest demo risk, independent of gameplay |
| 4 | `MissionSim` v1 (power, dust, drive, science targets, comms, terrain damage) with golden tests | The core of the missing half |
| 5 | `Twin` + `Scoring` + Digital Twin console + Results screen + Replay | Closes the loop end to end |
| 6 | Launch console (light time from the baked table) | The step between Twin and Mars |
| 7 | Sourced site values, storm scenarios, MMRTG part, `sources.json` | Turns the prototype values into evidence |
| 8 | MarsReplay scene (2D fallback first, then 3D) | Presentation after correctness |
| 9 | Hangar GI and draw-call pass; debug fast travel | Performance and demo polish |

## 14. Do not build

- A backend, REST API, database, login or analytics service.
- An LLM, agent or generated content that touches state, scoring, validity, physics or facts.
- Live calls to Horizons, NASA feeds or map-tile services at runtime.
- A web build of the facility.
- Real-time physics or frame-driven Mars outcomes.
- A generic event bus, entity component system, dependency-injection framework or plugin architecture for parts and sites.
- A save-game system beyond the optional authoritative-facts JSON.
- Shipping raw Mars Climate Database, HiRISE or MOLA products.
- Rocket cinematics or scientist NPCs.

## 15. Audit challenge log

The first audit pass was re-checked against the code before this document was written.

| Finding | Re-check | Final |
|---|---|---|
| The loop dead-ends after ACCEPT BUILD | No code sets `launch_confirmed`; `reset_mission()` is called only from tests | **Held** |
| The rules specification is missing | Only code and tests mention "Rules and Scoring v1.0" | **Held.** Reconstructed as [RULES.md](RULES.md) |
| GI caches are missing on a fresh checkout | `godot_sync.py` deletes them on purpose ("rebake on first load") | **Revised:** intentional for development. The gap is that no release step ships them. |
| `export/godot/` duplicates assets | It's the Blender export staging area that `godot_sync.py` copies from | **Revised:** a pipeline intermediate, not an error. The two `RF_MaterialLibrary.glb` copies differ, so one is stale; re-run the sync before release. |
| A Monte Carlo Digital Twin | Opaque percentages, randomness to tune, harder to explain | **Replaced** with named stress scenarios |
| Phase is the one stored value | Flags can be derived from facts (site, build, signatures), and the phase from those flags | **Strengthened:** store facts, derive the phase |
| Mars as a pure replay | Weakens the "drive on Mars" promise in the README | **Revised:** player agency is through target order and event decisions; arcade driving is deferred and limited to discrete commands |
| No AI | No runtime candidate passes the value test | **Held** |
| Hangar performance | Measured at 11–21 fps on Intel UHD [R]; a dedicated GPU was not measured | **Held,** and also measure on a dedicated GPU |

## 16. Open questions

- **Challenge:** the team has confirmed the entry is the **Space Mission Design Game Challenge** (NASA Space Apps Challenge 2026). NASA's registration timeline says full challenge statements and their NASA and partner datasets come out on **28 October 2026**. On that date, check §2 Requirements, the MVP scope and the data plan against the official statement and its required datasets, and record any change here.
- Whether pre-event work such as data-preparation scripts is allowed under Space Apps rules (already open in the Data Ledger).
- Art sign-off for a lower Hangar VoxelGI resolution.
- Game-balance mass and cost for an MMRTG part.
- A primary source for the Gale landing ellipse.
- Permission terms before any Mars Climate Database values are shipped.

## Sources

- [Godot: Exporting for the Web](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html)
- [Godot: Using VoxelGI](https://docs.godotengine.org/en/stable/tutorials/3d/global_illumination/using_voxel_gi.html)
- [JPL Horizons API documentation](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
- [The Planetary Society: NASA has lost a spacecraft around Mars](https://www.planetary.org/articles/nasa-has-lost-a-spacecraft-around-mars)
- [Godot issue: Vulkan device lost](https://github.com/godotengine/godot/issues/71929)
