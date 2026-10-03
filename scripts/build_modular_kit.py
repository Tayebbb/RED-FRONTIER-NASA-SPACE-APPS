"""
build_modular_kit.py - the modular kit as a reviewable catalog: blender/RF_Kit.blend.

Each piece lives in its own collection (KIT/<piece>) at the world origin, ready to link or
instance. A lineup copy is laid out on a grid with labels for the kit sheet render.
The facility builders call the same rf_kit generators, so the catalog never drifts from use.

Only the pieces the Hangar needs exist yet (Phase 3 rule: do not overbuild). Room-specific
pieces (desks, chairs, meeting table, stairs, railing, server rack...) are added in Phase 5.

Run:  blender -b --factory-startup --python scripts/build_modular_kit.py
"""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(__file__))
import rf_lib as rf, rf_kit as kit, rf_materials as rm

rf.reset_scene()
L = rm.build()
PIECES = [   # (name, builder, footprint width for the lineup)
    ('MOD_Cladding_Bay4p4',   lambda c: kit.cladding('MOD_Cladding_Bay4p4', 4.4, 10.0, L, c), 5.0),
    ('MOD_Cladding_Bay2p2',   lambda c: kit.cladding('MOD_Cladding_Bay2p2', 2.2, 10.0, L, c), 2.8),
    ('MOD_Column',            lambda c: kit.column('MOD_Column', 10.0, L, c), 1.4),
    ('MOD_Beam_Truss18',      lambda c: kit.truss('MOD_Beam_Truss18', 18.0, L, c), 19.0),
    ('PROP_HighBayLight',     lambda c: kit.high_bay_light('PROP_HighBayLight', L, c), 3.0),
    ('PROP_LargeDisplay',     lambda c: kit.display_frame('PROP_LargeDisplay', 2.4, 1.35, L['screen'], L, c), 3.0),
    ('PROP_ControlConsole',   lambda c: kit.console('PROP_ControlConsole', L, c), 2.2),
    ('PROP_StationBayFrame',  lambda c: kit.bay_frame('PROP_StationBayFrame', L, c), 2.6),
    ('PROP_EquipmentCabinet', lambda c: kit.cabinet('PROP_EquipmentCabinet', L, c), 1.2),
    ('PROP_ToolCart',         lambda c: kit.tool_cart('PROP_ToolCart', L, c), 1.4),
    ('PROP_CableReel',        lambda c: kit.cable_reel('PROP_CableReel', L, c), 1.2),
    ('PROP_SafetyStanchion',  lambda c: kit.stanchion('PROP_SafetyStanchion', L, c), 0.8),
    ('HERO_Turntable',        lambda c: kit.turntable('HERO_Turntable', 3.25, 0.12, L, c), 7.4),
    ('PROP_ServicePort',      lambda c: kit.service_port('PROP_ServicePort', L, c), 0.8),
    ('PROP_FloorHatch',       lambda c: kit.hatch('PROP_FloorHatch', L, c), 1.2),
]
lineup = rf.collection('KIT_LINEUP'); x = 0.0
label = rf.create_material('KIT_Label', '#2b2e33')
for name, build, w in PIECES:
    col = rf.collection(f'KIT/{name}')
    src = build(col)
    dup = bpy.data.objects.new(f'{name}_Lineup', src.data); lineup.objects.link(dup)
    for m in src.modifiers:
        n = dup.modifiers.new(m.name, m.type)
        for k in ('width', 'segments', 'limit_method', 'angle_limit', 'harden_normals', 'keep_sharp'):
            if hasattr(m, k): setattr(n, k, getattr(m, k))
    dup.location = (x + w / 2, 0, 0)
    rf.create_text_placeholder(f'{name}_Label', name, (x + w / 2, -2.2, 0.01), 'N', 0.22, lineup, label, flat=True)
    x += w + 0.6
cam = rf.create_camera('CAM_KitSheet', (x / 2, -26.0, 14.0), (x / 2, 0, 2.0), lineup, lens=26)
bpy.context.scene.camera = cam
bpy.context.scene.world = bpy.data.worlds.new('W')
rf.save(os.path.join(rf.ROOT, 'blender', 'RF_Kit.blend'))
print('KIT_OK pieces=', len(PIECES))
