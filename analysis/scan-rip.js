// Quick triage of RIP-relative .data references in a PE32+ binary.
// This scans byte patterns, not instruction boundaries; candidates need disassembly validation.
const fs = require('fs');

const file = process.argv[2];
if (!file) {
  console.error('usage: node scan-rip.js <POLYGON-Win64-Shipping.exe>');
  process.exit(2);
}
const pe = fs.readFileSync(file);
const peOffset = pe.readUInt32LE(0x3c);
const sectionCount = pe.readUInt16LE(peOffset + 6);
const optionalSize = pe.readUInt16LE(peOffset + 20);
const sectionOffset = peOffset + 24 + optionalSize;
const sections = [];
for (let i = 0; i < sectionCount; i++) {
  const offset = sectionOffset + i * 40;
  sections.push({
    name: pe.toString('ascii', offset, offset + 8).replace(/\0.*$/, ''),
    size: pe.readUInt32LE(offset + 8),
    rva: pe.readUInt32LE(offset + 12),
    rawSize: pe.readUInt32LE(offset + 16),
    rawOffset: pe.readUInt32LE(offset + 20),
  });
}
const code = sections.find(x => x.name === '.text');
const data = sections.find(x => x.name === '.data');
if (!code || !data) throw new Error('Missing .text or .data');
const hits = new Map();
const start = code.rawOffset;
const end = Math.min(pe.length, start + code.rawSize);
for (let p = start; p + 7 < end; p++) {
  const rex = pe[p];
  const opcode = pe[p + 1];
  const modrm = pe[p + 2];
  if (rex < 0x48 || rex > 0x4f || ![0x8b, 0x8d, 0x89].includes(opcode) ||
      (modrm & 0xc7) !== 0x05) continue;
  const sourceRva = code.rva + p - start;
  const targetRva = sourceRva + 7 + pe.readInt32LE(p + 3);
  if (targetRva < data.rva || targetRva >= data.rva + data.size) continue;
  let bucket = hits.get(targetRva);
  if (!bucket) hits.set(targetRva, bucket = {reads: 0, writes: 0, lea: 0, refs: []});
  const kind = opcode === 0x8b ? 'reads' : opcode === 0x89 ? 'writes' : 'lea';
  bucket[kind]++;
  if (bucket.refs.length < 8) bucket.refs.push('0x' + sourceRva.toString(16) + ':' + kind);
}
for (const rva of [0x7ff0840, 0x7df1100]) {
  console.log('previous RVA 0x' + rva.toString(16) + ':', hits.get(rva) || 'no matching RIP references');
}
console.log('Most-referenced .data RVAs:');
for (const [rva, hit] of [...hits].sort((a, b) =>
  (b[1].reads + b[1].writes + b[1].lea) - (a[1].reads + a[1].writes + a[1].lea)).slice(0, 40)) {
  const raw = data.rawOffset + rva - data.rva;
  console.log('0x' + rva.toString(16) + ' R' + hit.reads + ' W' + hit.writes +
    ' L' + hit.lea + ' raw=' + pe.subarray(raw, raw + 8).toString('hex') +
    ' ' + hit.refs.join(','));
}
