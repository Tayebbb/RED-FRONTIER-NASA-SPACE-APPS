extends Node3D
## Red Frontier - facility viewer. Rooms stream in and out with the camera (FacilityStreamer): only the current
## room and its neighbours on the mission route are resident. Materials and textures come from the shared library.
## Controls: 1-4 Hangar | 5-8 Mission Control | 9 Mars Intelligence | Tab every camera | 0 or hold right mouse = free fly
##           (WASD, Q/E down/up, Shift fast) | L = Launch Mode | F = quality preset | H = help | Esc = quit
## Test modes:  -- shots [hangar|mc|intel|brief|corridors] [launch] [preset high|laptop|integrated]
##              -- traverse [preset ...] [warmup]   walk the mission route, log streaming + performance

const CAMS := ["CAM_Hangar_Entrance", "CAM_Hangar_Wide", "CAM_Hangar_Rover", "CAM_Hangar_Station",
	"CAM_MissionControl_Hero", "CAM_MissionControl_Entry", "CAM_MissionControl_Launch", "CAM_MissionControl_Glass",
	"CAM_MarsIntel_Hero", "CAM_MarsIntel_Entry", "CAM_MarsIntel_Table", "CAM_MarsIntel_Sites",
	"CAM_Briefing_Hero", "CAM_Briefing_Table", "CAM_Briefing_Exit", "CAM_Briefing_Board",
	"CAM_Corridor01", "CAM_Corridor02"]
const CAM_ROOM := {"CAM_Hangar": "Hangar", "CAM_MissionControl": "MissionControl", "CAM_MarsIntel": "MarsIntel",
	"CAM_Briefing": "Briefing", "CAM_Corridor01": "Corridor01", "CAM_Corridor02": "Corridor02"}
const HELP := "RED FRONTIER - FACILITY\n1-4  Hangar   |   5-8  Mission Control   |   9  Mars Intelligence   |   Tab  next camera (all rooms + corridors)\n0 / hold right mouse  free fly (WASD, Q/E, Shift)   |   L  launch mode   |   F  quality preset   |   H  hide help   |   Esc  quit"
const AMBIENT := 0.12
const EXPOSURE := 1.0

var streamer: FacilityStreamer
var fly: Camera3D
var env: Environment
var preset := QualityPresets.LAPTOP
var yaw := 0.0
var pitch := 0.0
var cam_index := 0
var hud: Label

func _ready() -> void:
	streamer = FacilityStreamer.new()
	add_child(streamer)
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.02, 0.022, 0.026)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.62, 0.64, 0.68)
	env.ambient_light_energy = AMBIENT                   # low: bounce comes from VoxelGI (Hangar) or the room probe
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = EXPOSURE
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	fly = Camera3D.new()
	fly.fov = 60.0
	fly.near = 0.05
	add_child(fly)
	var layer := CanvasLayer.new()
	add_child(layer)
	hud = Label.new()
	hud.position = Vector2(16, 12)
	hud.add_theme_color_override("font_color", Color(0.9, 0.93, 0.97))
	hud.add_theme_color_override("font_outline_color", Color(0, 0, 0))
	hud.add_theme_constant_override("outline_size", 4)
	layer.add_child(hud)
	var args := OS.get_cmdline_user_args()
	preset = QualityPresets.default_preset()
	if args.has("preset"):
		preset = ["high", "laptop", "integrated"].find(args[args.find("preset") + 1])
	streamer.room_loaded.connect(func(_r, _ms): QualityPresets.apply_lights(preset, streamer.hero_spots))   # per room: lights only
	QualityPresets.apply(preset, env, get_viewport(), streamer.hero_spots)
	if "traverse" in args:
		_traverse_start()
	else:
		use_camera(1)

