import bpy
import math
from mathutils import Quaternion, Vector


def begin(name, replace=False):
    obj = bpy.data.objects[name]
    return {'obj': obj,
            'vertices': [] if replace else [tuple(vertex.co) for vertex in obj.data.vertices],
            'faces': [] if replace else [tuple(face.vertices) for face in obj.data.polygons],
            'materials': list(obj.data.materials),
            'assignments': [] if replace else [face.material_index for face in obj.data.polygons]}


def add(mesh, points, faces, material):
    offset = len(mesh['vertices'])
    mesh['vertices'].extend(tuple(point) for point in points)
    mesh['faces'].extend(tuple(offset + index for index in face) for face in faces)
    mat = bpy.data.materials[material]
    if mat not in mesh['materials']:
        mesh['materials'].append(mat)
    mesh['assignments'].extend([mesh['materials'].index(mat)] * len(faces))


def box(mesh, center, size, material, rotation=None):
    points = []
    for signs in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),
                  (1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]:
        point = Vector(tuple(signs[axis] * size[axis] / 2 for axis in range(3)))
        if rotation is not None:
            point = rotation @ point
        points.append(Vector(center) + point)
    add(mesh, points, [(0,4,6,2),(1,3,7,5),(0,1,5,4),
                      (2,6,7,3),(0,2,3,1),(4,5,7,6)], material)


def cylinder(mesh, start, end, radius, material, segments=12):
    start, end = Vector(start), Vector(end)
    rotation = (end - start).to_track_quat('Z', 'Y')
    points = []
    for center in [start, end]:
        for index in range(segments):
            angle = index * math.tau / segments
            points.append(center + rotation @ Vector((radius * math.cos(angle), radius * math.sin(angle), 0)))
    faces = [tuple(reversed(range(segments))), tuple(range(segments, segments * 2))]
    faces.extend((index, (index+1)%segments, (index+1)%segments+segments, index+segments) for index in range(segments))
    add(mesh, points, faces, material)


def beam(mesh, start, end, width, material, depth=None):
    start, end = Vector(start), Vector(end)
    box(mesh, (start+end)/2, (width, depth or width, (end-start).length), material,
        (end-start).to_track_quat('Z', 'Y'))


def finish(mesh):
    obj = mesh['obj']
    old = obj.data
    data = bpy.data.meshes.new(obj.name + '_QA')
    data.from_pydata(mesh['vertices'], [], mesh['faces'])
    for material in mesh['materials']:
        data.materials.append(material)
    for face, assignment in zip(data.polygons, mesh['assignments']):
        face.material_index = assignment
    data.update()
    obj.data = data
    if old.users == 0:
        bpy.data.meshes.remove(old)


METAL = 'MAT_Metal_Grey'
WHITE = 'MAT_Body_White'
DARK = 'MAT_Rubber_Black'
LENS = 'MAT_Lens'
PANEL = 'MAT_Panel_Blue'
ACCENT = 'MAT_Accent_Rust'


def build_wheel(name, reinforced=False):
    mesh = begin(name, replace=True)
    half_width = 0.21 if reinforced else 0.16
    cylinder(mesh, (-half_width+.012,0,0),(half_width-.012,0,0),.249,METAL,24)
    for side in [-1,1]:
        cylinder(mesh, (side*(half_width-.018),0,0),(side*half_width,0,0),.11,DARK,12)
        cylinder(mesh, (side*(half_width-.016),0,0),(side*(half_width-.003),0,0),.074,METAL,12)
        for index in range(6):
            angle = index*math.tau/6
            center = Vector((side*(half_width-.005),.09*math.cos(angle),.09*math.sin(angle)))
            cylinder(mesh, center,center+Vector((side*.004,0,0)),.008,WHITE,6)
    for index in range(16):
        angle = index*math.tau/16
        for side in [-1,1]:
            points = []
            for radius in [.247,.2625]:
                for axial, skew in [(0,0),(side*half_width,.1)]:
                    for edge in [-1,1]:
                        phase = angle + skew + edge*(.022 if reinforced else .016)
                        points.append((axial,radius*math.cos(phase),radius*math.sin(phase)))
                add(mesh, points,[(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)],METAL)
            maximum = max(abs(point[axis]) for point in mesh['vertices'] for axis in [1,2])
    ratio = .2625/maximum
    mesh['vertices'] = [(point[0],point[1]*ratio,point[2]*ratio) for point in mesh['vertices']]
    finish(mesh)


