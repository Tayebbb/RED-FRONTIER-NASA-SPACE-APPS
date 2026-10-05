"""
rf_lightsets.py - switch the facility between LIGHTSET_Day_Operational and LIGHTSET_Launch_Mode.

Lights: a light set is a collection under 04_LIGHTS; Launch Mode holds its own copies of the
Mission Control lights (ambient -30 %) plus the beacon glow. Materials that change between sets
carry 'rf_emit_day' / 'rf_emit_launch' (screens up, fixtures down, beacon lenses on).
Hangar lights are not part of either switch and stay as they are.

Use:  import rf_lightsets; rf_lightsets.apply('Launch_Mode')    (render_cycles.py: RF_LIGHTSET=Launch_Mode)
"""
import bpy

SWITCHED_DAY = 'LIGHTS_MissionControl_Day'
LAUNCH = 'LIGHTSET_Launch_Mode'

def apply(mode='Day_Operational'):
    launch = mode == 'Launch_Mode'
    for name, on in ((SWITCHED_DAY, not launch), (LAUNCH, launch)):
        col = bpy.data.collections.get(name)
        for o in (col.all_objects if col else ()):
            o.hide_render = o.hide_viewport = not on
    for m in bpy.data.materials:
        if 'rf_emit_day' in m and m.node_tree:
            m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value = m['rf_emit_launch' if launch else 'rf_emit_day']
    print('LIGHTSET', mode)
