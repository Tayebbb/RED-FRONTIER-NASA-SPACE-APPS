extends SceneTree
## Windowed render + performance check. Rebuilds lights from RF_Hangar_lights.json (area lights
## cannot travel through glTF), places the rover, screenshots each approved camera, logs perf.
## Run: Godot --path D:/RedFrontier/godot --script res://tests/render_hangar.gd

var OUT := "D:/RedFrontier/renders/godot/" + ("lite/" if "lite" in OS.get_cmdline_user_args() else "")
const SHOTS := ["CAM_Hangar_Entrance", "CAM_Hangar_Wide", "CAM_Hangar_Rover", "CAM_Hangar_Station"]
var hangar: Node3D
var shot := 0
var frames := 0
var fps_samples := []

func _initialize() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	get_root().size = Vector2i(1600, 900)
	DirAccess.make_dir_recursive_absolute(OUT)
	hangar = load("res://assets/RF_Hangar.glb").instantiate()
	get_root().add_child(hangar)
	var man = JSON.parse_string(FileAccess.get_file_as_string("res://assets/RF_Hangar_lights.json"))
	if man.rover != null and ResourceLoader.exists("res://assets/" + man.rover.asset):
		var rv: Node3D = load("res://assets/" + man.rover.asset).instantiate()
		get_root().add_child(rv)
		rv.position = Vector3(man.rover.pos[0], man.rover.pos[1], man.rover.pos[2])
		rv.rotation_degrees.y = man.rover.rot_y_deg
	for L in man.lights:
		var sl := SpotLight3D.new()
		get_root().add_child(sl)
		var pos := Vector3(L.pos[0], L.pos[1], L.pos[2])
		var dir := Vector3(L.dir[0], L.dir[1], L.dir[2]).normalized()
		var up := Vector3.FORWARD if absf(dir.y) > 0.9 else Vector3.UP
		sl.look_at_from_position(pos, pos + dir, up)
		sl.light_color = Color(L.color[0], L.color[1], L.color[2])
		var hero: bool = String(L.name).begins_with("LGT_Hero")
		sl.light_energy = L.watts / (180.0 if hero else 150.0)
		sl.spot_range = 22.0
		sl.spot_angle = 38.0 if hero else 72.0
		sl.light_size = 0.5
		sl.shadow_enabled = hero
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.02, 0.022, 0.026)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.62, 0.64, 0.68)
	env.ambient_light_energy = 0.55
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	var lite := "lite" in OS.get_cmdline_user_args()          # A/B: same geometry, no SSR / SSAO / shadows
	env.ssao_enabled = not lite
	env.ssr_enabled = not lite
	if lite:
		for n in get_root().get_children():
			if n is SpotLight3D:
				n.shadow_enabled = false
	env.glow_enabled = true
	env.glow_intensity = 0.35
	var we := WorldEnvironment.new()
	we.environment = env
	get_root().add_child(we)
	_use_camera(SHOTS[0])

func _use_camera(name: String) -> void:
	var cam: Camera3D = hangar.find_child(name, true, false)
	if cam == null:
		print("RENDER_WARN camera missing: ", name)
		return
	cam.current = true

func _process(_delta: float) -> bool:
	frames += 1
	if frames > 60:
		fps_samples.append(Performance.get_monitor(Performance.TIME_FPS))
	if frames == 150:
		var img := get_root().get_texture().get_image()
		img.save_png(OUT + SHOTS[shot] + ".png")
		var avg := 0.0
		for f in fps_samples:
			avg += f
		avg /= max(1, fps_samples.size())
		print("RENDER %s fps=%.1f draw_calls=%d primitives=%d objects=%d vram_mb=%.0f" % [SHOTS[shot], avg,
			Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0])
		print("RENDER_GPU ", RenderingServer.get_video_adapter_name(), " | ", RenderingServer.get_video_adapter_api_version())
		shot += 1
		frames = 0
		fps_samples.clear()
		if shot >= SHOTS.size():
			quit(0)
			return true
		_use_camera(SHOTS[shot])
	return false
