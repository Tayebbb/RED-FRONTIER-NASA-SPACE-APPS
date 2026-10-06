extends RefCounted
## The RF-01 part sheet, read once from rover_parts.json (Rules and Scoring v1.0 §2.3; the only copy of the numbers).
## Use: const RoverParts := preload("res://game/data/rover_parts.gd")
##      RoverParts.part("shield_heavy") -> {name, mass, value, cost, ...}   RoverParts.category_parts("shield")

const PATH := "res://game/data/rover_parts.json"

static var _data: Dictionary = {}

static func _load() -> Dictionary:
	if _data.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH))
		if not parsed is Dictionary or not parsed.has("parts") or not parsed.has("categories"):
			push_error("Rover part data missing or invalid: " + PATH)
			return {"order": [], "categories": {}, "parts": {}}
		for id in parsed.parts:
			for key in ["name", "mass", "cost"]:
				if not parsed.parts[id].has(key):
					push_error("Rover part '%s' has no '%s'" % [id, key])
		_data = parsed
	return _data

## Category keys in presentation order: solar, battery, shield, antenna, instruments.
static func categories() -> Array:
	return _load().order

static func category(key: String) -> Dictionary:
	return _load().categories.get(key, {})

static func category_parts(key: String) -> Array:
	return category(key).get("parts", [])

static func has(id: String) -> bool:
	return _load().parts.has(id)

## A copy of one part's record, {} if unknown.
static func part(id: String) -> Dictionary:
	return _load().parts.get(id, {}).duplicate()

## Which category a part belongs to ("" if unknown).
static func category_of(id: String) -> String:
	for key in categories():
		if id in category_parts(key):
			return key
	return ""