func use_camera(i: int) -> void:
	if i == 0:
		var cur := get_viewport().get_camera_3d()
		if cur != null and cur != fly:
			fly.global_transform = cur.global_transform
		var e := fly.global_transform.basis.get_euler()
		pitch = e.x
		yaw = e.y
		fly.current = true
		return
	var cam_name: String = CAMS[i - 1]
	for prefix in CAM_ROOM:
		if cam_name.begins_with(prefix):
			streamer.focus(CAM_ROOM[prefix])                 # load that room and its neighbours first
	var cam := streamer.find_camera(cam_name)
	if cam != null:
		cam.current = true
		cam_index = i

func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and not ev.echo:
		var k: int = ev.keycode
		if k >= KEY_1 and k <= KEY_9:
			use_camera(k - KEY_0)
		elif k >= KEY_KP_1 and k <= KEY_KP_9:
			use_camera(k - KEY_KP_0)
		elif k == KEY_TAB:
			use_camera(cam_index % CAMS.size() + 1)
		match k:
			KEY_0, KEY_KP_0: use_camera(0)
			KEY_L: streamer.apply_launch_mode(not streamer.launch_mode)
			KEY_F:
				preset = (preset + 1) % 3
				QualityPresets.apply(preset, env, get_viewport(), streamer.hero_spots)
			KEY_H: hud.visible = not hud.visible
			KEY_ESCAPE: get_tree().quit()
	elif ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_RIGHT:
		if ev.pressed:
			if not fly.current:
				use_camera(0)
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		else:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	elif ev is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		yaw -= ev.relative.x * 0.003
		pitch = clampf(pitch - ev.relative.y * 0.003, -1.4, 1.4)
		fly.rotation = Vector3(pitch, yaw, 0.0)

## --- screenshot mode -----------------------------------------------------------------------------------
var shot_list: Array = []
var shot_i := -1
var shot_frames := 0

func _shots() -> void:
	var args := OS.get_cmdline_user_args()
	if shot_i < 0:
		shot_i = 0
		var groups := {"hangar": CAMS.slice(0, 4), "mc": CAMS.slice(4, 8), "intel": CAMS.slice(8, 12), "brief": CAMS.slice(12, 16),
			"corridors": CAMS.slice(16, 18)}
		shot_list = CAMS
		for g in groups:
			if g in args:
				shot_list = groups[g]
		hud.visible = false
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
		if "launch" in args:
			streamer.apply_launch_mode(true)
		use_camera(CAMS.find(shot_list[0]) + 1)
	shot_frames += 1
	if shot_frames == 120:
		var out := ProjectSettings.globalize_path("res://").path_join("../renders/godot_gi/") + ("launch/" if streamer.launch_mode else "")
		DirAccess.make_dir_recursive_absolute(out)
		get_viewport().get_texture().get_image().save_png(out + shot_list[shot_i] + ".png")
		print("SHOT %s fps=%d draw_calls=%d vram_mb=%.0f tex_mb=%.0f ram_mb=%.0f resident=%s" % [shot_list[shot_i],
			Engine.get_frames_per_second(), Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
			Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0,
			Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0,
			Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0, ",".join(streamer.loaded.keys())])
		shot_i += 1
		shot_frames = 0
		if shot_i >= shot_list.size():
			get_tree().quit()
		else:
			use_camera(CAMS.find(shot_list[shot_i]) + 1)

## --- traversal test: walk the mission route Briefing -> Mission Control ---------------------------------
const WALK := 1.6                                    # m/s
const EYE := 1.65
var route: Array = []
var seg := 0
var seg_t := 0.0
var t_walk := 0.0
var log_events: Array = []
var frame_ms: Array = []                             # [t, ms]
var stats := {"vram_peak": 0.0, "tex_peak": 0.0, "ram_peak": 0.0, "draw_max": 0, "draw_sum": 0, "frames": 0,
	"resident_max": 0, "missing": 0, "local": 0}
var per_second: Array = []
var sec_frames := 0
var sec_start := 0.0
var finishing := -1.0

