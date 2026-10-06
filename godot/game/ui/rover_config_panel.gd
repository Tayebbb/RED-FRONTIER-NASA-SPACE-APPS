extends CanvasLayer
## Engineering Hangar: build RF-01. The panel edits a working copy of the build and shows RoverBuild.evaluate() for
## it after every pick; it holds no formulas. ACCEPT BUILD asks the game to store the build (accept_requested);
## on success the game calls show_saved(). BACK / Esc discards unsaved edits (closed(false)).

signal accept_requested(build: Dictionary)
signal closed(saved: bool)

const RoverParts := preload("res://game/data/rover_parts.gd")
const RoverBuild := preload("res://game/data/rover_build.gd")
const RED := Color("#E05A47")                 # warning only (VISUAL_LANGUAGE.md)
const CARD := Vector2(272, 66)
const BAR_W := 330.0

var build: Dictionary = RoverBuild.empty_build()
var site: Dictionary = {}
var stats: Dictionary = {}
var cards := {}                               # part id -> Button
var accept_button: Button
var back_button: Button
var continue_button: Button
var _editor: Control
var _saved_view: Control
var _saved := false
var _instrument_count: Label
var _instrument_hint: Label
var _rows := {}                               # "mass" | "budget" | "power" | "safety" | "science" -> {value, note, bar}
var _status: VBoxContainer

## start: the saved build to edit (or an empty build); site: the locked landing-site record.
func setup(start: Dictionary, landing_site: Dictionary) -> void:
	build = start.duplicate(true)
	site = landing_site

func _ready() -> void:
	layer = 20
	var dim := ColorRect.new()
	dim.color = Color(UiStyle.NAVY, 0.6)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var panel := PanelContainer.new()
	var sb := UiStyle.panel(0.96, UiStyle.ORANGE)
	sb.border_width_left = 0
	sb.border_width_top = 4
	sb.content_margin_left = 32
	sb.content_margin_right = 32
	sb.content_margin_top = 22
	sb.content_margin_bottom = 22
	panel.add_theme_stylebox_override("panel", sb)
	center.add_child(panel)
	var stack := VBoxContainer.new()
	panel.add_child(stack)
	_editor = _build_editor()
	_saved_view = _build_saved()
	_saved_view.visible = false
	stack.add_child(_editor)
	stack.add_child(_saved_view)
	refresh()

# --- layout --------------------------------------------------------------------------------------------------

func _build_editor() -> Control:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 4)
	col.add_child(UiStyle.label("ENGINEERING HANGAR", 12, UiStyle.CYAN, 2))
	col.add_child(UiStyle.label("RF-01 ENGINEERING CONFIGURATION", 24, UiStyle.WHITE, 2))
	col.add_child(_gap(8))
	var main := HBoxContainer.new()
	main.add_theme_constant_override("separation", 34)
	col.add_child(main)

	var left := VBoxContainer.new()
	left.add_theme_constant_override("separation", 4)
	main.add_child(left)
	for key in RoverParts.categories():
		var head := HBoxContainer.new()
		head.add_child(UiStyle.label(RoverParts.category(key).title, 12, UiStyle.CYAN, 2))
		if key == "instruments":
			var spacer := Control.new()
			spacer.custom_minimum_size.x = 16
			head.add_child(spacer)
			_instrument_count = UiStyle.label("", 12, UiStyle.WHITE, 1)
			head.add_child(_instrument_count)
			_instrument_hint = UiStyle.label("", 12, UiStyle.DIM)
			head.add_child(_gap_x(12))
			head.add_child(_instrument_hint)
		left.add_child(head)
		var grid := GridContainer.new()
		grid.columns = 3
		grid.add_theme_constant_override("h_separation", 8)
		grid.add_theme_constant_override("v_separation", 8)
		for id in RoverParts.category_parts(key):
			grid.add_child(_card(id))
		left.add_child(grid)
		left.add_child(_gap(6))

	var right := VBoxContainer.new()
	right.custom_minimum_size.x = BAR_W + 20
	right.add_theme_constant_override("separation", 4)
	main.add_child(right)
	right.add_child(UiStyle.label("LANDING SITE", 12, UiStyle.CYAN, 2))
	right.add_child(UiStyle.label(site.get("display_name", "NOT LOCKED"), 20))
	right.add_child(_gap(8))
	for key in ["mass", "budget", "power", "safety", "science"]:
		right.add_child(_stat_row(key, {"mass": "MASS", "budget": "BUDGET", "power": "POWER", "safety": "SAFETY",
			"science": "SCIENCE POTENTIAL"}[key]))
	right.add_child(_gap(6))
	right.add_child(_rule())
	right.add_child(UiStyle.label("BUILD STATUS", 12, UiStyle.CYAN, 2))
	_status = VBoxContainer.new()
	_status.custom_minimum_size.y = 110
	_status.add_theme_constant_override("separation", 2)
	right.add_child(_status)
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 12)
	back_button = UiStyle.outline_button("BACK")
	back_button.custom_minimum_size.x = 110
	back_button.pressed.connect(back)
	actions.add_child(back_button)
	accept_button = UiStyle.button("ACCEPT BUILD")
	accept_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	accept_button.pressed.connect(_on_accept)
	actions.add_child(accept_button)
	right.add_child(actions)
	return col

