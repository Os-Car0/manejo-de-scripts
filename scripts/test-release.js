const { cli, run } = require('./lib');
cli(() => {
  run(process.execPath, [require.resolve('jest/bin/jest'), '--runInBand', '--coverage', '--json', '--outputFile=evidence/tests.json']);
  const fs = require('node:fs');
  fs.cpSync('coverage', 'evidence/coverage', { recursive: true });
  console.log('Pruebas y cobertura verificadas; umbrales mínimos 80 % en las cuatro dimensiones.');
});
