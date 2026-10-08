extends RefCounted
## Read-only mission-simulation constants and provenance. These are game-balance values;
## source rows explain the real observations used to scale scenarios.

const PATH := "res://game/data/rules.json"
static var _data: Dictionary = {}

static func _load() -> Dictionary:
	if _data.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH))
		if not parsed is Dictionary or not parsed.has("mission") or not parsed.has("sources"):
			push_error("Mission rules missing or invalid: " + PATH)
			return {"mission": {}, "sources": {}}
		for key in ["sols", "base_draw", "instrument_draw", "drive_draw", "rest_draw", "hibernate_draw", "solar_scale", "tau_seed_jitter", "storm_warning_tau", "low_power_fraction", "terrain_damage", "storm_damage", "target_science_scale", "passive_science_per_sol", "relay_game_units_per_sol"]:
			if not parsed.mission.has(key):
				push_error("Mission rules missing '%s'" % key)
				return {"mission": {}, "sources": {}}
		_data = parsed
	return _data

static func values() -> Dictionary:
	return _load().mission.duplicate()

static func sources() -> Dictionary:
	return _load().sources.duplicate(true)
