class_name RF01Visual
extends Node3D
## Visual-only driver for the RF-01 Mission Systems Engineer model (assets/characters/rf01/RF01_Engineer.glb).
## Picks Idle / Walk / Run from the velocity of the CharacterBody3D it sits under and scales playback to the
## ground speed. It only reads the body: movement, camera, collision and interaction stay in player.gd.

## Ground speeds the clips were keyed at (art/character/scripts/game_3_rig.py).
const WALK_CLIP_SPEED := 2.27       # m/s
const RUN_CLIP_SPEED := 4.80        # m/s
const IDLE_BELOW := 0.25            # m/s
const BLEND := 0.2                  # s cross-fade between clips

var _body: CharacterBody3D
var _anim: AnimationPlayer
var _clip := ""

func _ready() -> void:
	_body = _find_body()
	_anim = find_child("AnimationPlayer", true, false) as AnimationPlayer
	if _anim == null:
		push_warning("RF01Visual: no AnimationPlayer in the character model")
		return
	for clip in ["Idle", "Walk", "Run"]:
		if _anim.has_animation(clip):
			_anim.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
	_play("Idle", 1.0)

func _find_body() -> CharacterBody3D:
	var n := get_parent()
	while n != null and not (n is CharacterBody3D):
		n = n.get_parent()
	return n as CharacterBody3D

func _process(_delta: float) -> void:
	if _anim == null or _body == null:
		return
	var v := _body.velocity
	v.y = 0.0
	var speed := v.length()
	var run_above := 0.5 * (GameConfig.WALK_SPEED + GameConfig.SPRINT_SPEED)
	if speed < IDLE_BELOW:
		_play("Idle", 1.0)
	elif speed < run_above:
		_play("Walk", clampf(speed / WALK_CLIP_SPEED, 0.6, 1.6))
	else:
		_play("Run", clampf(speed / RUN_CLIP_SPEED, 0.7, 1.4))

func _play(clip: String, rate: float) -> void:
	if _clip != clip and _anim.has_animation(clip):
		_anim.play(clip, BLEND)
		_clip = clip
	_anim.speed_scale = rate
