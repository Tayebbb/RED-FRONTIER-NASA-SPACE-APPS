"""Verify that the canonical art rover is installed at both runtime paths."""
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art" / "export" / "rover" / "perseverance" / "perseverance_rover.glb"
RUNTIME_PATHS = (ROOT / "assets" / "rover" / "RF01_Rover.glb",
                 ROOT / "godot" / "assets" / "RF01_Rover.glb")
MANIFEST = ROOT / "godot" / "assets" / "RF_Hangar_lights.json"
REQUIRED = {"SM_Chassis", "SM_Mast", "SM_MMRTG", "SM_RoboticArm_StaticPose",
            "SM_Wheel_FL", "SM_Wheel_FR", "SM_Wheel_ML", "SM_Wheel_MR",
            "SM_Wheel_RL", "SM_Wheel_RR"}


def gltf_json(path):
    data = path.read_bytes()
    _, _, total = struct.unpack_from("<III", data, 0)
    offset = 12
    while offset < total:
        size, chunk_type = struct.unpack_from("<II", data, offset)
        offset += 8
        chunk = data[offset:offset + size]
        offset += size
        if chunk_type == 0x4E4F534A:
            return json.loads(chunk.decode("utf-8"))
    raise RuntimeError(f"GLB JSON chunk missing: {path}")


def main():
    if not SOURCE.is_file():
        raise SystemExit(f"FAIL missing canonical source: {SOURCE}")
    source_json = gltf_json(SOURCE)
    source_names = {node.get("name") for node in source_json.get("nodes", [])}
    missing = REQUIRED - source_names
    if missing:
        raise SystemExit(f"FAIL canonical source missing nodes: {sorted(missing)}")
    for runtime in RUNTIME_PATHS:
        if not runtime.is_file():
            raise SystemExit(f"FAIL missing runtime rover: {runtime}")
        runtime_json = gltf_json(runtime)
        runtime_names = {node.get("name") for node in runtime_json.get("nodes", [])}
        if not REQUIRED <= runtime_names:
            raise SystemExit(f"FAIL runtime rover missing required nodes: {runtime}")
        if len(runtime_json.get("meshes", [])) != len(source_json.get("meshes", [])):
            raise SystemExit(f"FAIL runtime mesh count differs from canonical source: {runtime}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("rover", {}).get("asset") != "RF01_Rover.glb":
        raise SystemExit("FAIL Hangar manifest does not reference RF01_Rover.glb")
    print("ROVER_INTEGRATION_PASS")
    print(f"source_bytes={SOURCE.stat().st_size} nodes={len(source_json.get('nodes', []))}")
    print(f"runtime_paths={len(RUNTIME_PATHS)} manifest_asset=RF01_Rover.glb")


if __name__ == "__main__":
    main()
