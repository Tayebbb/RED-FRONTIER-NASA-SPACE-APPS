class_name Interactable
extends Area3D
## Something the player can use with E. Placed on an INT_* marker by InteractionManager (or added by hand to any
## scene). Owns no gameplay: it only reports that it was used; whoever registered for its id decides what happens.

signal interacted(interactable: Interactable, interactor: Node)

@export var interaction_id := ""
@export var label := ""
@export var prompt := "INTERACT"
@export var radius := GameConfig.INTERACT_RADIUS
@export var enabled := true

func _ready() -> void:
	collision_layer = GameConfig.LAYER_INTERACTABLE
	collision_mask = 0
	monitoring = false
	var shape := CylinderShape3D.new()
	shape.radius = radius
	shape.height = 2.4
	var cs := CollisionShape3D.new()
	cs.shape = shape
	cs.position.y = 1.2
	add_child(cs)

func can_interact() -> bool:
	return enabled and is_inside_tree()

func interact(interactor: Node) -> void:
	if can_interact():
		interacted.emit(self, interactor)