func _traverse_start() -> void:
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
	hud.visible = false
	var d = JSON.parse_string(FileAccess.get_file_as_string("res://assets/RF_Route.json"))
	for p in d.route:
		route.append(Vector3(p[0], EYE, p[1]))
	streamer.room_loaded.connect(_on_loaded)
	streamer.room_unloaded.connect(func(r): _event("unload", r, 0.0))
	streamer.focus("Briefing")                       # start-up load, before the clock starts
	fly.global_position = route[0]
	fly.look_at(Vector3(route[1].x, EYE - 0.15, route[1].z), Vector3.UP)
	fly.current = true
	if "warmup" in OS.get_cmdline_user_args():          # opt-in: off by default (see docs/GAME_READINESS.md)
		warm = streamer.warm_up(fly)                     # compile pipelines up front instead of at room transitions
	print("TRAVERSE_START preset=%s gpu=%s" % [QualityPresets.NAMES[preset], RenderingServer.get_video_adapter_name()])

func _on_loaded(room: String, ms: float) -> void:
	var a := streamer.audit(room)
	stats.missing += a.missing
	stats.local += a.local
	_event("load", room, ms, a)

func _event(kind: String, room: String, ms: float, audit := {}) -> void:
	var e := {"t": snappedf(t_walk, 0.01), "event": kind, "room": room, "instance_ms": snappedf(ms, 0.1),
		"resident": streamer.loaded.keys(), "audit": audit}
	log_events.append(e)
	print("TRAVERSE_EVENT ", JSON.stringify(e))

var warm: Node3D = null
var warm_frames := 0