func _card(id: String) -> Button:
	var p := RoverParts.part(id)
	var key := RoverParts.category_of(id)
	var b := UiStyle.outline_button("", true)
	b.custom_minimum_size = CARD
	var box := VBoxContainer.new()
	box.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT, Control.PRESET_MODE_MINSIZE, 8)
	box.add_theme_constant_override("separation", 0)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var lines := [p.name, "%d KG  ·  %d CREDITS" % [p.mass, p.cost]]
	match key:
		"solar": lines.append("OUTPUT %d" % p.value)
		"battery": lines.append("CAPACITY %d" % p.capacity)
		"shield": lines.append("PROTECTION %d" % p.value)
		"antenna": lines.append("RELIABILITY %d%%  ·  POWER DRAW %d" % [roundi(p.reliability * 100.0), p.draw])
		"instruments": lines.append("SCIENCE +%d  ·  %s" % [p.value, p.get("note", "")])
	for i in lines.size():
		var l := UiStyle.label(lines[i], 14 if i == 0 else 11, UiStyle.WHITE if i == 0 else UiStyle.DIM)
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		box.add_child(l)
	b.add_child(box)
	b.pressed.connect(pick.bind(id))
	cards[id] = b
	return b

func _stat_row(key: String, title: String) -> Control:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	var head := HBoxContainer.new()
	var t := UiStyle.label(title, 12, UiStyle.CYAN, 2)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(t)
	var value := UiStyle.label("", 17)
	head.add_child(value)
	box.add_child(head)
	var bar := Control.new()
	bar.custom_minimum_size = Vector2(BAR_W, 6)
	bar.set_meta("fill", 0.0)
	bar.set_meta("colour", UiStyle.CYAN)
	bar.draw.connect(func():
		bar.draw_rect(Rect2(Vector2.ZERO, bar.size), Color(UiStyle.DIM, 0.18))
		bar.draw_rect(Rect2(Vector2.ZERO, Vector2(bar.size.x * float(bar.get_meta("fill")), bar.size.y)), bar.get_meta("colour")))
	box.add_child(bar)
	var note := UiStyle.label("", 11, UiStyle.DIM)
	box.add_child(note)
	_rows[key] = {"value": value, "note": note, "bar": bar}
	return box

func _build_saved() -> Control:
	var col := VBoxContainer.new()
	col.custom_minimum_size = Vector2(620, 300)
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	col.add_theme_constant_override("separation", 8)
	var lines := [UiStyle.label("RF-01 CONFIGURATION SAVED", 26, UiStyle.WHITE, 3),
		UiStyle.label("%d KG LIMIT VERIFIED" % RoverBuild.mass_limit(), 15, UiStyle.CYAN, 2),
		UiStyle.label("%d CREDIT LIMIT VERIFIED" % RoverBuild.budget_limit(), 15, UiStyle.CYAN, 2),
		UiStyle.label("READY FOR SIMULATION", 15, UiStyle.DIM, 2)]
	for l in lines:
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		col.add_child(l)
	col.add_child(_gap(16))
	continue_button = UiStyle.button("CONTINUE")
	continue_button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	continue_button.pressed.connect(_finish)
	col.add_child(continue_button)
	return col

func _gap(h: float) -> Control:
	var c := Control.new()
	c.custom_minimum_size.y = h
	return c

func _gap_x(w: float) -> Control:
	var c := Control.new()
	c.custom_minimum_size.x = w
	return c

