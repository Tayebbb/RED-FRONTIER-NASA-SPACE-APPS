class_name FacilityStreamer
extends Node3D
## Room streaming for the Red Frontier facility.
## The rooms form one chain (the mission route). Only the current room and its two neighbours on the chain are
## resident; everything else is freed. Each room root owns its geometry, light rig, GI, reflection probe,
## occluders and (Hangar) the rover, so unloading a room releases all of it. Materials and textures are the
## shared library (res://shared/), so they are never loaded twice and stay resident only while a room uses them.
##
## Lighting policy (game-readiness pass). GI volumes are baked once per room and cached (assets/<room>_voxelgi.res):
##   Hangar          VoxelGI 256, dynamic lights + reflection probe - highest quality, unchanged
##   MissionControl  VoxelGI 64, dynamic lights (Launch Mode switches them) + probe
##   MarsIntel       VoxelGI 64, lights baked STATIC into the GI (no per-frame light injection) + probe
##   Briefing        VoxelGI 64, lights baked STATIC into the GI + probe
##   Corridors       no GI volume, no probe: lit by their line light and the rooms either side
## Probe-only ambient was tried for the three smaller rooms and rejected: 12-28 levels darker than the approved look.

signal room_loaded(room: String, ms: float)
signal room_unloaded(room: String)

const ASSETS := "res://assets/"
const ORDER := ["Briefing", "Corridor01", "MarsIntel", "Corridor02", "Hangar", "MissionControl"]
const GI_POLICY := {"Hangar": "voxelgi256", "MissionControl": "voxelgi64", "MarsIntel": "voxelgi64_static", "Briefing": "voxelgi64_static"}
const GI_ENERGY := 1.6
## Light scale per room. The approved look was captured with every room resident, when unshadowed downlights from
## the other rooms leaked through walls into each room. Streaming removes the leak; scaling the room's own
## downlights puts that light back where it fell (floor and lower walls, ceilings stay dark). Calibrated against the
## pre-streaming screenshots (2026-10-05): every camera within +-1.5 levels. GI energy stays 1.6.
var light_scale := {"Briefing": 1.6, "MarsIntel": 1.6, "MissionControl": 1.3}
var gi_energy := {}

var manifests := {}                         # room -> manifest (footprint, lights, emission sets)
var loaded := {}                            # room -> root Node3D
var pending := {}                           # room -> request start (ms)
var current := ""
var launch_mode := false
var voxel_quality := RenderingServer.VOXEL_GI_QUALITY_HIGH
var hero_spots: Array[SpotLight3D] = []
var gi_override := {}
## Door impostors: the forward route looks through a corridor into a room that is not resident yet. That doorway
## shows a captured image of the real room (tools/make_impostors.gd) until the room loads. Godot coordinates.
const IMPOSTORS := {
	"MarsIntel": {"before": "Corridor01", "focus": "Corridor01", "centre": Vector3(2.75, 1.15, -16.02), "size": Vector2(1.2, 2.3),
		"eye": Vector3(2.75, 1.65, -8.0)},
	"Hangar": {"before": "Corridor02", "focus": "Corridor02", "centre": Vector3(0.0, 1.45, -33.02), "size": Vector2(2.6, 2.9),
		"eye": Vector3(0.0, 1.65, -24.0)},
}
var impostors_enabled := true
var _impostor_nodes := {}                       # room -> "voxelgi" | "probe" | "none" (tests and measurement only)

func _ready() -> void:
	for room in ORDER:
		var path := ASSETS + "RF_%s_lights.json" % room
		if FileAccess.file_exists(path):
			manifests[room] = JSON.parse_string(FileAccess.get_file_as_string(path))

