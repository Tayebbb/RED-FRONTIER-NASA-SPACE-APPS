extends RefCounted
## Pure, deterministic, sol-by-sol RF-01 mission model. It has no Node, frame-time,
## scene, or MissionState dependency. Presentation layers replay the returned log.

const LandingSites := preload("res://game/data/landing_sites.gd")
const MissionRules := preload("res://game/data/mission_rules.gd")
const MissionScenarios := preload("res://game/data/mission_scenarios.gd")
const RoverBuild := preload("res://game/data/rover_build.gd")
const RoverParts := preload("res://game/data/rover_parts.gd")

const EVENTS := {"storm_warning": ["hibernate", "press_on"], "low_power": ["rest", "drive"]}

## setup = {site_id, build, seed}; targets are ordered instrument-site ids; decisions
## are [{sol, event, choice}]. scenario_id names bundled content. Every failure is a
## data result so callers can display it without catching errors.
static func run(setup: Dictionary, targets: Array, decisions: Array, scenario_id: String) -> Dictionary:
	var rules := MissionRules.values()
	if rules.is_empty():
		return _invalid("MISSION RULES UNAVAILABLE")
	var site_id := String(setup.get("site_id", ""))
	if not LandingSites.has(site_id):
		return _invalid("UNKNOWN SITE '%s'" % site_id)
	if not MissionScenarios.has(scenario_id):
		return _invalid("UNKNOWN SCENARIO '%s'" % scenario_id)
	var site := LandingSites.get_site(site_id)
	var build: Dictionary = setup.get("build", {})
	var build_stats := RoverBuild.evaluate(build, site)
	if not build_stats.valid:
		return _invalid("INVALID BUILD: " + ", ".join(build_stats.problems))
	var target_error := _validate_targets(targets)
	if target_error != "":
		return _invalid(target_error)
	var decision_result := _index_decisions(decisions, int(rules.sols))
	if not decision_result.valid:
		return _invalid(decision_result.error)

	var parts := _parts_for(build)
	var scenario := MissionScenarios.get_scenario(scenario_id)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(setup.get("seed", 0))
	var capacity := float(parts.battery.get("capacity", 0.0))
	var battery := capacity
	var health := 100.0
	var gathered := 0.0
	var buffered := 0.0
	var returned := 0.0
	var target_index := 0
	var log: Array = []
	var ending := "returned"
	var cause := "mission_duration_complete"
	var end_sol := int(rules.sols)

	for sol in range(1, int(rules.sols) + 1):
		var tau := _tau_for(scenario, sol, rng, float(rules.tau_seed_jitter))
		var events: Array = []
		var action := "drive" if target_index < targets.size() else "rest"
		var storm_active := tau >= float(rules.storm_warning_tau)
		var low_power := battery / capacity <= float(rules.low_power_fraction)
		if storm_active:
			events.append("storm_warning")
			action = _choice_or_default(decision_result.index, sol, "storm_warning", "hibernate")
		if low_power:
			events.append("low_power")
			if not storm_active:
				action = _choice_or_default(decision_result.index, sol, "low_power", "rest")
		if action == "press_on":
			action = "drive" if target_index < targets.size() else "rest"
		if action == "drive" and target_index >= targets.size():
			action = "rest"

		var solar := float(parts.solar.get("value", 0.0)) * (0.6 + float(site.solar) * 0.8)
		solar *= float(rules.solar_scale) / (1.0 + tau)
		var draw := float(rules.base_draw) + float(parts.antenna.get("draw", 0.0))
		draw += build.instruments.size() * float(rules.instrument_draw)
		match action:
			"drive": draw += float(rules.drive_draw)
			"rest": draw += float(rules.rest_draw)
			"hibernate": draw += float(rules.hibernate_draw)
		battery = clampf(battery + solar - draw, 0.0, capacity)

		var science_gain := 0.0
		var damage := 0.0
		if action != "hibernate":
			for instrument in parts.instruments:
				science_gain += float(instrument.get("passive_science", 0.0)) * float(rules.passive_science_per_sol)
		if action == "drive":
			var target := String(targets[target_index])
			for instrument in parts.instruments:
				if String(instrument.get("site", "")) == target:
					science_gain += float(instrument.get("value", 0.0)) * float(site.science) * float(rules.target_science_scale)
			target_index += 1
			var shield_factor := 1.0 - float(parts.shield.get("value", 0.0)) / 46.0 * 0.7
			damage += float(site.terrain_risk) * float(rules.terrain_damage) * shield_factor
		if storm_active and action != "hibernate":
			var radiation_relief := 0.0
			for instrument in parts.instruments:
				radiation_relief += float(instrument.get("storm_damage", 0.0))
			damage += maxf(0.0, float(rules.storm_damage) * tau / float(rules.storm_warning_tau) + radiation_relief)
		health = maxf(0.0, health - damage)
		gathered += science_gain
		buffered += science_gain
		var relay := float(rules.relay_game_units_per_sol) * float(parts.antenna.get("reliability", 0.0)) * float(scenario.relay_multiplier)
		var downlink := minf(buffered, relay)
		buffered -= downlink
		returned += downlink

		log.append({"sol": sol, "action": action, "tau": tau, "battery": battery, "health": health,
			"target_index": target_index, "science_gathered": gathered, "data_buffered": buffered,
			"data_returned": returned, "events": events})
		if battery <= 0.0 or health <= 0.0:
			ending = "partial" if returned > 0.0 else "lost"
			cause = "power_depleted" if battery <= 0.0 else "rover_damage"
			end_sol = sol
			break

	return {"valid": true, "error": "", "scenario_id": scenario_id, "seed": int(setup.get("seed", 0)),
		"ending": ending, "cause": cause, "end_sol": end_sol, "completed_targets": target_index,
		"final": {"battery": battery, "health": health, "science_gathered": gathered, "data_buffered": buffered, "data_returned": returned},
		"log": log, "log_hash": JSON.stringify(log).md5_text()}

