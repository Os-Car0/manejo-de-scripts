const fs = require('node:fs');
const path = require('node:path');
const net = require('node:net');
const { once } = require('node:events');
const { spawn } = require('node:child_process');
const { cli, commit, sha, evidence } = require('./lib');
const { verifyHealth } = require('./deployment');
cli(async () => {
  const expected = sha(commit());
  fs.mkdirSync('tmp', { recursive: true });
  const directory = fs.mkdtempSync(path.resolve('tmp/health-version-'));
  const probe = net.createServer(); probe.listen(0, '127.0.0.1');
  await once(probe, 'listening'); const port = probe.address().port;
  await new Promise(resolve => probe.close(resolve));
  const child = spawn(process.execPath, ['src/server.js'], { env: { ...process.env, NODE_ENV: 'test', PORT: String(port), APP_COMMIT: expected, RENDER_GIT_COMMIT: '', DATA_FILE: path.join(directory, 'tasks.json') }, stdio: 'pipe', windowsHide: true });
  const errors = [];
  child.stderr.on('data', data => errors.push(String(data)));
  try {
    const result = await verifyHealth({ origin: `http://127.0.0.1:${port}`, expected, timeoutMs: 30000, intervalMs: 100 });
    const wrong = expected[0] === 'a' ? 'b'.repeat(40) : 'a'.repeat(40);
    let rejected = false;
    try { await verifyHealth({ origin: `http://127.0.0.1:${port}`, expected: wrong, timeoutMs: 0 }); }
    catch { rejected = true; }
    if (!rejected) throw new Error('El verificador aceptó una versión distinta.');
    evidence('local-version-check.json', { ...result, scope: 'Servidor temporal real del equipo local; no es un despliegue en Render.', rejectedDifferentCommit: rejected, stderr: errors });
    console.log('Health check real correcto y commit distinto rechazado.');
  } finally {
    child.kill();
    await once(child, 'exit');
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
