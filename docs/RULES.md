# Red Frontier Rules and Scoring v1.0

_Status: **authoritative** for game rules. The original "Rules and Scoring v1.0" document (4 Oct 2026, adopted 6 Oct 2026) is cited throughout the code but was never committed. This file rebuilds it from the implementation (`godot/game/data/rover_build.gd`, `rover_parts.json`, `landing_sites.json`, `game_config.gd`) and the reference runs in `godot/tests/rover_build_test.gd`. Section numbers match the citations in the code._

Architecture and ownership are defined in [SYSTEM_DESIGN.md](SYSTEM_DESIGN.md). Every value here is a **game-balance value**, not a NASA measurement, unless a source id is given. Masses are in game kilograms, and costs are in abstract credits.

**Change rule:** change a number here, in its JSON file, and in `rover_build_test.gd` together. The headless test is what enforces this document.

## 1. Scope

| Section | Covers | Status |
|---|---|---|
| §2 | Building RF-01 | Implemented |
| §3 | Build scores | Implemented |
| §4 | Mission simulation v1 | Implemented; scoring remains planned |
| §5 | Reference runs | Implemented as tests |

## 2. Building RF-01

### 2.1 Categories

| Category | Pick |
|---|---|
| Solar array | exactly 1 |
| Battery | exactly 1 |
| Shielding | exactly 1 |
| Antenna | exactly 1 |
| Instruments | exactly 3, all different |

Picking a part in a single-pick category replaces the previous one. Picking a selected instrument removes it. A fourth instrument is refused.

### 2.2 Legal build

A build can be accepted only when all of the following hold:

1. Every single-pick category has a part.
2. Exactly 3 instruments are selected.
3. Total mass ≤ **260 kg**.
4. Total cost ≤ **400 credits**.
5. A landing site is locked.

The player sees the problems in this order: missing categories, instrument count, `OVER MASS BY n KG`, `OVER BUDGET BY n CREDITS`, `NO LANDING SITE LOCKED`.

An accepted build can be edited until launch. Accepting a build with a different signature makes any Digital Twin result stale. The signature is the four single-pick ids plus the sorted instrument ids.

### 2.3 Part sheet

The source is `godot/game/data/rover_parts.json`. A blank cell means the part has no such attribute.

| Id | Name | Mass | Cost | Value | Other |
|---|---|---|---|---|---|
| `solar_light` | Light solar array | 30 | 40 | 20 | |
| `solar_high` | High-output solar array | 60 | 85 | 38 | |
| `battery_standard` | Standard battery | 35 | 50 | 25 | capacity 100 |
| `battery_extended` | Extended battery | 70 | 110 | 50 | capacity 200 |
| `shield_minimal` | Minimal shielding | 10 | 20 | 8 | |
| `shield_standard` | Standard shielding | 40 | 60 | 24 | |
| `shield_heavy` | Heavy shielding | 90 | 130 | 46 | |
| `antenna_standard` | Standard antenna | 20 | 30 | | reliability 0.60, draw 3 |
| `antenna_high_gain` | High-gain antenna | 45 | 90 | | reliability 0.95, draw 6 |
| `spectrometer` | Spectrometer | 25 | 70 | 20 | target `ancient_delta` |
| `ground_radar` | Ground radar | 30 | 60 | 16 | target `crater` |
| `hires_camera` | Hi-res camera | 15 | 35 | 12 | target `ridge` |
| `soil_analyzer` | Soil analyzer | 20 | 45 | 14 | target `rock_field` |
| `weather_sensor` | Weather sensor | 10 | 20 | 6 | passive_science 6 |
| `radiation_detector` | Radiation detector | 10 | 20 | 6 | passive_science 6, storm_damage −3 |

The `target`, `capacity`, `passive_science` and `storm_damage` attributes are inputs to the mission simulation (§4). They don't affect the build scores in §3.

## 3. Build scores

### 3.1 Inputs and clamp

`clamp(x)` limits every score to 0..100.

The landing sites below are **prototype** values (`landing_sites.json`, `provenance: PROTOTYPE`), pending sourced values:

| Site | science | solar | terrain_risk |
|---|---|---|---|
| Jezero Crater | 0.91 | 0.64 | 0.58 |
| Elysium Planitia | 0.62 | 0.86 | 0.30 |
| Gale Crater | 0.88 | 0.60 | 0.78 |

### 3.2 Formulas

`n` is the number of selected instruments. A score whose inputs aren't chosen yet is **null** and shown as "—", never as a number.

