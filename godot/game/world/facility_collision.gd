class_name FacilityCollision
extends Node
## Walkable collision for the streamed facility. The room GLBs carry render geometry only, so when a room finishes
## loading its meshes get trimesh collision, a few per frame (the Hangar's ~150 ms of shape building would
## otherwise land in one frame). Bodies are parented under the meshes, so they unload with the room.
## The rover (200k triangles) gets one box from its bounds instead.
## A room is_ready() once all of its collision exists; the game keeps the player out of rooms that are not.

const FRAME_BUDGET_MS := 3.0
## Not worth colliding with: flat decals, screen planes on their props, overhead light fixtures. Ceilings stay:
## they keep the camera inside the room.
const SKIP_PREFIXES := ["DEC_", "UI_"]
const SKIP_CONTAINS := ["LinearLight"]
const ROVER_SCENE := "res://assets/RF01_Rover.glb"

var _queue: Array = []                # [room, MeshInstance3D]; floors at the back, so they are built first
var _pending := {}                    # room -> meshes still to build
var _ready := {}                      # room -> true

func bind_streamer(streamer: FacilityStreamer) -> void:
	streamer.room_loaded.connect(func(room, _ms): add_room(room, streamer.loaded.get(room)))
	streamer.room_unloaded.connect(_forget)
	for room in streamer.loaded:
		add_room(room, streamer.loaded[room])

func is_ready(room: String) -> bool:
	return _ready.has(room)

func pending() -> int:
	return _queue.size()

## Queue a loaded room. build_now = true does it all this frame (start-up, before the player can move).
func add_room(room: String, room_root: Node3D, build_now := false) -> void:
	if room_root == null:
		return
	for rover in room_root.get_children():
		if rover is Node3D and rover.scene_file_path == ROVER_SCENE and not rover.has_node("RoverCollision"):
			_add_rover_box(rover)
	var floors: Array = []
	for mi in room_root.find_children("*", "MeshInstance3D", true, false):
		if _wanted(mi):
			(floors if "Floor" in String(mi.name) else _queue).append([room, mi])
			_pending[room] = _pending.get(room, 0) + 1
	_queue.append_array(floors)
	if _pending.get(room, 0) == 0:
		_ready[room] = true
	if build_now:
		while not _queue.is_empty():
			_build(_queue.pop_back())

func _forget(room: String) -> void:
	_ready.erase(room)
	_pending.erase(room)
	_queue = _queue.filter(func(item): return item[0] != room)

func _process(_delta: float) -> void:
	var t0 := Time.get_ticks_usec()
	while not _queue.is_empty() and (Time.get_ticks_usec() - t0) < FRAME_BUDGET_MS * 1000.0:
		_build(_queue.pop_back())

func _wanted(mi: MeshInstance3D) -> bool:
	var n := String(mi.name)
	for p in SKIP_PREFIXES:
		if n.begins_with(p):
			return false
	for s in SKIP_CONTAINS:
		if s in n:
			return false
	var p := mi.get_parent()
	while p != null:                                   # skip the rover's own meshes
		if p is Node3D and p.scene_file_path == ROVER_SCENE:
			return false
		p = p.get_parent()
	return mi.mesh != null and not mi.has_node("Collision")

func _build(item: Array) -> void:
	var room: String = item[0]
	var mi: MeshInstance3D = item[1]
	if is_instance_valid(mi) and mi.is_inside_tree() and not mi.has_node("Collision"):
		var shape := mi.mesh.create_trimesh_shape()
		if shape != null:
			var body := StaticBody3D.new()
			body.name = "Collision"
			body.collision_layer = GameConfig.LAYER_WORLD
			body.collision_mask = 0
			var cs := CollisionShape3D.new()
			cs.shape = shape
			body.add_child(cs)
			mi.add_child(body)
	if _pending.has(room):
		_pending[room] -= 1
		if _pending[room] <= 0:
			_ready[room] = true

func _add_rover_box(rover: Node3D) -> void:
	var inv := rover.global_transform.affine_inverse()
	var box := AABB()
	var first := true
	for mi in rover.find_children("*", "MeshInstance3D", true, false):
		var b: AABB = (inv * mi.global_transform) * mi.get_aabb()
		box = b if first else box.merge(b)
		first = false
	if first:
		return
	var body := StaticBody3D.new()
	body.name = "RoverCollision"
	body.collision_layer = GameConfig.LAYER_WORLD
	body.collision_mask = 0
	var shape := BoxShape3D.new()
	shape.size = box.size
	var cs := CollisionShape3D.new()
	cs.shape = shape
	cs.position = box.get_center()
	body.add_child(cs)
	rover.add_child(body)