## Shader/pipeline warm-up (call once at start-up, e.g. behind a loading screen): every shared material and the
## rover are rendered for a few frames right in front of the camera, so their pipelines are compiled before the
## first room transition instead of during it. Returns the node; free it after warmup_frames frames.
const WARMUP_FRAMES := 4
func warm_up(cam: Camera3D) -> Node3D:
	var w := Node3D.new()
	w.name = "WarmUp"
	add_child(w)
	var lib: Node3D = load("res://shared/RF_MaterialLibrary.glb").instantiate()
	w.add_child(lib)
	var meshes := lib.find_children("*", "MeshInstance3D", true, false)
	var i := 0
	for mi in meshes:                                              # a 12 x 10 grid of tiny quads filling the view
		mi.global_transform = Transform3D(Basis().scaled(Vector3.ONE * 0.02), Vector3((i % 12) * 0.022 - 0.13, (i / 12) * 0.022 - 0.11, 0))
		i += 1
	var rv: Node3D = load(ASSETS + "RF01_Rover.glb").instantiate()
	w.add_child(rv)
	rv.scale = Vector3.ONE * 0.05
	rv.position = Vector3(0.2, -0.05, 0)
	var light := OmniLight3D.new()                                 # lit + shadowed variants too
	light.shadow_enabled = true
	w.add_child(light)
	light.position = Vector3(0, 0.3, 0.3)
	w.global_transform = cam.global_transform.translated_local(Vector3(0, 0, -0.6))
	return w

## Room containing a Godot-space position ("" in a doorway / wall gap: keep the current room).
func room_at(p: Vector3) -> String:
	for room in manifests:
		var f: Dictionary = manifests[room].footprint
		if p.x >= f.x[0] and p.x <= f.x[1] and p.z >= f.z[0] and p.z <= f.z[1]:
			return room
	return ""

func wanted(room: String) -> Array:
	var i := ORDER.find(room)
	var out := []
	for j in [i - 1, i, i + 1]:
		if j >= 0 and j < ORDER.size() and manifests.has(ORDER[j]):
			out.append(ORDER[j])
	return out

## Call every frame with the player / camera position: loads the neighbourhood in the background.
func update(p: Vector3) -> void:
	var r := room_at(p)
	if r != "" and r != current:
		_set_current(r, false)
	_poll()

## Jump straight to a room (camera switch): its neighbourhood is loaded before returning.
func focus(room: String) -> void:
	_set_current(room, true)

func _set_current(room: String, sync: bool) -> void:
	current = room
	var keep := wanted(room)
	for r in loaded.keys():
		if not r in keep:
			_unload(r)
	for r in keep:
		if not loaded.has(r) and not pending.has(r):
			if sync or r == room:
				_instance(r, load(ASSETS + "RF_%s.glb" % r), Time.get_ticks_usec())
			else:
				for dep in _deps(r):                             # room + rover + GI cache, all off the main thread
					ResourceLoader.load_threaded_request(dep)
				pending[r] = Time.get_ticks_usec()

func _update_impostors() -> void:
	for room in IMPOSTORS:
		var show: bool = impostors_enabled and loaded.has(IMPOSTORS[room].before) and not loaded.has(room)
		if show and not _impostor_nodes.has(room):
			var path := ASSETS + "RF_Impostor_%s.png" % room
			if not ResourceLoader.exists(path):
				continue
			var q := MeshInstance3D.new()
			var quad := QuadMesh.new()
			quad.size = IMPOSTORS[room].size
			var m := StandardMaterial3D.new()
			m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.albedo_texture = load(path)
			quad.material = m
			q.mesh = quad
			q.name = "Impostor_" + room
			add_child(q)
			q.position = IMPOSTORS[room].centre                  # faces +Z: back toward the room before it
			_impostor_nodes[room] = q
		elif not show and _impostor_nodes.has(room):
			_impostor_nodes[room].queue_free()
			_impostor_nodes.erase(room)

## Everything a room needs from disk: its scene, the rover (Hangar) and its cached GI data.
func _deps(room: String) -> Array:
	var out := [ASSETS + "RF_%s.glb" % room]
	var man: Dictionary = manifests[room]
	if man.rover != null and ResourceLoader.exists(ASSETS + man.rover.asset):
		out.append(ASSETS + man.rover.asset)
	var cache := "res://assets/%s_voxelgi.res" % room.to_lower()
	if GI_POLICY.has(room) and ResourceLoader.exists(cache):
		out.append(cache)
	return out

