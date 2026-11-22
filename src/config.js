const path = require('node:path');

function getConfig(env = process.env) {
  const mode = env.NODE_ENV || 'development';
  if (!['development', 'test', 'production'].includes(mode)) throw new Error('NODE_ENV debe ser development, test o production.');
  const port = Number(env.PORT || 3000);
  if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('PORT debe ser un entero entre 1 y 65535.');
  const commit = env.RENDER_GIT_COMMIT || env.APP_COMMIT || 'local';
  if (commit !== 'local' && !/^[a-f0-9]{40}$/.test(commit)) throw new Error('El commit debe ser un SHA Git completo de 40 caracteres.');
  if (mode === 'production' && commit === 'local') throw new Error('Producción requiere RENDER_GIT_COMMIT o APP_COMMIT verificable.');
  const dataFile = env.DATA_FILE || './data/tasks.json';
  if (!dataFile.trim() || path.extname(dataFile) !== '.json') throw new Error('DATA_FILE debe indicar un archivo .json.');
  return { mode, port, commit, dataFile: path.resolve(dataFile) };
}
module.exports = { getConfig };