static func _invalid(error: String) -> Dictionary:
	return {"valid": false, "error": error, "ending": "", "cause": "", "end_sol": 0, "final": {}, "log": [], "log_hash": ""}

static func _parts_for(build: Dictionary) -> Dictionary:
	var instruments: Array = []
	for id in build.get("instruments", []):
		instruments.append(RoverParts.part(String(id)))
	return {"solar": RoverParts.part(String(build.get("solar", ""))), "battery": RoverParts.part(String(build.get("battery", ""))),
		"shield": RoverParts.part(String(build.get("shield", ""))), "antenna": RoverParts.part(String(build.get("antenna", ""))), "instruments": instruments}

static func _valid_target_ids() -> Array:
	var ids: Array = []
	for category in RoverParts.categories():
		for id in RoverParts.category_parts(category):
			var target := String(RoverParts.part(id).get("site", ""))
			if target != "" and not (target in ids):
				ids.append(target)
	return ids

static func _validate_targets(targets: Array) -> String:
	if targets.is_empty():
		return "SELECT AT LEAST ONE SCIENCE TARGET"
	var valid := _valid_target_ids()
	var seen: Array = []
	for target in targets:
		var id := String(target)
		if not (id in valid):
			return "UNKNOWN SCIENCE TARGET '%s'" % id
		if id in seen:
			return "DUPLICATE SCIENCE TARGET '%s'" % id
		seen.append(id)
	return ""

static func _index_decisions(decisions: Array, max_sol: int) -> Dictionary:
	var index := {}
	for decision in decisions:
		if not decision is Dictionary:
			return {"valid": false, "error": "MALFORMED DECISION"}
		var sol := int(decision.get("sol", 0))
		var event := String(decision.get("event", ""))
		var choice := String(decision.get("choice", ""))
		if sol < 1 or sol > max_sol or not EVENTS.has(event) or not (choice in EVENTS[event]):
			return {"valid": false, "error": "INVALID DECISION"}
		if index.has(sol):
			return {"valid": false, "error": "CONFLICTING DECISIONS ON SOL %d" % sol}
		index[sol] = {"event": event, "choice": choice}
	return {"valid": true, "error": "", "index": index}

static func _choice_or_default(index: Dictionary, sol: int, event: String, fallback: String) -> String:
	var decision: Dictionary = index.get(sol, {})
	return String(decision.choice) if decision.get("event", "") == event else fallback

static func _tau_for(scenario: Dictionary, sol: int, rng: RandomNumberGenerator, jitter: float) -> float:
	var overrides: Dictionary = scenario.get("tau_overrides", {})
	if overrides.has(str(sol)):
		return float(overrides[str(sol)])
	return maxf(0.0, float(scenario.default_tau) + rng.randf_range(-jitter, jitter))