func _poll() -> void:
	_run_job()
	_update_impostors()
	for r in pending.keys():
		var deps := _deps(r)
		var done := true
		for dep in deps:
			var st := ResourceLoader.load_threaded_get_status(dep)
			if st == ResourceLoader.THREAD_LOAD_FAILED or st == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
				push_error("room load failed: %s (%s)" % [r, dep])
				pending.erase(r)
				done = false
				break
			done = done and st == ResourceLoader.THREAD_LOAD_LOADED
		if done and pending.has(r):
			var t0: int = pending[r]
			pending.erase(r)
			var scene: PackedScene = ResourceLoader.load_threaded_get(deps[0])
			for dep in deps.slice(1):
				ResourceLoader.load_threaded_get(dep)                # now cached: load() below is instant
			if r in wanted(current):
				_instance(r, scene, t0, true)

## --- staging: streamed rooms enter and leave the scene a few nodes per frame, one heavy step per frame -----
const STAGE_NODES := 24                     # geometry nodes moved into the live scene per frame
var _jobs: Array = []                       # [room, Callable] - one per frame, in order
var _staging := {}                          # room -> [geo, build]: off-tree nodes still being moved in

func _run_job() -> void:
	if _jobs.is_empty():
		return
	var j: Array = _jobs.pop_front()
	j[1].call()

func _unload(room: String) -> void:
	var root: Node3D = loaded[room]
	for sp in hero_spots.duplicate():
		if root.is_ancestor_of(sp):
			hero_spots.erase(sp)
	loaded.erase(room)
	_jobs = _jobs.filter(func(j): return j[0] != room)          # cancel staging still queued for this room
	if _staging.has(room):                                       # and free what had not moved in yet
		for n in _staging[room]:
			if is_instance_valid(n): n.free()
		_staging.erase(room)
	var kids := root.get_children()
	var heavy := kids.filter(func(n): return n is VoxelGI or n is ReflectionProbe)
	var rest := kids.filter(func(n): return not (n is VoxelGI or n is ReflectionProbe))
	for n in heavy:                                              # GI and probe each free in a frame of their own
		_jobs.append([room + "~", func(): if is_instance_valid(n): n.queue_free()])
	for k in range(0, rest.size(), STAGE_NODES):
		var chunk := rest.slice(k, k + STAGE_NODES)
		_jobs.append([room + "~", func():
			for n in chunk:
				if is_instance_valid(n): n.queue_free()])
	_jobs.append([room + "~", func(): if is_instance_valid(root): root.queue_free()])
	_update_impostors()
	room_unloaded.emit(room)

