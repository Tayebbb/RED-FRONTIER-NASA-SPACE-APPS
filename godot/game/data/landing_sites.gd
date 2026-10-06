extends RefCounted
## Candidate landing sites, read once from landing_sites.json (the single copy of the site data).
## Use: const LandingSites := preload("res://game/data/landing_sites.gd")
##      LandingSites.ids() -> ["jezero", ...]   LandingSites.get_site("gale") -> {science, solar, terrain_risk, ...}
## The numbers are PROTOTYPE values (Rules and Scoring v1.0 §3.1) until the NASA-derived file replaces them.

const PATH := "res://game/data/landing_sites.json"
const REQUIRED := ["id", "display_name", "science", "solar", "terrain_risk", "science_label", "solar_label",
	"terrain_label", "mission_profile"]

static var _data: Dictionary = {}

static func _load() -> Dictionary:
	if _data.is_empty():
		var parsed = JSON.parse_string(FileAccess.get_file_as_string(PATH))
		if not parsed is Dictionary or not parsed.has("sites"):
			push_error("Landing site data missing or invalid: " + PATH)
			return {"order": [], "sites": {}}
		for id in parsed.sites:
			for key in REQUIRED:
				if not parsed.sites[id].has(key):
					push_error("Landing site '%s' has no '%s'" % [id, key])
		_data = parsed
	return _data

## Site ids in presentation order.
static func ids() -> Array:
	return _load().get("order", _load().sites.keys())

static func has(id: String) -> bool:
	return _load().sites.has(id)

## A copy of one site's record, {} if unknown.
static func get_site(id: String) -> Dictionary:
	return _load().sites.get(id, {}).duplicate()

## "PROTOTYPE" until real NASA-derived values are in.
static func provenance() -> String:
	return _load().get("provenance", "")
