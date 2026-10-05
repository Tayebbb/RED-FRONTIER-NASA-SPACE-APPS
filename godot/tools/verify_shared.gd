extends SceneTree
## Every surface of every room must use a shared material (res://shared/materials/) whose textures are the single
## shared copies (res://shared/). Reports missing materials/textures and any room-local duplicates.
## Run: Godot --headless --path godot --script res://tools/verify_shared.gd

const ROOMS := ["Briefing", "Corridor01", "MarsIntel", "Corridor02", "Hangar", "MissionControl"]
const TEX_PROPS := ["albedo_texture", "roughness_texture", "metallic_texture", "normal_texture", "emission_texture"]

func _initialize() -> void:
	var bad := 0
	var mats := {}
	var texs := {}
	for room in ROOMS:
		var root: Node = load("res://assets/RF_%s.glb" % room).instantiate()
		var surfaces := 0
		for mi in root.find_children("*", "MeshInstance3D", true, false):
			for i in mi.mesh.get_surface_count():
				surfaces += 1
				var m: Material = mi.mesh.surface_get_material(i)
				if m == null:
					print("VERIFY_MISSING_MATERIAL %s %s" % [room, mi.name]); bad += 1; continue
				if not m.resource_path.begins_with("res://shared/materials/"):
					print("VERIFY_LOCAL_MATERIAL %s %s %s" % [room, mi.name, m.resource_name]); bad += 1
				mats[m.resource_path] = true
				if m is BaseMaterial3D:
					for p in TEX_PROPS:
						var t: Texture2D = m.get(p)
						if t != null:
							if not t.resource_path.begins_with("res://shared/"):
								print("VERIFY_LOCAL_TEXTURE %s %s" % [room, t.resource_path]); bad += 1
							texs[t.resource_path] = true
		print("VERIFY_ROOM %s surfaces=%d" % [room, surfaces])
		root.free()
	var uncompressed := 0
	for t in texs:
		var cfg := ConfigFile.new()
		cfg.load(String(t) + ".import")
		if not cfg.get_value("remap", "metadata", {}).get("vram_texture", false):
			uncompressed += 1
			print("VERIFY_NOT_VRAM ", t)
	print("VERIFY_DONE problems=%d shared_materials_used=%d shared_textures_used=%d not_vram_compressed=%d" % [bad, mats.size(), texs.size(), uncompressed])
	quit(0)
