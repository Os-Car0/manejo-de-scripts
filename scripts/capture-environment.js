const { spawnSync } = require('node:child_process');
const { cli, evidence, commit } = require('./lib');
cli(() => {
  const git = spawnSync('git', ['--version'], { encoding: 'utf8', windowsHide: true });
  const npm = spawnSync(process.execPath, [process.env.npm_execpath, '--version'], { encoding: 'utf8', windowsHide: true });
  const docker = spawnSync('docker', ['--version'], { encoding: 'utf8', windowsHide: true });
  const result = { timestamp: new Date().toISOString(), node: process.version, npm: npm.stdout.trim(), git: git.stdout.trim(), docker: docker.status === 0 ? docker.stdout.trim() : 'NO DISPONIBLE', platform: process.platform, architecture: process.arch, commit: commit(), shellNote: 'PowerShell bloquea npm.ps1 en este equipo; se utiliza npm.cmd sin cambiar políticas.', runnerNote: 'El ejecutor restringido tuvo setup refresh had errors; validaciones continuadas con autorizaciones de ejecución del entorno.' };
  evidence('tool-availability.json', result);
  const options = ['-c', `safe.directory=${process.cwd().replaceAll('\\', '/')}`];
  const branch = spawnSync('git', [...options, 'branch', '--show-current'], { encoding: 'utf8', windowsHide: true });
  const remotes = spawnSync('git', [...options, 'remote'], { encoding: 'utf8', windowsHide: true });
  evidence('git-status.json', { timestamp: new Date().toISOString(), branch: branch.stdout.trim(), commit: commit(), remoteNames: remotes.stdout.trim().split('\n').filter(Boolean), scope: 'Repositorio local; no se realizó push.' });
  console.log(JSON.stringify(result, null, 2));
});
