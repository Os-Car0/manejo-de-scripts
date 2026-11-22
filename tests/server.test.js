const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const net = require('node:net');
const { once } = require('node:events');
const { spawn } = require('node:child_process');
const { start } = require('../src/server');

async function freePort() {
  const server = net.createServer();
  server.listen(0, '127.0.0.1');
  await once(server, 'listening');
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}
test('inicia un servidor real y responde health', async () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'tareas-server-'));
  const termBefore = process.listeners('SIGTERM');
  const intBefore = process.listeners('SIGINT');
  const server = start({ PORT: String(await freePort()), NODE_ENV: 'test', DATA_FILE: path.join(directory, 'tasks.json') });
  try {
    await once(server, 'listening');
    const response = await fetch(`http://127.0.0.1:${server.address().port}/health`);
    expect(response.status).toBe(200);
    expect((await response.json()).commit).toBe('local');
  } finally {
    await new Promise(resolve => server.close(resolve));
    for (const listener of process.listeners('SIGTERM')) if (!termBefore.includes(listener)) process.removeListener('SIGTERM', listener);
    for (const listener of process.listeners('SIGINT')) if (!intBefore.includes(listener)) process.removeListener('SIGINT', listener);
    fs.rmSync(directory, { recursive: true, force: true });
  }
});
test('proceso falla con código no cero si PORT es inválido', async () => {
  const child = spawn(process.execPath, ['src/server.js'], { env: { ...process.env, PORT: 'invalido' }, stdio: 'pipe', windowsHide: true });
  let stderr = '';
  child.stderr.on('data', data => { stderr += data; });
  const [code] = await once(child, 'exit');
  expect(code).toBe(1);
  expect(stderr).toContain('No se pudo iniciar');
});
