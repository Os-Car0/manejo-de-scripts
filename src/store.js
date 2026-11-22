const fs = require('node:fs');
const path = require('node:path');
const { randomUUID } = require('node:crypto');

class TaskStore {
  constructor(file) {
    this.file = file;
    fs.mkdirSync(path.dirname(file), { recursive: true });
    if (!fs.existsSync(file)) this.save([]);
    this.read();
  }

  read() {
    const tasks = JSON.parse(fs.readFileSync(this.file, 'utf8'));
    if (!Array.isArray(tasks) || tasks.some(task => !task || typeof task.id !== 'string' || typeof task.title !== 'string' || typeof task.description !== 'string' || typeof task.completed !== 'boolean' || typeof task.createdAt !== 'string' || typeof task.updatedAt !== 'string')) {
      throw new Error('El archivo de tareas no tiene un formato válido.');
    }
    return tasks;
  }

  save(tasks) {
    const temporary = `${this.file}.${process.pid}.tmp`;
    try {
      fs.writeFileSync(temporary, JSON.stringify(tasks, null, 2), { mode: 0o600 });
      fs.renameSync(temporary, this.file);
    } finally {
      if (fs.existsSync(temporary)) fs.unlinkSync(temporary);
    }
  }

  health() {
    this.read();
    fs.accessSync(this.file, fs.constants.R_OK | fs.constants.W_OK);
    fs.accessSync(path.dirname(this.file), fs.constants.W_OK);
    return true;
  }

  create(input) {
    const tasks = this.read();
    if (tasks.length >= 1000) {
      const error = new Error('Se alcanzó el límite de 1000 tareas de esta demostración.');
      error.status = 409;
      throw error;
    }
    const now = new Date().toISOString();
    const task = { id: randomUUID(), title: input.title, description: input.description || '', completed: input.completed || false, createdAt: now, updatedAt: now };
    tasks.unshift(task);
    this.save(tasks);
    return task;
  }

  update(id, input) {
    const tasks = this.read();
    const index = tasks.findIndex(task => task.id === id);
    if (index === -1) return null;
    tasks[index] = { ...tasks[index], ...input, updatedAt: new Date().toISOString() };
    this.save(tasks);
    return tasks[index];
  }

  remove(id) {
    const tasks = this.read();
    const index = tasks.findIndex(task => task.id === id);
    if (index === -1) return false;
    tasks.splice(index, 1);
    this.save(tasks);
    return true;
  }
}
module.exports = { TaskStore };