func _traverse(delta: float) -> void:
	if warm != null:                                   # start-up warm-up frames: not part of the timed walk
		warm_frames += 1
		if warm_frames > FacilityStreamer.WARMUP_FRAMES:
			warm.queue_free()
			warm = null
			print("TRAVERSE_WARMUP frames=%d" % warm_frames)
		return
	t_walk += delta
	var ms := delta * 1000.0
	frame_ms.append([t_walk, ms])
	var vram := Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0
	stats.vram_peak = maxf(stats.vram_peak, vram)
	stats.tex_peak = maxf(stats.tex_peak, Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0)
	stats.ram_peak = maxf(stats.ram_peak, OS.get_static_memory_peak_usage() / 1048576.0)
	var dc := int(Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
	stats.draw_max = maxi(stats.draw_max, dc)
	stats.draw_sum += dc
	stats.frames += 1
	stats.resident_max = maxi(stats.resident_max, streamer.loaded.size())
	sec_frames += 1
	if t_walk - sec_start >= 1.0:
		per_second.append({"t": snappedf(t_walk, 0.1), "fps": sec_frames, "room": streamer.current, "draw": dc,
			"vram_mb": snappedf(vram, 1)})
		print("TRAVERSE_SEC t=%.0f room=%s fps=%d draw=%d vram_mb=%.0f resident=%s" % [t_walk, streamer.current, sec_frames, dc, vram,
			",".join(streamer.loaded.keys())])
		sec_frames = 0
		sec_start = t_walk
	if finishing >= 0.0:                                  # dwell at the launch console, then Launch Mode, then stop
		finishing += delta
		if finishing > 2.0 and not streamer.launch_mode:
			streamer.apply_launch_mode(true)
			_event("launch_mode_on", "MissionControl", 0.0)
		if finishing > 4.0:
			_traverse_report()
		streamer.update(fly.global_position)
		return
	var a: Vector3 = route[seg]
	var b: Vector3 = route[seg + 1]
	var L := a.distance_to(b)
	seg_t += WALK * delta
	while seg_t >= L and seg < route.size() - 2:
		seg_t -= L
		seg += 1
		a = route[seg]
		b = route[seg + 1]
		L = a.distance_to(b)
	if seg_t >= L:
		finishing = 0.0
		seg_t = L
	var pos := a.lerp(b, clampf(seg_t / maxf(L, 0.001), 0.0, 1.0))
	var ahead: Vector3 = b if (seg_t / maxf(L, 0.001) < 0.85 or seg >= route.size() - 2) else route[seg + 2]
	fly.global_position = pos
	if Vector2(ahead.x - pos.x, ahead.z - pos.z).length() > 0.05:        # at a corner the target can coincide
		var target := fly.global_transform.looking_at(Vector3(ahead.x, EYE - 0.15, ahead.z), Vector3.UP)
		fly.global_transform.basis = fly.global_transform.basis.slerp(target.basis, clampf(delta * 3.0, 0.0, 1.0)).orthonormalized()
	streamer.update(pos)

func _traverse_report() -> void:
	finishing = 100.0                                    # report once
	var hitches := []
	for e in log_events:
		if e.event in ["load", "unload"]:
			var worst := 0.0
			for f in frame_ms:
				if absf(f[0] - e.t) <= 0.5:
					worst = maxf(worst, f[1])
			hitches.append({"t": e.t, "event": e.event, "room": e.room, "worst_frame_ms": snappedf(worst, 0.1)})
	var fps_vals := per_second.map(func(s): return s.fps)
	var report := {"preset": QualityPresets.NAMES[preset], "gpu": RenderingServer.get_video_adapter_name(),
		"duration_s": snappedf(t_walk, 0.1), "events": log_events, "hitches": hitches, "per_second": per_second,
		"vram_peak_mb": snappedf(stats.vram_peak, 1), "texture_peak_mb": snappedf(stats.tex_peak, 1),
		"ram_peak_mb": snappedf(stats.ram_peak, 1), "draw_calls_max": stats.draw_max,
		"draw_calls_avg": snappedf(float(stats.draw_sum) / maxi(stats.frames, 1), 1),
		"fps_min": fps_vals.min(), "fps_avg": snappedf(fps_vals.reduce(func(x, y): return x + y, 0) / float(maxi(fps_vals.size(), 1)), 0.1),
		"resident_max": stats.resident_max, "missing_materials": stats.missing, "non_shared_materials": stats.local}
	var f := FileAccess.open("res://logs/traversal_report.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(report, "  "))
	f.close()
	print("TRAVERSE_DONE ", JSON.stringify({"vram_peak_mb": report.vram_peak_mb, "ram_peak_mb": report.ram_peak_mb,
		"fps_min": report.fps_min, "fps_avg": report.fps_avg, "draw_max": report.draw_calls_max, "resident_max": report.resident_max,
		"missing": report.missing_materials, "non_shared": report.non_shared_materials,
		"worst_hitch_ms": hitches.map(func(h): return h.worst_frame_ms).max()}))
	get_tree().quit()

func _process(delta: float) -> void:
	var args := OS.get_cmdline_user_args()
	if "traverse" in args:
		if finishing < 99.0:
			_traverse(delta)
		return
	if "shots" in args:
		_shots()
		return
	var cam := get_viewport().get_camera_3d()
	if fly.current:
		var v := Vector3.ZERO
		if Input.is_key_pressed(KEY_W): v.z -= 1.0
		if Input.is_key_pressed(KEY_S): v.z += 1.0
		if Input.is_key_pressed(KEY_A): v.x -= 1.0
		if Input.is_key_pressed(KEY_D): v.x += 1.0
		if Input.is_key_pressed(KEY_E): v.y += 1.0
		if Input.is_key_pressed(KEY_Q): v.y -= 1.0
		if v != Vector3.ZERO:
			fly.translate(v.normalized() * (7.0 if Input.is_key_pressed(KEY_SHIFT) else 2.5) * delta)
	if cam != null:
		streamer.update(cam.global_position)
	hud.text = "%s\n\nview: %s   |   room: %s   |   resident: %s\nlights: %s   |   quality: %s   |   %d fps" % [HELP,
		"free fly" if cam == fly else String(cam.name), streamer.current, ", ".join(streamer.loaded.keys()),
		"LAUNCH MODE" if streamer.launch_mode else "day operational", QualityPresets.NAMES[preset], Engine.get_frames_per_second()]
