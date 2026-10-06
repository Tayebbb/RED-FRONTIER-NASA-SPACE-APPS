extends Node
## Gameplay acceptance test: drives the real game with simulated input through the opening mission beat.
## Run windowed:  Godot --path godot -- gameplay_test
## Spawn -> walk -> wall collision -> briefing prompt -> E -> briefing (input locked) -> Continue -> objective
## updates -> walk on through Corridor 01 into Mars Intelligence (room streaming) -> landing site analysis (inspect
## all three, BACK, reopen, confirm) -> walk to the Hangar -> build RF-01 (empty start, live meters, 3/3 instruments,
## over mass, over budget, legal, accept, edit, Twin invalidation) -> MissionState reset. Screenshots: godot/logs/gameplay/

const OUT := "res://logs/gameplay/"
var game: Node
var player: Player
var results: Array = []
var failed := 0
var camera_outside := 0

func _ready() -> void:
	game = get_parent()
	player = game.player
	player.mouse_look = false                  # a real mouse moving during the run must not steer the test
	player._pitch = deg_to_rad(-12.0)
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT))
	_run.call_deferred()

func check(name: String, ok: bool, detail := "") -> void:
	results.append({"check": name, "ok": ok, "detail": detail})
	if not ok:
		failed += 1
	print("GAMEPLAY_CHECK %s %s %s" % ["PASS" if ok else "FAIL", name, detail])

func frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

## Input events are handled on idle (process) frames; at low fps several physics frames fit in one of those.
func idle(n: int) -> void:
	for i in n:
		await get_tree().process_frame

func shot(name: String) -> void:
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png(ProjectSettings.globalize_path(OUT + name + ".png"))

func hold(action: String, seconds: float) -> void:
	Input.action_press(action)
	await get_tree().create_timer(seconds).timeout
	Input.action_release(action)
	await frames(12)

func tap(action: String) -> void:
	var ev := InputEventAction.new()
	ev.action = action
	ev.pressed = true
	Input.parse_input_event(ev)
	await idle(3)
	ev = ev.duplicate()
	ev.pressed = false
	Input.parse_input_event(ev)
	await idle(3)

## A real left click on a control (the mouse must be free, as it is while a panel is open).
func click(c: Control) -> void:
	var pos := c.get_global_rect().get_center()
	for down in [true, false]:
		var ev := InputEventMouseButton.new()
		ev.button_index = MOUSE_BUTTON_LEFT
		ev.pressed = down
		ev.position = pos
		ev.global_position = pos
		Input.parse_input_event(ev)
		await idle(3)

## Steer toward a point (sets the camera yaw, holds forward) until within reach or out of time.
func walk_to(target: Vector3, reach := 0.35, timeout := 15.0) -> bool:
	var t := 0.0
	Input.action_press("move_forward")
	while t < timeout:
		var d := target - player.global_position
		d.y = 0.0
		if d.length() < reach:
			break
		player._yaw = atan2(-d.x, -d.z)
		_watch_camera()
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
	Input.action_release("move_forward")
	await frames(10)
	var left := Vector2(target.x - player.global_position.x, target.z - player.global_position.z).length()
	return left < reach + 0.3

func _watch_camera() -> void:
	if not _camera_inside():
		camera_outside += 1
		print("GAMEPLAY_CAMERA_OUTSIDE cam=%s player=%s room=%s" % [player.camera.global_position, player.global_position, game.streamer.current])

## Inside a (padded) room footprint, whether or not that room is loaded.
func _in_footprint(p: Vector3) -> bool:
	for room in game.streamer.manifests:
		var f: Dictionary = game.streamer.manifests[room].footprint
		var pad := GameConfig.FOOTPRINT_PAD
		if p.x >= f.x[0] - pad and p.x <= f.x[1] + pad and p.z >= f.z[0] - pad and p.z <= f.z[1] + pad:
			return true
	return false