def build_suspension(name, side):
    mesh = begin(name, replace=True)
    rocker = Vector((side*.96,-.35,.73))
    bogie = Vector((side*.96,.62,.49))
    front = Vector((side*.96,-1.2375,.264))
    middle = Vector((side*.96,0,.264))
    rear = Vector((side*.96,1.2375,.264))
    beam(mesh, (side*.58,-.35,.73),rocker,.12,METAL)
    for start,end in [(rocker,front),(rocker,bogie),(bogie,middle),(bogie,rear)]:
        beam(mesh, start,end,.105,METAL,.075)
    for pivot in [rocker,bogie,front,middle,rear]:
        cylinder(mesh, pivot-Vector((.067,0,0)),pivot+Vector((.067,0,0)),.071,METAL,12)
        cylinder(mesh, pivot-Vector((.072,0,0)),pivot+Vector((.072,0,0)),.027,WHITE,8)
    for wheel in [front,middle,rear]:
        cylinder(mesh, wheel,(side*1.075,wheel.y,wheel.z),.043,METAL,12)
        if wheel != middle:
                cylinder(mesh, wheel-Vector((0,0,.05)),wheel+Vector((0,0,.05)),.05,DARK,8)
            finish(mesh)


def refine_mobility():
    for name in ['Wheel_Standard','SM_Wheel_FL','SM_Wheel_FR','SM_Wheel_ML',
                 'SM_Wheel_MR','SM_Wheel_RL','SM_Wheel_RR']:
        build_wheel(name)
    build_wheel('Wheel_Reinforced',True)
    build_suspension('SM_Arm_Bogie_L',-1)
    build_suspension('SM_Arm_Bogie_R',1)
    chassis = begin('SM_Chassis')
    for side in [-1,1]:
        cylinder(chassis, (side*.58,-.35,.73),(side*.68,-.35,.73),.105,METAL,12)
    finish(chassis)
    for name, metallic, roughness in [(METAL,.8,.36),(WHITE,.12,.52),
                                     (DARK,0,.8),(LENS,.15,.12),(PANEL,.3,.27),(ACCENT,.15,.5)]:
        material = bpy.data.materials[name]
        node = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
        node.inputs['Metallic'].default_value = metallic
        node.inputs['Roughness'].default_value = roughness


