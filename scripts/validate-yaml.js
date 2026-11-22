const fs = require('node:fs');
const YAML = require('yaml');
const { cli, evidence } = require('./lib');
cli(() => {
  const files = ['render.yaml', '.github/workflows/ci-cd.yml'];
  const parsed = files.map(file => {
    const document = YAML.parseDocument(fs.readFileSync(file, 'utf8'), { uniqueKeys: true });
    if (document.errors.length) throw new Error(`YAML inválido en ${file}: ${document.errors[0].message}`);
    return document.toJS();
  });
  const [render, workflow] = parsed;
  if (render.services[0].autoDeployTrigger !== 'off' || render.services[0].plan !== 'free') throw new Error('Render debe usar plan gratuito y autoDeployTrigger off.');
  if (!workflow.on.push.branches.includes('main') || !workflow.on.pull_request || workflow.jobs.deploy.needs !== 'validate' || !workflow.jobs.deploy.if.includes("github.event_name == 'push'")) throw new Error('Faltan controles del pipeline.');
  evidence('yaml-validation.json', { timestamp: new Date().toISOString(), status: 'correcto', files, scope: 'Parseo YAML, claves únicas y controles básicos; no sustituye ejecución en GitHub ni validación del proveedor.' });
  console.log('Archivos YAML válidos; controles básicos de despliegue verificados.');
});
