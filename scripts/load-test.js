const { performance } = require('node:perf_hooks');
const { cli, evidence } = require('./lib');
const { baseUrl } = require('./deployment');
cli(async () => {
  const origin = baseUrl(process.env.DEPLOY_BASE_URL || 'http://localhost:3000');
  if (!['localhost', '127.0.0.1', '[::1]'].includes(new URL(origin).hostname)) throw new Error('Carga local exclusivamente; no ejecutar contra un servicio remoto.');
  for (let i = 0; i < 10; i += 1) {
    const warm = await fetch(`${origin}/api/tasks`); await warm.arrayBuffer();
    if (!warm.ok) throw new Error('El calentamiento no devolvió HTTP 200.');
  }
  const timings = [], statuses = {};
  let failures = 0;
  const started = performance.now();
  await Promise.all(Array.from({ length: 5 }, async () => {
    for (let i = 0; i < 40; i += 1) {
      const start = performance.now();
      try {
        const response = await fetch(`${origin}/api/tasks`, { signal: AbortSignal.timeout(5000) });
        await response.arrayBuffer();
        timings.push(performance.now() - start);
        statuses[response.status] = (statuses[response.status] || 0) + 1;
      } catch { failures += 1; }
    }
  }));
  const elapsedMs = performance.now() - started;
  timings.sort((a, b) => a - b);
  const p95Ms = timings.length ? timings[Math.ceil(timings.length * .95) - 1] : null;
  const serverErrors = Object.entries(statuses).filter(([status]) => Number(status) >= 500).reduce((sum, [, count]) => sum + count, 0);
  const result = { timestamp: new Date().toISOString(), scope: 'Ensayo local breve; no demuestra disponibilidad mensual ni rendimiento de Render.', origin, node: process.version, platform: process.platform, concurrency: 5, warmupRequests: 10, measuredRequests: 200, completed: timings.length, networkFailures: failures, statuses, p95Ms, elapsedMs, requestsPerSecond: 200 / (elapsedMs / 1000), http5xxPercentage: serverErrors / 200 * 100, objectivesMetInThisSample: p95Ms !== null && p95Ms < 500 && serverErrors / 200 < .01 && failures === 0 };
  evidence('load-test.json', result); console.log(JSON.stringify(result, null, 2));
  if (!result.objectivesMetInThisSample) throw new Error('El ensayo local no alcanzó los criterios propuestos.');
});