## Camera inside a room's footprint and below its ceiling.
func _camera_inside() -> bool:
	var c := player.camera.global_position
	if not _in_footprint(c):
		return false
	var room: String = game.streamer.room_at(c)
	return room == "" or c.y < float(game.streamer.manifests[room].footprint.h) - 0.05

## Route walking state (RF_Route.json waypoints), shared by the Hangar approach and the `full` run.
var route: Array = []
var rooms_seen: Array = []
var resident_max := 0
var prompts_seen := {}
var lowest := 0.0
var waited_at_door := 0.0

## Walk route waypoints from..to (inclusive); returns "" or where the player got stuck.
func _walk_route(from_i: int, to_i: int) -> String:
	if route.is_empty():
		route = JSON.parse_string(FileAccess.get_file_as_string("res://assets/RF_Route.json")).route
	for i in range(from_i, to_i + 1):
		var wp := Vector3(route[i][0], 0.0, route[i][1])
		var t := 0.0
		Input.action_press("move_forward")
		while t < 25.0:
			var to := wp - player.global_position
			to.y = 0.0
			if to.length() < 0.9:                          # stations stand on their markers: arrive near, not on
				break
			player._yaw = atan2(-to.x, -to.z)
			_watch_camera()
			if player.get_real_velocity().length() < 0.05:
				waited_at_door += get_physics_process_delta_time()
			if player.interactor.focused != null:
				prompts_seen[player.interactor.focused.interaction_id] = true
			resident_max = maxi(resident_max, game.streamer.loaded.size())
			if player.global_position.y < -0.3 and lowest >= -0.3:
				print("GAMEPLAY_FALL at %s room=%s resident=%s collision_queue=%d" % [player.global_position, game.streamer.current,
					game.streamer.loaded.keys(), game.collision.pending()])
			lowest = minf(lowest, player.global_position.y)
			if game.streamer.current != rooms_seen.back() and game.streamer.current != "":
				rooms_seen.append(game.streamer.current)
			await get_tree().physics_frame
			t += get_physics_process_delta_time()
		Input.action_release("move_forward")
		if Vector2(wp.x - player.global_position.x, wp.z - player.global_position.z).length() > 1.2:
			return "waypoint %d %s, player at %s" % [i, wp, player.global_position]
		if i == 13:
			await shot("20_hangar")
	await frames(10)
	return ""

## `-- gameplay_test full`: on from the configuration console round the Hangar loop to the launch console.
func _walk_on_to_mission_control() -> void:
	var stuck := await _walk_route(12, route.size() - 1)
	await frames(30)
	check("full route: reached the launch console", stuck == "", stuck)
	check("full route: every room in order", rooms_seen == ["Briefing", "Corridor01", "MarsIntel", "Corridor02", "Hangar", "MissionControl"],
		str(rooms_seen))
	check("full route: at most 3 rooms resident", resident_max <= 3, "max=%d" % resident_max)
	check("full route: a streamed-in room is walkable", game._inside_facility(Vector3(17.4, 0, -47.75)))
	check("full route: never fell through a floor", lowest > -0.3, "lowest y=%.2f" % lowest)
	print("GAMEPLAY_INFO waited %.1f s for rooms to finish streaming" % waited_at_door)
	var stray := prompts_seen.keys().filter(func(id): return not game.interactions._handlers.has(id))
	check("full route: unregistered stations stay silent", stray.is_empty(), str(stray))
	check("full route: camera never left the facility", camera_outside == 0, "%d frames outside" % camera_outside)
	await shot("21_missioncontrol")

