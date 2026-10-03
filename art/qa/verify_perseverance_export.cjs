const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const filePath = path.resolve(__dirname, '../export/rover/perseverance/perseverance_rover.glb');
const file = fs.readFileSync(filePath);
assert.equal(file.readUInt32LE(0), 0x46546c67, 'GLB magic');
assert.equal(file.readUInt32LE(4), 2, 'GLB version');
assert.equal(file.readUInt32LE(8), file.length, 'GLB file length');
const jsonLength = file.readUInt32LE(12);
assert.equal(file.readUInt32LE(16), 0x4e4f534a, 'JSON chunk');
const document = JSON.parse(file.subarray(20, 20 + jsonLength).toString('utf8'));
const binaryHeader = 20 + jsonLength;
assert.equal(file.readUInt32LE(binaryHeader + 4), 0x004e4942, 'BIN chunk');
const binary = file.subarray(binaryHeader + 8);
assert.equal(file.readUInt32LE(binaryHeader), binary.length, 'BIN length');
assert.equal(document.asset.version, '2.0');
assert.equal((document.animations || []).length, 0, 'static rover has no animations');
assert.equal((document.cameras || []).length, 0, 'export excludes cameras');
assert.equal((document.lights || []).length, 0, 'export excludes lights');

const nodeNames = new Set((document.nodes || []).map(node => node.name).filter(Boolean));
const requiredNodes = [
  'SM_Chassis', 'SM_Mast', 'SM_MMRTG', 'SM_RIMFAX_Bowtie_Underside', 'SM_RoboticArm_StaticPose',
  'SM_MEDA_WindSensor_Assembly',
  'SM_Antenna_XBand_HighGain', 'SM_Antenna_UHF_Whip', 'SM_Antenna_XBand_LowGain',
  'SM_Wheel_FL', 'SM_Wheel_FR', 'SM_Wheel_ML', 'SM_Wheel_MR', 'SM_Wheel_RL', 'SM_Wheel_RR',
];
for (const name of requiredNodes) assert.equal(nodeNames.has(name), true, `required node ${name}`);
for (const name of nodeNames) {
  assert.equal(/^(Solar_|Battery_|Shield_|Antenna_HighGain|Antenna_Std)/.test(name), false, `non-flight option excluded: ${name}`);
}

const materials = document.materials || [];
const colorTextureMaterials = materials.filter(material => material.pbrMetallicRoughness?.baseColorTexture).length;
const normalTextureMaterials = materials.filter(material => material.normalTexture).length;
const roughnessTextureMaterials = materials.filter(material => material.pbrMetallicRoughness?.metallicRoughnessTexture).length;
assert.equal((document.images || []).length >= 10, true, 'embedded texture images');
assert.equal(colorTextureMaterials >= 6, true, 'base-color image textures');
assert.equal(normalTextureMaterials >= 5, true, 'normal maps');
assert.equal(roughnessTextureMaterials >= 5, true, 'metallic-roughness maps');

let triangles = 0;
let primitiveCount = 0;
for (const mesh of document.meshes || []) {
  for (const primitive of mesh.primitives || []) {
    primitiveCount += 1;
    assert.equal(primitive.mode ?? 4, 4, `${mesh.name}: triangle primitive`);
    const positionAccessor = document.accessors[primitive.attributes.POSITION];
    const normalAccessor = document.accessors[primitive.attributes.NORMAL];
    const uvAccessor = document.accessors[primitive.attributes.TEXCOORD_0];
    assert.equal(positionAccessor?.type, 'VEC3', `${mesh.name}: positions`);
    assert.equal(normalAccessor?.type, 'VEC3', `${mesh.name}: normals`);
    assert.equal(uvAccessor?.type, 'VEC2', `${mesh.name}: UV coordinates`);
    assert.equal(positionAccessor.count > 0, true, `${mesh.name}: non-empty positions`);
    assert.equal(normalAccessor.count, positionAccessor.count, `${mesh.name}: normal count`);
    assert.equal(uvAccessor.count, positionAccessor.count, `${mesh.name}: UV count`);
    const positionView = document.bufferViews[positionAccessor.bufferView];
    const positionOffset = (positionView.byteOffset || 0) + (positionAccessor.byteOffset || 0);
    const stride = positionView.byteStride || 12;
    for (let index = 0; index < positionAccessor.count; index++) {
      for (let axis = 0; axis < 3; axis++) {
        assert.equal(Number.isFinite(binary.readFloatLE(positionOffset + index * stride + axis * 4)), true, `${mesh.name}: finite vertex`);
      }
    }
    const indexAccessor = document.accessors[primitive.indices];
    assert.equal(indexAccessor.count % 3, 0, `${mesh.name}: triangle indices`);
    const indexView = document.bufferViews[indexAccessor.bufferView];
    const indexOffset = (indexView.byteOffset || 0) + (indexAccessor.byteOffset || 0);
    const indexSize = { 5121: 1, 5123: 2, 5125: 4 }[indexAccessor.componentType];
    assert.equal(Boolean(indexSize), true, `${mesh.name}: supported index type`);
    for (let index = 0; index < indexAccessor.count; index++) {
      const vertexIndex = binary.readUIntLE(indexOffset + index * indexSize, indexSize);
      assert.equal(vertexIndex < positionAccessor.count, true, `${mesh.name}: valid vertex index`);
    }
    triangles += indexAccessor.count / 3;
  }
}
assert.equal(primitiveCount > 0, true, 'mesh primitives exist');
assert.equal(triangles > 10000, true, 'detailed geometry budget is above the low-poly hybrid');

process.stdout.write(`${JSON.stringify({
  status: 'PASS',
  file: path.basename(filePath),
  bytes: file.length,
  meshes: document.meshes.length,
  primitives: primitiveCount,
  triangles,
  images: document.images.length,
  colorTextureMaterials,
  normalTextureMaterials,
  roughnessTextureMaterials,
  requiredNodes,
}, null, 2)}\n`);
