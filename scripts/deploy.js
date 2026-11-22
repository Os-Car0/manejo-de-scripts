const fs = require('node:fs');
const { cli, commit, sha, evidence } = require('./lib');
const { deploymentConfig, verifyHealth } = require('./deployment');
cli(async () => {
  const version = sha(process.env.EXPECTED_COMMIT || process.env.GITHUB_SHA || commit());
  const plan = { timestamp: new Date().toISOString(), provider: 'Render', commit: version, branch: 'main', mechanism: 'Deploy hook HTTPS con ref igual al SHA validado', steps: ['Validar configuración', 'Solicitar despliegue del SHA', 'Confirmar /health con el mismo SHA'], executed: false };
  if (process.argv.includes('--plan')) { evidence('deployment-plan.json', plan); console.log('Plan generado en evidence/deployment-plan.json. No se contactó a Render.'); return; }
  if (!process.argv.includes('--execute')) throw new Error('Indica --plan o --execute.');
  if (process.env.GITHUB_ACTIONS !== 'true' || process.env.GITHUB_EVENT_NAME !== 'push' || process.env.GITHUB_REF !== 'refs/heads/main') throw new Error('El despliegue solo se ejecuta en GitHub Actions mediante push a main, después del job de validación.');
  const config = deploymentConfig({ ...process.env, EXPECTED_COMMIT: version });
  const receipt = JSON.parse(fs.readFileSync('dist/manifest.json', 'utf8'));
  if (receipt.commit !== version) throw new Error('El artefacto no pertenece al commit que se intenta desplegar.');
  // Idempotencia para una repetición del mismo workflow ya publicado.
  try {
    await verifyHealth({ origin: config.origin, expected: version, timeoutMs: 0 });
    evidence('deployment.json', { ...plan, executed: false, result: 'La versión esperada ya está publicada; no se duplicó el despliegue.' });
    console.log('La versión esperada ya está saludable. No se generó otro despliegue.'); return;
  } catch { /* Continuar con un único POST. */ }
  config.hook.searchParams.set('ref', version);
  let response;
  try { response = await fetch(config.hook, { method: 'POST', redirect: 'error', signal: AbortSignal.timeout(20000) }); }
  catch { throw new Error('No se confirmó la respuesta del hook. Revisa Render antes de reintentar para evitar duplicados.'); }
  if (![200, 202].includes(response.status)) throw new Error(`Render rechazó el despliegue con HTTP ${response.status}. No se imprimió el hook secreto.`);
  evidence('deployment.json', { ...plan, executed: true, responseStatus: response.status, result: 'solicitado; pendiente de health check del mismo commit' });
  console.log('Despliegue solicitado una vez. El paso siguiente debe confirmar el commit en /health.');
});