def refine_science():
    mast = begin('SM_Mast')
    cylinder(mast, (0,-.176,2.13),(0,-.207,2.13),.045,METAL,12)
    cylinder(mast, (0,-.207,2.13),(0,-.209,2.13),.033,LENS,12)
    box(mast, (0,-.19,2.187),(.17,.08,.016),WHITE)
    finish(mast)
    radar = begin('Inst_Radar',True)
    box(radar, (0,0,.015),(.4,.4,.03),METAL)
    box(radar, (0,0,.10),(.30,.28,.14),WHITE)
    beam(radar, (.13,.12,.16),(.3,.96,.23),.035,METAL)
    beam(radar, (.3,.96,.23),(.3,.96,-.54),.035,METAL)
    box(radar, (.3,.96,-.56),(.38,.28,.024),DARK)
    for side in [-1,1]:
        points = [(.3+side*.012,.96,-.573),(.3+side*.175,.85,-.573),(.3+side*.175,1.07,-.573)]
        add(radar, points, [(0,1,2)],METAL)
    finish(radar)
    soil = begin('Inst_Soil',True)
    box(soil, (0,0,.025),(.4,.4,.05),METAL)
    box(soil, (0,0,.13),(.28,.28,.18),WHITE)
    shoulder = (0,-.13,.52)
    elbow = (0,-1.12,.54)
    wrist = (0,-1.12,-.84)
    cylinder(soil, (0,-.13,.2),shoulder,.035,METAL,12)
    beam(soil, shoulder,elbow,.07,METAL)
    beam(soil, elbow,wrist,.06,METAL)
    for joint in [shoulder,elbow,wrist]:
        center = Vector(joint)
        cylinder(soil, center-Vector((.06,0,0)),center+Vector((.06,0,0)),.06,WHITE,12)
    cylinder(soil, wrist,(0,-1.12,-1.0),.025,METAL,12)
    finish(soil)
    weather = begin('Inst_Weather',True)
    box(weather, (0,0,.02),(.4,.4,.04),METAL)
    box(weather, (0,0,.1),(.20,.22,.12),WHITE)
    beam(weather, (0,0,.16),(.39,0,.38),.035,METAL)
    for height in [.34,.37,.40,.43]:
        cylinder(weather, (.39,0,height),(.39,0,height+.014),.06,WHITE,12)
    cylinder(weather, (.39,0,.32),(.39,0,.46),.018,METAL,8)
    beam(weather, (.25,0,.30),(.25,-.15,.30),.014,METAL)
    cylinder(weather, (.25,-.15,.28),(.25,-.15,.33),.019,DARK,8)
    finish(weather)
    radiation = begin('Inst_Radiation',True)
    box(radiation, (0,0,.02),(.4,.4,.04),METAL)
    box(radiation, (0,0,.12),(.28,.28,.16),WHITE)
    cylinder(radiation, (0,0,.20),(0,0,.27),.068,METAL,12)
    cylinder(radiation, (0,0,.27),(0,0,.275),.054,LENS,12)
    finish(radiation)
    for name in ['Inst_Camera','Inst_Spectrometer']:
        mesh = begin(name)
        for side in [-1,1]:
            cylinder(mesh, (side*.16,-.16,.028),(side*.16,-.16,.037),.012,METAL,6)
        if name == 'Inst_Spectrometer':
            mesh['vertices'] = [(point[0]+.25,point[1],point[2]+.15) for point in mesh['vertices']]
            beam(mesh, (0,0,.015),(.25,0,.16),.035,METAL)
        finish(mesh)


