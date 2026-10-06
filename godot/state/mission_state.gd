class_name MissionState
extends RefCounted

const DEFAULTS := {
	"site": "",
	"science": "CAMERA",
	"power": "RTG",
	"mobility": "ROCKER_BOGIE",
	"comms": "HIGH_GAIN",
}

var selected_site := ""
var science_payload := "CAMERA"
var power_system := "RTG"
var mobility_system := "ROCKER_BOGIE"
var communications_system := "HIGH_GAIN"
var battery_capacity := 100.0
var mass_kg := 850.0
var power_budget := 100.0
var science_score := 50.0
var rover_health := 100.0
var is_configuration_locked := false
var digital_twin_passed := false

func set_station_selection(station: String, selection: String) -> bool:
	if is_configuration_locked:
		return false
	match station:
		"SCIENCE":
			science_payload = selection
		"POWER":
			power_system = selection
		"MOBILITY":
			mobility_system = selection
		"COMMS":
			communications_system = selection
		_:
			return false
	_recalculate()
	return true

func select_site(site: String) -> bool:
	if is_configuration_locked or site.is_empty():
		return false
	selected_site = site
	return true

func can_lock_configuration() -> bool:
	return not is_configuration_locked and not selected_site.is_empty()

func lock_configuration() -> bool:
	if not can_lock_configuration():
		return false
	is_configuration_locked = true
	return true

func run_digital_twin() -> bool:
	digital_twin_passed = can_lock_configuration() and power_budget >= 70.0 and battery_capacity >= 70.0
	return digital_twin_passed

func summary() -> String:
	return "SITE %s | SCI %s | PWR %s | MOB %s | COMMS %s | MASS %.0f kg | POWER %.0f%%" % [
		selected_site if not selected_site.is_empty() else "UNSELECTED",
		science_payload, power_system, mobility_system, communications_system, mass_kg, power_budget]

func _recalculate() -> void:
	mass_kg = 850.0
	power_budget = 100.0
	battery_capacity = 100.0
	if power_system == "SOLAR":
		power_budget += 8.0
		battery_capacity -= 12.0
	if mobility_system == "AUTONOMOUS":
		mass_kg += 35.0
		power_budget -= 14.0
	if science_payload == "SPECTROMETER":
		mass_kg += 24.0
		science_score += 10.0
	if communications_system == "LOW_GAIN":
		power_budget += 4.0
	else:
		mass_kg += 12.0