| Quantity | Formula | Needs |
|---|---|---|
| Mass, cost | Sum over all selected parts | — |
| Demand | `12 + 7 × n + antenna.draw` | Antenna |
| Supply | `solar.value × (0.6 + site.solar × 0.8)` | Site, solar |
| Power | `clamp((supply + battery.value × 0.5) / (demand × 1.8) × 100)` | Supply, demand, battery |
| Safety | `clamp(shield.value / 46 × 45 + (1 − site.terrain_risk) × 35 + antenna.reliability × 20)` | Site, shield, antenna |
| Build science | `clamp(site.science × 45 + Σ instrument.value)` | Site, at least one instrument |
| Engineering | `round(0.55 × power + 0.45 × safety)` | Power, safety |

[SYSTEM_DESIGN.md §12](SYSTEM_DESIGN.md) plans to move the constants (12, 7, 0.6, 0.8, 0.5, 1.8, 46, 45, 35, 20, 45, 0.55, 0.45) into a `rules.json` content file. The values must stay as listed here.

## 4. Mission simulation v1

`MissionSim.run(setup, targets, decisions, scenario_id)` is implemented as a pure, deterministic GDScript module. `setup` contains a locked site id, a legal accepted build, and a seed; targets are ordered instrument-site ids; decisions are `{sol, event, choice}` rows. It returns a stable per-sol log, final state, ending, cause, and `log_hash`. It does not read `MissionState`, scene state, frame time, or the network.

- **Step:** 100 sols. The authoritative constants and source rows are in `game/data/rules.json`.
- **Energy:** `solar.value × (0.6 + site.solar × 0.8) × 2 / (1 + tau)` is stored in battery capacity units. Each sol spends base, antenna, instrument, and action draw. A run creates one seeded random generator; it applies ±0.05 tau variation only on scenario baseline sols. Explicit historical storm tau values are never varied. The `solar_scale`, demand values, and battery units are game-balance values.
- **Science:** driving reaches one ordered target per sol. Matching instruments earn `instrument.value × site.science × 10`; passive instruments add `passive_science × 0.1` on active sols. Science enters a buffer before it is relayed.
- **Hazards:** terrain drive damage is reduced by shielding. A storm warning occurs at tau ≥ 3; continuing through it adds dust damage, reduced by the radiation detector. A depleted battery or health ends the run.
- **Comms:** a sol returns up to `20 × antenna.reliability × scenario relay multiplier` game data units. The nominal relay anchor is TGO, MRO, and Odyssey; MAVEN is excluded.
- **Decisions:** `storm_warning` accepts `hibernate` or `press_on`; `low_power` accepts `rest` or `drive`. At most one decision may be supplied for a sol. Missing choices use the conservative policy: hibernate during a storm and rest on low power.
- **Outcomes:** completing all 100 sols is `returned`; an early end after any data was returned is `partial`; an early end before data return is `lost`. The result carries the terminal sol and cause (`power_depleted` or `rover_damage`).
- **Scenarios:** `nominal`, `opportunity_2018`, and `relay_degraded` are bundled in `game/data/mission_scenarios.json`. Opportunity's tau 10.5 / 21 Wh observation, InSight's 5,000 / 500 Wh observations, current NASA relay volumes, and MDAD provenance are recorded in the rules file. They anchor scenario scale; RF-01 remains a game model, not an engineering prediction.

Digital Twin, scoring, results, and Mars presentation consume this core in later work.

## 5. Reference runs

These runs are checked by `godot/tests/rover_build_test.gd`:

```sh
godot --headless --path godot --script res://tests/rover_build_test.gd
```

| Run | Site | Build | Mass / cost | Power | Safety | Build science | Engineering |
|---|---|---|---|---|---|---|---|
| Breakthrough | Elysium | high solar, extended battery, minimal shield, standard antenna; spectrometer, ground radar, radiation detector | 225 / 395 | 100 (raw 114.1) | 44.33 | 69.9 | **75** |
| High-risk success | Jezero | high solar, standard battery, minimal shield, high-gain antenna; spectrometer, hi-res camera, weather sensor | 200 / 370 | 78.00 | 41.53 | 78.95 | **62** |
| Safe but limited | Elysium | high solar, standard battery, heavy shield, standard antenna; hi-res camera, soil analyzer, weather sensor | 250 / 395 | 94.82 | 81.5 | — | **89** |
| Same build at Gale | Gale | as "Safe but limited" | 250 / 395 | 82.62 | 64.7 | 71.6 | **75** |

A "—" means the test doesn't assert that value. The formula gives 59.9 for "Safe but limited".

The test file also checks these edge cases:

- **Empty build:** all scores are null, and every missing category is listed.
- **Partial build:** mass and cost are live, and the dependent scores wait for their inputs.
- **No landing site:** the build is not valid.
- **Over mass:** 310 kg reports `OVER MASS BY 50 KG`.
- **Over budget only:** 415 credits reports `OVER BUDGET BY 15 CREDITS`.
- **Fourth instrument:** it's refused.
- **Signature:** instrument order doesn't change it.
