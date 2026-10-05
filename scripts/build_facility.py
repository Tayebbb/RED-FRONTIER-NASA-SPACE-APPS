"""
build_facility.py - the whole facility, as far as it is finished: rebuild RF_Facility.blend from empty.

  Engineering Hangar   near-final, LOCKED (build_hangar.py)
  Mission Control      near-final, Phase 5 (build_mission_control.py)
  Mars Intelligence    near-final, Phase 5 (build_mars_intelligence.py)
  Briefing             near-final, Phase 5 (build_briefing.py), LOCKED
  Corridors 01 + 02    Phase 5 (build_corridors.py)

Each Phase 5 room is listed in ROOMS: its greybox is skipped and its builder runs after the Hangar,
so the Hangar's shared helpers, materials and walls are in place.

Textures first when they change:  python scripts/gen_textures.py mc | intel | brief | corridor
Run:  blender -b --factory-startup --python scripts/build_facility.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import rf_lib as rf, build_hangar as bh, build_mission_control as mc, build_mars_intelligence as mi, build_briefing as br, build_corridors as co
import bpy

ROOMS = {'MissionControl': mc.build, 'MarsIntel': mi.build, 'Briefing': br.build, 'Corridor01': None, 'Corridor02': co.build}   # one builder makes both corridors

def main():
    L = bh.main(save=False, skip=tuple(ROOMS))
    for build in ROOMS.values():
        if build: build(L)
    out = os.path.join(rf.ROOT, 'blender', 'RF_Facility.blend')
    rf.save(out)
    print('FACILITY_OK objects=', len(bpy.data.objects), 'saved', out)

if __name__ == '__main__':
    main()
