extends Node3D
## Mission: Red Frontier - game entry. Streams the facility around the player (FacilityStreamer, unchanged),
## adds walkable collision and the INT_* interactions to each room as it loads, spawns the player on PLAYER_Start
## and runs the mission flow (briefing, landing site, RF-01 build). Systems that do not exist yet (rover configuration,
## Digital Twin, launch) plug in later through interactions.register_handler(<INT id>, ...).
##
## The facility test modes still run the viewer: Godot --path godot -- traverse | shots ... | viewer

const VIEWER_SCENE := "res://viewer/hangar_viewer.tscn"
const LandingSitePanel := preload("res://game/ui/landing_site_panel.gd")
const RoverConfigPanel := preload("res://game/ui/rover_config_panel.gd")
const RoverBuild := preload("res://game/data/rover_build.gd")
const VIEWER_ARGS := ["traverse", "shots", "viewer"]
## Same look as the approved facility viewer (viewer/hangar_viewer.gd).
const AMBIENT := 0.12
const EXPOSURE := 1.0

var streamer: FacilityStreamer
var collision: FacilityCollision
var interactions: InteractionManager
var player: Player
var hud: Hud
var env: Environment
var preset := QualityPresets.LAPTOP
var briefing: BriefingPanel = null
var landing_panel: CanvasLayer = null
var config_panel: CanvasLayer = null

func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	for a in VIEWER_ARGS:
		if a in args:
			get_tree().change_scene_to_file.call_deferred(VIEWER_SCENE)
			return
	_build_environment()
	streamer = FacilityStreamer.new()
	streamer.name = "Facility"
	add_child(streamer)
	collision = FacilityCollision.new()
	add_child(collision)
	collision.bind_streamer(streamer)
	interactions = InteractionManager.new()
	add_child(interactions)
	interactions.bind_streamer(streamer)
	preset = QualityPresets.default_preset()
	if args.has("preset"):
		preset = ["high", "laptop", "integrated"].find(args[args.find("preset") + 1])
	streamer.room_loaded.connect(func(_r, _ms): QualityPresets.apply_lights(preset, streamer.hero_spots))
	QualityPresets.apply(preset, env, get_viewport(), streamer.hero_spots)

	streamer.focus(GameConfig.PLAYER_START_ROOM)          # start room + neighbour loaded before the first frame
	collision.add_room(GameConfig.PLAYER_START_ROOM, streamer.loaded.get(GameConfig.PLAYER_START_ROOM), true)   # spawn room now
	_add_safety_floor()

	player = preload("res://game/player/player.tscn").instantiate()
	add_child(player)
	player.place(_player_start())
	player.position_allowed = _inside_facility

	hud = Hud.new()
	add_child(hud)
	player.interactor.focus_changed.connect(hud.show_prompt)

	interactions.register_handler("BriefingTable", func(_ia, _who): open_briefing())
	MissionState.state_changed.connect(func(_k, _v): _sync_interactions())
	MissionState.mission_reset.connect(_sync_interactions)
	_sync_interactions()

	if "gameplay_test" in args:
		add_child(load("res://tests/gameplay_smoke.gd").new())

func _build_environment() -> void:
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.02, 0.022, 0.026)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.62, 0.64, 0.68)
	env.ambient_light_energy = AMBIENT
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = EXPOSURE
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

func _player_start() -> Transform3D:
	var room: Node3D = streamer.loaded.get(GameConfig.PLAYER_START_ROOM)
	var marker: Node3D = room.find_child(GameConfig.PLAYER_START_MARKER, true, false) if room != null else null
	if marker == null:
		push_warning("PLAYER_Start marker not found, using the fallback position")
		return Transform3D(Basis(), GameConfig.PLAYER_START_FALLBACK)
	return marker.global_transform.orthonormalized()

