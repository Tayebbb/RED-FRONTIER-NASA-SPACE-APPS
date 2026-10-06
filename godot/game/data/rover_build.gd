extends RefCounted
## RF-01 build numbers and validation: the one implementation of Rules and Scoring v1.0 §2.2 and §3.1.
## The Hangar UI, MissionState, the Digital Twin, Mars and the outcome screen all call evaluate(); no formula lives
## anywhere else.
##
## A build is {"solar": id, "battery": id, "shield": id, "antenna": id, "instruments": [id, ...]} ("" / [] = none yet).
## A site is a landing-site record (landing_sites.gd): science, solar, terrain_risk.
## Scores whose inputs are not chosen yet are null (shown as "—"), never a misleading number.

const RoverParts := preload("res://game/data/rover_parts.gd")
const SINGLE := ["solar", "battery", "shield", "antenna"]
const MISSING := {"solar": "SELECT A SOLAR ARRAY", "battery": "SELECT A BATTERY", "shield": "SELECT SHIELDING",
	"antenna": "SELECT AN ANTENNA"}

static func empty_build() -> Dictionary:
	return {"solar": "", "battery": "", "shield": "", "antenna": "", "instruments": []}

## §3.1 clamp(): every score is held to 0..100.
static func clamp_score(v: float) -> float:
	return clampf(v, 0.0, 100.0)

static func mass_limit() -> int:
	return GameConfig.ACTIVE_RULES.mass_limit

static func budget_limit() -> int:
	return GameConfig.ACTIVE_RULES.budget_limit

static func instrument_slots() -> int:
	return GameConfig.ACTIVE_RULES.instrument_slots

## Everything about a build at a site:
##   mass, cost, instruments (count), demand, supply, power, safety, build_science, engineering (null until their
##   inputs exist), problems (ordered, player-facing), valid, over_mass, over_budget.
static func evaluate(build: Dictionary, site: Dictionary) -> Dictionary:
	var parts := {}
	for key in SINGLE:
		var id: String = build.get(key, "")
		parts[key] = RoverParts.part(id) if id != "" else {}
	var instruments: Array = build.get("instruments", [])
	var mass := 0
	var cost := 0
	for key in SINGLE:
		mass += int(parts[key].get("mass", 0))
		cost += int(parts[key].get("cost", 0))
	var instrument_value := 0.0
	for id in instruments:
		var p := RoverParts.part(id)
		mass += int(p.get("mass", 0))
		cost += int(p.get("cost", 0))
		instrument_value += float(p.get("value", 0))
	var has_site := site.has("science") and site.has("solar") and site.has("terrain_risk")
	var out := {"mass": mass, "cost": cost, "instruments": instruments.size(), "demand": null, "supply": null,
		"power": null, "safety": null, "build_science": null, "engineering": null}

	if not parts.antenna.is_empty():
		out.demand = 12.0 + 7.0 * instruments.size() + float(parts.antenna.draw)
	if has_site and not parts.solar.is_empty():
		out.supply = float(parts.solar.value) * (0.6 + float(site.solar) * 0.8)
	if out.supply != null and out.demand != null and not parts.battery.is_empty():
		out.power = clamp_score((out.supply + float(parts.battery.value) * 0.5) / (out.demand * 1.8) * 100.0)
	if has_site and not parts.shield.is_empty() and not parts.antenna.is_empty():
		out.safety = clamp_score(float(parts.shield.value) / 46.0 * 45.0 + (1.0 - float(site.terrain_risk)) * 35.0
			+ float(parts.antenna.reliability) * 20.0)
	if has_site and instruments.size() > 0:
		out.build_science = clamp_score(float(site.science) * 45.0 + instrument_value)
	if out.power != null and out.safety != null:
		out.engineering = roundi(0.55 * out.power + 0.45 * out.safety)

	var problems: Array[String] = []
	for key in SINGLE:
		if parts[key].is_empty():
			problems.append(MISSING[key])
	var need := instrument_slots() - instruments.size()
	if need > 0:
		problems.append("SELECT %d MORE INSTRUMENT%s" % [need, "" if need == 1 else "S"])
	elif need < 0:
		problems.append("REMOVE %d INSTRUMENT%s" % [-need, "" if need == -1 else "S"])
	out.over_mass = maxi(mass - mass_limit(), 0)
	out.over_budget = maxi(cost - budget_limit(), 0)
	if out.over_mass > 0:
		problems.append("OVER MASS BY %d KG" % out.over_mass)
	if out.over_budget > 0:
		problems.append("OVER BUDGET BY %d CREDITS" % out.over_budget)
	if not has_site:
		problems.append("NO LANDING SITE LOCKED")
	out.problems = problems
	out.valid = problems.is_empty()
	return out

## Stable text for one build: equal builds (instrument order ignored) give equal signatures. A Digital Twin result
## records the signature it was run on; a different signature means that result is stale.
static func signature(build: Dictionary) -> String:
	var inst: Array = build.get("instruments", []).duplicate()
	inst.sort()
	var bits: Array = []
	for key in SINGLE:
		bits.append(build.get(key, ""))
	bits.append("+".join(inst))
	return "|".join(bits)

## Toggle helper for the UI: picks within a category (replacing for single-pick categories, add/remove for
## instruments, refusing a fourth). Returns the new build; never mutates the input.
static func with_part(build: Dictionary, id: String) -> Dictionary:
	var out := build.duplicate(true)
	var key := RoverParts.category_of(id)
	if key == "":
		return out
	if key == "instruments":
		var inst: Array = out.instruments
		if id in inst:
			inst.erase(id)
		elif inst.size() < instrument_slots():
			inst.append(id)
	else:
		out[key] = id
	return out