func _rule() -> Control:
	var r := ColorRect.new()
	r.color = Color(UiStyle.CYAN, 0.25)
	r.custom_minimum_size.y = 1
	return r

# --- behaviour ------------------------------------------------------------------------------------------------

## Pick (or, for an instrument already chosen, remove) a part, then show the consequences.
func pick(id: String) -> void:
	if _saved:
		return
	build = RoverBuild.with_part(build, id)
	refresh()

func refresh() -> void:
	stats = RoverBuild.evaluate(build, site)
	var chosen: Array = build.instruments
	var full: bool = chosen.size() >= RoverBuild.instrument_slots()
	for id in cards:
		var key := RoverParts.category_of(id)
		var on: bool = id in chosen if key == "instruments" else build[key] == id
		cards[id].set_pressed_no_signal(on)
		cards[id].disabled = key == "instruments" and full and not on
		cards[id].modulate.a = 0.35 if cards[id].disabled else 1.0         # unavailable until one is removed
		var details: Array = cards[id].get_child(0).get_children()
		for i in range(1, details.size()):                                  # detail lines stay legible on orange
			details[i].add_theme_color_override("font_color", UiStyle.WHITE if on else UiStyle.DIM)
	_instrument_count.text = "%d / %d" % [chosen.size(), RoverBuild.instrument_slots()]
	_instrument_count.add_theme_color_override("font_color", UiStyle.ORANGE if full else UiStyle.WHITE)
	_instrument_hint.text = "FULL: REMOVE ONE TO SWAP" if full else "SELECT EXACTLY %d" % RoverBuild.instrument_slots()

	_limit_row("mass", stats.mass, RoverBuild.mass_limit(), "KG", stats.over_mass, "OVER MASS BY %d KG")
	_limit_row("budget", stats.cost, RoverBuild.budget_limit(), "CREDITS", stats.over_budget, "OVER BUDGET BY %d CREDITS")
	_score_row("power", stats.power, "NEEDS SOLAR, BATTERY AND ANTENNA")
	_score_row("safety", stats.safety, "NEEDS SHIELDING AND ANTENNA")
	_score_row("science", stats.build_science, "NEEDS AN INSTRUMENT")

	for c in _status.get_children():
		c.queue_free()
	if stats.valid:
		_status.add_child(UiStyle.label("CONFIGURATION VALID", 15, UiStyle.CYAN, 1))
	else:
		for problem in stats.problems:
			_status.add_child(UiStyle.label(problem, 14, RED if problem.begins_with("OVER") else UiStyle.WHITE))
	accept_button.disabled = not stats.valid

func _limit_row(key: String, value: int, limit: int, unit: String, over: int, over_text: String) -> void:
	var row: Dictionary = _rows[key]
	row.value.text = "%d / %d %s" % [value, limit, unit]
	row.value.add_theme_color_override("font_color", RED if over > 0 else UiStyle.WHITE)
	row.note.text = over_text % over if over > 0 else ""
	row.note.add_theme_color_override("font_color", RED)
	row.bar.set_meta("fill", clampf(float(value) / limit, 0.0, 1.0))
	row.bar.set_meta("colour", RED if over > 0 else UiStyle.CYAN)
	row.bar.queue_redraw()

func _score_row(key: String, value, missing: String) -> void:
	var row: Dictionary = _rows[key]
	row.value.text = "—" if value == null else str(roundi(value))
	row.note.text = missing if value == null else ""
	row.bar.set_meta("fill", 0.0 if value == null else float(value) / 100.0)
	row.bar.queue_redraw()

## Shown text for one stat row (tests).
func shown(key: String) -> String:
	return _rows[key].value.text

func shown_problems() -> Array:
	return stats.get("problems", [])

func is_saved() -> bool:
	return _saved

func _on_accept() -> void:
	if stats.get("valid", false) and not _saved:
		accept_requested.emit(build.duplicate(true))

## Called by the game once MissionState has stored the build.
func show_saved() -> void:
	_saved = true
	_editor.visible = false
	_saved_view.visible = true
	continue_button.grab_focus.call_deferred()

func back() -> void:
	if _saved:
		return
	closed.emit(false)
	queue_free()

func _finish() -> void:
	closed.emit(true)
	queue_free()

func _unhandled_input(ev: InputEvent) -> void:
	if ev.is_action_pressed("ui_cancel"):
		if _saved:
			_finish()
		else:
			back()
	get_viewport().set_input_as_handled()                 # the panel owns input while open