## Engineering Hangar: walk from Mars Intelligence to the RF-01 configuration console (INT_MissionConfig) and build.
func _hangar() -> void:
	var stuck := await _walk_route(7, 11)
	check("hangar: walked from Mars Intelligence to the configuration console", stuck == "" and game.streamer.current == "Hangar",
		"%s room=%s" % [stuck, game.streamer.current])
	check("hangar: never fell through a floor on the way", lowest > -0.3, "lowest y=%.2f" % lowest)
	await frames(5)
	var focus := player.interactor.focused
	check("hangar: [E] CONFIGURE RF-01 prompt at the console", game.hud.prompt_visible() and focus != null
		and focus.interaction_id == "MissionConfig" and game.hud._prompt_key.text == "[E] CONFIGURE RF-01",
		"focus=%s key=%s" % [focus.interaction_id if focus else "none", game.hud._prompt_key.text])
	check("hangar: SCIENCE/POWER/MOBILITY/COMMS stations silent", not game.interactions._handlers.has("Station_POWER")
		and not game.interactions._handlers.has("Station_SCIENCE") and not game.interactions._handlers.has("Station_MOBILITY")
		and not game.interactions._handlers.has("Station_COMMS"))
	await shot("12_config_prompt")

	await tap("interact")
	var panel = game.config_panel
	check("config: E opens the RF-01 configuration", panel != null and is_instance_valid(panel))
	if panel == null:
		return
	var p := player.global_position
	await hold("move_forward", 0.5)
	check("config: movement locked, interaction off, mouse free", player.global_position.distance_to(p) < 0.05
		and not player.controls_enabled and not player.interactor.active and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE)
	var none_pressed := true
	for id in panel.cards:
		none_pressed = none_pressed and not panel.cards[id].button_pressed
	check("config: nothing selected at the start", none_pressed and panel.shown("mass") == "0 / 260 KG"
		and panel.shown("budget") == "0 / 400 CREDITS" and panel.shown("power") == "—" and panel.shown("safety") == "—"
		and panel.shown("science") == "—" and panel.accept_button.disabled, "%s %s" % [panel.shown("mass"), panel.shown("power")])
	check("config: status lists every missing category", panel.shown_problems().size() == 5, str(panel.shown_problems()))
	await shot("13_config_empty")

	# Gale (locked in Mission 2). Meters react to every pick.
	await click(panel.cards["solar_high"])
	check("config: high-output solar -> 60 KG, 85 CREDITS, power still incomplete", panel.shown("mass") == "60 / 260 KG"
		and panel.shown("budget") == "85 / 400 CREDITS" and panel.shown("power") == "—")
	await click(panel.cards["battery_standard"])
	await click(panel.cards["antenna_standard"])
	check("config: solar + battery + antenna -> power appears (100, no instruments yet)", panel.shown("power") == "100", panel.shown("power"))
	await click(panel.cards["shield_heavy"])
	check("config: heavy shielding -> safety 65", panel.shown("safety") == "65", panel.shown("safety"))
	await click(panel.cards["hires_camera"])
	check("config: first instrument -> science 52", panel.shown("science") == "52", panel.shown("science"))
	await click(panel.cards["soil_analyzer"])
	await click(panel.cards["weather_sensor"])
	check("config: third instrument raises demand -> power falls to 83", panel.shown("power") == "83" and panel._instrument_count.text == "3 / 3",
		"%s %s" % [panel.shown("power"), panel._instrument_count.text])
	check("config: unselected instruments unavailable at 3/3", panel.cards["spectrometer"].disabled and panel.cards["ground_radar"].disabled
		and not panel.cards["hires_camera"].disabled)
	await click(panel.cards["spectrometer"])
	check("config: a fourth instrument cannot be added", panel.build.instruments.size() == 3 and not "spectrometer" in panel.build.instruments)
	await shot("14_config_full_instruments")

	await click(panel.cards["battery_extended"])                    # 285 kg / 455 credits
	check("config: overweight -> OVER MASS BY 25 KG, ACCEPT blocked", panel.shown("mass") == "285 / 260 KG"
		and panel.shown_problems().has("OVER MASS BY 25 KG") and panel.accept_button.disabled, str(panel.shown_problems()))
	await shot("15_config_over_mass")
	for id in ["battery_standard", "shield_standard", "antenna_high_gain", "weather_sensor", "spectrometer"]:
		await click(panel.cards[id])
	check("config: over budget only -> OVER BUDGET BY 35 CREDITS, ACCEPT blocked", panel.shown("budget") == "435 / 400 CREDITS"
		and panel.shown("mass") == "240 / 260 KG" and panel.shown_problems() == ["OVER BUDGET BY 35 CREDITS"] and panel.accept_button.disabled,
		str(panel.shown_problems()))
	await shot("16_config_over_budget")
	await click(panel.cards["antenna_standard"])                   # 215 kg / 375 credits
	check("config: legal build -> CONFIGURATION VALID, ACCEPT enabled", panel.shown_problems().is_empty() and not panel.accept_button.disabled
		and panel.shown("mass") == "215 / 260 KG" and panel.shown("budget") == "375 / 400 CREDITS")
	check("config: Gale meters match the formulas (power 83, safety 43, science 86)", panel.shown("power") == "83"
		and panel.shown("safety") == "43" and panel.shown("science") == "86",
		"%s %s %s" % [panel.shown("power"), panel.shown("safety"), panel.shown("science")])
	check("config: nothing stored before ACCEPT", not MissionState.rover_configured and MissionState.solar_system == "")
	await shot("17_config_valid")

	await click(panel.accept_button)
	var st: Dictionary = MissionState.build_stats()
	check("accept: MissionState holds the stable ids", MissionState.rover_configured and MissionState.solar_system == "solar_high"
		and MissionState.battery_system == "battery_standard" and MissionState.shielding == "shield_standard"
		and MissionState.antenna == "antenna_standard" and MissionState.selected_instruments == ["hires_camera", "soil_analyzer", "spectrometer"],
		str(MissionState.current_build()))
	check("accept: stored numbers match the formulas", MissionState.mass == 215 and MissionState.budget == 375 and st.demand == 36.0
		and absf(st.supply - 41.04) < 0.001 and absf(st.power - 82.6234568) < 0.001 and absf(st.safety - 43.1782609) < 0.001
		and absf(st.build_science - 85.6) < 0.001 and st.engineering == 65, str(st))
	check("accept: phase DIGITAL_TWIN, objective Run the Digital Twin", MissionState.mission_phase == MissionState.Phase.DIGITAL_TWIN
		and MissionState.current_objective == &"run_digital_twin")
	check("accept: RF-01 CONFIGURATION SAVED shown", panel.is_saved())
	await shot("18_config_saved")
	await click(panel.continue_button)
	check("accept: Continue closes and restores control", game.config_panel == null and player.controls_enabled and player.interactor.active)
	check("objective: now Run the Digital Twin", game.hud.objective_shown() == "Run the Digital Twin", game.hud.objective_shown())
	await frames(5)
	check("config: station stays available for edits until launch", game.hud.prompt_visible()
		and player.interactor.focused != null and player.interactor.focused.interaction_id == "MissionConfig")
	await shot("19_objective_twin")

	# Edits after acceptance, with a stand-in Digital Twin result (the Twin itself is a later mission).
	MissionState.set_value(&"digital_twin_completed", true)
	MissionState.set_value(&"twin_build_signature", MissionState.build_signature())
	MissionState.set_value(&"predicted_success", 0.7)
	check("twin hook: a result on the current build is current", MissionState.twin_is_current())
	check("twin hook: re-accepting the identical build keeps it", MissionState.accept_build(MissionState.current_build())
		and MissionState.twin_is_current() and MissionState.predicted_success == 0.7)
	await tap("interact")
	panel = game.config_panel
	check("edit: reopening shows the saved build", panel != null and panel.cards["shield_standard"].button_pressed
		and panel.cards["spectrometer"].button_pressed and panel.shown("mass") == "215 / 260 KG")
	if panel == null:
		return
	await click(panel.cards["shield_heavy"])
	await click(panel.back_button)
	check("edit: BACK discards unsaved changes", game.config_panel == null and MissionState.shielding == "shield_standard"
		and MissionState.twin_is_current())
	await frames(5)
	await tap("interact")
	panel = game.config_panel
	if panel == null:
		check("edit: station reopens", false)
		return
	await click(panel.cards["shield_minimal"])
	await click(panel.accept_button)
	check("edit: changed build saved", MissionState.shielding == "shield_minimal" and MissionState.mass == 185 and MissionState.budget == 335)
	check("edit: the stale Digital Twin result is invalidated", not MissionState.digital_twin_completed
		and MissionState.predicted_success == null and MissionState.twin_build_signature == "" and not MissionState.twin_is_current())
	check("edit: objective back to Run the Digital Twin", MissionState.current_objective == &"run_digital_twin")
	await click(panel.continue_button)
	check("edit: control restored", game.config_panel == null and player.controls_enabled)

