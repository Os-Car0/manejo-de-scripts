const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');

function run(command, args, options = {}) {
  console.log(`[ejecutar] ${path.basename(command)} ${args.join(' ')}`);
  const result = spawnSync(command, args, { cwd: root, stdio: 'inherit', ...options });
  if (result.error) throw new Error(`No se pudo ejecutar ${command}: ${result.error.code}`);
  if (result.status !== 0) throw new Error(`${path.basename(command)} terminó con código ${result.status}.`);
}
function npm(args) {
  const cli = process.env.npm_execpath || path.join(path.dirname(process.execPath), 'node_modules/npm/bin/npm-cli.js');
  if (!fs.existsSync(cli)) throw new Error('Ejecuta este script mediante npm run.');
  run(process.execPath, [cli, ...args]);
}
function commit() {
  if (process.env.GITHUB_SHA) return sha(process.env.GITHUB_SHA);
  const result = spawnSync('git', ['-c', `safe.directory=${root.replaceAll('\\', '/')}`, 'rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8', windowsHide: true });
  return result.status === 0 ? result.stdout.trim() : 'local';
}
function sha(value) {
  if (!/^[a-f0-9]{40}$/.test(value || '')) throw new Error('Se requiere un commit SHA completo de 40 caracteres.');
  return value;
}
function evidence(name, value) {
  fs.mkdirSync(path.join(root, 'evidence'), { recursive: true });
  fs.writeFileSync(path.join(root, 'evidence', name), JSON.stringify(value, null, 2) + '\n');
}
function cli(work) {
  Promise.resolve().then(work).catch(error => { console.error(`[ERROR] ${error.message}`); process.exitCode = 1; });
}
module.exports = { run, npm, commit, sha, evidence, cli, root };
