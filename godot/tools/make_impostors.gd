extends SceneTree
## Captures the door impostors: what you see through a room's entrance door from the room before it, with the real
## room resident. FacilityStreamer shows the image at that door only while the room itself is not resident.
## Captured with a linear tonemap and no glow; shown unshaded, so the viewer's AgX tonemap is applied once.
## Run windowed: Godot --path godot --script res://tools/make_impostors.gd

var s: FacilityStreamer
var env: Environment
var cam: Camera3D
var todo: Array = []
var frames := 0

func _initialize() -> void:
	get_root().size = Vector2i(1920, 1080)
	env = Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = Color(0.02, 0.022, 0.026)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(0.62, 0.64, 0.68)
	env.ambient_light_energy = 0.12; env.tonemap_mode = Environment.TONE_MAPPER_LINEAR; env.ssao_enabled = true
	var we := WorldEnvironment.new(); we.environment = env; get_root().add_child(we)
	s = FacilityStreamer.new(); get_root().add_child(s)
	s.impostors_enabled = false
	cam = Camera3D.new(); get_root().add_child(cam)
	todo = FacilityStreamer.IMPOSTORS.keys()

func _process(_d: float) -> bool:
	frames += 1
	if todo.is_empty():
		return true
	var room: String = todo[0]
	var d: Dictionary = FacilityStreamer.IMPOSTORS[room]
	if frames == 1:
		s.focus(d.focus)
		cam.global_position = d.eye
		cam.look_at(d.centre, Vector3.UP)
		cam.fov = 36.0
		cam.current = true
	if frames < 90:
		return false
	var c: Vector3 = d.centre
	var hw: float = d.size.x / 2.0
	var hh: float = d.size.y / 2.0
	var tl := cam.unproject_position(c + Vector3(-hw, hh, 0)); var br := cam.unproject_position(c + Vector3(hw, -hh, 0))
	var img := get_root().get_texture().get_image()
	var rect := Rect2i(Vector2i(tl), Vector2i(br - tl))
	var crop := img.get_region(rect)
	var path := "res://assets/RF_Impostor_%s.png" % room
	crop.save_png(ProjectSettings.globalize_path(path))
	print("IMPOSTOR %s %s px=%s" % [room, path, crop.get_size()])
	todo.pop_front()
	frames = 0
	return false
