const fs = require('node:fs');
const path = require('node:path');
const { cli, root, run, evidence, commit } = require('./lib');
cli(() => {
  let checked = 0;
  for (const folder of ['src', 'public', 'scripts']) {
    for (const entry of fs.readdirSync(path.join(root, folder))) {
      if (entry.endsWith('.js')) { run(process.execPath, ['--check', path.join(folder, entry)]); checked += 1; }
    }
  }
  for (const name of ['public/index.html', 'public/styles.css', 'public/favicon.svg']) {
    if (!fs.statSync(path.join(root, name)).size) throw new Error(`Archivo vacío: ${name}`);
  }
  evidence('build.json', { timestamp: new Date().toISOString(), commit: commit(), checkedJavaScriptFiles: checked, result: 'correcto', type: 'Validación de sintaxis y recursos; aplicación sin transpilación' });
  console.log(`Construcción validada: ${checked} archivos JavaScript y recursos estáticos.`);
});
