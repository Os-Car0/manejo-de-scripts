const fs = require('node:fs');
const path = require('node:path');
const { cli, evidence } = require('./lib');
cli(() => {
  const excluded = new Set(['.git', 'node_modules', 'tmp', 'dist', 'data', 'coverage']);
  const rules = [/gh[pousr]_[A-Za-z0-9]{30,}/, /github_pat_[A-Za-z0-9_]{40,}/, /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/, /api\.render\.com\/deploy\/srv-[\w-]+\?key=[A-Za-z0-9]{8,}/, /AKIA[A-Z0-9]{16}/];
  const findings = [];
  let count = 0;
  function walk(directory) {
    for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
      if (excluded.has(entry.name)) continue;
      const file = path.join(directory, entry.name);
      if (entry.isDirectory()) walk(file);
      else if (/\.(js|json|ya?ml|md|txt|html|css|example)$/.test(entry.name) || entry.name.startsWith('.env')) {
        count += 1;
        if (entry.name === '.env') findings.push(file);
        if (rules.some(rule => rule.test(fs.readFileSync(file, 'utf8')))) findings.push(file);
      }
    }
  }
  walk('.');
  evidence('secret-scan.json', { timestamp: new Date().toISOString(), scannedFiles: count, findings: [...new Set(findings)], scope: 'Patrones locales de credenciales comunes; no garantiza detección de todo secreto.' });
  if (findings.length) throw new Error('Se detectaron archivos que requieren revisión de secretos. Consulta evidence/secret-scan.json.');
  console.log(`Revisión de ${count} archivos de texto: sin coincidencias de los patrones de credenciales.`);
});
