class_name GameConfig
## Every tunable gameplay number and mission text in one place. Change values here, not in the systems.

## --- Player and camera --------------------------------------------------------------------------------------
const WALK_SPEED := 3.2               # m/s
const SPRINT_SPEED := 5.5             # m/s, Shift
const ACCELERATION := 14.0            # m/s² toward the target speed
const DECELERATION := 18.0            # m/s² back to rest
const TURN_SPEED := 12.0              # how fast the body turns to face its movement (rad/s-ish, exponential)
const MOUSE_SENSITIVITY := 0.0025     # rad per pixel
const CAMERA_PITCH_MIN := -70.0       # degrees (looking down)
const CAMERA_PITCH_MAX := 35.0        # degrees (looking up)
const CAMERA_DISTANCE := 3.2          # m behind the shoulder; shortened near walls
const CAMERA_PIVOT_HEIGHT := 1.55     # m above the feet
const CAMERA_SHOULDER_OFFSET := 0.35  # m to the right
const CAMERA_FOV := 65.0

## --- Facility -----------------------------------------------------------------------------------------------
const PLAYER_START_MARKER := "PLAYER_Start"
const PLAYER_START_ROOM := "Briefing"
const PLAYER_START_FALLBACK := Vector3(0.0, 0.0, -1.2)      # PLAYER_Start in RF_Briefing.glb, if the marker is missing
## The player stays inside the union of the room footprints, padded by this much so door thresholds (the 0.25 m
## wall between two footprints) connect. Stops the player walking out of an open exterior door into the void.
const FOOTPRINT_PAD := 0.35

## Physics layers (named in project.godot).
const LAYER_WORLD := 1
const LAYER_PLAYER := 2
const LAYER_INTERACTABLE := 4         # bit value of layer 3

## --- Interactions -------------------------------------------------------------------------------------------
## Keyed by the INT_<id> marker name exported from Blender. A marker becomes usable only when a gameplay system
## registers a handler for its id (InteractionManager.register_handler); the rest stay silent until then.
const INTERACT_RADIUS := 1.6          # m, default reach around a marker
const INTERACTIONS := {
	"BriefingTable":     {"label": "Mission Briefing", "radius": 1.8},
	"LandingSystem":     {"label": "Landing Site Analysis"},
	"LandingSiteA":      {"label": "Landing Site A", "radius": 0.8},
	"LandingSiteB":      {"label": "Landing Site B", "radius": 0.8},
	"LandingSiteC":      {"label": "Landing Site C", "radius": 0.8},
	"MissionConfig":     {"label": "RF-01 Configuration", "prompt": "CONFIGURE RF-01"},
	"Station_SCIENCE":   {"label": "Science Station"},
	"Station_POWER":     {"label": "Power Station"},
	"Station_MOBILITY":  {"label": "Mobility Station"},
	"Station_COMMS":     {"label": "Comms Station"},
	"DigitalTwin":       {"label": "Digital Twin"},
	"LaunchConsole":     {"label": "Launch Console"},
}

## --- Objectives ---------------------------------------------------------------------------------------------
const OBJECTIVES := {
	&"attend_briefing": "Attend the Mission Briefing",
	&"proceed_mars_intel": "Proceed to Mars Intelligence",
	&"proceed_engineering_hangar": "Proceed to Engineering Hangar",
	&"run_digital_twin": "Run the Digital Twin",
}

## --- Mission text -------------------------------------------------------------------------------------------
const BRIEFING := {
	"mission": "MISSION RF-01",
	"objective": "Investigate evidence of ancient water.",
	"priorities": ["Collect valuable science.", "Bring RF-01 home."],
	"warning": "Every engineering decision you make before launch may affect the mission on Mars.",
}

## --- Engineering rules ---------------------------------------------------------------------------------------
## Red Frontier Rules and Scoring v1.0 is authoritative (decided 2026-10-06); the other sets are kept only as a record
## of what the older documents said. Nothing enforces these limits yet: that is the rover configuration task.
const RULE_CANDIDATES := {
	"rules_and_scoring_v1_0": {"mass_limit_kg": 260, "budget_limit": 400, "instrument_slots": 3,
		"note": "Red Frontier Rules and Scoring v1.0 (4 Oct 2026): whole-build limits, costs per part sheet"},
	"design_brief": {"mass_limit_kg": 3800, "budget_limit_musd": 750, "power_units": 100, "instrument_slots": 3,
		"note": "Mission: Red Frontier brief, challenge-fit table"},
	"facility_plan": {"payload_limit_kg": [900, 1100], "budget_musd": [150, 250], "instrument_slots": 3,
		"note": "docs/PLAN.md: launch vehicle sets payload and budget"},
}
const ACTIVE_RULES := {"source": "rules_and_scoring_v1_0", "mass_limit": 260, "budget_limit": 400, "power_limit": null,
	"instrument_slots": 3}
