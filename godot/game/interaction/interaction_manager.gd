class_name InteractionManager
extends Node
## Turns the INT_* markers exported from Blender into Interactables whenever their room streams in, and routes
## each use to the gameplay system registered for that id. Rooms free their Interactables when they unload.
##
##   interactions.register_handler("BriefingTable", func(_ia, _who): open_briefing())
##
## A marker without a handler stays silent (no prompt), so future stations cost nothing until they exist.

signal interaction_triggered(id: String, interactable: Interactable)

const MARKER_PREFIX := "INT_"

var _handlers := {}                   # id -> Callable(interactable, interactor)
var _live := {}                       # id -> Interactable currently in the scene

func bind_streamer(streamer: FacilityStreamer) -> void:
	streamer.room_loaded.connect(func(room, _ms): bind_room(streamer.loaded.get(room)))
	for room in streamer.loaded:
		bind_room(streamer.loaded[room])

func register_handler(id: String, handler: Callable) -> void:
	_handlers[id] = handler
	_refresh(id)

func unregister_handler(id: String) -> void:
	_handlers.erase(id)
	_refresh(id)

func get_interactable(id: String) -> Interactable:
	var ia = _live.get(id)                              # untyped: the room may have streamed out and freed it
	if not is_instance_valid(ia):
		_live.erase(id)
		return null
	return ia

## Attach an Interactable to every INT_* marker under a freshly loaded room.
func bind_room(room_root: Node) -> void:
	if room_root == null:
		return
	for marker in room_root.find_children(MARKER_PREFIX + "*", "Node3D", true, false):
		if marker.has_node("Interactable"):
			continue
		var id := String(marker.name).trim_prefix(MARKER_PREFIX)
		var cfg: Dictionary = GameConfig.INTERACTIONS.get(id, {})
		var ia := Interactable.new()
		ia.name = "Interactable"
		ia.interaction_id = id
		ia.label = cfg.get("label", id.capitalize())
		ia.prompt = cfg.get("prompt", ia.prompt)
		ia.radius = cfg.get("radius", GameConfig.INTERACT_RADIUS)
		ia.enabled = _handlers.has(id)
		ia.interacted.connect(_on_interacted)
		marker.add_child(ia)
		_live[id] = ia

func _refresh(id: String) -> void:
	var ia := get_interactable(id)
	if ia != null:
		ia.enabled = _handlers.has(id)

func _on_interacted(ia: Interactable, interactor: Node) -> void:
	interaction_triggered.emit(ia.interaction_id, ia)
	var h: Callable = _handlers.get(ia.interaction_id, Callable())
	if h.is_valid():
		h.call(ia, interactor)