## Mars Intelligence: the landing-analysis console (INT_LandingSystem), standing next to it.
func _landing_site() -> void:
	await frames(5)
	var focus := player.interactor.focused
	check("landing: [E] prompt at the landing-analysis console", game.hud.prompt_visible() and focus != null
		and focus.interaction_id == "LandingSystem", "focus=%s" % (focus.interaction_id if focus else "none"))
	await shot("08_landing_prompt")

	await tap("interact")
	var panel = game.landing_panel
	check("landing: E opens the analysis panel", panel != null and is_instance_valid(panel))
	if panel == null:
		return
	check("landing: player movement and interaction disabled, mouse free", not player.controls_enabled and not player.interactor.active
		and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE)
	var p := player.global_position
	await hold("move_forward", 0.5)
	var look := Vector2(player._yaw, player._pitch)
	player.mouse_look = true
	var motion := InputEventMouseMotion.new()
	motion.relative = Vector2(300, 120)
	Input.parse_input_event(motion)
	await frames(3)
	player.mouse_look = false
	check("landing: no movement or camera turn while open", player.global_position.distance_to(p) < 0.05
		and Vector2(player._yaw, player._pitch) == look)
	check("landing: opening commits nothing", not MissionState.landing_site_selected and MissionState.landing_site == "")

	var expect := {"jezero": ["JEZERO CRATER", "VERY HIGH", "MODERATE", "MODERATE-HIGH"],
		"elysium": ["ELYSIUM PLANITIA", "MODERATE", "HIGH", "LOW"],
		"gale": ["GALE CRATER", "VERY HIGH", "MODERATE", "HIGH"]}
	check("landing: Jezero shown first", panel.shown_name() == "JEZERO CRATER", panel.shown_name())
	var n := 0
	for id in ["elysium", "gale", "jezero"]:
		await click(panel.site_buttons[id])
		var e: Array = expect[id]
		check("landing: clicking %s shows its analysis" % id.to_upper(), panel.current_id == id and panel.shown_name() == e[0]
			and panel.shown_label("science") == e[1] and panel.shown_label("solar") == e[2] and panel.shown_label("terrain_risk") == e[3],
			"%s %s/%s/%s" % [panel.shown_name(), panel.shown_label("science"), panel.shown_label("solar"), panel.shown_label("terrain_risk")])
		n += 1
		await shot("09_landing_%d_%s" % [n, id])
	check("landing: inspecting commits nothing", not MissionState.landing_site_selected and MissionState.landing_site == "")

	await click(panel.back_button)
	check("landing: BACK closes without selecting", game.landing_panel == null and not MissionState.landing_site_selected
		and MissionState.current_objective == &"proceed_mars_intel" and player.controls_enabled)
	await frames(5)

	await tap("interact")
	panel = game.landing_panel
	check("landing: console reopens after BACK", panel != null and is_instance_valid(panel))
	if panel == null:
		return
	await click(panel.site_buttons["gale"])
	await click(panel.confirm_button)
	var site: Dictionary = MissionState.landing_site_data()
	check("landing: CONFIRM stores the stable site id", MissionState.landing_site_selected and MissionState.landing_site == "gale",
		"landing_site=%s" % MissionState.landing_site)
	check("landing: site data retrievable from MissionState", site.get("science") == 0.88 and site.get("solar") == 0.60
		and site.get("terrain_risk") == 0.78, str(site))
	check("landing: LANDING SITE LOCKED card shown", panel.is_locked() and panel.shown_name() == "GALE CRATER", panel.shown_name())
	await shot("10_landing_locked")
	await click(panel.continue_button)
	check("landing: Continue closes the panel and restores control", game.landing_panel == null and player.controls_enabled
		and player.interactor.active)
	check("landing: phase advanced to ROVER_CONFIG", MissionState.mission_phase == MissionState.Phase.ROVER_CONFIG)
	check("objective: now Proceed to Engineering Hangar", MissionState.current_objective == &"proceed_engineering_hangar"
		and game.hud.objective_shown() == "Proceed to Engineering Hangar", game.hud.objective_shown())
	await frames(5)
	check("landing: console silent once the site is locked", not game.hud.prompt_visible())
	check("landing: a second selection is refused", not MissionState.select_landing_site("jezero") and MissionState.landing_site == "gale")
	await shot("11_objective_hangar")

