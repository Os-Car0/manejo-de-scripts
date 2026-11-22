# Informe final de implementación local

Fecha académica: 22 de noviembre de 2026. Proyecto: C:/dev/manejo-de-scripts. Rama main local; no se creó remoto ni se realizó push.

## Resultado comprobado

Se aprobaron 35 de 35 pruebas en 3 suites. La cobertura fue de 98.07 % en líneas, 92.50 % en funciones, 97.31 % en ramas y 96.03 % en sentencias.

ESLint: 0 errores, 0 advertencias. Construcción: 25 archivos JS. Auditoría: 0 vulnerabilidades. YAML: parseo y controles básicos correctos. Docker: no instalado; construcción pendiente. GitHub Actions y Render: preparados, sin ejecución remota.

La muestra local completó 200 solicitudes, p95 17.578 ms, 5xx 0.00 %, errores de red 0. Es una muestra corta con lista vacía, no una medición mensual ni una prueba de Render. Chrome: 9 comprobaciones y 4 capturas reales.

## Archivos y entregables

```text
src/                    API, configuración, servidor, métricas y persistencia
public/                 Interfaz HTML, CSS, JavaScript e icono
tests/                  Pruebas de API, servidor y verificador de despliegue
scripts/                Preparación, instalación, configuración, pruebas, build,
                        artefacto, Docker, despliegue, health, smoke, carga y UI
.github/workflows/      ci-cd.yml, flujo único para PR y push a main
docs/                   Word, PDF, diagrama, informe y matriz de cumplimiento
evidence/               Logs, JSON, cobertura y capturas reales
dist/                   Artefacto tar.gz y manifest SHA-256 (ignorado por Git)
data/                   JSON local (ignorado por Git)
Dockerfile              Imagen Node 24 con usuario sin privilegios y healthcheck
render.yaml             Blueprint Docker gratuito, autoDeploy off
package*.json           Comandos, dependencias y lockfile
```

URL local comprobada: http://localhost:3000. Arranque: `npm.cmd start`. El servidor de verificación puede detenerse al terminar la revisión; ejecutar el comando para abrirlo de nuevo.

Documentos: `docs/Manejo-de-Scripts.docx` y `docs/Manejo-de-Scripts.pdf`. Evidencias: `evidence/`. Matriz individual de los requisitos originales y adicionales: `docs/matriz-cumplimiento.md` y `.json`.

Word abre, actualiza el índice y pagina el editable, pero su exportación PDF se bloquea; LibreOffice tampoco está disponible. El PDF se genera con ReportLab desde el mismo contenido y figuras, con índice propio. Su paginación puede diferir. Se revisa el PDF por separado; la fidelidad visual exacta de Word queda como limitación (A10 PARCIAL en la matriz).

## Funcionalidades y tecnologías

Node.js, Express, HTML/CSS/JavaScript, Jest, Supertest, ESLint, Helmet, Git, Dockerfile, GitHub Actions y Blueprint de Render. Playwright verifica la interfaz con Chrome. La aplicación permite crear, consultar, editar, completar, reabrir, buscar, filtrar y eliminar tareas; valida entradas y muestra mensajes. Persistencia JSON con reemplazo atómico, máximo 1000 tareas y una instancia. Render gratuito tiene almacenamiento efímero.

## Scripts y pipeline

Preparación, npm ci, configuración, pruebas con cobertura, build, artefacto y plan local se ejecutaron. Smoke, carga e interfaz también se ejecutaron. Docker devuelve error explícito por ausencia de herramienta. deploy:render rechaza ejecución fuera de Actions. El verificador posterior se prueba contra una versión anterior y una esperada; no hay health check público real todavía.

El job deploy depende de validate, se limita a push a main y exige RENDER_DEPLOY_ENABLED=true. El hook solicita el SHA probado, Render mantiene AutoDeploy off y /health debe devolver el mismo commit. No hay secretos reales configurados, dominio público ni despliegue remoto demostrado. Validar YAML local no equivale a ejecutar el workflow ni a validarlo en el proveedor.

## Incidencias y soluciones

- PowerShell bloqueó npm.ps1: se usó npm.cmd, sin modificar la política del sistema.
- El ejecutor restringido y el navegador integrado fallaron al iniciar: se utilizaron las autorizaciones de ejecución y Chrome mediante Playwright para completar las comprobaciones.
- Git detectó distinta propiedad del directorio: se limitó safe.directory al comando y ruta del proyecto, sin modificar configuración global.
- Alertas de dependencias de desarrollo: actualización a ESLint 10 y overrides de glob/minimatch, con suite completa posterior y auditoría sin alertas.
- Docker no está instalado: archivos y validación de ausencia implementados; imagen no construida localmente.
- Render y GitHub no están vinculados: se conserva la restricción de no crear recursos ni publicar sin autorización.

## Pendientes autorizables

1. Instalar o disponer de Docker Engine y ejecutar la construcción, arranque y healthcheck del contenedor.
2. Autorizar creación del repositorio remoto y push de main.
3. Configurar protección de main y validación obligatoria en GitHub.
4. Autorizar servicio web gratuito de Render y revisar AutoDeploy off.
5. Definir Secrets RENDER_DEPLOY_HOOK_URL y DEPLOY_BASE_URL; environment production; variable RENDER_DEPLOY_ENABLED=true.
6. Ejecutar Actions y conservar enlace, commit, logs y health del mismo SHA en Render.
7. Medir disponibilidad durante un mes, ejecutar carga de 10 minutos con hasta 1000 tareas y ensayar recuperación. Los SLO siguen siendo objetivos propuestos.

Se completó la implementación local posible. No se solicitan credenciales ni se realiza despliegue sin autorización posterior.

## Verificación final de esta entrega

PDF final: 28 páginas inspeccionadas, nueve tablas y cuatro figuras; márgenes y formato comprobados. Word abrió y paginó el editable (véase evidence/word-validation.json); su fidelidad visual exacta continúa PARCIAL por el bloqueo del convertidor.

El comando independiente npm run health:check también pasó contra un servidor temporal local con el SHA real. Su evidencia se llama local-health-check-cli.json y no acredita un despliegue en Render.

Se corrigió la propiedad de .git con una copia verificada de sus metadatos, preservando commits e índice y conservando un respaldo dentro de tmp. Git funciona normalmente sin modificar configuración global. El intento previo de Set-Acl fue rechazado por Windows y quedó registrado.

El SHA-256 del artefacto documentado se comprobó leyendo el tar.gz, y su contenido no incluye .env, datos, node_modules ni .git. La revisión complementaria de secretos incluyó scripts Python y PowerShell y no encontró coincidencias. Las evidencias de cierre son final-review.json, artifact-validation.json y document-visual-review.json.
