extends Node3D

var streamer: FacilityStreamer
var registry: InteractionRegistry
var player: FacilityPlayer
var prompt: Label
var status: Label

func _ready() -> void:
	streamer = FacilityStreamer.new()
	streamer.name = "FacilityStreamer"
	add_child(streamer)
	registry = InteractionRegistry.new()
	registry.name = "InteractionRegistry"
	add_child(registry)
	streamer.room_loaded.connect(_on_room_loaded)
	streamer.room_unloaded.connect(_on_room_unloaded)
	registry.target_changed.connect(_on_target_changed)
	registry.interaction_requested.connect(_on_interaction_requested)
	player = $Player
	_build_hud()
	streamer.focus("Briefing")
	await get_tree().process_frame
	var start := _find_marker("PLAYER_Start")
	if start != null:
		player.global_position = start.global_position
	else:
		player.global_position = Vector3(0, 0.05, -0.3)

func _physics_process(_delta: float) -> void:
	if player == null:
		return
	streamer.update(player.global_position)
	registry.update_focus(player.camera.global_position, -player.camera.global_transform.basis.z)
	status.text = "ROOM: %s\n%s" % [streamer.current, MissionStateAutoload.state.summary()]
	if Input.is_action_just_pressed("interact"):
		registry.request_interaction()

func _on_room_loaded(room: String, _ms: float) -> void:
	if streamer.loaded.has(room):
		var root: Node3D = streamer.loaded[room]
		registry.register_room(root)
		_add_floor_collision(root, room)

func _on_room_unloaded(room: String) -> void:
	if streamer.loaded.has(room):
		registry.unregister_room(streamer.loaded[room])

func _on_target_changed(target: Node3D, interaction_type: String) -> void:
	prompt.text = "[E] %s" % interaction_type if target != null else ""

func _on_interaction_requested(interaction_type: String, _target: Node3D) -> void:
	var state: MissionState = MissionStateAutoload.state
	match interaction_type:
		"POWER", "SCIENCE", "MOBILITY", "COMMS":
			var options := {"POWER": "SOLAR" if state.power_system == "RTG" else "RTG",
				"SCIENCE": "SPECTROMETER" if state.science_payload == "CAMERA" else "CAMERA",
				"MOBILITY": "AUTONOMOUS" if state.mobility_system == "ROCKER_BOGIE" else "ROCKER_BOGIE",
				"COMMS": "LOW_GAIN" if state.communications_system == "HIGH_GAIN" else "HIGH_GAIN"}
			state.set_station_selection(interaction_type, options[interaction_type])
		"MissionConfig":
			if state.selected_site.is_empty():
				state.select_site("Jezero")
			elif not state.is_configuration_locked:
				state.lock_configuration()
		"DigitalTwin":
			state.run_digital_twin()
		"LANDING_SITE":
			state.select_site("Jezero")
	status.text = "ROOM: %s\n%s" % [streamer.current, state.summary()]

func _find_marker(marker_name: String) -> Node3D:
	for root in streamer.loaded.values():
		var marker: Node = root.find_child(marker_name, true, false)
		if marker != null:
			return marker as Node3D
	return null

func _build_hud() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	prompt = Label.new()
	prompt.position = Vector2(700, 780)
	prompt.add_theme_font_size_override("font_size", 24)
	layer.add_child(prompt)
	status = Label.new()
	status.position = Vector2(18, 18)
	status.add_theme_color_override("font_color", Color(0.9, 0.93, 0.97))
	status.add_theme_color_override("font_outline_color", Color.BLACK)
	status.add_theme_constant_override("outline_size", 4)
	layer.add_child(status)

func _add_floor_collision(root: Node3D, room: String) -> void:
	if root.has_node("GameplayFloorCollision") or not streamer.manifests.has(room):
		return
	var footprint: Dictionary = streamer.manifests[room].footprint
	var floor_body := StaticBody3D.new()
	floor_body.name = "GameplayFloorCollision"
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(footprint.x[1] - footprint.x[0], 0.2, footprint.z[1] - footprint.z[0])
	shape.shape = box
	floor_body.position = Vector3((footprint.x[0] + footprint.x[1]) * 0.5, -0.1, (footprint.z[0] + footprint.z[1]) * 0.5)
	floor_body.add_child(shape)
	root.add_child(floor_body)
	_add_wall_collisions(root)

func _add_wall_collisions(root: Node3D) -> void:
	var wall_index := 0
	for mesh_instance in root.find_children("*_Wall*", "MeshInstance3D", true, false):
		if "Glass" in String(mesh_instance.name) or mesh_instance.mesh == null:
			continue
		var wall_body := StaticBody3D.new()
		wall_body.name = "GameplayWallCollision_%02d" % wall_index
		wall_body.global_transform = mesh_instance.global_transform
		var wall_shape := CollisionShape3D.new()
		var wall_box := BoxShape3D.new()
		wall_box.size = mesh_instance.mesh.get_aabb().size
		wall_shape.position = mesh_instance.mesh.get_aabb().get_center()
		wall_shape.shape = wall_box
		wall_body.add_child(wall_shape)
		root.add_child(wall_body)
		wall_index += 1
