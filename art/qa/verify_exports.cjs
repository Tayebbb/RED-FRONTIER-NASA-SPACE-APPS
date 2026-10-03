const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const exportDirectory = path.resolve(__dirname, '../export/rover');
const partNames = [
  'Antenna_HighGain', 'Antenna_Std', 'Battery_Extended', 'Battery_Standard',
  'Inst_Camera', 'Inst_Radar', 'Inst_Radiation', 'Inst_Soil',
  'Inst_Spectrometer', 'Inst_Weather', 'Power_Nuclear', 'Shield_Heavy',
  'Shield_Minimal', 'Shield_Standard', 'Solar_Large', 'Solar_Light',
  'Wheel_Reinforced', 'Wheel_Standard',
];

function inspectExport(name) {
  const file = fs.readFileSync(path.join(exportDirectory, `${name}.glb`));
  assert.equal(file.readUInt32LE(0), 0x46546c67, `${name}: GLB magic`);
  assert.equal(file.readUInt32LE(4), 2, `${name}: GLB version`);
  assert.equal(file.readUInt32LE(8), file.length, `${name}: file length`);
  const jsonLength = file.readUInt32LE(12);
  assert.equal(file.readUInt32LE(16), 0x4e4f534a, `${name}: JSON chunk`);
  const document = JSON.parse(file.subarray(20, 20 + jsonLength).toString('utf8'));
  const binaryHeader = 20 + jsonLength;
  assert.equal(file.readUInt32LE(binaryHeader + 4), 0x004e4942, `${name}: BIN chunk`);
  const binary = file.subarray(binaryHeader + 8);
  assert.equal(file.readUInt32LE(binaryHeader), binary.length, `${name}: BIN length`);
  assert.equal(document.buffers[0].byteLength <= binary.length, true);
  assert.equal(document.asset.version, '2.0');
  assert.equal((document.animations || []).length, 0);
  assert.equal((document.cameras || []).length, 0);
  assert.equal((document.images || []).length, 0);
  assert.equal((document.textures || []).length, 0);
  let triangles = 0;
  for (const mesh of document.meshes) {
    for (const primitive of mesh.primitives) {
      assert.equal(primitive.mode ?? 4, 4, `${name}: triangle primitives`);
      const positions = document.accessors[primitive.attributes.POSITION];
      assert.equal(positions.componentType, 5126);
      assert.equal(positions.type, 'VEC3');
      assert.equal(positions.count > 0, true);
      const positionView = document.bufferViews[positions.bufferView];
      const positionOffset = (positionView.byteOffset || 0) + (positions.byteOffset || 0);
      const stride = positionView.byteStride || 12;
      for (let index = 0; index < positions.count; index++) {
        for (let axis = 0; axis < 3; axis++) {
          assert.equal(Number.isFinite(binary.readFloatLE(positionOffset + index * stride + axis * 4)), true);
        }
      }
      const indices = document.accessors[primitive.indices];
      assert.equal(indices.count % 3, 0);
      const indexView = document.bufferViews[indices.bufferView];
      const indexOffset = (indexView.byteOffset || 0) + (indices.byteOffset || 0);
      const size = { 5121: 1, 5123: 2, 5125: 4 }[indices.componentType];
      assert.equal(Boolean(size), true);
      for (let index = 0; index < indices.count; index++) {
        const value = binary.readUIntLE(indexOffset + index * size, size);
        assert.equal(value < positions.count, true, `${name}: valid vertex indices`);
      }
      triangles += indices.count / 3;
    }
  }
  if (name === 'rover_base') {
    assert.equal(document.meshes.length, 10);
    assert.equal(document.nodes.filter(node => node.name?.startsWith('SKT_')).length, 9);
    assert.equal(triangles, 7804);
    assert.equal(triangles < 8000, true);
  } else {
    assert.equal(document.meshes.length, 1, `${name}: no unintended base mesh`);
    assert.equal(document.nodes.length, 1, `${name}: socket-local standalone node`);
    assert.equal(document.nodes[0].name, name);
    assert.deepEqual(document.nodes[0].translation || [0, 0, 0], [0, 0, 0]);
    assert.deepEqual(document.nodes[0].scale || [1, 1, 1], [1, 1, 1]);
    assert.deepEqual(document.nodes[0].rotation || [0, 0, 0, 1], [0, 0, 0, 1]);
  }
  return { name, triangles, bytes: file.length };
}

const results = ['rover_base', ...partNames].map(inspectExport);
process.stdout.write(`${JSON.stringify({ status: 'PASS', files: results }, null, 2)}\n`);