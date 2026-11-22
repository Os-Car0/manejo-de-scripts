const { spawnSync } = require('node:child_process');
const { cli, run, commit, evidence } = require('./lib');
cli(() => {
  const result = spawnSync('docker', ['info'], { encoding: 'utf8', windowsHide: true });
  if (result.error || result.status !== 0) {
    evidence('docker.json', { timestamp: new Date().toISOString(), status: 'PENDIENTE', reason: result.error ? 'Docker no está instalado o no se encuentra en PATH.' : 'Docker Engine no está disponible.' });
    throw new Error('Docker no está disponible. Instala/inicia Docker Engine para construir la imagen.');
  }
  const version = commit();
  if (!/^(local|[a-f0-9]{40})$/.test(version)) throw new Error('Versión de imagen inválida.');
  run('docker', ['build', '--build-arg', `APP_COMMIT=${version}`, '-t', `manejo-de-scripts:${version}`, '.']);
  evidence('docker.json', { timestamp: new Date().toISOString(), status: 'CUMPLE', image: `manejo-de-scripts:${version}` });
});
