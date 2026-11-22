const fs = require('node:fs');
/* global document, window -- El callback de page.evaluate se ejecuta en Chrome. */
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const { cli, evidence } = require('./lib');
const { baseUrl } = require('./deployment');

cli(async () => {
  const origin = baseUrl(process.env.DEPLOY_BASE_URL || 'http://localhost:3000');
  if (!['localhost', '127.0.0.1', '[::1]'].includes(new URL(origin).hostname)) throw new Error('La prueba de interfaz solo modifica datos locales.');
  const executablePath = process.env.CHROME_PATH || (process.platform === 'win32' ? 'C:/Program Files/Google/Chrome/Application/chrome.exe' : undefined);
  if (executablePath && !fs.existsSync(executablePath)) throw new Error('No se encontró Chrome. Define CHROME_PATH o instala un navegador compatible con Playwright.');
  const browser = await chromium.launch({ headless: true, executablePath });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1040 }, locale: 'es-MX' });
  const page = await context.newPage();
  const errors = [], checks = [];
  const createdIds = new Set();
  page.on('pageerror', error => errors.push(error.message));
  page.on('response', async response => {
    if (response.request().method() === 'POST' && response.url() === origin + '/api/tasks' && response.status() === 201) {
      createdIds.add((await response.json()).data.id);
    }
  });
  const waitFor = async (locator, text) => {
    await locator.filter({ hasText: text }).first().waitFor({ state: 'visible' });
  };
  const createTask = async (title, description) => {
    await page.getByRole('button', { name: 'Nueva tarea', exact: false }).click();
    await page.getByRole('textbox', { name: 'Título' }).fill(title);
    await page.getByRole('textbox', { name: 'Descripción' }).fill(description);
    await page.getByRole('button', { name: 'Crear tarea', exact: true }).click();
    await page.getByRole('heading', { name: title, exact: true }).waitFor();
  };
  fs.mkdirSync('evidence/screenshots', { recursive: true });
  try {
    await page.goto(origin, { waitUntil: 'networkidle' });
    await page.locator('#loading').waitFor({ state: 'hidden' });
    const initialTasks = await (await context.request.get(origin + '/api/tasks')).json();
    assert.equal(initialTasks.data.length, 0, 'La evidencia visual requiere una instancia local de prueba vacía.');
    await createTask('Revisar el pipeline de liberación', 'Confirmar las validaciones antes del despliegue en Render.');
    checks.push('Crear tarea desde el formulario y confirmar respuesta de la API.');
    await createTask('Documentar las métricas de la aplicación', 'Registrar tiempos de respuesta, errores HTTP y estado de salud.');
    await createTask('Preparar la entrega de Manejo de Scripts', 'Integrar el documento académico y las evidencias reales de ejecución.');
    await page.getByRole('button', { name: 'Editar Revisar el pipeline de liberación', exact: true }).click();
    await page.getByRole('textbox', { name: 'Título' }).fill('Validar el pipeline de liberación');
    await page.getByRole('button', { name: 'Guardar cambios', exact: true }).click();
    await page.getByRole('heading', { name: 'Validar el pipeline de liberación', exact: true }).waitFor();
    checks.push('Editar y guardar el título.');
    await page.getByRole('checkbox', { name: 'Completar Validar el pipeline de liberación', exact: true }).check();
    await page.getByRole('checkbox', { name: 'Reabrir Validar el pipeline de liberación', exact: true }).waitFor();
    checks.push('Completar una tarea y actualizar contadores.');
    await page.reload({ waitUntil: 'networkidle' });
    await page.getByRole('checkbox', { name: 'Reabrir Validar el pipeline de liberación', exact: true }).waitFor();
    checks.push('Conservar el estado al recargar la página.');
    await page.screenshot({ path: 'evidence/screenshots/aplicacion-escritorio.png', fullPage: true });
    await page.getByRole('button', { name: 'Completadas', exact: true }).click();
    assert.equal(await page.locator('.task-row').count(), 1);
    await page.getByRole('button', { name: 'Pendientes', exact: true }).click();
    assert.equal(await page.locator('.task-row').count(), 2);
    await page.getByRole('button', { name: 'Todas', exact: true }).click();
    await page.getByRole('searchbox').fill('Documentar');
    assert.equal(await page.locator('.task-row').count(), 1);
    await page.getByRole('searchbox').fill('');
    checks.push('Filtros de completadas y pendientes; búsqueda por texto.');
    await page.getByRole('button', { name: 'Nueva tarea', exact: false }).click();
    await page.getByRole('textbox', { name: 'Título' }).fill('   ');
    await page.getByRole('button', { name: 'Crear tarea', exact: true }).click();
    await waitFor(page.locator('#form-error'), '3 caracteres');
    await page.screenshot({ path: 'evidence/screenshots/validacion-formulario.png', fullPage: true });
    await page.getByRole('button', { name: 'Cancelar', exact: true }).click();
    checks.push('Rechazar título de solo espacios con mensaje visible.');
    await page.getByRole('button', { name: 'Nueva tarea', exact: false }).click();
    await page.getByRole('textbox', { name: 'Título' }).fill('Verificar mensaje de error HTTP');
    await page.route('**/api/tasks', route => route.request().method() === 'POST' ? route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: 'Error controlado de prueba de interfaz.' }) }) : route.continue());
    await page.getByRole('button', { name: 'Crear tarea', exact: true }).click();
    await waitFor(page.locator('#form-error'), 'Error controlado');
    await page.unroute('**/api/tasks');
    await page.getByRole('button', { name: 'Cancelar', exact: true }).click();
    checks.push('Mostrar error HTTP controlado en prueba de navegador; no es una caída real del servidor.');
    await page.locator('#toast').waitFor({ state: 'hidden' });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: 'evidence/screenshots/aplicacion-movil.png', fullPage: false });
    await page.screenshot({ path: 'evidence/screenshots/aplicacion-movil-completa.png', fullPage: true });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true);
    checks.push('Vista móvil de 390 px sin desbordamiento horizontal.');
    await page.getByRole('button', { name: 'Eliminar Documentar las métricas de la aplicación', exact: true }).click();
    await page.getByRole('button', { name: 'Conservar tarea', exact: true }).click();
    assert.equal(await page.locator('.task-row').count(), 3);
    await page.getByRole('button', { name: 'Eliminar Documentar las métricas de la aplicación', exact: true }).click();
    await page.getByRole('button', { name: 'Eliminar tarea', exact: true }).click();
    await page.getByRole('heading', { name: 'Documentar las métricas de la aplicación', exact: true }).waitFor({ state: 'hidden' });
    checks.push('Cancelar eliminación y después confirmar eliminación real.');
    assert.deepEqual(errors, []);
    evidence('browser-check.json', { timestamp: new Date().toISOString(), status: 'correcto', browser: await browser.version(), checks, consoleErrors: errors, screenshots: ['aplicacion-escritorio.png', 'aplicacion-movil.png', 'aplicacion-movil-completa.png', 'validacion-formulario.png'], note: 'Capturas reales de tareas creadas durante la prueba; los datos se eliminan al finalizar. Un error HTTP se intercepta deliberadamente para verificar la presentación del mensaje.' });
    console.log(`Interfaz verificada: ${checks.length} comprobaciones; capturas reales guardadas.`);
  } finally {
    for (const id of createdIds) await context.request.delete(`${origin}/api/tasks/${id}`);
    await browser.close();
  }
});
