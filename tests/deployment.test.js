const { baseUrl, deploymentConfig, verifyHealth } = require('../scripts/deployment');
const { sha } = require('../scripts/lib');
const expected = 'b'.repeat(40);
// URLs reservadas y hooks deliberadamente no operativos, utilizados solo como fixtures.
test('valida origen HTTPS y permite loopback HTTP', () => {
  expect(baseUrl('http://localhost:3000')).toBe('http://localhost:3000');
  expect(baseUrl('https://example.invalid')).toBe('https://example.invalid');
  for (const url of ['ftp://example.invalid', 'http://example.invalid', 'https://u:p@example.invalid', 'https://example.invalid/ruta', 'https://example.invalid?x=1']) expect(() => baseUrl(url)).toThrow();
  expect(() => sha('local')).toThrow();
});
test('faltantes y hooks de otros hosts son rechazados sin imprimir secretos', () => {
  expect(() => deploymentConfig({})).toThrow('Faltan');
  expect(() => deploymentConfig({ RENDER_DEPLOY_HOOK_URL: 'https://example.invalid', DEPLOY_BASE_URL: 'https://example.invalid' })).toThrow('hook');
  const config = deploymentConfig({ RENDER_DEPLOY_HOOK_URL: 'https://api.render.com/deploy/srv-fixture?key=x', DEPLOY_BASE_URL: 'https://example.invalid', EXPECTED_COMMIT: expected });
  expect(config.commit).toBe(expected);
});
test('rechaza una versión anterior saludable y acepta solo SHA esperado', async () => {
  let clock = 0;
  const fetcher = jest.fn().mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'ok', storage: 'ok', commit: 'a'.repeat(40) }) }).mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'ok', storage: 'ok', commit: expected }) });
  const result = await verifyHealth({ origin: 'https://example.invalid', expected, fetcher, now: () => clock, sleep: async ms => { clock += ms; }, intervalMs: 10, timeoutMs: 30 });
  expect(result.attempts).toBe(2);
  expect(fetcher).toHaveBeenCalledTimes(2);
});
test('falla por tiempo máximo ante respuesta anterior, caída o salud degradada', async () => {
  for (const fetcher of [async () => { throw new Error('offline'); }, async () => ({ ok: false }), async () => ({ ok: true, json: async () => ({ status: 'degraded', commit: expected }) })]) {
    await expect(verifyHealth({ origin: 'http://localhost:3000', expected, fetcher, timeoutMs: 0 })).rejects.toThrow('no se confirmó');
  }
});