func _instance(room: String, scene: PackedScene, t0: int, staged := false) -> void:
	var t1 := Time.get_ticks_usec()
	var cache := "res://assets/%s_voxelgi.res" % room.to_lower()
	if GI_POLICY.has(room) and not ResourceLoader.exists(cache):
		staged = false                                           # first run: the GI bake needs the room in the tree
	var root := Node3D.new()
	root.name = "Room_" + room
	var build := Node3D.new() if staged else root                # staged: build off-tree, then move in by chunks
	if not staged:
		add_child(root)
	var geo: Node3D = scene.instantiate()
	build.add_child(geo)
	_add_occluders(geo)
	var man: Dictionary = manifests[room]
	if man.rover != null and ResourceLoader.exists(ASSETS + man.rover.asset):
		var rv: Node3D = load(ASSETS + man.rover.asset).instantiate()
		build.add_child(rv)
		rv.position = Vector3(man.rover.pos[0], man.rover.pos[1], man.rover.pos[2])
		rv.rotation_degrees.y = man.rover.rot_y_deg
	_build_lights(build, room, man)
	_build_gi(build, room, man)
	loaded[room] = root
	if not staged:
		_finish(room, t1)
		return
	add_child(root)
	var parts: Array = []                                        # geometry first, then rover, lights, GI, probe
	for n in geo.get_children():
		parts.append(n)
		_clear_owner(n)                                           # staged nodes change parent: drop the scene owner
	geo.get_parent().remove_child(geo)
	_staging[room] = [geo, build]
	var holder := Node3D.new()
	holder.name = geo.name
	root.add_child(holder)
	for k in range(0, parts.size(), STAGE_NODES):
		var chunk := parts.slice(k, k + STAGE_NODES)
		_jobs.append([room, func():
			for n in chunk:
				geo.remove_child(n); holder.add_child(n)])
	var lights := build.get_children().filter(func(n): return n is Light3D)
	_jobs.append([room, func():
		for n in build.get_children():
			if not (n is VoxelGI or n is ReflectionProbe or n is Light3D):
				build.remove_child(n); root.add_child(n)
		for n in lights:
			build.remove_child(n); root.add_child(n)])
	for heavy in build.get_children().filter(func(n): return n is VoxelGI or n is ReflectionProbe):
		_jobs.append([room, func(): build.remove_child(heavy); root.add_child(heavy)])
	_jobs.append([room, func(): geo.free(); build.free(); _staging.erase(room); _finish(room, t1)])

func _clear_owner(n: Node) -> void:
	n.owner = null
	for c in n.get_children():
		_clear_owner(c)

func _finish(room: String, t1: int) -> void:
	_update_impostors()
	apply_launch_mode(launch_mode)
	room_loaded.emit(room, (Time.get_ticks_usec() - t1) / 1000.0)

## Every solid wall segment (<Room>_Wall<N|S|E|W>_<nn>, glass excluded) becomes a box occluder.
func _add_occluders(geo: Node3D) -> void:
	for mi in geo.find_children("*_Wall*", "MeshInstance3D", true, false):
		if "Glass" in String(mi.name):
			continue
		var aabb: AABB = mi.get_aabb()
		var occ := OccluderInstance3D.new()
		var box := BoxOccluder3D.new()
		box.size = aabb.size
		occ.occluder = box
		mi.add_child(occ)
		occ.position = aabb.get_center()

func _build_lights(root: Node3D, room: String, man: Dictionary) -> void:
	for L in man.lights:
		var pos := Vector3(L.pos[0], L.pos[1], L.pos[2])
		var light: Light3D
		if L.type == "POINT":                                    # beacon glow
			var ol := OmniLight3D.new()
			ol.omni_range = 4.0
			ol.light_energy = L.watts / 25.0 * light_scale.get(room, 1.0)
			root.add_child(ol)
			ol.position = pos
			light = ol
		else:
			var sl := SpotLight3D.new()
			root.add_child(sl)
			var dir := Vector3(L.dir[0], L.dir[1], L.dir[2]).normalized()
			var up := Vector3.FORWARD if absf(dir.y) > 0.9 else Vector3.UP
			sl.look_at_from_position(pos, pos + dir, up)
			var hero: bool = String(L.name).begins_with("LGT_Hero")
			var spread: float = L.get("spread_deg", 180.0)
			sl.light_energy = L.watts / (180.0 if hero else 150.0) * light_scale.get(room, 1.0)
			sl.spot_range = 22.0
			sl.spot_angle = 38.0 if hero else (minf(spread * 0.5 + 8.0, 72.0) if spread < 179.0 else 72.0)
			sl.light_size = 0.6 if hero else 1.2
			sl.shadow_enabled = String(L.name) == "LGT_Hero_Key"
			if room != "Hangar":
				sl.light_specular = 0.15      # a spot stands in for a linear fixture: keep its round highlight off glass
			if hero:
				hero_spots.append(sl)
			light = sl
		light.name = L.name
		light.light_color = Color(L.color[0], L.color[1], L.color[2])
		light.set_meta("set", L.get("set", "Day_Operational"))
		light.set_meta("switched", L.get("switch", false))

