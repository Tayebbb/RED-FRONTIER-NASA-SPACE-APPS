class_name UiStyle
## Temporary mission-control UI palette (docs/VISUAL_LANGUAGE.md): navy panels, cyan information, white values,
## orange only for the selected / actionable element.

const NAVY := Color("#08111F")
const CYAN := Color("#74B6FF")
const ORANGE := Color("#C2501C")
const WHITE := Color(0.93, 0.95, 0.97)
const DIM := Color(0.62, 0.68, 0.76)

static func panel(alpha := 0.86, accent := CYAN) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(NAVY, alpha)
	sb.border_color = accent
	sb.border_width_left = 3
	sb.content_margin_left = 16
	sb.content_margin_right = 16
	sb.content_margin_top = 10
	sb.content_margin_bottom = 10
	return sb

static func label(text: String, size := 16, color := WHITE, spacing := 0) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	if spacing != 0:
		var f := SystemFont.new()
		var fv := FontVariation.new()
		fv.base_font = f
		fv.spacing_glyph = spacing
		l.add_theme_font_override("font", fv)
	return l

static func button(text: String) -> Button:
	var b := Button.new()
	b.text = text
	b.add_theme_font_size_override("font_size", 18)
	b.custom_minimum_size = Vector2(200, 44)
	for state in ["normal", "hover", "pressed", "focus"]:
		var sb := StyleBoxFlat.new()
		sb.bg_color = ORANGE if state != "pressed" else ORANGE.darkened(0.2)
		if state == "hover" or state == "focus":
			sb.bg_color = ORANGE.lightened(0.12)
		sb.set_corner_radius_all(2)
		b.add_theme_stylebox_override(state, sb)
	b.add_theme_color_override("font_color", WHITE)
	b.add_theme_color_override("font_hover_color", WHITE)
	b.add_theme_color_override("font_focus_color", WHITE)
	var off := StyleBoxFlat.new()                         # blocked action: grey, not orange
	off.bg_color = Color(DIM, 0.18)
	off.set_corner_radius_all(2)
	b.add_theme_stylebox_override("disabled", off)
	b.add_theme_color_override("font_disabled_color", Color(DIM, 0.6))
	return b

## Secondary action / selectable option: navy with a thin border; orange fill once selected (toggle buttons).
static func outline_button(text: String, toggle := false) -> Button:
	var b := Button.new()
	b.text = text
	b.toggle_mode = toggle
	b.add_theme_font_size_override("font_size", 17)
	b.custom_minimum_size = Vector2(150, 44)
	var states := {"normal": Color(NAVY, 0.9), "hover": NAVY.lightened(0.12), "pressed": ORANGE, "hover_pressed": ORANGE.lightened(0.12),
		"focus": Color(0, 0, 0, 0), "disabled": Color(NAVY, 0.9)}
	for state in states:
		var sb := StyleBoxFlat.new()
		sb.bg_color = states[state]
		sb.border_color = CYAN if state != "focus" else WHITE
		sb.set_border_width_all(1)
		if state in ["pressed", "hover_pressed"]:
			sb.border_color = ORANGE
		if state == "focus":
			sb.draw_center = false
		sb.set_corner_radius_all(2)
		b.add_theme_stylebox_override(state, sb)
	for c in ["font_color", "font_hover_color", "font_pressed_color", "font_hover_pressed_color", "font_focus_color"]:
		b.add_theme_color_override(c, WHITE)
	return b
