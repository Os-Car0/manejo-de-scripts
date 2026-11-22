const { cli, npm } = require('./lib');
cli(() => { npm(['ci', '--ignore-scripts', '--no-fund']); console.log('Dependencias instaladas desde package-lock.json mediante npm ci.'); });
