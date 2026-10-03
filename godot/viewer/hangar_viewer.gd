extends Node3D
## Red Frontier - Hangar viewer. Loads the exported Hangar, the rover and the light rig
## (rebuilt from RF_Hangar_lights.json because glTF cannot carry area lights).
## Controls: 1-4 approved cameras | 0 or hold right mouse = free fly (WASD, Q/E down/up, Shift fast)
##           F = toggle high quality (reflections + all shadows) | Esc = quit

const ASSETS := "res://assets/"
const CAMS := ["CAM_Hangar_Entrance", "CAM_Hangar_Wide", "CAM_Hangar_Rover", "CAM_Hangar_Station"]
const HELP := "RED FRONTIER - ENGINEERING HANGAR\n1-4  cameras   |   0 / hold right mouse  free fly (WASD, Q/E, Shift)\nF  quality   |   H  hide help   |   Esc  quit"

var hangar: Node3D
var fly: Camera3D
var env: Environment
var hero_spots: Array[SpotLight3D] = []
var high_quality := false
var yaw := 0.0
var pitch := 0.0
var hud: Label

func _ready() -> void:
	hangar = load(ASSETS + "RF_Hangar.glb").instantiate()
	add_child(hangar)
	var man = JSON.parse_string(FileAccess.get_file_as_string(ASSETS + "RF_Hangar_lights.json"))
	if man.rover != null and ResourceLoader.exists(ASSETS + man.rover.asset):
		var rv: Node3D = load(ASSETS + man.rover.asset).instantiate()
		add_child(rv)
		rv.position = Vector3(man.rover.pos[0], man.rover.pos[1], man.rover.pos[2])
		rv.rotation_degrees.y = man.rover.rot_y_deg
	for L in man.lights:
		var sl := SpotLight3D.new()
		add_child(sl)
		var pos := Vector3(L.pos[0], L.pos[1], L.pos[2])
		var dir := Vector3(L.dir[0], L.dir[1], L.dir[2]).normalized()
		var up := Vector3.FORWARD if absf(dir.y) > 0.9 else Vector3.UP
		sl.look_at_from_position(pos, pos + dir, up)
		sl.light_color = Color(L.color[0], L.color[1], L.color[2])
		var hero: bool = String(L.name).begins_with("LGT_Hero")
		sl.light_energy = L.watts / (180.0 if hero else 150.0)
		sl.spot_range = 22.0
		sl.spot_angle = 38.0 if hero else 72.0
		sl.light_size = 0.6 if hero else 1.2                       # soft shadows sized like the real fixtures
		sl.shadow_enabled = String(L.name) == "LGT_Hero_Key"     # one shadow by default: laptop-friendly
		if hero:
			hero_spots.append(sl)
	env = Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.02, 0.022, 0.026)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.62, 0.64, 0.68)
	env.ambient_light_energy = AMBIENT                   # low: bounce light comes from VoxelGI, not a flat fill
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = EXPOSURE
	env.ssao_enabled = true
	env.ssr_enabled = false
	env.glow_enabled = true
	env.glow_intensity = 0.2
	_setup_gi()
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
	use_camera(1)

## --- look settings (tuned against the Cycles reference renders) -------------------
const AMBIENT := 0.12
const EXPOSURE := 1.0
const GI_ENERGY := 1.6
const HALL_CENTRE := Vector3(0.0, 5.0, -44.0)        # Hangar interior centre in Godot coordinates
const HALL_SIZE := Vector3(19.0, 10.8, 23.0)
const GI_CACHE := "res://assets/hangar_voxelgi.res"

func _setup_gi() -> void:
	# Real bounced light: voxelise the Hangar once, cache it, reuse it on every launch.
	var gi := VoxelGI.new()
	gi.position = HALL_CENTRE
	gi.size = HALL_SIZE
	gi.subdiv = VoxelGI.SUBDIV_256
	add_child(gi)
	if ResourceLoader.exists(GI_CACHE) and not "rebake" in OS.get_cmdline_user_args():
		gi.data = load(GI_CACHE)
	else:
		var t := Time.get_ticks_msec()
		gi.bake(self)
		gi.data.energy = GI_ENERGY
		gi.data.propagation = 0.7
		gi.data.interior = true
		ResourceSaver.save(gi.data, GI_CACHE)
		print("VOXELGI_BAKED ms=", Time.get_ticks_msec() - t)
	gi.data.energy = GI_ENERGY
	# Static reflections of the room in the epoxy floor and screens (cheap, unlike SSR).
	var probe := ReflectionProbe.new()
	probe.position = HALL_CENTRE
	probe.size = HALL_SIZE
	probe.box_projection = true
	probe.interior = true
	probe.update_mode = ReflectionProbe.UPDATE_ONCE
	add_child(probe)

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
	var cam: Camera3D = hangar.find_child(CAMS[i - 1], true, false)
	if cam != null:
		cam.current = true

func set_quality(high: bool) -> void:
	high_quality = high
	env.ssr_enabled = high
	for s in hero_spots:
		s.shadow_enabled = high or s.name == "LGT_Hero_Key"

func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and not ev.echo:
		match ev.keycode:
			KEY_1, KEY_KP_1: use_camera(1)
			KEY_2, KEY_KP_2: use_camera(2)
			KEY_3, KEY_KP_3: use_camera(3)
			KEY_4, KEY_KP_4: use_camera(4)
			KEY_0, KEY_KP_0: use_camera(0)
			KEY_F: set_quality(not high_quality)
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

## --- screenshot mode: `-- shots` captures the four cameras for comparison with Cycles, then quits
var shot_i := -1
var shot_frames := 0

func _shots(delta: float) -> void:
	if shot_i < 0:
		shot_i = 0
		hud.visible = false
		DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
		use_camera(1)
	shot_frames += 1
	if shot_frames == 120:
		var out := "D:/RedFrontier/renders/godot_gi/"
		DirAccess.make_dir_recursive_absolute(out)
		get_viewport().get_texture().get_image().save_png(out + CAMS[shot_i] + ".png")
		print("SHOT %s fps=%d" % [CAMS[shot_i], Engine.get_frames_per_second()])
		shot_i += 1
		shot_frames = 0
		if shot_i >= CAMS.size():
			get_tree().quit()
		else:
			use_camera(shot_i + 1)

func _process(delta: float) -> void:
	if "shots" in OS.get_cmdline_user_args():
		_shots(delta)
		return
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
	var cam := get_viewport().get_camera_3d()
	hud.text = "%s\n\nview: %s   |   quality: %s   |   %d fps" % [HELP, "free fly" if cam == fly else String(cam.name),
		"high" if high_quality else "laptop", Engine.get_frames_per_second()]
