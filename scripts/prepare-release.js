const fs = require('node:fs');
const path = require('node:path');
const { cli, root, commit, evidence } = require('./lib');
cli(() => {
  const major = Number(process.versions.node.split('.')[0]);
  if (major < 24 || major >= 27) throw new Error('Utiliza Node.js 24, 25 o 26; CI y Docker utilizan Node.js 24 LTS.');
  for (const name of ['package-lock.json', 'Dockerfile', 'render.yaml']) {
    if (!fs.existsSync(path.join(root, name))) throw new Error(`Falta ${name}.`);
  }
  for (const directory of ['dist', 'evidence', 'tmp']) fs.mkdirSync(path.join(root, directory), { recursive: true });
  evidence('release-environment.json', { timestamp: new Date().toISOString(), node: process.version, platform: process.platform, architecture: process.arch, commit: commit(), status: 'preparado' });
  console.log('Entorno de liberación preparado. No se alteraron los datos de la aplicación.');
});
