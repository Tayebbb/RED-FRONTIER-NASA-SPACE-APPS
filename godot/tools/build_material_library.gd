extends SceneTree
## Saves every material of the imported RF_MaterialLibrary.glb as res://shared/materials/<name>.tres.
## Textures stay references to the one shared copy (res://shared/RF_MaterialLibrary_*.png).
## Run: Godot --headless --path godot --script res://tools/build_material_library.gd

func _initialize() -> void:
	var root: Node = load("res://shared/RF_MaterialLibrary.glb").instantiate()
	var n := 0
	var tex := {}
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var mesh: Mesh = mi.mesh
		for i in mesh.get_surface_count():
			var m: Material = mesh.surface_get_material(i)
			if m == null or m.resource_name == "":
				continue
			var path := "res://shared/materials/%s.tres" % m.resource_name
			var copy: Material = m.duplicate()
			copy.resource_name = m.resource_name
			if ResourceSaver.save(copy, path) == OK:
				n += 1
			if copy is BaseMaterial3D:
				for p in ["albedo_texture", "roughness_texture", "metallic_texture", "normal_texture", "emission_texture"]:
					var t: Texture2D = copy.get(p)
					if t != null:
						tex[t.resource_path] = true
	print("MATLIB_OK materials=%d textures_referenced=%d" % [n, tex.size()])
	for t in tex:
		if not String(t).begins_with("res://shared/"):
			print("MATLIB_WARN texture outside shared: ", t)
	root.free()
	quit(0)
