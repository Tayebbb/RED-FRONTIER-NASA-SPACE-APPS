extends SceneTree
## Stress test for runtime room streaming: walks the room chain back and forth (staged loads/unloads, as at
## runtime) for N cycles and reports. Diagnostic: `-- nosmallgi` disables the small rooms' VoxelGI volumes.
## Run windowed: Godot --path godot --script res://tools/stream_stress.gd -- [cycles N] [nosmallgi]
const ORDER := ["Briefing", "Corridor01", "MarsIntel", "Corridor02", "Hangar", "MissionControl"]
var s: FacilityStreamer
var cam: Camera3D
var idx := 0
var dir := 1
var frames := 0
var steps := 0
var max_steps := 60
func _initialize() -> void:
	get_root().size = Vector2i(1600, 900)
	var env := Environment.new(); env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.tonemap_mode = Environment.TONE_MAPPER_AGX
	var we := WorldEnvironment.new(); we.environment = env; get_root().add_child(we)
	s = FacilityStreamer.new(); get_root().add_child(s)
	cam = Camera3D.new(); get_root().add_child(cam); cam.current = true
	var a := OS.get_cmdline_user_args()
	if a.has("cycles"): max_steps = int(a[a.find("cycles") + 1])
	if "nosmallgi" in a: s.gi_override = {"Briefing": "probe", "MarsIntel": "probe", "MissionControl": "probe"}
	print("STRESS start steps=%d nosmallgi=%s" % [max_steps, "nosmallgi" in a])
func _process(_d: float) -> bool:
	frames += 1
	if frames == 3:
		s.focus(ORDER[0])
	if frames < 5: return false
	s.update(cam.global_position)
	if frames % 40 == 0:                                         # every 40 frames: move to the next room centre
		idx += dir
		if idx == ORDER.size() - 1 or idx == 0: dir = -dir
		var f: Dictionary = s.manifests[ORDER[idx]].footprint
		cam.global_position = Vector3((f.x[0] + f.x[1]) / 2.0, 1.65, (f.z[0] + f.z[1]) / 2.0)
		steps += 1
		print("STRESS step=%d room=%s resident=%s vram=%.0f" % [steps, ORDER[idx], ",".join(s.loaded.keys()), Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0])
		if steps >= max_steps:
			print("STRESS_DONE steps=%d" % steps)
			return true
	return false
