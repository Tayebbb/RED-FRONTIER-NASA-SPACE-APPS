# Red Frontier Data Strategy and Integration Roadmap

_Red Frontier · Data research brief · NASA Space Apps Challenge 2026_

This document maps candidate NASA and partner data to the complete game concept, records source checks, and tracks future integration work. Source research is not proof that a dataset is already used by the playable prototype. Source checks summarized here were reviewed on **5 October 2026**.

> Design goal: make mission decisions traceable to planetary and rover evidence. Current landing-site values are explicitly marked as prototypes, not NASA measurements.

|        |                                           |
| ------ | ----------------------------------------- |
| **14** | candidate datasets inventoried            |
| **6**  | priority source groups researched         |
| **5**  | proposed data-driven gameplay concepts    |
| **17** | source/value claims reviewed, 3 corrected |

**Contents:** [1 · Big picture](#1--the-big-picture) · [2 · Unique ideas](#2--out-of-the-box) · [3 · Data, drawn](#3--real-numbers-drawn) · [4 · Dataset list](#4--the-dataset-list) · [5 · Checks & next steps](#5--checks--next-steps) · [Sources](#sources)

---

## 1 · The big picture

### Intended data flow through the complete game

These are target integrations for the full mission, not a claim that all six systems are implemented today.

| Step                      | Intended gameplay                                                                      | Candidate datasets                                                                               | Current implementation                                                                                             |
| ------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| **1. Pick a site**        | Compare science opportunity, sunlight, terrain, storms, and temperature.               | MOLA/HiRISE terrain, Mars Dust Activity Database, Mars Climate Database, landing-ellipse studies | Landing-site UI exists; its current scores are prototype values, not NASA-derived.                                 |
| **2. Build the rover**    | Balance mass, power, budget, communications, and science capability.                   | Rover engineering facts, climate data, Opportunity solar-dust study                              | Configuration UI and game-balance rules exist; source-backed engineering values remain to be integrated and cited. |
| **3. Launch**             | Choose a vehicle and launch date; use mission geometry for cruise and signal delay.    | Launch vehicle/trajectory sources, JPL Horizons                                                  | Planned; no playable launch or date-driven mission system yet.                                                     |
| **4. Drive on Mars**      | Traverse Jezero terrain, visit science targets, and compare against real rover travel. | MOLA/HiRISE terrain, Perseverance waypoints, MEDA                                                | Planned; no Mars driving or source-backed route simulation yet.                                                    |
| **5. Storm and blackout** | Manage solar loss, dust events, and communication delays.                              | Mars Dust Activity Database, Mars Climate Database, JPL Horizons, Opportunity/InSight records    | Planned; these hazards are not currently simulated.                                                                |
| **6. Results**            | Explain mission outcomes and compare decisions with real missions.                     | Opportunity/InSight cases, Perseverance traverse, ESA partner sources                            | Planned; scoring, outcome explanation, and comparison are not implemented.                                         |

---

## 2 · Out of the box

### Play against real Mars history

These are proposed differentiators for the full game. They are research-backed design directions, not features in the current playable prototype.

**Proposed implementation priority:** ③ The clock follows real Mars · ② Relive Opportunity's last storm · ① Real panoramas at real places

#### 01 · Real panoramas at real places _(planned)_

_Data: Perseverance waypoints_

- **The player** reaches a spot Perseverance really visited and sees the panorama Perseverance took there.
- **Why it stands out:** The game world turns into real Mars photos. The route file already links a panorama to each stop.
- ⚠️ **Watch:** Panoramas are large and come from an undocumented feed. Download and shrink 3–4 of them in advance; credit NASA/JPL-Caltech.

#### 02 · Relive Opportunity's last storm _(planned)_

_Data: Real power-loss cases · Opportunity dust study_

| Date        | Energy         |
| ----------- | -------------- |
| 1 Jun 2018  | 645 Wh per sol |
| 10 Jun 2018 | 22 Wh per sol  |

Dust opacity (tau) reached **10.8**; normal is about 0.5.

- **The player** unlocks a scenario that replays June 2018. Can a different build survive the storm that ended Opportunity?
- **Why it stands out:** It rewrites real history, and shows exactly why nuclear power matters.

#### 03 · The clock follows real Mars _(planned)_

_Data: JPL Horizons_

- **The player** gets a blackout and cruise time based on the real Earth–Mars distance on the day they play: **11.0 min** during the hackathon, **5.6 min** in Feb 2027, **20.1 min** in May 2028.
- **Why it stands out:** The same game plays differently depending on the date, and judges can check the number themselves. The blackout needs this anyway.

Chart: Earth–Mars one-way light time in minutes, from the JPL Horizons API, sampled every two weeks from Oct 2026 to Dec 2028 (full table in [Appendix A](#appendix-a--earthmars-light-time-table)).

#### 04 · Race Perseverance's ghost

_Data: Perseverance waypoints · Jezero terrain_

- **The player** sees a faint trail of the real route on Jezero. Results: _"You drove 640 m in 3 sols. Perseverance's median drive is 46 m."_
- **Why it stands out:** A real benchmark makes players curious about how the real rover did it.

#### 05 · Real storms, not random ones

_Data: MDAD storm database_

> Mars Year 30: "This storm really happened."

- **The player** faces storms taken from the real record (place, size, season). The results screen names the Mars Year it happened.
- **Why it stands out:** Storms become history instead of dice rolls, and give the daily mission a natural seed.

### More ideas

| Idea                             | Description                                                                                       | Data                              |
| -------------------------------- | ------------------------------------------------------------------------------------------------- | --------------------------------- |
| **Choose your landing season**   | Site cards change with the Martian season; landing in dusty season becomes a choice.              | Mars Climate Database · MDAD      |
| **Land on real hazards**         | Drop your landing ellipse onto real Jezero terrain; precision landing shrinks it to 7.7 × 6.6 km. | HiRISE terrain · Landing ellipses |
| **Real slopes stop the rover**   | Perseverance's median tilt was 6.9°; steep real slopes block or tip a weak build.                 | HiRISE terrain · Route tilt       |
| **Wind cleans the panels**       | Dust builds at the real rate; a gust can suddenly restore power, as it did for Opportunity.       | Opportunity dust study            |
| **An orbiter fails mid-mission** | MAVEN's real 2025 loss becomes an event that cuts relay capacity by about 898 Mb a day.           | Mars Relay update                 |
| **Build for 2028**               | A bonus mission to Oxia Planum that compares your rover with ESA's Rosalind Franklin.             | ESA mission facts                 |

---

## 3 · Research examples and intended use

### What the data says

These sourced examples inform future game rules. Their presence in this research document does not mean the corresponding display or simulation is already in the game.

#### Signal delay on your launch date

The page lets you drag to pick a date (default 12 Nov 2026: **11.2 min one way**, 1.341 AU).

- **Planned use:** Drive a "SIGNAL LOST" countdown from the mission date.
- _Source: JPL Horizons API_

#### Energy a rover gets per sol

Real records, watt-hours per Martian day. Nuclear stays steady; solar collapses in dust.

| Rover / source | When                  | Wh per sol |
| -------------- | --------------------- | ---------- |
| InSight        | after landing, 2018   | 5,000      |
| Nuclear MMRTG  | steady, day and night | 2,700      |
| Opportunity    | 1 Jun 2018            | 645        |
| InSight        | spring 2022, dusty    | 500        |
| Opportunity    | 10 Jun 2018, storm    | 22         |

- **Planned use:** Inform power options and show how dust can constrain a solar mission.
- _Sources: MMRTG fact sheet (110 W × 24.6 h, derived) · Planetary Society · NASA Photojournal_

#### Orbiters that carry data home

Average data relayed per day, Feb–May 2026.

| Orbiter        | Mb per day                        |
| -------------- | --------------------------------- |
| TGO (ESA)      | 2,228                             |
| MRO (NASA)     | 851                               |
| Odyssey (NASA) | 107                               |
| MAVEN (NASA)   | **lost** (was ~898 Mb; lost 2025) |

- **Planned use:** Keep communications choices aligned with current relay availability.
- _Sources: NASA Mars Relay Network update · MAVEN figure is its share before the loss_

#### How far a real rover drives

Every Perseverance drive step from landing to sol 1,980.

| Stat            | Value                                  |
| --------------- | -------------------------------------- |
| Median drive    | **46 m**                               |
| 90th percentile | **212 m** (9 in 10 drives are shorter) |
| Total           | **45.1 km**                            |

Drive length histogram (546 drive steps):

| Drive length (m) | Drives |
| ---------------- | ------ |
| 0–50             | 283    |
| 50–100           | 82     |
| 100–150          | 60     |
| 150–200          | 52     |
| 200–250          | 44     |
| 250–300          | 18     |
| 300–400          | 4      |
| 400+             | 3      |

- **Planned use:** Set plausible daily traverse ranges and mission duration.
- _Source: Perseverance waypoints GeoJSON, 546 drive steps_

---

## 4 · The dataset list

### 14 datasets, one line each

**Core six**

| Dataset                            | From                                  | Why                                                         | Status                   |
| ---------------------------------- | ------------------------------------- | ----------------------------------------------------------- | ------------------------ |
| JPL Horizons API                   | NASA JPL                              | Real Earth–Mars signal delay for any date                   | ✓ Verified live          |
| Mars Dust Activity Database (MDAD) | Battalio & Wang · MRO MARCI           | Real storm odds per site and season                         | ✓ Verified               |
| Mars Climate Database v6.2         | LMD · ESA/CNES-funded                 | Sunlight, temperature and dust per site, clear vs storm     | ! Licence: ask first     |
| MOLA DEM + Jezero HiRISE DTM       | USGS Astrogeology                     | Real elevation for the globe and the drivable Jezero map    | ✓ Verified               |
| Perseverance waypoints & traverse  | NASA JPL Mars 2020 map                | Real drive lengths, slopes and panoramas                    | ! Verified · snapshot it |
| Rover engineering facts            | NASA Science · JPL · MMRTG fact sheet | Mass, watts and data for every part; working relay orbiters | ✓ Verified               |

**Extras**

| Dataset                         | From                                  | Why                                                      | Status                 |
| ------------------------------- | ------------------------------------- | -------------------------------------------------------- | ---------------------- |
| Opportunity solar dust study    | NASA NTRS                             | How fast panels lose output and how dust settles         | ✓ Verified             |
| Real power-loss cases           | Planetary Society · NASA Photojournal | Opportunity and InSight stories to calibrate storms      | ✓ Verified             |
| MEDA weather archive            | NASA PDS · Perseverance               | Real Jezero day and night temperatures                   | ✓ Verified             |
| Curiosity weather feed          | CAB · REMS                            | Optional "Today on Mars" panel                           | ! Lags · outreach only |
| Mars Trek map tiles             | NASA Solar System Treks               | Ready-made colour map for the Data Lab                   | ✓ Verified             |
| Landing ellipses & site studies | NASA JPL · Oxia Planum study          | Real landing-zone sizes for the precision-landing choice | ! Gale to confirm      |
| ESA partner data                | ESA · DLR HRSC · Rosalind Franklin    | Partner imagery and a 2028 rover to compare against      | ! Confirm with ESA     |
| Launch vehicles & trajectories  | NASA LSP · Trajectory Browser · JPL   | Rocket capacity and launch dates                         | ! Manual lookup        |

### Dataset details

The verification statuses below describe source checks, not runtime integration or permission to redistribute downloaded data.

#### JPL Horizons API _(core)_

- **Used in:** Twin Room, Blackout, Launch Pad
- **Format & licence:** JSON API · free
- **What we checked:** 14 Nov 2026: 1.324 AU, 11.0 min one way. Closest 0.678 AU, 5.6 min (18 Feb 2027).
- **Link:** <https://ssd-api.jpl.nasa.gov/doc/horizons.html>

#### Mars Dust Activity Database _(core)_

- **Used in:** Data Lab, Twin Room, Mars map
- **Format & licence:** 115 MB · NetCDF + CSV · CC BY 4.0 · Mars Years 28–32
- **What we checked:** Zenodo record v1.1: licence and files confirmed.
- **Link:** <https://zenodo.org/records/7480334>

#### Mars Climate Database v6.2 _(core)_

- **Used in:** Data Lab, Hangar, Twin Room
- **Format & licence:** Web interface or registered download
- **What we checked:** Free for science; commercial use needs permission. Dust-storm scenarios confirmed.
- **Link:** <https://www-mars.lmd.jussieu.fr/mcd_python/>

#### MOLA DEM + Jezero HiRISE DTM _(core)_

- **Used in:** Mars map, Data Lab globe
- **Format & licence:** MOLA 463 m, 2 GB, CC0 · HiRISE 1 m, 5.3 GB zip
- **What we checked:** USGS product pages: resolution, size and licence confirmed.
- **Link:** <https://astrogeology.usgs.gov/search/map/mars_mgs_mola_dem_463m>

#### Perseverance waypoints & traverse _(core)_

- **Used in:** Mobility, Mars map, Results
- **Format & licence:** GeoJSON · 0.6 MB + 1.7 MB
- **What we checked:** 703 waypoints, 45.13 km by sol 1980, tilt and panorama per stop. Undocumented feed.
- **Link:** <https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_waypoints.json>

#### Rover engineering facts _(core)_

- **Used in:** Hangar stations, Twin Room
- **Format & licence:** Web pages + PDF
- **What we checked:** MMRTG 110 W → ~72 W after 17 yr, 45 kg. Relay: TGO 2,228, MRO 851, Odyssey 107 Mb/day.
- **Link:** <https://science.nasa.gov/mars/mars-relay-network-update/>

#### Opportunity solar dust study _(extra)_

- **Used in:** Twin Room
- **Format & licence:** PDF paper
- **What we checked:** 419 data points, 4.95 Mars years; ~21 sols to settle; <23% loss per Mars year.
- **Link:** <https://ntrs.nasa.gov/api/citations/20190028687/downloads/20190028687.pdf>

#### Real power-loss cases _(extra)_

- **Used in:** Storm scenario, Results
- **Format & licence:** Articles
- **What we checked:** Opportunity 645 → 22 Wh, tau 10.8. InSight 5,000 → 500 Wh.
- **Link:** <https://www.planetary.org/articles/06-mer-update-opportunity-dust-storm-sleep>

#### MEDA weather archive _(extra)_

- **Used in:** Thermal, Day/night
- **Format & licence:** CSV per sol · Aug 2026 release
- **What we checked:** Release readme: raw, calibrated and derived products.
- **Link:** <https://pds.nasa.gov/data/pds4/releases/atmos/mars2020_meda-20260811/readme.txt>

#### Curiosity weather feed _(extra)_

- **Used in:** Briefing Room
- **Format & licence:** JSON feed
- **What we checked:** Newest entry sol 4995, 25 Aug 2026 (−71 to −5 °C).
- **Link:** <https://mars.nasa.gov/rss/api/?feed=weather&category=msl&feedtype=json>

#### Mars Trek map tiles _(extra)_

- **Used in:** Data Lab wall
- **Format & licence:** WMTS image tiles
- **What we checked:** Tile request returned an image. Download ahead of time.
- **Link:** <https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars>

#### Landing ellipses & site studies _(extra)_

- **Used in:** Data Lab, Landing
- **Format & licence:** Captions + paper
- **What we checked:** Jezero 7.7 × 6.6 km and Oxia ~19 × 120 km confirmed; Gale not yet sourced.
- **Link:** <https://www.jpl.nasa.gov/images/pia24350-perseverance-rover-landing-ellipse-in-jezero-crater/>

#### ESA partner data _(extra)_

- **Used in:** Data Lab, Results
- **Format & licence:** Images CC BY-SA · mission facts
- **What we checked:** Rosalind Franklin: Oct 2028 launch, Nov 2030 landing at Oxia Planum, ~310 kg (secondary source).
- **Link:** <https://www.dlr.de/en/blog/archive/2014/simpler-usage-rights-as-of-today-mars-express-hrsc-images-licensed-under-creative-commons-licence>

#### Launch vehicles & trajectories _(extra)_

- **Used in:** Launch Pad
- **Format & licence:** Interactive web tools
- **What we checked:** Public tools, manual queries. Perseverance: Atlas V 541, 213-day cruise.
- **Link:** <https://elvperf.ksc.nasa.gov/>

### Coverage matrix (datasets × game systems)

● sets the rule or number · ○ supports or adds flavour

| Dataset                           | Landing site | Terrain | Power | Thermal | Storms | Mobility | Comms | Blackout | Launch | Hangar | Results |
| --------------------------------- | :----------: | :-----: | :---: | :-----: | :----: | :------: | :---: | :------: | :----: | :----: | :-----: |
| JPL Horizons API                  |              |         |       |         |        |          |   ○   |    ●     |   ●    |        |         |
| Mars Dust Activity Database       |      ●       |         |   ○   |         |   ●    |          |       |          |        |        |         |
| Mars Climate Database v6.2        |      ○       |         |   ●   |    ●    |   ○    |          |       |          |        |        |         |
| MOLA DEM + Jezero HiRISE DTM      |      ○       |    ●    |       |         |        |    ○     |       |          |        |        |         |
| Perseverance waypoints & traverse |              |    ○    |       |         |        |    ●     |       |          |        |        |    ●    |
| Rover engineering facts           |              |         |   ●   |         |        |          |   ●   |          |   ○    |   ●    |         |
| Opportunity solar dust study      |              |         |   ●   |         |   ○    |          |       |          |        |        |         |
| Real power-loss cases             |              |         |   ○   |         |   ○    |          |       |          |        |        |    ●    |
| MEDA weather archive              |      ○       |         |       |    ●    |        |          |       |          |        |        |         |
| Curiosity weather feed            |              |         |       |    ○    |        |          |       |          |        |        |    ○    |
| Mars Trek map tiles               |      ○       |    ○    |       |         |        |          |       |          |        |        |         |
| Landing ellipses & site studies   |      ●       |         |       |         |        |          |       |          |   ○    |        |         |
| ESA partner data                  |      ○       |    ○    |       |         |        |          |       |          |        |        |    ●    |
| Launch vehicles & trajectories    |              |         |       |         |        |          |       |          |   ●    |   ○    |         |

---

## 5 · Checks & next steps

### What we verified

**✓ Confirmed: 11 · ! Needs care: 3 · ✕ Corrected: 3**

| Claim                             | Value found                               | How checked                | Result                |
| --------------------------------- | ----------------------------------------- | -------------------------- | --------------------- |
| Signal delay on hackathon day     | 11.0 min · 1.324 AU                       | Horizons API, live         | ✕ Replaces "14 min"   |
| Closest Earth–Mars distance       | 5.6 min · 0.678 AU, 18 Feb 2027           | Horizons API, live         | ✓ Confirmed           |
| Perseverance distance driven      | 45.13 km by sol 1980 · 703 waypoints      | Waypoint GeoJSON, live     | ✓ Confirmed           |
| Curiosity weather feed is current | Newest: sol 4995, 25 Aug 2026             | JSON feed, live            | ! Lags ~6 weeks       |
| MMRTG output                      | 110 W → ~72 W after 17 yr · 45 kg         | NASA fact sheet            | ✓ Confirmed           |
| Relay orbiter capacity            | TGO 2,228 · MRO 851 · Odyssey 107 Mb/day  | NASA Mars Relay update     | ✓ Confirmed           |
| MAVEN available as relay          | Lost Dec 2025, declared lost June 2026    | NASA + Scientific American | ✕ Removed from Comms  |
| Jezero landing ellipse            | 7.7 × 6.6 km                              | JPL PIA24350               | ✓ Confirmed           |
| Oxia Planum ellipse               | ~19 × 120 km · −2.6 to −3.1 km            | Peer-reviewed study        | ✓ Confirmed           |
| Gale landing ellipse              | 20 × 7 km (earlier plan)                  | Not stated on NASA page    | ! Needs a source      |
| Opportunity storm energy          | 645 → 22 Wh · tau 10.8                    | Planetary Society          | ✓ Confirmed           |
| InSight dust loss                 | 5,000 → 500 Wh per sol                    | NASA Photojournal          | ✓ Confirmed           |
| Solar dust degradation            | <23% per Mars year · 21 sols to settle    | NASA NTRS study            | ✓ Confirmed           |
| MDAD licence and coverage         | CC BY 4.0 · 115 MB · MY 28–32             | Zenodo record              | ✓ Confirmed           |
| MOLA licence                      | CC0 · 463 m · 2 GB                        | USGS page                  | ✓ Confirmed           |
| MCD free to use                   | Science only; commercial needs permission | LMD access page            | ! Cite and inform LMD |
| Instrument masses                 | Main-unit and total figures mixed         | NASA instrument pages      | ✕ Use totals          |

### Target data pipeline

1. **Raw sources:** terrain GeoTIFFs, storm database, climate per site, Horizons and route data, NASA fact sheets.
2. **Offline scripts:** crop terrain to 16-bit heightmaps, count storms per site, compute light time per date, compute drive statistics.
3. **Small game files:** `site_jezero.json` (plus gale, oxia), `light_time.json`, `parts.json`, `sources.json`.
4. **Godot reads locally:** no live API calls, works offline for judges, and every number has its source URL.

### Research decisions recorded

- **Blackout delay:** use the Horizons value (11.0 min on 14 Nov 2026), not "14 min".
- **Instrument masses:** use whole-instrument totals everywhere.
- **Comms research:** candidate relay set is TGO, MRO and Odyssey; MAVEN is excluded from future planning following its loss. This does not mean those choices are already offered in-game.

### Still to do

- [ ] Ask the Local Lead whether data-prep scripts count as early work.
- [ ] Find a primary source for the Gale landing ellipse.
- [ ] Confirm Rosalind Franklin dates on ESA pages.
- [ ] Cite the Mars Climate Database and tell the LMD team.

### Submission wording: current status

The current playable prototype uses explicitly identified game-balance values for landing-site comparisons and rover configuration. This ledger records candidate authoritative sources and intended mappings for later implementation. Do not describe the planned storm, communications, terrain simulation, or Mars-driving systems as current NASA-data features. Before integrating or redistributing any downloaded dataset, verify its license and cite the exact data product and version.

---

## Sources

- [JPL Horizons API](https://ssd-api.jpl.nasa.gov/doc/horizons.html)
- [Mars Dust Activity Database](https://zenodo.org/records/7480334)
- [Mars Climate Database v6.2](https://www-mars.lmd.jussieu.fr/mcd_python/)
- [MOLA DEM + Jezero HiRISE DTM](https://astrogeology.usgs.gov/search/map/mars_mgs_mola_dem_463m)
- [Perseverance waypoints & traverse](https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_waypoints.json)
- [Rover engineering facts](https://science.nasa.gov/mars/mars-relay-network-update/)
- [Opportunity solar dust study](https://ntrs.nasa.gov/api/citations/20190028687/downloads/20190028687.pdf)
- [Real power-loss cases](https://www.planetary.org/articles/06-mer-update-opportunity-dust-storm-sleep)
- [MEDA weather archive](https://pds.nasa.gov/data/pds4/releases/atmos/mars2020_meda-20260811/readme.txt)
- [Curiosity weather feed](https://mars.nasa.gov/rss/api/?feed=weather&category=msl&feedtype=json)
- [Mars Trek map tiles](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars)
- [Landing ellipses & site studies](https://www.jpl.nasa.gov/images/pia24350-perseverance-rover-landing-ellipse-in-jezero-crater/)
- [ESA partner data](https://www.dlr.de/en/blog/archive/2014/simpler-usage-rights-as-of-today-mars-express-hrsc-images-licensed-under-creative-commons-licence)
- [Launch vehicles & trajectories](https://elvperf.ksc.nasa.gov/)
- [Space Apps participant FAQ](https://www.spaceappschallenge.org/resources/participant-faqs/)
- [Jezero HiRISE DTM – USGS](https://astrogeology.usgs.gov/search/map/mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic)
- [MCD access terms – LMD](https://www-mars.lmd.jussieu.fr/mars/access.html)
- [MMRTG fact sheet](https://science.nasa.gov/wp-content/uploads/2024/02/mmrtg-factsheet-updated-5-18-20-1.pdf)
- [InSight power – NASA](https://science.nasa.gov/photojournal/insights-power-generation-after-landing-and-spring-2022)
- [MAVEN lost – Scientific American](https://scientificamerican.com/article/nasas-mars-mission-maven-is-lost-forever)
- [Oxia Planum study – PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC7987365/)
- [Mars 2020 launch – JPL](https://www.jpl.nasa.gov/news/press_kits/mars_2020/launch/mission)
- [NASA Trajectory Browser](https://trajbrowser.arc.nasa.gov/)

---

## Appendix A · Earth–Mars light time table

JPL Horizons API, every two weeks. Hackathon reference point: **14 Nov 2026 · 1.3244 AU · 11.01 min**.

| Date        | Distance (AU) | One-way light time (min) |
| ----------- | ------------- | ------------------------ |
| 2026-Oct-01 | 1.6654        | 13.85                    |
| 2026-Oct-15 | 1.5651        | 13.02                    |
| 2026-Oct-29 | 1.4567        | 12.11                    |
| 2026-Nov-12 | 1.3413        | 11.16                    |
| 2026-Nov-26 | 1.2211        | 10.16                    |
| 2026-Dec-10 | 1.0989        | 9.14                     |
| 2026-Dec-24 | 0.9790        | 8.14                     |
| 2027-Jan-07 | 0.8676        | 7.22                     |
| 2027-Jan-21 | 0.7732        | 6.43                     |
| 2027-Feb-04 | 0.7065        | 5.88                     |
| 2027-Feb-18 | 0.6784        | 5.64                     |
| 2027-Mar-04 | 0.6939        | 5.77                     |
| 2027-Mar-18 | 0.7497        | 6.23                     |
| 2027-Apr-01 | 0.8352        | 6.95                     |
| 2027-Apr-15 | 0.9397        | 7.82                     |
| 2027-Apr-29 | 1.0541        | 8.77                     |
| 2027-May-13 | 1.1725        | 9.75                     |
| 2027-May-27 | 1.2903        | 10.73                    |
| 2027-Jun-10 | 1.4049        | 11.68                    |
| 2027-Jun-24 | 1.5141        | 12.59                    |
| 2027-Jul-08 | 1.6169        | 13.45                    |
| 2027-Jul-22 | 1.7122        | 14.24                    |
| 2027-Aug-05 | 1.7998        | 14.97                    |
| 2027-Aug-19 | 1.8792        | 15.63                    |
| 2027-Sep-02 | 1.9506        | 16.22                    |
| 2027-Sep-16 | 2.0141        | 16.75                    |
| 2027-Sep-30 | 2.0702        | 17.22                    |
| 2027-Oct-14 | 2.1192        | 17.63                    |
| 2027-Oct-28 | 2.1619        | 17.98                    |
| 2027-Nov-11 | 2.1987        | 18.29                    |
| 2027-Nov-25 | 2.2306        | 18.55                    |
| 2027-Dec-09 | 2.2582        | 18.78                    |
| 2027-Dec-23 | 2.2823        | 18.98                    |
| 2028-Jan-06 | 2.3036        | 19.16                    |
| 2028-Jan-20 | 2.3227        | 19.32                    |
| 2028-Feb-03 | 2.3400        | 19.46                    |
| 2028-Feb-17 | 2.3559        | 19.59                    |
| 2028-Mar-02 | 2.3704        | 19.71                    |
| 2028-Mar-16 | 2.3834        | 19.82                    |
| 2028-Mar-30 | 2.3947        | 19.92                    |
| 2028-Apr-13 | 2.4036        | 19.99                    |
| 2028-Apr-27 | 2.4098        | 20.04                    |
| 2028-May-11 | 2.4121        | 20.06                    |
| 2028-May-25 | 2.4099        | 20.04                    |
| 2028-Jun-08 | 2.4021        | 19.98                    |
| 2028-Jun-22 | 2.3879        | 19.86                    |
| 2028-Jul-06 | 2.3662        | 19.68                    |
| 2028-Jul-20 | 2.3363        | 19.43                    |
| 2028-Aug-03 | 2.2970        | 19.10                    |
| 2028-Aug-17 | 2.2480        | 18.70                    |
| 2028-Aug-31 | 2.1884        | 18.20                    |
| 2028-Sep-14 | 2.1180        | 17.61                    |
| 2028-Sep-28 | 2.0364        | 16.94                    |
| 2028-Oct-12 | 1.9439        | 16.17                    |
| 2028-Oct-26 | 1.8407        | 15.31                    |
| 2028-Nov-09 | 1.7276        | 14.37                    |
| 2028-Nov-23 | 1.6056        | 13.35                    |
| 2028-Dec-07 | 1.4766        | 12.28                    |
| 2028-Dec-21 | 1.3424        | 11.16                    |

---

_Red Frontier · Data brief. Checked 5 Oct 2026. Game balance values are proposals; real values carry their source._
