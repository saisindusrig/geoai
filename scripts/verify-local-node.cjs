// Local launcher preflight only. No application, credential or network imports.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { execFileSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const runtime = path.join(root, '.local-tooling/node-24.22.1-validation/runtime/node-v24.22.1-win-x64');
const expected = {
  "node.exe": "d702daa815eabbff763c7d3808e235cf031cf2ca70211b56847bc72f51e240e5",
  "node_modules/npm/bin/npm-cli.js": "3ce7cba6f5128dd5f54c98b6a5036b0f850496878cc2e21044b675fe3c594e3e",
  "node_modules/npm/package.json": "d5b859b88af16e893fbc2d28819db601a8543b241f8c80459f70898be2777c12",
  "npm.cmd": "21b46c69ad6e2f231f02a9e120f4ba6c8e75fef5a45637103002eab99f888ab8",
  "npm": "13372aa943f8eb32c9a8b6f946ed6a49118edd60051321953288b1f35611aefb",
  "npm.ps1": "e8aedc8c76d6cb9423b70ede071228f7cb1644094c114b8721ae6d121100d4fe"
};
const canonical = file => fs.realpathSync(file).toLowerCase();
try {
  if (process.platform !== 'win32' || process.arch !== 'x64' || process.version !== 'v24.22.1') {
    throw new Error('The local frontend requires the verified Windows x64 Node.js 24.22.1 (Firebase requires >=24.12.0).');
  }
  const node = path.join(runtime, 'node.exe');
  if (canonical(process.execPath) !== canonical(node)) throw new Error('The launcher did not select the retained project-local Node executable.');
  for (const [relative, sha256] of Object.entries(expected)) {
    const file = path.join(runtime, relative);
    if (crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex') !== sha256) {
      throw new Error(`Retained runtime file does not match the validated archive: ${relative}`);
    }
  }
  const child = JSON.parse(execFileSync('node', ['-e', 'console.log(JSON.stringify({version:process.version,execPath:process.execPath,arch:process.arch}))'], { encoding: 'utf8', windowsHide: true }));
  if (child.version !== 'v24.22.1' || child.arch !== 'x64' || canonical(child.execPath) !== canonical(node)) {
    throw new Error('A PATH-selected Node child would use a different runtime. No frontend was started.');
  }
  const npmCandidates = execFileSync('where.exe', ['npm'], { encoding: 'utf8', windowsHide: true }).trim().split(/\r?\n/);
  if (![ 'npm', 'npm.cmd', 'npm.ps1' ].some(name => canonical(npmCandidates[0]) === canonical(path.join(runtime, name))) || !npmCandidates.some(file => canonical(file) === canonical(path.join(runtime, 'npm.cmd')))) {
    throw new Error('PATH-selected npm is not the verified portable npm.');
  }
  const npm = JSON.parse(fs.readFileSync(path.join(runtime, 'node_modules/npm/package.json'), 'utf8'));
  if (npm.version !== '11.19.1') throw new Error('The matching portable npm 11.19.1 is required.');
  const report = { node: process.version, execPath: process.execPath, child, npm: npm.version, npmCli: path.join(runtime, 'node_modules/npm/bin/npm-cli.js'), archiveFilesVerified: Object.keys(expected).length };
  console.log(process.argv.includes('--json') ? JSON.stringify(report) : 'StruvoCivil local runtime: Node 24.22.1, npm 11.19.1; main and PATH child verified.');
} catch (error) {
  console.error(`StruvoCivil runtime preflight failed: ${error.message}`);
  console.error('Restore the retained verified portable runtime; no automatic installation or Node 22 fallback is performed.');
  process.exitCode = 1;
}
