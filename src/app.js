const express = require('express');
const helmet = require('helmet');
const path = require('node:path');
const { Metrics } = require('./metrics');

function validate(body, partial = false) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return 'Se requiere un objeto JSON.';
  const keys = Object.keys(body);
  if (keys.some(key => !['title', 'description', 'completed'].includes(key))) return 'Se recibieron campos no permitidos.';
  if (partial && keys.length === 0) return 'Incluye al menos un campo para actualizar.';
  if ((!partial || 'title' in body) && (typeof body.title !== 'string' || body.title.trim().length < 3 || body.title.trim().length > 120)) return 'El título debe tener entre 3 y 120 caracteres.';
  if ('description' in body && (typeof body.description !== 'string' || body.description.length > 1000)) return 'La descripción debe ser texto de hasta 1000 caracteres.';
  if ('completed' in body && typeof body.completed !== 'boolean') return 'El estado completado debe ser booleano.';
  return null;
}

function createApp({ store, commit = 'local', logger = console }) {
  const app = express();
  const metrics = new Metrics();
  app.disable('x-powered-by');
  app.use(helmet());
  app.use((req, res, next) => {
    const start = process.hrtime.bigint();
    res.on('finish', () => metrics.record(res.statusCode, Number(process.hrtime.bigint() - start) / 1e6, req.path === '/api/tasks' || req.path.startsWith('/api/tasks/')));
    next();
  });
  app.use(express.json({ limit: '16kb', strict: false }));
  const healthy = () => { try { return store.health(); } catch { return false; } };
  app.get('/health', (_req, res) => {
    res.set('Cache-Control', 'no-store');
    const ok = healthy();
    res.status(ok ? 200 : 503).json({ status: ok ? 'ok' : 'degraded', commit, storage: ok ? 'ok' : 'unavailable', uptimeSeconds: process.uptime(), timestamp: new Date().toISOString() });
  });
  app.get('/metrics', (_req, res) => {
    res.set('Cache-Control', 'no-store').json(metrics.snapshot(healthy(), commit));
  });
  app.get('/api/tasks', (_req, res) => res.json({ data: store.read() }));
  app.get('/api/tasks/:id', (req, res) => {
    const task = store.read().find(task => task.id === req.params.id);
    if (!task) return res.status(404).json({ error: 'Tarea no encontrada.' });
    res.json({ data: task });
  });
  app.use('/api/tasks', (req, res, next) => {
    if (['POST', 'PATCH', 'PUT'].includes(req.method) && !req.is('application/json')) return res.status(415).json({ error: 'Utiliza Content-Type application/json.' });
    next();
  });
  const input = (req, res, next) => {
    const error = validate(req.body, req.method === 'PATCH');
    if (error) return res.status(400).json({ error });
    if ('title' in req.body) req.body.title = req.body.title.trim();
    next();
  };
  app.post('/api/tasks', input, (req, res) => {
    const task = store.create(req.body);
    res.status(201).location(`/api/tasks/${task.id}`).json({ data: task, message: 'Tarea creada.' });
  });
  const update = (req, res) => {
    const task = store.update(req.params.id, req.body);
    if (!task) return res.status(404).json({ error: 'Tarea no encontrada.' });
    res.json({ data: task, message: 'Tarea actualizada.' });
  };
  app.patch('/api/tasks/:id', input, update);
  app.put('/api/tasks/:id', input, (req, res) => {
    req.body = { description: '', completed: false, ...req.body };
    update(req, res);
  });
  app.delete('/api/tasks/:id', (req, res) => {
    if (!store.remove(req.params.id)) return res.status(404).json({ error: 'Tarea no encontrada.' });
    res.status(204).end();
  });
  app.use(express.static(path.join(__dirname, '../public')));
  app.use((_req, res) => res.status(404).json({ error: 'Recurso no encontrado.' }));
  app.use((error, _req, res, _next) => {
    const status = error.status >= 400 && error.status < 600 ? error.status : 500;
    if (status >= 500) logger.error('Error interno de almacenamiento o aplicación.');
    const message = status === 413 ? 'El cuerpo excede el límite de 16 KB.' : status === 400 ? 'JSON inválido.' : status >= 500 ? 'Error interno. Intenta de nuevo más tarde.' : error.message;
    res.status(status).json({ error: message });
  });
  return app;
}
module.exports = { createApp, validate };