## Where the player (and camera) may be: inside a room footprint (padded so doorways between rooms connect) whose
## room has finished streaming in, collision included. On slow machines the player waits a moment at the Hangar
## door instead of walking into a room with no walls or floor yet.
func _inside_facility(p: Vector3) -> bool:
	var pad := GameConfig.FOOTPRINT_PAD
	for room in streamer.manifests:
		var f: Dictionary = streamer.manifests[room].footprint
		var inside: bool = p.x >= f.x[0] - pad and p.x <= f.x[1] + pad and p.z >= f.z[0] - pad and p.z <= f.z[1] + pad
		if inside and collision.is_ready(room):
			return true
	return false

## Every facility floor is at y = 0: an infinite plane there means no gap in a floor mesh can drop the player.
func _add_safety_floor() -> void:
	var body := StaticBody3D.new()
	body.name = "SafetyFloor"
	body.collision_layer = GameConfig.LAYER_WORLD
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	cs.shape = WorldBoundaryShape3D.new()
	body.add_child(cs)
	add_child(body)

func _process(_delta: float) -> void:
	if player == null:
		return
	streamer.update(player.global_position)
	hud.set_debug("room %s  ·  resident %s  ·  collision queue %d  ·  %d fps\n%s" % [streamer.current,
		", ".join(streamer.loaded.keys()), collision.pending(), Engine.get_frames_per_second(), QualityPresets.NAMES[preset]])

## --- Mission flow ----------------------------------------------------------------------------------------

func open_briefing() -> void:
	if briefing != null:
		return
	player.controls_enabled = false
	briefing = BriefingPanel.new()
	briefing.continued.connect(_on_briefing_continued)
	add_child(briefing)

func _on_briefing_continued() -> void:
	briefing = null
	if not MissionState.briefing_completed:
		MissionState.complete_briefing()
		MissionState.set_objective(&"proceed_mars_intel")
	player.controls_enabled = true

## Stage interactions that depend on mission progress: each is live only while it is the current step.
func _sync_interactions() -> void:
	if MissionState.briefing_completed and not MissionState.landing_site_selected:
		interactions.register_handler("LandingSystem", func(_ia, _who): open_landing_analysis())
	else:
		interactions.unregister_handler("LandingSystem")
	if MissionState.landing_site_selected and not MissionState.launch_confirmed:   # editable until launch
		interactions.register_handler("MissionConfig", func(_ia, _who): open_rover_config())
	else:
		interactions.unregister_handler("MissionConfig")

func open_landing_analysis() -> void:
	if landing_panel != null:
		return
	player.controls_enabled = false
	landing_panel = LandingSitePanel.new()
	landing_panel.confirmed.connect(_on_landing_site_confirmed)
	landing_panel.closed.connect(_on_landing_panel_closed)
	add_child(landing_panel)

func _on_landing_site_confirmed(site_id: String) -> void:
	if MissionState.select_landing_site(site_id):
		MissionState.set_objective(&"proceed_engineering_hangar")

func _on_landing_panel_closed(_locked: bool) -> void:
	landing_panel = null
	player.controls_enabled = true

## Engineering Hangar: RF-01 configuration, opened on the saved build (or an empty one the first time).
func open_rover_config() -> void:
	if config_panel != null:
		return
	player.controls_enabled = false
	config_panel = RoverConfigPanel.new()
	var start: Dictionary = MissionState.current_build() if MissionState.rover_configured else RoverBuild.empty_build()
	config_panel.setup(start, MissionState.landing_site_data())
	config_panel.accept_requested.connect(_on_build_accept_requested)
	config_panel.closed.connect(_on_config_panel_closed)
	add_child(config_panel)

func _on_build_accept_requested(build: Dictionary) -> void:
	if not MissionState.accept_build(build):
		return
	if not MissionState.twin_is_current():
		MissionState.set_objective(&"run_digital_twin")
	config_panel.show_saved()

func _on_config_panel_closed(_saved: bool) -> void:
	config_panel = null
	player.controls_enabled = true
