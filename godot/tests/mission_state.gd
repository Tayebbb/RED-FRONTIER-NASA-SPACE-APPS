extends SceneTree

const MissionState = preload("res://state/mission_state.gd")

func _initialize() -> void:
	var state = MissionState.new()
	assert(state.selected_site == "")
	assert(state.is_configuration_locked == false)
	assert(state.set_station_selection("POWER", "RTG"))
	assert(state.power_system == "RTG")
	assert(state.set_station_selection("MOBILITY", "ROCKER_BOGIE"))
	assert(state.mobility_system == "ROCKER_BOGIE")
	assert(state.select_site("Jezero"))
	assert(state.can_lock_configuration())
	state.lock_configuration()
	assert(state.is_configuration_locked)
	assert(not state.set_station_selection("POWER", "SOLAR"))
	print("MISSION_STATE_TEST_PASS")
	quit(0)
