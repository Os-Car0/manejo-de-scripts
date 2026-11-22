const { cli, evidence } = require('./lib');
const { baseUrl } = require('./deployment');
cli(async () => {
  const origin = baseUrl(process.env.DEPLOY_BASE_URL || 'http://localhost:3000');
  if (!['localhost', '127.0.0.1', '[::1]'].includes(new URL(origin).hostname)) throw new Error('Smoke con escritura limitado al servidor local.');
  const results = [];
  async function call(route, options, expected) {
    const response = await fetch(origin + route, { ...options, headers: { 'Content-Type': 'application/json' }, signal: AbortSignal.timeout(10000) });
    const body = response.status === 204 ? null : await response.json();
    results.push({ route, method: options?.method || 'GET', status: response.status, body });
    if (response.status !== expected) throw new Error(`Smoke falló en ${route}: HTTP ${response.status}.`);
    return body;
  }
  let id;
  try {
    await call('/health', {}, 200);
    const created = await call('/api/tasks', { method: 'POST', body: JSON.stringify({ title: 'Evidencia temporal de ejecución', description: 'Esta tarea se elimina al terminar la verificación.' }) }, 201);
    id = created.data.id;
    await call(`/api/tasks/${id}`, { method: 'PATCH', body: JSON.stringify({ title: 'Evidencia actualizada', completed: true }) }, 200);
    await call('/api/tasks', {}, 200);
    await call('/api/tasks', { method: 'POST', body: JSON.stringify({ title: 'a' }) }, 400);
    await call('/ruta-ausente', {}, 404);
    await call(`/api/tasks/${id}`, { method: 'DELETE' }, 204); id = null;
    const health = await call('/health', {}, 200); evidence('health-response.json', health);
    const metrics = await call('/metrics', {}, 200); evidence('metrics-response.json', metrics);
    console.log('Smoke local correcto: CRUD, validación, errores, salud y métricas reales.');
  } finally {
    if (id) await fetch(`${origin}/api/tasks/${id}`, { method: 'DELETE' }).catch(() => {});
    evidence('endpoints.json', { timestamp: new Date().toISOString(), origin, results });
  }
});
