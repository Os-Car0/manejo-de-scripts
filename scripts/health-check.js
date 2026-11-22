const { cli, sha, evidence } = require('./lib');
const { verifyHealth } = require('./deployment');
cli(async () => {
  const expected = sha(process.env.EXPECTED_COMMIT || process.env.GITHUB_SHA);
  if (!process.env.DEPLOY_BASE_URL) throw new Error('Falta DEPLOY_BASE_URL.');
  const result = await verifyHealth({ origin: process.env.DEPLOY_BASE_URL, expected, timeoutMs: 600000 });
  evidence('post-deploy-health.json', result);
  console.log(`Health check correcto. La instancia publicada corresponde a ${result.commit}.`);
});
