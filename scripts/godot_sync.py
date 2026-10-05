"""
godot_sync.py - bring the Blender exports into the Godot project with shared materials (system Python).

  1. RF_MaterialLibrary.glb -> res://shared/. Its textures are extracted once (res://shared/RF_MaterialLibrary_*.png)
     and imported VRAM-compressed (BPTC high quality; BC5/RGTC for normal maps). Its materials are extracted to
     res://shared/materials/<MAT_name>.tres by tools/build_material_library.gd.
  2. Room GLBs (no images) -> res://assets/. Each room's import maps every material, by name, to its shared .tres
     (_subresources / use_external, as the Advanced Import dialog writes it): one resource per material, one
     texture per image, however many rooms use them.
  3. The rover's own textures get the same VRAM compression (import settings only; the asset is untouched).
  4. Door impostors are captured (tools/make_impostors.gd, windowed) and imported compressed; GI caches are cleared.
Old per-room texture copies (RF_<Room>_T_*.png) are removed.

Godot only reimports when an output is missing, so after patching an .import file its outputs are deleted.
Run:  python scripts/godot_sync.py          (after export_material_library.py + export_gltf.py for each room)
"""
import os, re, shutil, subprocess, glob, json, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GODOT = os.environ.get('GODOT_BIN', r"D:\Godot_v4.7-stable_win64.exe\Godot_v4.7-stable_win64_console.exe")   # set GODOT_BIN elsewhere
PROJ = os.path.join(ROOT, 'godot'); EXP = os.path.join(ROOT, 'export', 'godot')
ROOMS = ['Briefing', 'Corridor01', 'MarsIntel', 'Corridor02', 'Hangar', 'MissionControl']
SHARED = os.path.join(PROJ, 'shared'); ASSETS = os.path.join(PROJ, 'assets')

def run_import(tag):
    r = subprocess.run([GODOT, '--headless', '--path', PROJ, '--import'], capture_output=True, text=True, errors='replace')
    log = r.stdout + r.stderr
    open(os.path.join(PROJ, 'logs', f'sync_{tag}.log'), 'w', encoding='utf-8').write(log)
    errs = [l for l in log.splitlines() if 'ERROR' in l or 'WARNING' in l]
    print(f'IMPORT {tag}: {len(errs)} errors/warnings'); [print('  ', e) for e in errs[:12]]
    return errs

def patch_import(path, params):
    """Set key=value pairs in the [params] section of a .import file, then delete its outputs (forces reimport)."""
    txt = open(path, encoding='utf-8').read()
    for k, v in params.items():
        line = f'{k}={v}'
        txt, n = re.subn(rf'^{re.escape(k)}=.*$', line.replace('\\', '\\\\'), txt, flags=re.M)
        if n == 0: txt = txt.replace('[params]\n', f'[params]\n\n{line}\n', 1)
    open(path, 'w', encoding='utf-8').write(txt)
    m = re.search(r'^dest_files=\[(.*)\]$', txt, flags=re.M)
    for dest in re.findall(r'"res://([^"]+)"', m.group(1) if m else ''):
        p = os.path.join(PROJ, dest.replace('/', os.sep))
        if os.path.exists(p): os.remove(p)

def set_subresources(path, names):
    """Map every material of a room to res://shared/materials/<name>.tres (replaces any _subresources block)."""
    txt = open(path, encoding='utf-8').read()
    txt = re.sub(r'^_subresources=\{\}\n|^_subresources=\{\n.*?^\}\n', '', txt, flags=re.M | re.S)
    entry = '"{n}": {{\n"use_external/enabled": true,\n"use_external/path": "res://shared/materials/{n}.tres"\n}}'
    body = ',\n'.join(entry.format(n=n) for n in names)
    txt = txt.replace('[params]\n', '[params]\n\n_subresources={\n"materials": {\n' + body + '\n}\n}\n', 1)
    open(path, 'w', encoding='utf-8').write(txt)