func _run() -> void:
	await frames(30)
	var p0 := player.global_position
	check("boot: player spawned at PLAYER_Start", Vector2(p0.x, p0.z).distance_to(Vector2(0.0, -1.2)) < 0.25 and absf(p0.y) < 0.2,
		"pos=%s" % p0)
	check("boot: start room resident", game.streamer.loaded.has("Briefing"), str(game.streamer.loaded.keys()))
	check("boot: objective is Attend the Mission Briefing",
		MissionState.current_objective == &"attend_briefing" and game.hud.objective_shown() == "Attend the Mission Briefing", game.hud.objective_shown())
	check("boot: player on the floor", player.is_on_floor())
	check("boot: landing console inactive before the briefing", not game.interactions._handlers.has("LandingSystem"))
	check("boot: rooms not streamed in yet are off-limits", game._inside_facility(p0) and not game._inside_facility(Vector3(0, 0, -44)))
	check("boot: third-person camera active", player.camera.current and player.camera.global_position.distance_to(player.global_position) > 1.5,
		"cam=%s" % player.camera.global_position)
	check("boot: camera behind the player at shoulder height", _camera_inside() and player.camera.global_position.z > p0.z + 1.0
		and player.camera.global_position.y > 1.5 and player.camera.global_position.y < 3.0, "cam=%s" % player.camera.global_position)
	await shot("01_spawn")

	await hold("move_forward", 0.8)
	var p1 := player.global_position
	check("movement: W moves toward the camera's facing (-Z)", p1.z < p0.z - 1.0 and absf(p1.x - p0.x) < 0.2, "from %s to %s" % [p0, p1])

	await hold("move_left", 3.0)                           # into the west wall (inner face x = -4.0)
	var p2 := player.global_position
	check("collision: west wall stops the player", p2.x > -3.8 and p2.x < -3.0, "x=%.2f" % p2.x)
	check("camera: stays inside the room against the wall", _camera_inside(),
		"cam=%s" % player.camera.global_position)
	await shot("02_wall")

	check("interaction: no prompt away from the table", not game.hud.prompt_visible())
	var marker: Vector3 = game.interactions.get_interactable("BriefingTable").global_position
	var arrived := await walk_to(marker + Vector3(0.0, 0.0, 0.6))
	check("interaction: reached the briefing table", arrived, "pos=%s" % player.global_position)
	await frames(5)
	var focus := player.interactor.focused
	check("interaction: [E] INTERACT prompt shown", game.hud.prompt_visible() and focus != null and focus.interaction_id == "BriefingTable",
		"focus=%s" % (focus.interaction_id if focus else "none"))
	await shot("03_prompt")

	await tap("interact")
	check("briefing: E opens the briefing panel", game.briefing != null and is_instance_valid(game.briefing))
	check("briefing: player controls disabled", not player.controls_enabled and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE)
	check("briefing: prompt hidden while open", not game.hud.prompt_visible())
	await shot("04_briefing")
	var p3 := player.global_position
	await hold("move_forward", 0.6)
	check("briefing: movement ignored while open", player.global_position.distance_to(p3) < 0.05,
		"moved %.3f m" % player.global_position.distance_to(p3))
	await tap("interact")
	check("briefing: E does not close or re-open it", game.briefing != null and is_instance_valid(game.briefing))

	await tap("ui_accept")                                 # CONTINUE has focus
	if game.briefing != null and is_instance_valid(game.briefing):
		check("briefing: CONTINUE has keyboard focus", false)
		game.briefing.continue_button.pressed.emit()
		await frames(3)
	check("briefing: Continue closes the panel", game.briefing == null)
	check("state: MissionState.briefing_completed = true", MissionState.briefing_completed)
	check("state: phase advanced to LANDING_SITE", MissionState.mission_phase == MissionState.Phase.LANDING_SITE)
	check("objective: now Proceed to Mars Intelligence",
		MissionState.current_objective == &"proceed_mars_intel" and game.hud.objective_shown() == "Proceed to Mars Intelligence", game.hud.objective_shown())
	check("control: player control restored", player.controls_enabled and player.interactor.active)
	await shot("05_objective")

	var rooms_seen := [game.streamer.current]
	var resident_max := 0
	for wp in [Vector3(2.75, 0, -6.4), Vector3(2.75, 0, -10.6), Vector3(2.75, 0, -15.6), Vector3(2.75, 0, -17.6), Vector3(0.4, 0, -18.6)]:
		var ok := await walk_to(wp, 0.4, 20.0)
		if not ok:
			check("walk: reached waypoint %s" % wp, false, "stuck at %s" % player.global_position)
			break
		if game.streamer.current != rooms_seen.back():
			rooms_seen.append(game.streamer.current)
		resident_max = maxi(resident_max, game.streamer.loaded.size())
		if wp.z < -10.0 and wp.z > -16.0:
			await shot("06_corridor01")
	await frames(90)
	resident_max = maxi(resident_max, game.streamer.loaded.size())
	check("streaming: walked Briefing -> Corridor01 -> MarsIntel", rooms_seen == ["Briefing", "Corridor01", "MarsIntel"], str(rooms_seen))
	check("streaming: Briefing unloaded, Corridor02 loaded", not game.streamer.loaded.has("Briefing") and game.streamer.loaded.has("Corridor02"),
		str(game.streamer.loaded.keys()))
	check("streaming: at most 3 rooms resident", resident_max <= 3, "max=%d" % resident_max)
	check("collision: Mars Intelligence floor holds the player", player.is_on_floor() and absf(player.global_position.y) < 0.2,
		"pos=%s" % player.global_position)
	check("camera: never left the facility while walking", camera_outside == 0, "%d frames outside" % camera_outside)
	await shot("07_marsintel")

	await _landing_site()
	self.rooms_seen = rooms_seen
	await _hangar()

	if "full" in OS.get_cmdline_user_args():
		await _walk_on_to_mission_control()

	MissionState.reset_mission()
	await frames(3)
	check("reset: MissionState back to a fresh run", not MissionState.briefing_completed and not MissionState.landing_site_selected
		and MissionState.landing_site == "" and MissionState.landing_site_data().is_empty()
		and MissionState.mission_phase == MissionState.Phase.BRIEFING and MissionState.current_objective == &"attend_briefing")
	check("reset: HUD objective and landing console follow the reset", game.hud.objective_shown() == "Attend the Mission Briefing"
		and not game.interactions._handlers.has("LandingSystem"))
	check("reset: build cleared, configuration station inactive", not MissionState.rover_configured and MissionState.current_build()
		== {"solar": "", "battery": "", "shield": "", "antenna": "", "instruments": []} and MissionState.mass == null
		and not game.interactions._handlers.has("MissionConfig"))

	print("GAMEPLAY_DONE ", JSON.stringify({"failed": failed, "checks": results.size(), "state": MissionState.snapshot()}))
	get_tree().quit(1 if failed else 0)
