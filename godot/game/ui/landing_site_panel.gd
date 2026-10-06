extends CanvasLayer
## Mars Intelligence: compare the candidate landing sites and lock one. Inspecting a site commits nothing; only
## CONFIRM LANDING SITE emits confirmed(id). Then a short LANDING SITE LOCKED card, and closed(true) on Continue.
## BACK / Esc before confirming emits closed(false). Site data: game/data/landing_sites.json (prototype values).

signal confirmed(site_id: String)
signal closed(locked: bool)

const LandingSites := preload("res://game/data/landing_sites.gd")
const AMBER := Color("#E3A928")              # hazard colour (VISUAL_LANGUAGE.md): terrain risk only
const SEGMENTS := 10

var current_id := ""
var site_buttons := {}                        # id -> Button
var confirm_button: Button
var back_button: Button
var continue_button: Button
var _analysis: Control
var _locked_view: Control
var _locked := false
var _name: Label
var _profile: Label
var _locked_name: Label
var _meters := {}                             # "science" | "solar" | "terrain_risk" -> [segments: Array, label: Label]

func _ready() -> void:
	layer = 20
	var dim := ColorRect.new()
	dim.color = Color(UiStyle.NAVY, 0.55)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
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
	sb.content_margin_top = 30
	sb.content_margin_bottom = 30
	panel.add_theme_stylebox_override("panel", sb)
	panel.custom_minimum_size = Vector2(760, 0)
	center.add_child(panel)
	var stack := VBoxContainer.new()
	panel.add_child(stack)
	_analysis = _build_analysis()
	_locked_view = _build_locked()
	_locked_view.visible = false
	stack.add_child(_analysis)
	stack.add_child(_locked_view)
	show_site(LandingSites.ids()[0])
	site_buttons[current_id].grab_focus.call_deferred()

func _build_analysis() -> Control:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 6)
	col.add_child(UiStyle.label("MARS INTELLIGENCE", 13, UiStyle.CYAN, 2))
	col.add_child(UiStyle.label("LANDING SITE ANALYSIS", 28, UiStyle.WHITE, 3))
	col.add_child(UiStyle.label("MISSION DATA  ·  %s ANALYSIS" % LandingSites.provenance(), 11, UiStyle.DIM, 1))
	col.add_child(_gap(14))
	col.add_child(UiStyle.label("SELECT LANDING ZONE", 13, UiStyle.CYAN, 2))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	var group := ButtonGroup.new()
	for id in LandingSites.ids():
		var b := UiStyle.outline_button(LandingSites.get_site(id).get("short_name", id.to_upper()), true)
		b.button_group = group
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.pressed.connect(show_site.bind(id))
		row.add_child(b)
		site_buttons[id] = b
	col.add_child(row)
	col.add_child(_gap(10))
	col.add_child(_rule())
	col.add_child(_gap(6))
	_name = UiStyle.label("", 26, UiStyle.WHITE, 2)
	col.add_child(_name)
	col.add_child(_gap(6))
	col.add_child(_meter("science", "SCIENCE POTENTIAL", UiStyle.CYAN))
	col.add_child(_meter("solar", "SOLAR AVAILABILITY", UiStyle.CYAN))
	col.add_child(_meter("terrain_risk", "TERRAIN RISK", AMBER))
	col.add_child(_gap(8))
	col.add_child(UiStyle.label("MISSION PROFILE", 12, UiStyle.CYAN, 2))
	_profile = UiStyle.label("", 17)
	_profile.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_profile.custom_minimum_size.y = 48
	col.add_child(_profile)
	col.add_child(_gap(10))
	col.add_child(_rule())
	col.add_child(_gap(10))
	var actions := HBoxContainer.new()
	back_button = UiStyle.outline_button("BACK")
	back_button.pressed.connect(back)
	actions.add_child(back_button)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	actions.add_child(spacer)
	confirm_button = UiStyle.button("CONFIRM LANDING SITE")
	confirm_button.custom_minimum_size.x = 260
	confirm_button.pressed.connect(confirm)
	actions.add_child(confirm_button)
	col.add_child(actions)
	return col

func _build_locked() -> Control:
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 8)
	col.custom_minimum_size.y = 260
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	var title := UiStyle.label("LANDING SITE LOCKED", 15, UiStyle.CYAN, 3)
	_locked_name = UiStyle.label("", 34, UiStyle.WHITE, 3)
	var note := UiStyle.label("Mission profile recorded.", 17, UiStyle.DIM)
	for l in [title, _locked_name, note]:
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		col.add_child(l)
	col.add_child(_gap(18))
	continue_button = UiStyle.button("CONTINUE")
	continue_button.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	continue_button.pressed.connect(_finish)
	col.add_child(continue_button)
	return col

func _meter(key: String, title: String, colour: Color) -> Control:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 3)
	box.add_child(UiStyle.label(title, 12, UiStyle.CYAN, 2))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 4)
	var segs: Array = []
	for i in SEGMENTS:
		var s := ColorRect.new()
		s.custom_minimum_size = Vector2(26, 12)
		s.set_meta("on", colour)
		row.add_child(s)
		segs.append(s)
	var spacer := Control.new()
	spacer.custom_minimum_size.x = 14
	row.add_child(spacer)
	var value := UiStyle.label("", 17)
	row.add_child(value)
	box.add_child(row)
	_meters[key] = [segs, value]
	return box

func _gap(h: float) -> Control:
	var c := Control.new()
	c.custom_minimum_size.y = h
	return c

func _rule() -> Control:
	var r := ColorRect.new()
	r.color = Color(UiStyle.CYAN, 0.25)
	r.custom_minimum_size.y = 1
	return r

## Inspect a site (does not commit it).
func show_site(id: String) -> void:
	var site := LandingSites.get_site(id)
	if site.is_empty() or _locked:
		return
	current_id = id
	site_buttons[id].set_pressed_no_signal(true)
	_name.text = site.display_name
	_profile.text = site.mission_profile
	for key in _meters:
		var filled := roundi(clampf(float(site[key]), 0.0, 1.0) * SEGMENTS)
		var segs: Array = _meters[key][0]
		for i in segs.size():
			segs[i].color = segs[i].get_meta("on") if i < filled else Color(UiStyle.DIM, 0.18)
		_meters[key][1].text = site[{"science": "science_label", "solar": "solar_label", "terrain_risk": "terrain_label"}[key]]

func shown_name() -> String:
	return _locked_name.text if _locked else _name.text

func shown_label(key: String) -> String:
	return _meters[key][1].text

func is_locked() -> bool:
	return _locked

func confirm() -> void:
	if _locked or current_id == "":
		return
	_locked = true
	_locked_name.text = LandingSites.get_site(current_id).display_name
	_analysis.visible = false
	_locked_view.visible = true
	continue_button.grab_focus.call_deferred()
	confirmed.emit(current_id)

func back() -> void:
	if _locked:
		return
	closed.emit(false)
	queue_free()

func _finish() -> void:
	closed.emit(true)
	queue_free()

func _unhandled_input(ev: InputEvent) -> void:
	if ev.is_action_pressed("ui_cancel"):
		if _locked:
			_finish()
		else:
			back()
	get_viewport().set_input_as_handled()                 # the panel owns input while open
