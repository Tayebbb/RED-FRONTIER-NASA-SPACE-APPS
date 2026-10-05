extends SceneTree
## Headless import check for RF_Hangar.glb: materials, textures, normals, emissive, scale, counts.
## Run: Godot --headless --path D:/RedFrontier/godot --script res://tests/inspect_hangar.gd

func _all(n: Node) -> Array:
	var out := [n]
	for c in n.get_children():
		out.append_array(_all(c))
	return out

func _xf(n: Node) -> Transform3D:
	# composed local transforms: works before the node enters the tree
	var t := Transform3D.IDENTITY
	var cur := n
	while cur != null and cur is Node3D:
		t = (cur as Node3D).transform * t
		cur = cur.get_parent()
	return t

func _initialize() -> void:
	var ps: PackedScene = load("res://assets/RF_Hangar.glb")
	if ps == null:
		print("INSPECT_FAIL cannot load res://assets/RF_Hangar.glb")
		quit(1)
		return
	var root := ps.instantiate()
	get_root().add_child(root)
	var mesh_instances := 0
	var surfaces := 0
	var tris := 0
	var no_normals := []
	var no_uv := []
	var materials := {}
	var missing_tex := []
	var emissive := {}
	var transparent := {}
	var textures := {}
	var cameras := []
	var markers := []
	var aabb := AABB()
	var first := true
	for n in _all(root):
		if n is MeshInstance3D and n.mesh:
			mesh_instances += 1
			var m: Mesh = n.mesh
			var w: AABB = _xf(n) * m.get_aabb()
			if first:
				aabb = w
				first = false
			else:
				aabb = aabb.merge(w)
			for s in m.get_surface_count():
				surfaces += 1
				var arr := m.surface_get_arrays(s)
				var idx = arr[Mesh.ARRAY_INDEX]
				tris += (idx.size() / 3) if idx != null else (arr[Mesh.ARRAY_VERTEX].size() / 3)
				if arr[Mesh.ARRAY_NORMAL] == null or arr[Mesh.ARRAY_NORMAL].size() == 0:
					no_normals.append(n.name)
				var mat = n.get_active_material(s)
				if mat == null:
					continue
				var nm: String = mat.resource_name
				materials[nm] = true
				if mat is BaseMaterial3D:
					for t in [mat.albedo_texture, mat.normal_texture, mat.roughness_texture, mat.emission_texture]:
						if t != null:
							textures[t.get_rid().get_id()] = "%s %dx%d" % [nm, t.get_width(), t.get_height()]
					var textured := nm.begins_with("MAT_Decal") or nm.begins_with("MAT_Floor_Epoxy") or nm.begins_with("MAT_Floor_Metal")
					if nm.begins_with("MAT_Screen_") and nm != "MAT_Screen_Dark" and nm != "MAT_Screen_Emissive":
						textured = true
					if textured and mat.albedo_texture == null and mat.emission_texture == null:
						missing_tex.append(nm)
					if (textured or nm.begins_with("MAT_Floor")) and (arr[Mesh.ARRAY_TEX_UV] == null or arr[Mesh.ARRAY_TEX_UV].size() == 0):
						no_uv.append(n.name)
					if mat.emission_enabled:
						emissive[nm] = "%.2f%s" % [mat.emission_energy_multiplier, " tex" if mat.emission_texture != null else ""]
					if mat.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED:
						transparent[nm] = true
		elif n is Camera3D:
			cameras.append(n.name)
		elif String(n.name).begins_with("INT_") or String(n.name).begins_with("TRIG_"):
			markers.append(n.name)
	print("INSPECT mesh_instances=%d surfaces=%d triangles=%d materials=%d textures=%d" % [mesh_instances, surfaces, tris, materials.size(), textures.size()])
	print("INSPECT size_m=%s (x, y-up, z)  origin=%s" % [str(aabb.size), str(aabb.position)])
	print("INSPECT cameras=%s" % str(cameras))
	print("INSPECT markers=%s" % str(markers))
	print("INSPECT emissive=%s" % str(emissive))
	print("INSPECT transparent_materials=%d %s" % [transparent.size(), str(transparent.keys().slice(0, 8))])
	print("INSPECT missing_textures=%s" % str(missing_tex))
	print("INSPECT missing_normals=%s" % str(no_normals.slice(0, 10)))
	print("INSPECT missing_uvs=%s" % str(no_uv.slice(0, 10)))
	var big := textures.values()
	big.sort()
	print("INSPECT texture_sample=%s" % str(big.slice(0, 12)))
	quit(0)
