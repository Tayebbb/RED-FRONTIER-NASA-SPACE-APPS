class_name Player
extends CharacterBody3D
## Third-person walker for the facility. WASD moves relative to the camera, the mouse orbits the camera, and a
## sphere cast keeps the camera out of walls and inside the facility. Tunables live in GameConfig.

@onready var camera_rig: Node3D = $CameraRig
@onready var camera: Camera3D = $CameraRig/Camera
@onready var visual: Node3D = $Visual
@onready var interactor: Interactor = $Interactor

## Optional: returns false for positions the player may not stand on (outside the facility).
var position_allowed: Callable
var controls_enabled := true: set = set_controls_enabled
var mouse_look := true                    # off for scripted camera (tests, later cutscenes)
var first_person := false

var _yaw := 0.0
var _pitch := deg_to_rad(-12.0)
var _ignore_motion_until := 0             # msec: capturing the mouse warps the cursor, which arrives as one big jump
var _arm := GameConfig.CAMERA_DISTANCE
var _cam_probe := SphereShape3D.new()
var _gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity", 9.8)

func _ready() -> void:
	first_person = "fpp" in OS.get_cmdline_user_args()
	collision_layer = GameConfig.LAYER_PLAYER
	collision_mask = GameConfig.LAYER_WORLD
	camera_rig.top_level = true
	_cam_probe.radius = 0.2
	camera.fov = GameConfig.CAMERA_FOV
	camera.h_offset = 0.0 if first_person else GameConfig.CAMERA_SHOULDER_OFFSET
	visual.visible = not first_person
	_snap_camera()
	capture_mouse(true)

## Put the player on a marker, facing the marker's -Z.
func place(xf: Transform3D) -> void:
	global_position = xf.origin
	var fwd := -xf.basis.z
	_yaw = atan2(-fwd.x, -fwd.z)
	visual.rotation.y = _yaw
	velocity = Vector3.ZERO
	_snap_camera()

func set_controls_enabled(on: bool) -> void:
	controls_enabled = on
	if is_node_ready():
		interactor.active = on
	capture_mouse(on)

func capture_mouse(on: bool) -> void:
	if on and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		_ignore_motion_until = Time.get_ticks_msec() + 150
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if on else Input.MOUSE_MODE_VISIBLE

func _unhandled_input(ev: InputEvent) -> void:
	if not controls_enabled:
		return
	var captured := Input.mouse_mode == Input.MOUSE_MODE_CAPTURED
	if ev is InputEventMouseMotion and captured:
		if not mouse_look or Time.get_ticks_msec() < _ignore_motion_until:
			return
		_yaw -= ev.relative.x * GameConfig.MOUSE_SENSITIVITY
		_pitch = clampf(_pitch - ev.relative.y * GameConfig.MOUSE_SENSITIVITY,
			deg_to_rad(GameConfig.CAMERA_PITCH_MIN), deg_to_rad(GameConfig.CAMERA_PITCH_MAX))
	elif ev.is_action_pressed("ui_cancel") and captured:
		capture_mouse(false)
		get_viewport().set_input_as_handled()
	elif ev is InputEventMouseButton and ev.pressed and not captured:
		capture_mouse(true)
		get_viewport().set_input_as_handled()

func _physics_process(delta: float) -> void:
	if not is_on_floor():
		velocity.y -= _gravity * delta
	var input := Vector2.ZERO
	if controls_enabled:
		input = Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var dir := Basis(Vector3.UP, _yaw) * Vector3(input.x, 0.0, input.y)
	var speed := GameConfig.SPRINT_SPEED if Input.is_action_pressed("sprint") else GameConfig.WALK_SPEED
	var target := dir * speed
	var horizontal := Vector3(velocity.x, 0.0, velocity.z)
	var rate := GameConfig.ACCELERATION if dir != Vector3.ZERO else GameConfig.DECELERATION
	horizontal = horizontal.move_toward(target, rate * delta)
	velocity.x = horizontal.x
	velocity.z = horizontal.z
	if dir.length_squared() > 0.01:
		var face := atan2(-dir.x, -dir.z)
		visual.rotation.y = lerp_angle(visual.rotation.y, face, 1.0 - exp(-GameConfig.TURN_SPEED * delta))
	var before := global_position
	move_and_slide()
	if position_allowed.is_valid() and not position_allowed.call(global_position):
		global_position = Vector3(before.x, global_position.y, before.z)
		velocity.x = 0.0
		velocity.z = 0.0

func _process(delta: float) -> void:
	var pivot := global_position + Vector3.UP * GameConfig.CAMERA_PIVOT_HEIGHT
	camera_rig.global_position = camera_rig.global_position.lerp(pivot, 1.0 - exp(-25.0 * delta))
	camera_rig.rotation = Vector3(_pitch, _yaw, 0.0)
	_update_arm(delta)

## Camera distance this frame: pulled in at once by walls (sphere cast) and by the facility edge (an open exterior
## door has no wall to hit), eased back out when the view clears.
func _update_arm(delta: float) -> void:
	if first_person:
		camera.position = Vector3.ZERO
		return
	var origin := camera_rig.global_position
	var back := camera_rig.global_basis.z
	var want := GameConfig.CAMERA_DISTANCE
	if position_allowed.is_valid():
		while want > 0.4 and not position_allowed.call(origin + back * want):
			want -= 0.1
	var q := PhysicsShapeQueryParameters3D.new()
	q.shape = _cam_probe
	q.transform = Transform3D(Basis(), origin)
	q.motion = back * want
	q.collision_mask = GameConfig.LAYER_WORLD
	q.exclude = [get_rid()]
	var hit := get_world_3d().direct_space_state.cast_motion(q)
	want = maxf(want * hit[0], 0.25)
	_arm = want if want < _arm else lerpf(_arm, want, 1.0 - exp(-6.0 * delta))
	camera.position = Vector3(0.0, 0.0, _arm)

func _snap_camera() -> void:
	if is_node_ready():
		camera_rig.global_position = global_position + Vector3.UP * GameConfig.CAMERA_PIVOT_HEIGHT
		camera_rig.rotation = Vector3(_pitch, _yaw, 0.0)
		_arm = GameConfig.CAMERA_DISTANCE
		_update_arm(0.0)
