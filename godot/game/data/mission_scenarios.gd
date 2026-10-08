extends RefCounted
## Named, offline stress scenarios. A scenario supplies atmosphere and relay conditions only.

const PATH := "res://game/data/mission_scenarios.json"
const MissionRules := preload("res://game/data/mission_rules.gd")
static var _data: Dictionary = {}

static func _load() -> Dictionary:
	if _data.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH))
		if not parsed is Dictionary or not parsed.has("scenarios") or not parsed.has("order"):
			push_error("Mission scenarios missing or invalid: " + PATH)
			return {"order": [], "scenarios": {}}
		for id in parsed.order:
			var scenario: Dictionary = parsed.scenarios.get(id, {})
			for key in ["id", "title", "source_ids", "default_tau", "relay_multiplier"]:
				if not scenario.has(key):
					push_error("Mission scenario '%s' missing '%s'" % [id, key])
					return {"order": [], "scenarios": {}}
			for source_id in scenario.source_ids:
				if not MissionRules.sources().has(source_id):
					push_error("Mission scenario '%s' has unknown source '%s'" % [id, source_id])
					return {"order": [], "scenarios": {}}
		_data = parsed
	return _data

static func has(id: String) -> bool:
	return _load().scenarios.has(id)

static func get_scenario(id: String) -> Dictionary:
	return _load().scenarios.get(id, {}).duplicate(true)

static func ids() -> Array:
	return _load().order.duplicate()
