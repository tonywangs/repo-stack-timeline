'use strict';
// Runs only the explicitly provisioned independent reader, against fixture copies.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const reader = process.env.RST_ARBORIST;
if (!reader) throw Error('RST_ARBORIST must point to pinned @npmcli/arborist 7.5.4');
assert.equal(require(path.join(reader,'package.json')).version, '7.5.4');
const Shrinkwrap = require(path.join(reader, 'lib/shrinkwrap.js'));
(async () => {
  const output = [];
  for (const file of process.argv.slice(2)) {
    const root = fs.mkdtempSync(path.join(os.tmpdir(),'lock-reader-'));
    try {
      fs.copyFileSync(file,path.join(root,'package-lock.json'));
      const sw = await Shrinkwrap.load({path:root});
      if (!sw.loadedFromDisk || sw.loadingError) throw Error('Reader failed');
      const records = Object.fromEntries(Object.keys(sw.data.packages).sort().map(location => [location,sw.get(path.resolve(root,location))]));
      output.push({file,original_version:sw.originalLockfileVersion,records});
    } finally { fs.rmSync(root,{recursive:true,force:true}); }
  }
  console.log(JSON.stringify({reader:'@npmcli/arborist',version:'7.5.4',source_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(reader,'lib/shrinkwrap.js'))).digest('hex'),fixtures:output}));
})().catch(error=>{console.error(error);process.exitCode=1;});
