extends SceneTree
## Golden and contract tests for the pure MissionSim core.

const MissionSim := preload("res://game/mission_sim.gd")

const GOLDEN_HASHES := {
	"nominal": "fe8c880b8669becf7af899d580ba987e",
	"opportunity_2018": "be6dfec73c84521617ed08349bc5ff1f",
	"relay_degraded": "490abbd5ef98b606eda363845226d55e"
}

var failed := 0
var count := 0

func check(name: String, ok: bool, detail := "") -> void:
	count += 1
	if not ok:
		failed += 1
	print("MISSION_CHECK %s %s %s" % ["PASS" if ok else "FAIL", name, detail])

func near(a: float, b: float, epsilon := 0.001) -> bool:
	return absf(a - b) < epsilon

func setup() -> Dictionary:
	return {"site_id": "elysium", "seed": 42, "build": {"solar": "solar_high", "battery": "battery_extended",
		"shield": "shield_minimal", "antenna": "antenna_standard", "instruments": ["spectrometer", "ground_radar", "radiation_detector"]}}

func _initialize() -> void:
	var targets := ["ancient_delta", "crater"]
	var nominal := MissionSim.run(setup(), targets, [], "nominal")
	check("nominal run is valid", nominal.valid, nominal.error)
	check("nominal completes all targets and mission", nominal.ending == "returned" and nominal.completed_targets == 2 and nominal.end_sol == 100, str(nominal))
	check("nominal log contains one stable state per sol", nominal.log.size() == 100 and nominal.log[0].sol == 1 and nominal.log[99].sol == 100)
	check("nominal returns collected data", nominal.final.data_returned > 0.0 and nominal.final.data_buffered >= 0.0)
	check("nominal golden final state", near(nominal.final.battery, 200.0) and near(nominal.final.health, 97.365217)
		and near(nominal.final.science_gathered, 283.2) and near(nominal.final.data_returned, 283.2), str(nominal.final))
	check("same input produces the same log", MissionSim.run(setup(), targets, [], "nominal").log_hash == nominal.log_hash, nominal.log_hash)
	check("nominal log matches the fixed golden hash", nominal.log_hash == GOLDEN_HASHES.nominal, nominal.log_hash)
	var different_seed := setup()
	different_seed.seed = 43
	check("different seeds produce a different nominal log", MissionSim.run(different_seed, targets, [], "nominal").log_hash != nominal.log_hash)

	var storm := MissionSim.run(setup(), targets, [], "opportunity_2018")
	check("storm fixture is valid and emits a storm warning", storm.valid and storm.log[5].events.has("storm_warning"), storm.error)
	check("storm default policy hibernates", storm.log[5].action == "hibernate", str(storm.log[5]))
	check("storm golden final state", storm.ending == "returned" and near(storm.final.battery, 200.0)
		and near(storm.final.science_gathered, 278.4) and near(storm.final.health, 97.365217), str(storm.final))
	check("storm log matches the fixed golden hash", storm.log_hash == GOLDEN_HASHES.opportunity_2018, storm.log_hash)
	var press_on := MissionSim.run(setup(), targets, [{"sol": 6, "event": "storm_warning", "choice": "press_on"}], "opportunity_2018")
	check("explicit storm choice overrides conservative policy", press_on.valid and press_on.log[5].action == "rest", str(press_on.log[5]))

	var relay := MissionSim.run(setup(), targets, [], "relay_degraded")
	check("degraded relay returns less data than nominal", relay.valid and relay.final.data_returned < nominal.final.data_returned,
		"%s / %s" % [relay.final.data_returned, nominal.final.data_returned])
	check("degraded-relay log matches the fixed golden hash", relay.log_hash == GOLDEN_HASHES.relay_degraded, relay.log_hash)
	var fragile_setup := {"site_id": "elysium", "seed": 42, "build": {"solar": "solar_high", "battery": "battery_standard",
		"shield": "shield_minimal", "antenna": "antenna_high_gain", "instruments": ["spectrometer", "hires_camera", "weather_sensor"]}}
	var press_on_storm := MissionSim.run(fragile_setup, ["ancient_delta", "ridge"], [{"sol": 6, "event": "storm_warning", "choice": "press_on"},
		{"sol": 7, "event": "storm_warning", "choice": "press_on"}, {"sol": 8, "event": "storm_warning", "choice": "press_on"},
		{"sol": 9, "event": "storm_warning", "choice": "press_on"}, {"sol": 10, "event": "storm_warning", "choice": "press_on"}], "opportunity_2018")
	check("continuing through a severe storm can end the mission on power", press_on_storm.valid and press_on_storm.ending == "partial"
		and press_on_storm.cause == "power_depleted", str(press_on_storm))

	check("empty targets are rejected", not MissionSim.run(setup(), [], [], "nominal").valid)
	check("duplicate targets are rejected", not MissionSim.run(setup(), ["crater", "crater"], [], "nominal").valid)
	check("unknown scenario is rejected", not MissionSim.run(setup(), targets, [], "missing").valid)
	check("invalid build is rejected", not MissionSim.run({"site_id": "elysium", "build": {}}, targets, [], "nominal").valid)
	check("malformed decision is rejected", not MissionSim.run(setup(), targets, [{"sol": 0, "event": "storm_warning", "choice": "hibernate"}], "nominal").valid)
	check("same-sol decisions conflict", not MissionSim.run(setup(), targets, [{"sol": 6, "event": "storm_warning", "choice": "hibernate"},
		{"sol": 6, "event": "low_power", "choice": "rest"}], "opportunity_2018").valid)

	print("MISSION_DONE checks=%d failed=%d" % [count, failed])
	quit(1 if failed else 0)
