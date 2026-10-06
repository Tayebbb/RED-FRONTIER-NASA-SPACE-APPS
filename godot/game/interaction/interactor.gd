class_name Interactor
extends Area3D
## Lives on the player. Tracks the Interactables in reach, picks the nearest usable one, and uses it on E.

signal focus_changed(target: Interactable)

var active := true                    # false while a UI panel owns input
var focused: Interactable = null
var _in_reach: Array[Interactable] = []

func _ready() -> void:
	collision_layer = 0
	collision_mask = GameConfig.LAYER_INTERACTABLE
	monitorable = false
	var shape := SphereShape3D.new()
	shape.radius = 0.3
	var cs := CollisionShape3D.new()
	cs.shape = shape
	cs.position.y = 0.9
	add_child(cs)
	area_entered.connect(func(a): if a is Interactable and not a in _in_reach: _in_reach.append(a))
	area_exited.connect(func(a): _in_reach.erase(a))

func _physics_process(_delta: float) -> void:
	_in_reach = _in_reach.filter(func(a): return is_instance_valid(a))     # rooms stream out under us
	var best: Interactable = null
	if active:
		var best_d := INF
		for a in _in_reach:
			if not a.can_interact():
				continue
			var d := global_position.distance_squared_to(a.global_position)
			if d < best_d:
				best_d = d
				best = a
	if best != focused:
		focused = best
		focus_changed.emit(focused)

func _unhandled_input(ev: InputEvent) -> void:
	if active and focused != null and ev.is_action_pressed("interact"):
		get_viewport().set_input_as_handled()
		focused.interact(get_parent())
