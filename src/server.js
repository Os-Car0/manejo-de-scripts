const { getConfig } = require('./config');
const { TaskStore } = require('./store');
const { createApp } = require('./app');

function start(env = process.env) {
  const config = getConfig(env);
  const app = createApp({ store: new TaskStore(config.dataFile), commit: config.commit });
  const server = app.listen(config.port, '0.0.0.0', () => console.log(`Sistema de Gestión de Tareas: http://localhost:${config.port} | versión ${config.commit}`));
  const shutdown = () => {
    server.close(() => process.exit(0));
    setTimeout(() => process.exit(1), 10000).unref();
  };
  process.once('SIGTERM', shutdown);
  process.once('SIGINT', shutdown);
  return server;
}
if (require.main === module) {
  try { start(); } catch (error) { console.error(`No se pudo iniciar: ${error.message}`); process.exitCode = 1; }
}
module.exports = { start };