func _build_gi(root: Node3D, room: String, man: Dictionary) -> void:
	var policy: String = gi_override.get(room, GI_POLICY.get(room, "none"))
	if policy == "none":
		return
	var f: Dictionary = man.footprint
	var centre := Vector3((f.x[0] + f.x[1]) / 2.0, f.h / 2.0, (f.z[0] + f.z[1]) / 2.0)
	var size := Vector3(f.x[1] - f.x[0] + 1.0, f.h + 0.8, f.z[1] - f.z[0] + 1.0)
	if policy.begins_with("voxelgi"):
		if policy.ends_with("_static"):                          # bounce from these lights is baked into the GI data
			for l in root.find_children("*", "Light3D", true, false):
				l.light_bake_mode = Light3D.BAKE_STATIC
		var gi := VoxelGI.new()
		gi.position = centre
		gi.size = size
		gi.subdiv = {"voxelgi256": VoxelGI.SUBDIV_256, "voxelgi128": VoxelGI.SUBDIV_128}.get(policy.trim_suffix("_static"), VoxelGI.SUBDIV_64)
		root.add_child(gi)
		var cache := "res://assets/%s_voxelgi.res" % room.to_lower()
		var cache_file: FileAccess
		var has_cache := false
		if ResourceLoader.exists(cache):
			cache_file = FileAccess.open(cache, FileAccess.READ)
			has_cache = cache_file != null and cache_file.get_length() > 1024
			if cache_file != null:
				cache_file.close()
		if has_cache and not "rebake" in OS.get_cmdline_user_args():
			var cached_data = load(cache)
			if cached_data is VoxelGIData:
				gi.data = cached_data
			else:
				gi.bake(root)
		else:
			if DisplayServer.get_name() == "headless":
				gi.queue_free()
				return
			gi.bake(root)                                         # this room's geometry only
			gi.data.propagation = 0.7
			gi.data.interior = true
			ResourceSaver.save(gi.data, cache)
		gi.data.energy = gi_energy.get(room, GI_ENERGY)
	var probe := ReflectionProbe.new()
	probe.position = centre
	probe.size = size
	probe.box_projection = true
	probe.interior = true
	probe.update_mode = ReflectionProbe.UPDATE_ONCE                # static: captured once when the room loads
	root.add_child(probe)

## Launch Mode (Mission Control): ambient -30 %, screens up, amber beacons on. Other rooms keep their lights.
func apply_launch_mode(on: bool) -> void:
	launch_mode = on
	var key := "Launch_Mode" if on else "Day_Operational"
	for room in loaded:
		for l in loaded[room].find_children("*", "Light3D", true, false):
			if l.get_meta("set", "Day_Operational") == "Launch_Mode":
				l.visible = on
			elif l.get_meta("switched", false):
				l.visible = not on
		var sets: Dictionary = manifests[room].get("emission_sets", {})
		if sets.is_empty():
			continue
		for mi in loaded[room].find_children("*", "MeshInstance3D", true, false):
			for i in mi.mesh.get_surface_count():
				var m := mi.mesh.surface_get_material(i) as StandardMaterial3D
				if m != null and sets.has(m.resource_name):
					m.emission_energy_multiplier = sets[m.resource_name][key]

func find_camera(cam_name: String) -> Camera3D:
	for r in loaded:
		var c: Camera3D = loaded[r].find_child(cam_name, true, false)
		if c != null:
			return c
	return null

## Surfaces whose material is missing or not from the shared library (should always be 0).
func audit(room: String) -> Dictionary:
	var missing := 0
	var local := 0
	var surfaces := 0
	for mi in loaded[room].find_children("*", "MeshInstance3D", true, false):
		for i in mi.mesh.get_surface_count():
			surfaces += 1
			var m: Material = mi.mesh.surface_get_material(i)
			if m == null:
				missing += 1
			elif not m.resource_path.begins_with("res://shared/") and not m.resource_path.contains("RF01_Rover"):
				local += 1
	return {"surfaces": surfaces, "missing": missing, "local": local}
