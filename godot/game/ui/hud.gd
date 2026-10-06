class_name Hud
extends CanvasLayer
## In-world HUD: current objective (top left), interaction prompt (bottom centre), controls hint, F3 debug line.

var _objective: Label
var _prompt_box: PanelContainer
var _prompt_label: Label
var _prompt_key: Label
var _debug: Label

func _ready() -> void:
	layer = 10
	var obj_box := PanelContainer.new()
	obj_box.add_theme_stylebox_override("panel", UiStyle.panel())
	obj_box.position = Vector2(24, 24)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 2)
	col.add_child(UiStyle.label("MISSION OBJECTIVE", 12, UiStyle.CYAN, 2))
	_objective = UiStyle.label("", 20)
	col.add_child(_objective)
	obj_box.add_child(col)
	add_child(obj_box)

	_prompt_box = PanelContainer.new()
	_prompt_box.add_theme_stylebox_override("panel", UiStyle.panel(0.86, UiStyle.ORANGE))
	_prompt_box.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM, Control.PRESET_MODE_MINSIZE, 0)
	_prompt_box.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_prompt_box.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_prompt_box.offset_bottom = -110
	var pcol := VBoxContainer.new()
	pcol.alignment = BoxContainer.ALIGNMENT_CENTER
	_prompt_key = UiStyle.label("[E] INTERACT", 20, UiStyle.WHITE, 1)
	_prompt_key.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_prompt_label = UiStyle.label("", 13, UiStyle.CYAN)
	_prompt_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pcol.add_child(_prompt_key)
	pcol.add_child(_prompt_label)
	_prompt_box.add_child(pcol)
	_prompt_box.visible = false
	add_child(_prompt_box)

	var hint := UiStyle.label("WASD move  ·  Shift run  ·  Mouse look  ·  E interact  ·  Esc release mouse", 12, UiStyle.DIM)
	hint.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT, Control.PRESET_MODE_MINSIZE, 24)
	hint.grow_vertical = Control.GROW_DIRECTION_BEGIN
	add_child(hint)

	_debug = UiStyle.label("", 12, UiStyle.DIM)
	_debug.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT, Control.PRESET_MODE_MINSIZE, 24)
	_debug.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_debug.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_debug.visible = false
	add_child(_debug)

	MissionState.objective_changed.connect(func(_id, text): set_objective(text))
	set_objective(MissionState.objective_text())

func set_objective(text: String) -> void:
	_objective.text = text

func objective_shown() -> String:
	return _objective.text

func show_prompt(target: Interactable) -> void:
	_prompt_box.visible = target != null
	if target != null:
		_prompt_label.text = target.label.to_upper()
		_prompt_key.text = "[E] %s" % target.prompt

func prompt_visible() -> bool:
	return _prompt_box.visible

func set_debug(text: String) -> void:
	if _debug.visible:
		_debug.text = text

func _unhandled_input(ev: InputEvent) -> void:
	if ev is InputEventKey and ev.pressed and not ev.echo and ev.keycode == KEY_F3:
		_debug.visible = not _debug.visible