def refine_systems():
    for name, centers, width, depth in [('Solar_Light',[0],.58,.46),
                                      ('Solar_Large',[-.49,.49],.86,.62)]:
        mesh = begin(name,True)
        offset = .5 if name == 'Solar_Large' else 0
        box(mesh, (0,0,.045),(.32,.30,.08),WHITE)
        cylinder(mesh, (0,0,.07),(0,offset,.38),.027,METAL,12)
        cylinder(mesh, (-.09,offset,.40),(.09,offset,.40),.025,METAL,12)
        if len(centers)>1:
            beam(mesh, (-.49,offset,.40),(.49,offset,.40),.035,METAL)
        for center in centers:
            box(mesh, (center,offset,.417),(width+.018,depth+.018,.026),METAL)
            box(mesh, (center,offset,.433),(width,depth,.007),PANEL)
            for index in range(1,9):
                box(mesh, (center-width/2+index*width/9,offset,.438),(.003,depth,.003),METAL)
            for index in [-1,1]:
                box(mesh, (center,offset+index*depth/6,.438),(width,.003,.003),METAL)
        finish(mesh)
    for name in ['Battery_Standard','Battery_Extended']:
        mesh = begin(name)
        centers = [0] if name.endswith('Standard') else [-.21,.21]
        for center in centers:
            for side in [-1,1]:
                box(mesh, (center+side*.20,0,.375),(.006,.39,.009),DARK)
                box(mesh, (center,side*.195,.375),(.40,.006,.009),DARK)
        if name == 'Battery_Extended':
            mesh['vertices'] = [(point[0],point[1]-.04,point[2]) for point in mesh['vertices']]
        finish(mesh)
    for name in ['Shield_Minimal','Shield_Standard','Shield_Heavy']:
        mesh = begin(name)
        if name != 'Shield_Minimal':
            mesh['vertices'][:96] = [(point[0],point[1]*1.35,point[2]) for point in mesh['vertices'][:96]]
            mesh['vertices'][96:144] = [(point[0],point[1]+(.25 if point[1]>0 else -.25),point[2]) for point in mesh['vertices'][96:144]]
        points = [Vector(point) for point in mesh['vertices']]
        lower = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
        upper = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
        for index in [-1,1]:
            position = Vector((lower.x,index*.48,lower.z+.06))
            box(mesh, position,(.065,.12,.026),METAL)
            cylinder(mesh, position,(position.x,position.y,position.z+.025),.013,WHITE,6)
        finish(mesh)
    antenna = begin('Antenna_Std',True)
    for center in [(0,0,0)]:
        center = Vector(center)
        box(antenna, center+Vector((0,0,.035)),(.16,.16,.05),METAL)
        cylinder(antenna, center+Vector((0,0,.06)),center+Vector((0,0,.135)),.021,WHITE,10)
        cylinder(antenna, center+Vector((0,0,.135)),center+Vector((0,0,.995)),.007,METAL,8)
        cylinder(antenna, center+Vector((0,0,.985)),center+Vector((0,0,1.0)),.01,DARK,8)
    finish(antenna)
    dish = begin('Antenna_HighGain',True)
    box(dish, (0,0,.025),(.24,.24,.05),METAL)
    cylinder(dish, (0,0,.05),(0,0,.23),.045,METAL,12)
    cylinder(dish, (-.07,0,.23),(.07,0,.23),.045,WHITE,12)
    points = [(0,0,.245)]
    for radius in [.17,.34]:
        for index in range(24):
            angle = index*math.tau/24
            points.append((radius*math.cos(angle),radius*math.sin(angle),.245+.12*(radius/.34)**2))
    faces = [(0,1+index,1+(index+1)%24) for index in range(24)]
    faces.extend((1+index,25+index,25+(index+1)%24,1+(index+1)%24) for index in range(24))
    add(dish, points,faces,METAL)
    for index in range(3):
        angle = index*math.tau/3
        beam(dish, (.28*math.cos(angle),.28*math.sin(angle),.327),(0,0,.505),.008,METAL)
    cylinder(dish, (0,0,.48),(0,0,.525),.025,WHITE,10)
    cylinder(dish, (0,0,.478),(0,0,.484),.018,DARK,10)
    finish(dish)
    nuclear = begin('Power_Nuclear',True)
    box(nuclear, (0,0,.025),(.40,.32,.05),METAL)
    cylinder(nuclear, (0,0,.05),(0,0,.21),.035,METAL,12)
    beam(nuclear, (0,0,.21),(0,-.65,.21),.045,METAL)
    box(nuclear, (0,-.65,.205),(.28,.28,.03),METAL)
    cylinder(nuclear, (0,-.65,.26),(0,-.65,.64),.11,METAL,16)
    for index in range(8):
        angle = index*math.tau/8
        rotation = Quaternion((0,0,1),angle)
        for height in [.325,.45,.575]:
            box(nuclear, (.17*math.cos(angle),-.65+.17*math.sin(angle),height),(.12,.018,.11),METAL,rotation)
    cylinder(nuclear, (0,-.65,.24),(0,-.65,.26),.13,WHITE,16)
    cylinder(nuclear, (0,-.65,.64),(0,-.65,.66),.13,WHITE,16)
    finish(nuclear)


if '_QA' in bpy.data.objects['SM_Wheel_FL'].data.name:
    raise RuntimeError('Refinement is a one-time migration. Load red_frontier_rover_preqa.blend first.')

refine_mobility()
refine_science()
refine_systems()