const $ = selector => document.querySelector(selector);
let tasks = [];
let filter = 'all';
let editingId = null;
let deletingId = null;
let toastTimer;
let busy = false;

function notify(message, error = false) {
  clearTimeout(toastTimer);
  const toast = $('#toast');
  toast.textContent = message;
  toast.className = `toast${error ? ' error' : ''}`;
  toast.hidden = false;
  toastTimer = setTimeout(() => { toast.hidden = true; }, 6000);
}

async function request(url, options = {}) {
  const response = await fetch(url, { ...options, headers: { 'Content-Type': 'application/json' }, signal: AbortSignal.timeout(15000) });
  if (response.status === 204) return null;
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'No fue posible completar la operación.');
  return result;
}

function textElement(tag, value, className) {
  const element = document.createElement(tag);
  element.textContent = value;
  if (className) element.className = className;
  return element;
}

function render() {
  const completed = tasks.filter(task => task.completed).length;
  $('#total').textContent = tasks.length;
  $('#pending').textContent = tasks.length - completed;
  $('#completed').textContent = completed;
  $('#nav-count').textContent = tasks.length;
  $('#list-count').textContent = tasks.length;
  $('#progress-label').textContent = `${tasks.length ? Math.round(completed / tasks.length * 100) : 0} % del total`;
  const search = $('#search').value.toLocaleLowerCase('es');
  const visible = tasks.filter(task => (filter === 'all' || (filter === 'completed' ? task.completed : !task.completed)) && `${task.title} ${task.description}`.toLocaleLowerCase('es').includes(search));
  $('#tasks').replaceChildren();
  for (const task of visible) {
    const row = document.createElement('article');
    row.className = `task-row${task.completed ? ' done' : ''}`;
    const check = document.createElement('input');
    check.type = 'checkbox'; check.className = 'task-check'; check.checked = task.completed;
    check.setAttribute('aria-label', `${task.completed ? 'Reabrir' : 'Completar'} ${task.title}`);
    check.addEventListener('change', () => mutate(async () => {
      await request(`/api/tasks/${task.id}`, { method: 'PATCH', body: JSON.stringify({ completed: check.checked }) });
      notify(check.checked ? '¡Una tarea menos! Buen trabajo.' : 'Tarea marcada como pendiente.');
    }));
    const content = textElement('div', '', 'task-content');
    content.append(textElement('h3', task.title));
    if (task.description) content.append(textElement('p', task.description));
    const meta = textElement('div', '', 'task-meta');
    meta.append(textElement('span', task.completed ? 'Completada' : 'Pendiente', 'badge'), textElement('span', `Creada el ${new Date(task.createdAt).toLocaleDateString('es-MX', { day: 'numeric', month: 'short' })}`));
    content.append(meta);
    const actions = textElement('div', '', 'row-actions');
    const edit = textElement('button', '✎', 'icon-button');
    edit.setAttribute('aria-label', `Editar ${task.title}`); edit.addEventListener('click', () => openEditor(task));
    const remove = textElement('button', '×', 'icon-button');
    remove.setAttribute('aria-label', `Eliminar ${task.title}`); remove.addEventListener('click', () => {
      deletingId = task.id; $('#delete-description').textContent = task.title; $('#delete-error').textContent = ''; $('#delete-dialog').showModal();
    });
    actions.append(edit, remove); row.append(check, content, actions); $('#tasks').append(row);
  }
  $('#empty').hidden = visible.length > 0;
  $('#empty-title').textContent = tasks.length ? 'No hay tareas en esta vista' : 'Todo empieza con una tarea';
  $('#empty-description').textContent = tasks.length ? 'Prueba otro filtro o cambia tu búsqueda.' : 'Agrega tu primer pendiente y empieza a avanzar.';
  $('#empty-add').hidden = tasks.length > 0;
  $('#visible-count').textContent = `${visible.length} de ${tasks.length} tareas`;
}

async function refresh() {
  const result = await request('/api/tasks');
  tasks = result.data; render();
}

async function mutate(operation, errorTarget) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('button, .task-check').forEach(element => { element.disabled = true; });
  try { await operation(); await refresh(); }
  catch (error) {
    const message = error.name === 'TimeoutError' ? 'El servidor tardó demasiado. Reintenta y verifica la lista.' : error.message;
    notify(message, true);
    if (errorTarget) $(errorTarget).textContent = message;
    render();
  } finally {
    busy = false; document.querySelectorAll('button, .task-check').forEach(element => { element.disabled = false; });
  }
}

function openEditor(task) {
  editingId = task ? task.id : null;
  $('#task-form').reset(); $('#form-error').textContent = '';
  $('#dialog-title').textContent = task ? 'Editar tarea' : 'Nueva tarea';
  $('#save-task').textContent = task ? 'Guardar cambios' : 'Crear tarea';
  $('#title').value = task ? task.title : ''; $('#description').value = task ? task.description : '';
  $('#task-dialog').showModal(); $('#title').focus();
}
$('#new-task').addEventListener('click', () => openEditor());
$('#empty-add').addEventListener('click', () => openEditor());
document.querySelectorAll('[data-close]').forEach(button => button.addEventListener('click', () => $('#task-dialog').close()));
$('#cancel-delete').addEventListener('click', () => $('#delete-dialog').close());
$('#task-form').addEventListener('submit', event => {
  event.preventDefault();
  const title = $('#title').value.trim();
  if (title.length < 3) { $('#form-error').textContent = 'Escribe al menos 3 caracteres sin contar espacios externos.'; return; }
  mutate(async () => {
    await request(editingId ? `/api/tasks/${editingId}` : '/api/tasks', { method: editingId ? 'PATCH' : 'POST', body: JSON.stringify({ title, description: $('#description').value }) });
    $('#task-dialog').close(); notify(editingId ? 'Cambios guardados.' : 'Tarea creada. ¡Vamos por ello!');
  }, '#form-error');
});
$('#delete-form').addEventListener('submit', event => {
  event.preventDefault();
  mutate(async () => { await request(`/api/tasks/${deletingId}`, { method: 'DELETE' }); $('#delete-dialog').close(); notify('Tarea eliminada.'); }, '#delete-error');
});
document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {
  filter = button.dataset.filter;
  document.querySelectorAll('[data-filter]').forEach(tab => { tab.classList.toggle('selected', tab === button); tab.setAttribute('aria-pressed', String(tab === button)); }); render();
}));
$('#search').addEventListener('input', render);
refresh().catch(() => {
  $('#tasks').replaceChildren(); $('#empty').hidden = true;
  $('#loading').textContent = 'No se pudo cargar el espacio. Verifica la conexión y vuelve a cargar la página.';
  notify('No fue posible conectar con el servidor.', true);
}).finally(() => { if ($('#loading').textContent.startsWith('Cargando')) $('#loading').hidden = true; });
