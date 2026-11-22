"""Comprueba entregables y registra el alcance real de la revisión final local."""
from pathlib import Path
from datetime import datetime, timezone
import json
import hashlib
import re
import subprocess
import tarfile
import urllib.request
from zipfile import ZipFile

root = Path(__file__).resolve().parent.parent
evidence = root / 'evidence'
def read(name): return json.loads((evidence / name).read_text(encoding='utf-8-sig'))
def write(name, value): (evidence / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
now = datetime.now(timezone.utc).isoformat()
tests = read('tests.json')
coverage = read('coverage/coverage-summary.json')['total']
assert tests['success'] and tests['numFailedTests'] == 0
assert all(coverage[key]['pct'] >= 80 for key in ['lines', 'functions', 'branches', 'statements'])
assert all(item['errorCount'] == 0 and item['warningCount'] == 0 for item in read('eslint.json'))
assert read('yaml-validation.json')['status'] == 'correcto'
assert read('build.json')['result'] == 'correcto'
assert read('npm-audit.json')['metadata']['vulnerabilities']['total'] == 0
assert read('browser-check.json')['status'] == 'correcto'
assert read('local-health-check-cli.json')['status'] == 'ok'
assert read('git-ownership.json')['ordinaryGitWorks']
with ZipFile(root / 'docs/Manejo-de-Scripts.docx') as archive: assert archive.testzip() is None

artifact = read('artifact.json')
package = root / artifact['artifact']
assert package.is_file()
assert hashlib.sha256(package.read_bytes()).hexdigest() == artifact['sha256']
with tarfile.open(package, 'r:gz') as archive:
    members = archive.getnames()
    for member in members:
        normalized = member.replace('\\', '/')
        assert not normalized.startswith('/') and '..' not in normalized.split('/')
        assert not any(part in ['node_modules', '.git', 'data'] for part in normalized.split('/'))
        assert Path(normalized).name != '.env'
write('artifact-validation.json', {'timestamp': now, 'commit': artifact['commit'], 'sha256Verified': True, 'memberCount': len(members), 'forbiddenPathsFound': [], 'scope': 'Artefacto de implementación documentado; los commits posteriores agregan documentación y evidencias.'})

# Las páginas nuevas se observaron individualmente. Las demás tienen el mismo
# cuerpo de píxeles que páginas ya inspeccionadas en la revisión anterior.
document = read('document-validation.json')
observed_latest = {2, 18, 19, 20, 28}
unmatched = [item['page'] for item in document['pageRecords'] if not item['identicalBodyInPreviousRender'] and item['page'] not in observed_latest]
assert not unmatched, f'Falta inspeccionar cambios de estas páginas: {unmatched}'
visual = {'timestamp': now, 'pdfPagesReviewed': document['pages'], 'pdfStatus': 'CUMPLE', 'review': 'Inspección de páginas mostradas al asistente; comparación exacta de cuerpos renderizados para páginas sin cambios; verificación de las páginas nuevas y de numeración.', 'checked': ['Texto legible', 'Márgenes', 'Numeración', 'Tablas sin recortes', 'Diagrama', 'Capturas reales', 'Índice', 'Referencias', 'Ausencia de páginas vacías'], 'docxStatus': 'PARCIAL', 'docxLimit': 'Word abrió, actualizó y paginó el editable, pero no completó la exportación PDF. La fidelidad visual exacta del DOCX requiere revisión directa; el PDF se compuso con ReportLab.'}
write('document-visual-review.json', visual)

local = []
for route in ['/', '/health', '/metrics', '/api/tasks']:
    with urllib.request.urlopen('http://localhost:3000' + route, timeout=5) as response:
        body = response.read()
        assert response.status == 200
        local.append({'route': route, 'status': response.status, 'bytes': len(body)})
write('final-local-session.json', {'timestamp': now, 'origin': 'http://localhost:3000', 'checks': local, 'scope': 'Servidor local real; se detendrá después de terminar la revisión.'})

branch = subprocess.check_output(['git', 'branch', '--show-current'], cwd=root, text=True).strip()
remotes = subprocess.check_output(['git', 'remote'], cwd=root, text=True).strip()
assert branch == 'main' and not remotes
patterns = [re.compile(pattern) for pattern in [r'gh[pousr]_[A-Za-z0-9]{30,}', r'github_pat_[A-Za-z0-9_]{40,}', r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', r'api\.render\.com/deploy/srv-[\w-]+\?key=[A-Za-z0-9]{8,}', r'AKIA[A-Z0-9]{16}']]
findings = []
scanned = 0
excluded = {'.git', 'node_modules', 'tmp', 'dist', 'data', 'coverage', 'document-qa'}
for file in root.rglob('*'):
    if not file.is_file() or any(part in excluded for part in file.relative_to(root).parts): continue
    if file.suffix not in {'.js', '.py', '.ps1', '.json', '.yaml', '.yml', '.md', '.html', '.css', '.example'}: continue
    scanned += 1
    if any(pattern.search(file.read_text(encoding='utf-8-sig')) for pattern in patterns): findings.append(str(file.relative_to(root)))
assert not findings, findings
write('final-secret-scan.json', {'timestamp': now, 'filesScanned': scanned, 'includesPythonAndPowerShell': True, 'findings': findings, 'scope': 'Patrones comunes de credenciales; revisión local complementaria, no garantía de detección universal.'})
write('final-review.json', {'timestamp': now, 'localChecksPassed': True, 'testsPassed': tests['numPassedTests'], 'coverage': {key: coverage[key]['pct'] for key in ['lines', 'functions', 'branches', 'statements']}, 'branch': branch, 'remoteCount': 0, 'docker': read('docker.json')['status'], 'githubActionsRun': 'PENDIENTE', 'renderDeployment': 'PENDIENTE', 'pdf': 'CUMPLE', 'docxVisualFidelity': 'PARCIAL', 'productionReleaseAccepted': False, 'publicUrl': None})

report_path = root / 'docs/informe-final.md'
report = report_path.read_text(encoding='utf-8').split('\n## Verificación final de esta entrega')[0]
report += f'''\n## Verificación final de esta entrega

PDF final: {document['pages']} páginas inspeccionadas, nueve tablas y cuatro figuras; márgenes y formato comprobados. Word abrió y paginó el editable (véase evidence/word-validation.json); su fidelidad visual exacta continúa PARCIAL por el bloqueo del convertidor.

El comando independiente npm run health:check también pasó contra un servidor temporal local con el SHA real. Su evidencia se llama local-health-check-cli.json y no acredita un despliegue en Render.

Se corrigió la propiedad de .git con una copia verificada de sus metadatos, preservando commits e índice y conservando un respaldo dentro de tmp. Git funciona normalmente sin modificar configuración global. El intento previo de Set-Acl fue rechazado por Windows y quedó registrado.

El SHA-256 del artefacto documentado se comprobó leyendo el tar.gz, y su contenido no incluye .env, datos, node_modules ni .git. La revisión complementaria de secretos incluyó scripts Python y PowerShell y no encontró coincidencias. Las evidencias de cierre son final-review.json, artifact-validation.json y document-visual-review.json.
'''
report_path.write_text(report, encoding='utf-8')
print('Revisión final local completada; límites de Docker, Word y servicios remotos registrados.')
