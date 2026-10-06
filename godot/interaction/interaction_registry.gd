class_name InteractionRegistry
extends Node

signal target_changed(target: Node3D, interaction_type: String)
signal interaction_requested(interaction_type: String, target: Node3D)

var targets: Array[Node3D] = []
var current_target: Node3D
var current_type := ""

func register_room(root: Node) -> void:
	for node in root.find_children("INT_*", "Node3D", true, false):
		if node not in targets:
			targets.append(node)

func unregister_room(root: Node) -> void:
	targets = targets.filter(func(target: Node3D) -> bool:
		return is_instance_valid(target) and not root.is_ancestor_of(target))
	if current_target != null and not is_instance_valid(current_target):
		_set_target(null, "")

func update_focus(origin: Vector3, direction: Vector3, max_distance := 2.4) -> void:
	targets = targets.filter(func(target: Node3D) -> bool: return is_instance_valid(target))
	if current_target != null and not is_instance_valid(current_target):
		_set_target(null, "")
	var best: Node3D
	var best_type := ""
	var best_score := -1.0
	for target in targets:
		if not is_instance_valid(target):
			continue
		var offset := target.global_position - origin
		var distance := offset.length()
		if distance > max_distance or distance < 0.01:
			continue
		var facing := direction.normalized().dot(offset.normalized())
		if facing < 0.55:
			continue
		var score := facing - distance / max_distance * 0.35
		if score > best_score:
			best = target
			best_type = _type_for(target.name)
			best_score = score
	_set_target(best, best_type)

func request_interaction() -> void:
	if current_target != null and is_instance_valid(current_target):
		interaction_requested.emit(current_type, current_target)

func _set_target(target: Node3D, interaction_type: String) -> void:
	if target == current_target and interaction_type == current_type:
		return
	current_target = target
	current_type = interaction_type
	target_changed.emit(target, interaction_type)

func _type_for(marker_name: String) -> String:
	if marker_name.begins_with("INT_Station_"):
		return marker_name.trim_prefix("INT_Station_")
	if marker_name.begins_with("INT_LandingSite"):
		return "LANDING_SITE"
	return marker_name.trim_prefix("INT_")
