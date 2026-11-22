class Metrics {
  constructor() {
    this.total = 0;
    this.errors4xx = 0;
    this.errors5xx = 0;
    this.durationMs = 0;
    this.samples = [];
    this.api = { total: 0, errors5xx: 0, samples: [] };
    this.byStatus = {};
  }

  record(status, duration, api) {
    this.total += 1;
    this.byStatus[status] = (this.byStatus[status] || 0) + 1;
    if (status >= 400 && status < 500) this.errors4xx += 1;
    if (status >= 500) this.errors5xx += 1;
    this.durationMs += duration;
    this.samples.push(duration);
    if (this.samples.length > 1000) this.samples.shift();
    if (api) {
      this.api.total += 1;
      if (status >= 500) this.api.errors5xx += 1;
      this.api.samples.push(duration);
      if (this.api.samples.length > 1000) this.api.samples.shift();
    }
  }

  snapshot(healthy, commit) {
    const percentile = values => values.length ? [...values].sort((a, b) => a - b)[Math.ceil(values.length * 0.95) - 1] : null;
    return {
      timestamp: new Date().toISOString(), commit,
      scope: 'Proceso actual; contadores desde el inicio; p95 sobre las últimas 1000 respuestas finalizadas.',
      requests: { total: this.total, byStatus: { ...this.byStatus } },
      responseTimeMs: { average: this.total ? this.durationMs / this.total : null, p95: percentile(this.samples), sampleSize: this.samples.length },
      errors: { http4xx: this.errors4xx, http5xx: this.errors5xx, total: this.errors4xx + this.errors5xx, percentage: this.total ? (this.errors4xx + this.errors5xx) / this.total * 100 : 0, serverPercentage: this.total ? this.errors5xx / this.total * 100 : 0 },
      api: { requests: this.api.total, http5xx: this.api.errors5xx, serverErrorPercentage: this.api.total ? this.api.errors5xx / this.api.total * 100 : 0, p95Ms: percentile(this.api.samples), sampleSize: this.api.samples.length },
      uptimeSeconds: process.uptime(), health: healthy ? 'ok' : 'degraded', memoryBytes: process.memoryUsage()
    };
  }
}
module.exports = { Metrics };
