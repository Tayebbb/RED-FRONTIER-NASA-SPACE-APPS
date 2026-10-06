extends SceneTree
## Formula and validation tests for RF-01 builds (game/data/rover_build.gd) against Rules and Scoring v1.0.
## Run: Godot --headless --path godot --script res://tests/rover_build_test.gd
## The Engineering expectations for the three complete builds are the rules document's own §5 reference runs.

const RoverBuild := preload("res://game/data/rover_build.gd")
const RoverParts := preload("res://game/data/rover_parts.gd")
const LandingSites := preload("res://game/data/landing_sites.gd")

var failed := 0
var count := 0

func check(name: String, ok: bool, detail := "") -> void:
	count += 1
	if not ok:
		failed += 1
	print("BUILD_CHECK %s %s %s" % ["PASS" if ok else "FAIL", name, detail])

func near(a, b: float, eps := 0.001) -> bool:
	return a != null and absf(float(a) - b) < eps

func build(solar: String, battery: String, shield: String, antenna: String, inst: Array) -> Dictionary:
	return {"solar": solar, "battery": battery, "shield": shield, "antenna": antenna, "instruments": inst}

func _initialize() -> void:
	# --- part sheet -------------------------------------------------------------------------------------------
	var n := 0
	for key in RoverParts.categories():
		n += RoverParts.category_parts(key).size()
	check("part sheet: 15 parts in 5 categories", n == 15 and RoverParts.categories().size() == 5)
	var hg := RoverParts.part("antenna_high_gain")
	check("part sheet: high-gain antenna 45 kg, 90 cr, rel .95, draw 6, no value", hg.mass == 45 and hg.cost == 90
		and near(hg.reliability, 0.95) and hg.draw == 6 and not hg.has("value"))
	check("part sheet: extended battery capacity 200", RoverParts.part("battery_extended").capacity == 200)
	check("part sheet: radiation detector keeps its Mars metadata", RoverParts.part("radiation_detector").storm_damage == -3
		and RoverParts.part("radiation_detector").passive_science == 6 and RoverParts.part("spectrometer").site == "ancient_delta")

	var jezero := LandingSites.get_site("jezero")
	var elysium := LandingSites.get_site("elysium")
	var gale := LandingSites.get_site("gale")

	# --- §5 reference run "Breakthrough": Elysium, Engineering 75 -------------------------------------------------
	var b1 := build("solar_high", "battery_extended", "shield_minimal", "antenna_standard",
		["spectrometer", "ground_radar", "radiation_detector"])
	var r := RoverBuild.evaluate(b1, elysium)
	check("elysium breakthrough: mass 225, cost 395, valid", r.mass == 225 and r.cost == 395 and r.valid, str(r.problems))
	check("elysium breakthrough: demand 36, supply 48.944", near(r.demand, 36.0) and near(r.supply, 48.944))
	check("elysium breakthrough: power clamps to 100 (raw 114.1)", near(r.power, 100.0))
	check("elysium breakthrough: safety 44.326", near(r.safety, 7.826087 + 24.5 + 12.0))
	check("elysium breakthrough: science 69.9", near(r.build_science, 0.62 * 45.0 + 42.0))
	check("elysium breakthrough: ENGINEERING 75 (rules §5)", r.engineering == 75, str(r.engineering))

	# --- §5 "High-risk success": Jezero, Engineering 62 --------------------------------------------------------
	var b2 := build("solar_high", "battery_standard", "shield_minimal", "antenna_high_gain",
		["spectrometer", "hires_camera", "weather_sensor"])
	r = RoverBuild.evaluate(b2, jezero)
	check("jezero high-risk: mass 200, cost 370, valid", r.mass == 200 and r.cost == 370 and r.valid)
	check("jezero high-risk: demand 39, supply 42.256", near(r.demand, 39.0) and near(r.supply, 42.256))
	check("jezero high-risk: power 78.000", near(r.power, (42.256 + 12.5) / (39.0 * 1.8) * 100.0), str(r.power))
	check("jezero high-risk: safety 41.526", near(r.safety, 7.826087 + 14.7 + 19.0), str(r.safety))
	check("jezero high-risk: science 78.95", near(r.build_science, 0.91 * 45.0 + 38.0))
	check("jezero high-risk: ENGINEERING 62 (rules §5)", r.engineering == 62, str(r.engineering))

	# --- §5 "Safe but limited": Elysium, Engineering 89 --------------------------------------------------------
	var b3 := build("solar_high", "battery_standard", "shield_heavy", "antenna_standard",
		["hires_camera", "soil_analyzer", "weather_sensor"])
	r = RoverBuild.evaluate(b3, elysium)
	check("elysium safe: mass 250, cost 395", r.mass == 250 and r.cost == 395 and r.valid)
	check("elysium safe: power 94.82, safety 81.5", near(r.power, (48.944 + 12.5) / 64.8 * 100.0) and near(r.safety, 81.5))
	check("elysium safe: ENGINEERING 89 (rules §5)", r.engineering == 89, str(r.engineering))

	# --- Gale: same build as "safe", hand-computed -------------------------------------------------------------
	r = RoverBuild.evaluate(b3, gale)
	check("gale: supply 41.04, power 82.623", near(r.supply, 41.04) and near(r.power, (41.04 + 12.5) / 64.8 * 100.0), str(r.power))
	check("gale: safety 64.7, science 71.6, ENGINEERING 75", near(r.safety, 64.7) and near(r.build_science, 71.6)
		and r.engineering == 75, "%s %s %s" % [r.safety, r.build_science, r.engineering])

	# --- clamp -------------------------------------------------------------------------------------------------
	check("clamp: -5 -> 0, 150 -> 100, 42.5 unchanged", RoverBuild.clamp_score(-5.0) == 0.0 and RoverBuild.clamp_score(150.0) == 100.0
		and RoverBuild.clamp_score(42.5) == 42.5)

	# --- partial builds: never NaN, never a misleading score ---------------------------------------------------
	r = RoverBuild.evaluate(RoverBuild.empty_build(), jezero)
	check("empty build: 0 kg, 0 credits, all scores null", r.mass == 0 and r.cost == 0 and r.power == null and r.safety == null
		and r.build_science == null and r.engineering == null and r.demand == null)
	check("empty build: lists every missing category", r.problems == ["SELECT A SOLAR ARRAY", "SELECT A BATTERY", "SELECT SHIELDING",
		"SELECT AN ANTENNA", "SELECT 3 MORE INSTRUMENTS"] and not r.valid, str(r.problems))
	r = RoverBuild.evaluate(build("solar_high", "", "shield_heavy", "", ["spectrometer"]), jezero)
	check("partial: mass/cost live, power & safety wait for battery/antenna, science shown", r.mass == 175 and r.cost == 285
		and r.power == null and r.safety == null and near(r.build_science, 40.95 + 20.0) and r.problems.has("SELECT 2 MORE INSTRUMENTS"))
	r = RoverBuild.evaluate(b1, {})
	check("no landing site: no site-dependent scores, not valid", r.power == null and r.safety == null and r.build_science == null
		and not r.valid and r.problems.has("NO LANDING SITE LOCKED"))

	# --- limits ------------------------------------------------------------------------------------------------
	r = RoverBuild.evaluate(build("solar_high", "battery_extended", "shield_heavy", "antenna_standard",
		["spectrometer", "ground_radar", "hires_camera"]), gale)
	check("over mass: 310 kg -> OVER MASS BY 50 KG, invalid", r.mass == 310 and r.problems.has("OVER MASS BY 50 KG") and not r.valid,
		str(r.problems))
	r = RoverBuild.evaluate(build("solar_light", "battery_standard", "shield_standard", "antenna_high_gain",
		["spectrometer", "ground_radar", "soil_analyzer"]), gale)
	check("over budget only: 225 kg, 415 cr -> OVER BUDGET BY 15 CREDITS", r.mass == 225 and r.cost == 415
		and r.problems == ["OVER BUDGET BY 15 CREDITS"] and not r.valid, str(r.problems))
	r = RoverBuild.evaluate(build("solar_high", "battery_extended", "shield_heavy", "antenna_standard",
		["weather_sensor", "radiation_detector", "hires_camera"]), gale)
	check("exactly at the limit is not enough when over: 275 kg / 430 cr", r.over_mass == 15 and r.over_budget == 30)

	# --- selection helper --------------------------------------------------------------------------------------
	var b := RoverBuild.empty_build()
	for id in ["spectrometer", "ground_radar", "hires_camera", "soil_analyzer"]:
		b = RoverBuild.with_part(b, id)
	check("instruments: a fourth is refused", b.instruments == ["spectrometer", "ground_radar", "hires_camera"])
	b = RoverBuild.with_part(b, "ground_radar")
	check("instruments: picking a selected one removes it", b.instruments == ["spectrometer", "hires_camera"])
	b = RoverBuild.with_part(RoverBuild.with_part(b, "shield_minimal"), "shield_heavy")
	check("single categories: a new pick replaces the old", b.shield == "shield_heavy")
	check("signature ignores instrument order", RoverBuild.signature(b1) == RoverBuild.signature(build("solar_high", "battery_extended",
		"shield_minimal", "antenna_standard", ["radiation_detector", "spectrometer", "ground_radar"])) and RoverBuild.signature(b1) != RoverBuild.signature(b2))

	print("BUILD_DONE checks=%d failed=%d" % [count, failed])
	quit(1 if failed else 0)
