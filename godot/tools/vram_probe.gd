extends SceneTree
## Measures GPU memory step by step: empty frame -> environment -> rooms -> Hangar GI.
## Run windowed: Godot --path godot --script res://tools/vram_probe.gd

var step := 0
var frames := 0
var streamer: FacilityStreamer
var env: Environment
var cam: Camera3D

func mb(m: int) -> float:
	return Performance.get_monitor(m) / 1048576.0

func _initialize() -> void:
	get_root().size = Vector2i(1600, 900)
	cam = Camera3D.new(); get_root().add_child(cam); cam.position = Vector3(0, 1.6, -3); cam.current = true

func _process(_d: float) -> bool:
	frames += 1
	if frames < 30:
		return false
	frames = 0
	print("VRAM_STEP %d video=%.0f texture=%.0f buffer=%.0f" % [step, mb(Performance.RENDER_VIDEO_MEM_USED), mb(Performance.RENDER_TEXTURE_MEM_USED), mb(Performance.RENDER_BUFFER_MEM_USED)])
	step += 1
	match step:
		1:
			env = Environment.new(); env.ssao_enabled = true; env.glow_enabled = true; env.tonemap_mode = Environment.TONE_MAPPER_AGX
			var we := WorldEnvironment.new(); we.environment = env; get_root().add_child(we)
			print("  -> + environment (SSAO, glow)")
		2:
			streamer = FacilityStreamer.new(); get_root().add_child(streamer)
			streamer.GI_POLICY  # touch
			streamer.focus("Briefing")
			print("  -> + Briefing, Corridor01 (probe lighting)")
		3:
			streamer.focus("MarsIntel")
			print("  -> + MarsIntel neighbourhood")
		4:
			streamer.focus("MissionControl")
			print("  -> MissionControl + Hangar (VoxelGI 256)")
		5:
			for gi in streamer.find_children("*", "VoxelGI", true, false): gi.queue_free()
			print("  -> Hangar VoxelGI removed (measurement only)")
		6:
			for p in streamer.find_children("*", "ReflectionProbe", true, false): p.queue_free()
			print("  -> reflection probes removed (measurement only)")
		7:
			return true
	return false
