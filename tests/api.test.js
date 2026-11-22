const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const request = require('supertest');
const { TaskStore } = require('../src/store');
const { createApp, validate } = require('../src/app');
const { Metrics } = require('../src/metrics');
const { getConfig } = require('../src/config');

const commit = 'a'.repeat(40);
let directory, store, app, logger;
beforeEach(() => {
  directory = fs.mkdtempSync(path.join(os.tmpdir(), 'tareas-test-'));
  store = new TaskStore(path.join(directory, 'tasks.json'));
  logger = { error: jest.fn() };
  app = createApp({ store, commit, logger });
});
afterEach(() => { fs.rmSync(directory, { recursive: true, force: true }); });
const create = () => request(app).post('/api/tasks').send({ title: 'Preparar actividad', description: 'Revisar pipeline' });

test('crea, consulta, edita, completa, reemplaza y elimina una tarea persistida', async () => {
  const created = await create().expect(201);
  const id = created.body.data.id;
  expect(created.headers.location).toBe(`/api/tasks/${id}`);
  expect(created.body.data).toMatchObject({ title: 'Preparar actividad', description: 'Revisar pipeline', completed: false });
  const list = await request(app).get('/api/tasks').expect(200);
  expect(list.body.data).toHaveLength(1);
  expect(new TaskStore(store.file).read()[0].id).toBe(id);
  await request(app).get(`/api/tasks/${id}`).expect(200);
  const edited = await request(app).patch(`/api/tasks/${id}`).send({ title: '  Revisar actividad  ', completed: true }).expect(200);
  expect(edited.body.data).toMatchObject({ title: 'Revisar actividad', completed: true });
  const replaced = await request(app).put(`/api/tasks/${id}`).send({ title: 'Entregar actividad' }).expect(200);
  expect(replaced.body.data).toMatchObject({ description: '', completed: false });
  await request(app).delete(`/api/tasks/${id}`).expect(204);
  expect(store.read()).toEqual([]);
});
test('crear acepta valores opcionales y conserva completed true', async () => {
  const response = await request(app).post('/api/tasks').send({ title: 'Completa', completed: true }).expect(201);
  expect(response.body.data).toMatchObject({ description: '', completed: true });
});
test.each([
  {}, { title: '' }, { title: '  a  ' }, { title: 4 }, { title: 'x'.repeat(121) },
  { title: 'Título válido', description: 1 }, { title: 'Título válido', description: 'x'.repeat(1001) },
  { title: 'Título válido', completed: 'true' }, { title: 'Título válido', admin: true },
  [], null, 'texto'
])('rechaza entrada incorrecta %j', async body => {
  await request(app).post('/api/tasks').set('Content-Type', 'application/json').send(JSON.stringify(body)).expect(400);
  expect(store.read()).toHaveLength(0);
});
test('valida objetos ausentes, actualizaciones vacías y límites exactos', async () => {
  expect(validate(undefined)).toBeTruthy();
  expect(validate({ title: 'x'.repeat(120), description: 'x'.repeat(1000), completed: false })).toBeNull();
  const { body } = await create();
  const id = body.data.id;
  await request(app).patch(`/api/tasks/${id}`).send({}).expect(400);
  await request(app).patch(`/api/tasks/${id}`).send({ title: 'a' }).expect(400);
  await request(app).patch(`/api/tasks/${id}`).send({ completed: false }).expect(200);
  await request(app).put(`/api/tasks/${id}`).send({ description: 'Falta título' }).expect(400);
});
test.each(['get', 'patch', 'put', 'delete'])('%s maneja tarea inexistente', async method => {
  const call = request(app)[method]('/api/tasks/no-existe');
  if (['patch', 'put'].includes(method)) call.send({ title: 'No existe' });
  const response = await call.expect(404);
  expect(response.body.error).toBe('Tarea no encontrada.');
});
test('404 general, 415, JSON inválido y límite de cuerpo', async () => {
  await request(app).get('/no-existe').expect(404);
  await request(app).post('/api/tasks').type('form').send({ title: 'Prueba' }).expect(415);
  await request(app).post('/api/tasks').set('Content-Type', 'application/json').send('{').expect(400);
  await request(app).post('/api/tasks').send({ title: 'Prueba', description: 'x'.repeat(17000) }).expect(413);
});
test('salud comprueba almacenamiento e informa el commit sin caché', async () => {
  const response = await request(app).get('/health').expect(200);
  expect(response.body).toMatchObject({ status: 'ok', storage: 'ok', commit });
  expect(response.headers['cache-control']).toBe('no-store');
  expect(response.body.uptimeSeconds).toBeGreaterThan(0);
  fs.writeFileSync(store.file, 'corrupto');
  await request(app).get('/health').expect(503);
  const metrics = await request(app).get('/metrics').expect(200);
  expect(metrics.body.health).toBe('degraded');
});
test('métricas cuentan respuestas reales y separan tráfico API de monitoreo', async () => {
  await request(app).get('/api/tasks').expect(200);
  await request(app).get('/health').expect(200);
  await request(app).get('/ausente').expect(404);
  const response = await request(app).get('/metrics').expect(200);
  expect(response.body.requests).toEqual({ total: 3, byStatus: { 200: 2, 404: 1 } });
  expect(response.body.errors).toMatchObject({ http4xx: 1, http5xx: 0, total: 1 });
  expect(response.body.errors.percentage).toBeCloseTo(100 / 3);
  expect(response.body.api).toMatchObject({ requests: 1, http5xx: 0, sampleSize: 1 });
  expect(response.body.responseTimeMs.p95).toBeGreaterThan(0);
  expect(response.body.memoryBytes.rss).toBeGreaterThan(0);
  expect(response.body.memoryBytes.heapUsed).toBeGreaterThan(0);
});
test('error 500 real de almacenamiento sin exponer detalles internos', async () => {
  fs.writeFileSync(store.file, 'no-json');
  const response = await request(app).get('/api/tasks').expect(500);
  expect(response.body.error).toBe('Error interno. Intenta de nuevo más tarde.');
  expect(JSON.stringify(response.body)).not.toContain(directory);
  expect(logger.error).toHaveBeenCalledTimes(1);
  const metrics = await request(app).get('/metrics');
  expect(metrics.body.api.serverErrorPercentage).toBe(100);
  expect(metrics.body.errors.serverPercentage).toBe(100);
});
test('archivos estáticos y encabezados de seguridad', async () => {
  const response = await request(app).get('/').expect(200);
  expect(response.text).toContain('Sistema de Gestión de Tareas');
  expect(response.headers['content-security-policy']).toContain("script-src 'self'");
  expect(response.headers['x-powered-by']).toBeUndefined();
  await request(app).get('/styles.css').expect(200);
  await request(app).get('/app.js').expect(200);
});
test('almacenamiento rechaza estructuras inválidas y nunca las sobrescribe', () => {
  for (const value of [{}, [null], [{ id: 'a' }]]) {
    fs.writeFileSync(store.file, JSON.stringify(value));
    expect(() => new TaskStore(store.file)).toThrow('formato válido');
    expect(JSON.parse(fs.readFileSync(store.file, 'utf8'))).toEqual(value);
  }
});
test('límite de 1000 tareas genera 409 sin escribir otra tarea', async () => {
  const task = (await create()).body.data;
  store.save(Array.from({ length: 1000 }, (_, i) => ({ ...task, id: String(i) })));
  await create().expect(409);
  expect(store.read()).toHaveLength(1000);
});
test('limpia temporal si falla rename y conserva archivo anterior', () => {
  const original = fs.readFileSync(store.file, 'utf8');
  const mock = jest.spyOn(fs, 'renameSync').mockImplementation(() => { throw new Error('Permiso denegado'); });
  try { expect(() => store.save([{ test: true }])).toThrow('Permiso denegado'); }
  finally { mock.mockRestore(); }
  expect(fs.readFileSync(store.file, 'utf8')).toBe(original);
  expect(fs.readdirSync(directory)).toEqual(['tasks.json']);
});
test('métricas sin observaciones y ventana acotada de 1000 respuestas', () => {
  const metrics = new Metrics();
  expect(metrics.snapshot(true, commit).responseTimeMs).toEqual({ average: null, p95: null, sampleSize: 0 });
  expect(metrics.snapshot(true, commit).api.p95Ms).toBeNull();
  for (let i = 1; i <= 1001; i += 1) metrics.record(i % 2 ? 200 : 500, i, true);
  const result = metrics.snapshot(false, commit);
  expect(result.requests.total).toBe(1001);
  expect(result.responseTimeMs.sampleSize).toBe(1000);
  expect(result.responseTimeMs.p95).toBe(951);
  expect(result.api.sampleSize).toBe(1000);
  expect(result.errors.http5xx).toBe(500);
});
test('valida valores de configuración y su precedencia', () => {
  expect(getConfig({})).toMatchObject({ mode: 'development', port: 3000, commit: 'local' });
  expect(getConfig({ NODE_ENV: 'production', APP_COMMIT: commit, RENDER_GIT_COMMIT: 'b'.repeat(40), PORT: '10000' })).toMatchObject({ port: 10000, commit: 'b'.repeat(40) });
  for (const env of [{ NODE_ENV: 'otro' }, { PORT: '0' }, { PORT: '65536' }, { PORT: 'hola' }, { PORT: '1.5' }, { APP_COMMIT: 'fake' }, { NODE_ENV: 'production' }, { DATA_FILE: 'datos.txt' }, { DATA_FILE: ' ' }]) expect(() => getConfig(env)).toThrow();
});
