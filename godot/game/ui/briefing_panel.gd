class_name BriefingPanel
extends CanvasLayer
## Temporary mission briefing (text from GameConfig.BRIEFING). Emits continued when the player presses CONTINUE.

signal continued

var continue_button: Button

func _ready() -> void:
	layer = 20
	process_mode = Node.PROCESS_MODE_ALWAYS
	var dim := ColorRect.new()
	dim.color = Color(UiStyle.NAVY, 0.55)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dim)

	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var panel := PanelContainer.new()
	var sb := UiStyle.panel(0.95, UiStyle.ORANGE)
	sb.border_width_left = 0
	sb.border_width_top = 4
	sb.content_margin_left = 44
	sb.content_margin_right = 44
	sb.content_margin_top = 34
	sb.content_margin_bottom = 30
	panel.add_theme_stylebox_override("panel", sb)
	panel.custom_minimum_size = Vector2(620, 0)
	center.add_child(panel)

	var b: Dictionary = GameConfig.BRIEFING
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 6)
	col.add_child(UiStyle.label(b.mission, 30, UiStyle.WHITE, 3))
	col.add_child(_gap(18))
	col.add_child(UiStyle.label("PRIMARY OBJECTIVE", 13, UiStyle.CYAN, 2))
	col.add_child(UiStyle.label(b.objective, 20))
	col.add_child(_gap(14))
	col.add_child(UiStyle.label("MISSION PRIORITIES", 13, UiStyle.CYAN, 2))
	var i := 1
	for p in b.priorities:
		col.add_child(UiStyle.label("%d.  %s" % [i, p], 20))
		i += 1
	col.add_child(_gap(18))
	var warn := UiStyle.label(b.warning, 16, UiStyle.DIM)
	warn.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	col.add_child(warn)
	col.add_child(_gap(22))
	continue_button = UiStyle.button("CONTINUE")
	continue_button.size_flags_horizontal = Control.SIZE_SHRINK_END
	continue_button.pressed.connect(_on_continue)
	col.add_child(continue_button)
	panel.add_child(col)
	continue_button.grab_focus.call_deferred()

func _gap(h: float) -> Control:
	var c := Control.new()
	c.custom_minimum_size.y = h
	return c

func _on_continue() -> void:
	continued.emit()
	queue_free()

func _unhandled_input(ev: InputEvent) -> void:
	get_viewport().set_input_as_handled()                 # the panel owns input while open
