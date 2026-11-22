const { sha } = require('./lib');

function baseUrl(value) {
  const url = new URL(value);
  if (!['http:', 'https:'].includes(url.protocol) || url.username || url.password || url.search || url.hash || url.pathname !== '/') throw new Error('DEPLOY_BASE_URL debe ser un origen HTTP(S), sin credenciales, rutas ni parámetros.');
  if (url.protocol === 'http:' && !['localhost', '127.0.0.1', '[::1]'].includes(url.hostname)) throw new Error('Utiliza HTTPS fuera del equipo local.');
  return url.origin;
}
function deploymentConfig(env) {
  if (!env.RENDER_DEPLOY_HOOK_URL || !env.DEPLOY_BASE_URL) throw new Error('Faltan RENDER_DEPLOY_HOOK_URL o DEPLOY_BASE_URL. Configúralas en GitHub Actions Secrets tras autorizar el despliegue.');
  const hook = new URL(env.RENDER_DEPLOY_HOOK_URL);
  if (hook.protocol !== 'https:' || hook.hostname !== 'api.render.com' || !/^\/deploy\/srv-[a-zA-Z0-9-]+$/.test(hook.pathname) || !hook.searchParams.get('key') || hook.username || hook.password) throw new Error('El hook debe ser una URL de despliegue válida de api.render.com.');
  return { hook, origin: baseUrl(env.DEPLOY_BASE_URL), commit: sha(env.EXPECTED_COMMIT || env.GITHUB_SHA) };
}
async function verifyHealth({ origin, expected, timeoutMs = 180000, intervalMs = 5000, fetcher = fetch, sleep = ms => new Promise(resolve => setTimeout(resolve, ms)), now = Date.now }) {
  sha(expected);
  const deadline = now() + timeoutMs;
  let attempts = 0;
  do {
    attempts += 1;
    try {
      const response = await fetcher(`${baseUrl(origin)}/health?expected=${expected}&attempt=${attempts}`, { cache: 'no-store', redirect: 'error', signal: AbortSignal.timeout(10000) });
      if (response.ok) {
        const body = await response.json();
        if (body.status === 'ok' && body.storage === 'ok' && body.commit === expected) return { timestamp: new Date().toISOString(), status: 'ok', commit: body.commit, attempts, health: body };
      }
    } catch { /* Una instancia en arranque puede rechazar conexiones. */ }
    if (now() >= deadline) break;
    await sleep(Math.min(intervalMs, Math.max(0, deadline - now())));
  } while (now() <= deadline);
  throw new Error(`Health check falló tras ${attempts} intentos: no se confirmó una instancia saludable con el commit esperado.`);
}
module.exports = { baseUrl, deploymentConfig, verifyHealth };
