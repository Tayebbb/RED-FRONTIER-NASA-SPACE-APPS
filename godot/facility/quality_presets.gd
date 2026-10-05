class_name QualityPresets
## Render presets for the facility viewer / game.
##   HIGH        unchanged from the approved setup: SSAO, SSR, shadows on all three hero lights
##   LAPTOP      the approved default: SSAO, no SSR, one shadowed light (the hero key)
##   INTEGRATED  Intel UHD class: no SSR, no SSAO, restrained bloom (two lowest glow levels), one shadowed light on a
##               2048 atlas with very-low soft-shadow filtering. (Half-resolution GI is opt-in only: see apply().)
## Chosen automatically: INTEGRATED on an integrated GPU, LAPTOP otherwise. F cycles at runtime.

enum { HIGH, LAPTOP, INTEGRATED }
static var _defaults := {}
const NAMES := ["high", "laptop", "integrated GPU"]

static func default_preset() -> int:
	return INTEGRATED if RenderingServer.get_video_adapter_type() == RenderingDevice.DEVICE_TYPE_INTEGRATED_GPU else LAPTOP

## Per-room part: which hero lights cast shadows. Safe to call whenever a room loads.
static func apply_lights(preset: int, hero_spots: Array) -> void:
	for s in hero_spots:
		if is_instance_valid(s):
			s.shadow_enabled = preset == HIGH or s.name == "LGT_Hero_Key"

## Global part: environment, shadow atlas, filter quality, GI resolution. Call once at start-up and when the preset
## changes - never per room load: re-sending these can make the renderer reallocate its buffers mid-frame.
static func apply(preset: int, env: Environment, viewport: Viewport, hero_spots: Array) -> void:
	env.ssr_enabled = preset == HIGH
	env.ssao_enabled = preset != INTEGRATED
	env.glow_enabled = true
	env.glow_intensity = 0.2 if preset != INTEGRATED else 0.12
	env.glow_bloom = 0.0
	if preset == INTEGRATED:                       # restrained bloom: the two lowest glow levels only
		for i in range(7):                             # glow levels 1-2 (indices 0-1): small radius only
			env.set_glow_level(i, 1.0 if i <= 1 else 0.0)
	else:
		for i in range(7):
			env.set_glow_level(i, 1.0 if i in [2, 4] else 0.0)  # Godot defaults: levels 3 and 5
	apply_lights(preset, hero_spots)
	if _defaults.is_empty():                       # what HIGH / LAPTOP use: the project's own values, untouched
		_defaults = {"atlas": viewport.positional_shadow_atlas_size,
			"soft": ProjectSettings.get_setting("rendering/lights_and_shadows/positional_shadow/soft_shadow_filter_quality", 2)}
	viewport.positional_shadow_atlas_size = mini(2048, _defaults.atlas) if preset == INTEGRATED else _defaults.atlas
	RenderingServer.positional_soft_shadow_filter_set_quality(
		RenderingServer.SHADOW_QUALITY_SOFT_VERY_LOW if preset == INTEGRATED else _defaults.soft)
	# Half-resolution GI is OFF by default. It was in use when intermittent Vulkan device-lost resets happened, but so
	# was a per-room-load re-apply of these global settings (now fixed, see apply_lights). Opt in with `-- halfres`.
	RenderingServer.gi_set_use_half_resolution("halfres" in OS.get_cmdline_user_args())
	# VoxelGI quality stays at the project default (low) in every preset.