TEX_VRAM = {'compress/mode': 2, 'compress/high_quality': 'true', 'mipmaps/generate': 'true'}

def vram(pngs):
    for p in pngs:
        normal = bool(re.search(r'_n\.|Normal', os.path.basename(p)))
        patch_import(p + '.import', dict(TEX_VRAM, **{'compress/normal_map': 1 if normal else 0}))

def main():
    os.makedirs(os.path.join(SHARED, 'materials'), exist_ok=True); os.makedirs(os.path.join(PROJ, 'logs'), exist_ok=True)
    # remove per-room texture copies and stale room imports
    for p in set(glob.glob(os.path.join(ASSETS, 'RF_*_T_*.png*'))):
        os.remove(p)
    # 1. material library
    shutil.copy2(os.path.join(EXP, 'RF_MaterialLibrary.glb'), SHARED)
    shutil.copy2(os.path.join(EXP, 'RF_Route.json'), ASSETS)
    for r in ROOMS:
        shutil.copy2(os.path.join(EXP, f'RF_{r}.glb'), ASSETS); shutil.copy2(os.path.join(EXP, f'RF_{r}_lights.json'), ASSETS)
    run_import('pass1_defaults')
    lib_tex = sorted(glob.glob(os.path.join(SHARED, 'RF_MaterialLibrary_*.png')))
    vram(lib_tex)
    patch_import(os.path.join(SHARED, 'RF_MaterialLibrary.glb.import'), {'meshes/generate_lods': 'false', 'meshes/create_shadow_meshes': 'false'})
    run_import('pass2_library')
    r = subprocess.run([GODOT, '--headless', '--path', PROJ, '--script', 'res://tools/build_material_library.gd'],
                       capture_output=True, text=True, errors='replace')
    print(*[l for l in (r.stdout + r.stderr).splitlines() if 'MATLIB' in l or 'ERROR' in l][:10], sep='\n')
    shared = sorted(glob.glob(os.path.join(SHARED, 'materials', '*.tres')))
    print(f'LIBRARY materials={len(shared)} textures={len(lib_tex)}')
    # 2. rooms resolve to the shared materials by name
    for r in ROOMS:
        names = json.load(open(os.path.join(EXP, f'RF_{r}_lights.json')))['materials']
        missing = [n for n in names if not os.path.exists(os.path.join(SHARED, 'materials', f'{n}.tres'))]
        if missing: print(f'MISSING shared material for {r}:', missing)
        set_subresources(os.path.join(ASSETS, f'RF_{r}.glb.import'), names)
        patch_import(os.path.join(ASSETS, f'RF_{r}.glb.import'), {'gltf/embedded_image_handling': 0})
    # 3. rover textures: same compression
    vram(sorted(glob.glob(os.path.join(ASSETS, 'RF01_Rover_*.png')) + glob.glob(os.path.join(ASSETS, 'RF01_Rover_*.jpg'))))
    patch_import(os.path.join(ASSETS, 'RF01_Rover.glb.import'), {})
    errs = run_import('pass3_rooms')
    # 4. door impostors (needs a window: renders the approved view through each room's entrance), VRAM-compressed
    for p in glob.glob(os.path.join(ASSETS, '*_voxelgi.res')): os.remove(p)          # GI caches rebake on first load
    r = subprocess.run([GODOT, '--path', PROJ, '--script', 'res://tools/make_impostors.gd'], capture_output=True, text=True, errors='replace')
    print(*[l for l in (r.stdout + r.stderr).splitlines() if 'IMPOSTOR' in l or 'SCRIPT' in l], sep='\n')
    run_import('pass4_impostors_defaults')
    vram(sorted(glob.glob(os.path.join(ASSETS, 'RF_Impostor_*.png'))))
    errs += run_import('pass4_impostors')
    print(f'SYNC_OK rooms={len(ROOMS)} shared_materials={len(shared)} shared_textures={len(lib_tex)}')
    return 0 if not errs else 1

if __name__ == '__main__':
    sys.exit(main())
