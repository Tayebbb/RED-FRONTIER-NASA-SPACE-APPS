extends Node
## MissionState (autoload): the single source of truth for one run of Mission: Red Frontier.
## It stores state and announces changes. It does not compute anything: the systems that own a value (rover
## configuration, Digital Twin, Mars, scoring) write it here when they exist. null = not decided / not computed.

signal phase_changed(phase: Phase)
signal objective_changed(id: StringName, text: String)
signal state_changed(key: StringName, value: Variant)
signal mission_reset

const LandingSites := preload("res://game/data/landing_sites.gd")
const RoverBuild := preload("res://game/data/rover_build.gd")

enum Phase { BRIEFING, LANDING_SITE, ROVER_CONFIG, DIGITAL_TWIN, LAUNCH, MARS, RESULT }

## --- Mission progression --------------------------------------------------------------------------------
var mission_phase: Phase = Phase.BRIEFING
var current_objective: StringName = &""
var briefing_completed := false
var landing_site_selected := false
var rover_configured := false
var digital_twin_completed := false
var launch_confirmed := false

## --- Pre-launch configuration ---------------------------------------------------------------------------
var landing_site: String = ""                    # site id from game/data/landing_sites.json, "" until chosen
var solar_system: String = ""                    # accepted build: part ids from game/data/rover_parts.json,
var battery_system: String = ""                  # "" until a build is accepted (see accept_build / current_build)
var shielding: String = ""
var antenna: String = ""
var selected_instruments: Array[String] = []

## --- Engineering: copies of the accepted build's totals. The full, always-current set (demand, supply, safety,
## build_science, engineering...) comes from build_stats(), which recomputes them with RoverBuild.
var mass: Variant = null                         # kg
var power: Variant = null                        # 0..100 build score
var budget: Variant = null                       # credits spent

## --- Digital Twin prediction ----------------------------------------------------------------------------
var predicted_success: Variant = null
var power_risk: Variant = null
var thermal_risk: Variant = null
var comms_risk: Variant = null
var landing_risk: Variant = null
var radiation_risk: Variant = null
var twin_build_signature: String = ""            # RoverBuild.signature() of the build the prediction was run on

## --- Mars state (percent) ------------------------------------------------------------------------------
var battery := 100.0
var rover_health := 100.0
var science := 0.0
var data_integrity := 100.0

## --- Mission result ------------------------------------------------------------------------------------
var science_score: Variant = null
var engineering_score: Variant = null
var safety_score: Variant = null
var efficiency_score: Variant = null
var final_score: Variant = null
var ending_type: String = ""

var _defaults := {}

func _ready() -> void:
	for key in _keys():
		_defaults[key] = _copy(get(key))
	set_objective(&"attend_briefing")

## Every stored field, in declaration order.
func _keys() -> Array[StringName]:
	var out: Array[StringName] = []
	for p in get_property_list():
		if p.usage & PROPERTY_USAGE_SCRIPT_VARIABLE and not String(p.name).begins_with("_"):
			out.append(StringName(p.name))
	return out

func _copy(v: Variant) -> Variant:
	return v.duplicate() if v is Array or v is Dictionary else v

## Back to a fresh run (Replay).
func reset_mission() -> void:
	for key in _defaults:
		set(key, _copy(_defaults[key]))
	mission_reset.emit()
	phase_changed.emit(mission_phase)
	set_objective(&"attend_briefing")

## Generic write for later systems: MissionState.set_value(&"landing_site", "Jezero").
func set_value(key: StringName, value: Variant) -> void:
	if not _defaults.has(key):
		push_error("MissionState has no field '%s'" % key)
		return
	if key == &"current_objective":
		set_objective(value)
		return
	set(key, value)
	state_changed.emit(key, value)
	if key == &"mission_phase":
		phase_changed.emit(mission_phase)

func set_phase(phase: Phase) -> void:
	if phase != mission_phase:
		set_value(&"mission_phase", phase)

func set_objective(id: StringName) -> void:
	if not GameConfig.OBJECTIVES.has(id):
		push_error("Unknown objective '%s' (add it to GameConfig.OBJECTIVES)" % id)
		return
	current_objective = id
	state_changed.emit(&"current_objective", id)
	objective_changed.emit(id, objective_text())

func objective_text() -> String:
	return GameConfig.OBJECTIVES.get(current_objective, "")

func complete_briefing() -> void:
	if briefing_completed:
		return
	set_value(&"briefing_completed", true)
	set_phase(Phase.LANDING_SITE)

## Lock the landing site (Mars Intelligence). Returns false for an unknown id or if a site is already locked.
func select_landing_site(site_id: String) -> bool:
	if landing_site_selected or not LandingSites.has(site_id):
		return false
	set_value(&"landing_site", site_id)
	set_value(&"landing_site_selected", true)
	set_phase(Phase.ROVER_CONFIG)
	return true

## The chosen site's record (science, solar, terrain_risk, labels...); {} until a site is chosen.
func landing_site_data() -> Dictionary:
	return LandingSites.get_site(landing_site) if landing_site != "" else {}

## --- RF-01 build (Engineering Hangar) ---------------------------------------------------------------------

## The accepted build as {"solar", "battery", "shield", "antenna", "instruments"}.
func current_build() -> Dictionary:
	return {"solar": solar_system, "battery": battery_system, "shield": shielding, "antenna": antenna,
		"instruments": selected_instruments.duplicate()}

## Mass, cost, demand, supply, power, safety, build_science, engineering, problems, valid: for the accepted build
## at the locked landing site. Later systems read this; it is never stored separately, so it cannot go stale.
func build_stats() -> Dictionary:
	return RoverBuild.evaluate(current_build(), landing_site_data())

func build_signature() -> String:
	return RoverBuild.signature(current_build()) if rover_configured else ""

## Store a legal build (Rules §2.2). Refused when invalid or after launch. Accepting a build different from the
## one a Digital Twin result was run on makes that result stale.
func accept_build(build: Dictionary) -> bool:
	if launch_confirmed:
		return false
	var stats := RoverBuild.evaluate(build, landing_site_data())
	if not stats.valid:
		return false
	var inst: Array[String] = []
	inst.assign(build.instruments)
	set_value(&"solar_system", build.solar)
	set_value(&"battery_system", build.battery)
	set_value(&"shielding", build.shield)
	set_value(&"antenna", build.antenna)
	set_value(&"selected_instruments", inst)
	set_value(&"mass", stats.mass)
	set_value(&"budget", stats.cost)
	set_value(&"power", stats.power)
	set_value(&"rover_configured", true)
	if digital_twin_completed and twin_build_signature != build_signature():
		invalidate_twin()
	if not twin_is_current():
		set_phase(Phase.DIGITAL_TWIN)
	return true

## The Digital Twin result matches the accepted build.
func twin_is_current() -> bool:
	return digital_twin_completed and twin_build_signature != "" and twin_build_signature == build_signature()

## Drop a stale Digital Twin result: it must be run again.
func invalidate_twin() -> void:
	for key in [&"predicted_success", &"power_risk", &"thermal_risk", &"comms_risk", &"landing_risk", &"radiation_risk"]:
		set_value(key, null)
	set_value(&"twin_build_signature", "")
	set_value(&"digital_twin_completed", false)

## Plain dictionary of the whole run (debugging, saves, the Digital Twin request later).
func snapshot() -> Dictionary:
	var out := {}
	for key in _defaults:
		out[key] = _copy(get(key))
	return out
