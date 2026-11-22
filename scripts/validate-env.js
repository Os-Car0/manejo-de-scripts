const { getConfig } = require('../src/config');
const { cli, sha } = require('./lib');
cli(() => {
  const config = getConfig();
  if (process.argv.includes('--deploy')) {
    const { deploymentConfig } = require('./deployment');
    deploymentConfig(process.env);
    sha(process.env.EXPECTED_COMMIT || process.env.GITHUB_SHA);
  }
  console.log(`Configuración válida: NODE_ENV=${config.mode}, PORT=${config.port}, versión=${config.commit}. Valores secretos omitidos.`);
});
