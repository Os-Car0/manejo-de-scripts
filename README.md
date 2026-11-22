# Sistema de Gestión de Tareas

Actividad **Manejo de Scripts**, Gestión del Proceso de Desarrollo de Software. Oscar Martínez Martínez · 3523110806 · 10B. Fecha académica: 22 de noviembre de 2026.

Aplicación Express con interfaz HTML/CSS/JavaScript, CRUD REST, persistencia JSON y monitoreo real. La entrega se implementa y verifica localmente. **No se ha creado un repositorio remoto ni publicado en Render**. La integración está preparada; su vinculación y ejecución remotas están pendientes de autorización.

## Inicio en Windows

Requisitos: Node.js 24 LTS recomendado (compatibilidad declarada 24–26), npm 10 o superior, Git. Docker Engine es opcional para ejecutar la aplicación, obligatorio para construir la imagen. En este equipo se detectó Node 26.13.0, npm 11.20.0 y Git 2.55.0; Docker no está disponible. Si PowerShell bloquea npm.ps1, utiliza **npm.cmd**.

```powershell
cd C:\dev\manejo-de-scripts
npm.cmd ci --ignore-scripts --no-fund
npm.cmd run config:validate
npm.cmd start
```

Abrir <http://localhost:3000>. `.env` es opcional y se carga con `--env-file-if-exists`. Nunca subir `.env`. `.env.example` contiene únicamente valores locales y nombres de configuración. El proyecto no necesita compilador: `npm run build` valida la sintaxis y los recursos; `release:artifact` produce el paquete de fuentes.

## Funcionalidades

Crear, consultar, buscar, filtrar, editar, completar, reabrir y eliminar tareas. Formularios accesibles con validación, mensajes y confirmación de eliminación; interfaz adaptable a móvil. El cliente utiliza `textContent` para mostrar texto del usuario. Helmet configura encabezados de seguridad; las entradas solo aceptan los campos documentados.

## API

| Método | Ruta | Resultado |
|---|---|---|
| GET | `/api/tasks` | 200, `{data: [...]}` |
| GET | `/api/tasks/:id` | 200 o 404 |
| POST | `/api/tasks` | 201, Location y tarea creada |
| PATCH | `/api/tasks/:id` | Actualización parcial; 200 o 404 |
| PUT | `/api/tasks/:id` | Reemplaza campos; título obligatorio; opcionales vuelven a sus valores predeterminados |
| DELETE | `/api/tasks/:id` | 204 o 404 |
| GET | `/health` | 200 o 503; salud del archivo, uptime y commit |
| GET | `/metrics` | 200; métricas JSON del proceso |

POST y PUT exigen título de 3–120 caracteres después de trim; descripción opcional de hasta 1000 caracteres; completed opcional booleano. PATCH exige al menos un campo permitido. Campos desconocidos se rechazan. Todos los métodos con cuerpo usan `application/json`. Errores: 400 validación/JSON, 404 recurso ausente, 409 límite de tareas, 413 cuerpo mayor de 16 KB, 415 tipo de contenido, 500 almacenamiento. Las respuestas 500 no exponen rutas ni trazas.

## Persistencia y alcance

`DATA_FILE` apunta a `./data/tasks.json`. Se crea vacío sin datos precargados. Cada operación lee el archivo; las escrituras se realizan sobre un temporal y un rename en el mismo directorio. Un archivo corrupto produce fallo visible y no se sobrescribe para ocultarlo. Un reinicio local conserva tareas si se conserva el archivo. Máximo 1000 tareas para limitar el trabajo síncrono y la memoria.

El diseño admite **un solo proceso y una sola instancia**. No ofrece transacciones entre procesos, historial, autenticación, permisos por usuario, recuperación automática ni copias de seguridad. Las tareas son compartidas por quienes acceden a la aplicación: solo datos de demostración. La escritura atómica evita archivos parcialmente reemplazados, pero no garantiza durabilidad frente a pérdida de energía. Para uso real se requiere base de datos, identidad, autorización, límites de tráfico y respaldos.

En Render gratuito el filesystem es efímero: se pierden tareas en reinicios, despliegues y suspensión por inactividad. No se añade disco de pago ni se promete persistencia remota. La propia interfaz muestra este aviso. Véase [Render Free](https://render.com/docs/free).

## Entornos y configuración

| Variable | Desarrollo / liberación | Producción |
|---|---|---|
| NODE_ENV | development / test | production |
| PORT | 3000 | 10000 en Render; Docker local 3000 |
| DATA_FILE | ./data/tasks.json; tests usan temporales aislados | /app/data/tasks.json, efímero |
| APP_COMMIT | local o SHA completo | SHA de 40 caracteres obligatorio si falta RENDER_GIT_COMMIT |
| RENDER_GIT_COMMIT | No requerida | Valor automático del proveedor, prioridad sobre APP_COMMIT |
| GITHUB_SHA | La establece GitHub | Commit validado por el workflow |
| RENDER_DEPLOY_HOOK_URL | No se usa localmente | GitHub Actions Secret |
| DEPLOY_BASE_URL | Origen local opcional para smoke/carga | GitHub Actions Secret con origen HTTPS real |
| EXPECTED_COMMIT | SHA real para health check | github.sha |

Hardware propuesto para desarrollo: 2 núcleos, 4 GB RAM, 1 GB libre; para Docker, 8 GB RAM y virtualización recomendados. Son recomendaciones del proyecto, no mediciones de consumo ni garantías de Render. Internet se requiere para dependencias y servicios externos. CI utiliza ubuntu-latest y Node 24; el equipo local usa Node 26. Las versiones exactas de bibliotecas se fijan en `package-lock.json`. La imagen base y las acciones usan etiquetas mayores: deben actualizarse y revisarse; no se declara una reproducción binaria idéntica indefinida.

## Scripts

Ejecutar todos mediante `npm.cmd run <comando>` en Windows o `npm run <comando>` en Linux. Salida 0 indica éxito; fallos establecen salida 1 y detienen los pasos dependientes.

| Comando | Archivo | Propósito |
|---|---|---|
| release:prepare | scripts/prepare-release.js | Verifica Node, archivos base y crea directorios de salida |
| deps:ci | scripts/install-deps.js | npm ci reproducible, sin scripts de instalación |
| config:validate | scripts/validate-env.js | Valida puerto, entorno, archivo y versión; --deploy exige secretos |
| lint | eslint.config.js | Análisis estático de aplicación, scripts y pruebas |
| test:release | scripts/test-release.js | Jest, Supertest, JSON y cobertura mínima 80 % |
| build | scripts/build.js | Sintaxis JS y recursos estáticos |
| release:artifact | scripts/create-artifact.js | tar.gz con lista permitida, manifest y SHA-256 |
| docker:build | scripts/build-docker.js | Verifica Docker Engine y construye imagen etiquetada con commit |
| deploy:plan | scripts/deploy.js | Genera plan local sin contactar a Render; requiere commit Git |
| deploy:render | scripts/deploy.js | POST único al hook, solo push a main en Actions |
| health:check | scripts/health-check.js | Espera hasta 10 min una instancia saludable con el SHA esperado |
| yaml:validate | scripts/validate-yaml.js | Parseo y comprobaciones básicas del workflow y Blueprint |
| security:check | scripts/check-secrets.js | Busca patrones de secretos sin imprimir valores |
| smoke | scripts/smoke.js | CRUD real local y captura respuestas; elimina su propia tarea |
| load:test | scripts/load-test.js | 200 GET locales, 5 clientes, 10 solicitudes de calentamiento |
| verify | package.json | Configuración, lint, pruebas, build, YAML y revisión de secretos |

`scripts/lib.js` centraliza errores y ejecución sin concatenación de comandos de shell. Los scripts de despliegue no imprimen el hook. Las pruebas del verificador emplean respuestas controladas para comprobar el rechazo de versiones antiguas; no constituyen evidencia de un despliegue real. La auditoría usa overrides explícitos de glob y minimatch para resolver avisos transitivos; la compatibilidad se comprueba con toda la suite.

## Verificación y evidencia

```powershell
npm.cmd run release:prepare
npm.cmd run verify
npm.cmd run release:artifact
# Con el servidor iniciado en otra terminal:
npm.cmd run smoke
npm.cmd run load:test
```

Jest exige 80 % en líneas, funciones, ramas y sentencias para **todos los módulos src**, incluido el punto de entrada. El frontend se verifica mediante interacción real de navegador; esa comprobación es distinta de la cobertura de Jest. Tests y scripts usan datos temporales. `evidence/` conserva resultados reales, cobertura HTML/LCOV/JSON, lint y monitoreo; `docs/` contiene entrega académica y matriz. Los resultados concretos se registran en `docs/informe-final.md` y no deben sustituirse por objetivos.

## Pipeline CI/CD

`.github/workflows/ci-cd.yml` es un único flujo para PR y push a main. Orden: checkout → Node 24 → npm ci → preparar → configuración → ESLint → Jest y cobertura → build/YAML/secretos → artefacto → imagen Docker → guardar evidencia. `deploy` depende de todo el job `validate`. Un error de lint, pruebas, cobertura, build o Docker impide el despliegue; no hay continue-on-error. PR no recibe secretos del job de despliegue ni lo ejecuta.

Solo un push a main con la variable de repositorio `RENDER_DEPLOY_ENABLED=true` habilita despliegue. La variable está deshabilitada si no existe. El grupo concurrency permite una ejecución en curso por referencia sin cancelarla durante un despliegue; GitHub puede reemplazar una ejecución pendiente por otra más reciente. Repetir un commit que ya responde saludable no vuelve a invocar el hook. No se reintenta automáticamente un POST ambiguo. Proteger main, exigir el job de validación y revisar cambios al workflow son configuraciones remotas pendientes; los scripts no pueden impedir una intervención manual de un administrador en Render.

Render construye desde el mismo SHA del repositorio vinculado usando el Dockerfile; la imagen de CI verifica la construcción pero **no se publica en un registro**. El tar.gz es el artefacto auditable de código y no la entrada de Render. El hook usa `ref=<github.sha>`, y `/health` debe devolver exactamente ese SHA y almacenamiento sano. Una aplicación antigua con HTTP 200 falla la verificación. Contadores y memoria de `/metrics` corresponden al proceso consultado y se reinician al reiniciarlo.

## Vincular GitHub y Render después de autorización

1. Crear repositorio remoto y subir main únicamente tras autorización del alumno. Activar Actions y protección de rama con validación obligatoria.
2. Crear servicio web Docker gratuito desde este repositorio usando `render.yaml`, rama main. No contratar recursos. La creación inicial de un servicio puede iniciar una primera construcción del proveedor; registrar ese hecho como configuración inicial, diferente del flujo posterior de Actions.
3. Confirmar en Render `Auto-Deploy: Off` (`autoDeployTrigger: off`) y deshabilitar previews automáticas. Nunca activar simultáneamente los autodeploys por push y el hook.
4. Confirmar que RENDER_GIT_COMMIT está disponible en ejecución. No fijar un SHA manual que oculte la versión real; probar `/health`.
5. Crear el environment `production` en GitHub y restringirlo a main cuando el plan lo permita. Guardar `RENDER_DEPLOY_HOOK_URL` y `DEPLOY_BASE_URL` en Secrets. El hook se obtiene del servicio, no se inventa ni se versiona.
6. Definir `RENDER_DEPLOY_ENABLED=true` después de revisar la configuración. Un nuevo push con validaciones correctas invoca el hook una vez y espera el commit exacto en /health.
7. Incorporar URL real, enlace del workflow, commit, respuestas y captura del despliegue a evidence y al informe. No hay resultados remotos disponibles todavía.

Mecanismo documentado por [Deploy Hooks](https://render.com/docs/deploy-hooks), [Deploying on Render](https://render.com/docs/deploys) y [Blueprint YAML](https://render.com/docs/blueprint-spec). No utilizar hooks de terceros ni incluirlos en capturas.

## Docker

```powershell
npm.cmd run docker:build
# Sustituir SHA_REAL por el hash obtenido con git rev-parse HEAD:
docker run --rm -p 3000:3000 manejo-de-scripts:SHA_REAL
```

El Dockerfile instala solo dependencias productivas, usa usuario node, healthcheck y recibe APP_COMMIT como argumento. El script exige Docker Engine disponible y registra el estado pendiente si falta. Sin volumen las tareas son efímeras al borrar el contenedor; para persistencia local se puede montar `/app/data` con permisos de escritura para node. No se afirma que la imagen se construyó en este equipo si Docker no está disponible.

## Niveles de servicio propuestos

SLI es la medición; SLO es el objetivo; SLA es un acuerdo con compromisos y consecuencias. En esta actividad **no existe un SLA contractual firmado**. Se proponen disponibilidad mensual 99 %, p95 <500 ms, errores 5xx <1 % y recuperación 30 min. Para noviembre de 30 días el presupuesto de indisponibilidad al 1 % es 432 minutos (7 h 12 min). Se debe medir disponibilidad desde fuera del proceso con sondeos cada minuto durante todo el mes, incluyendo arranques fríos; uptime no la demuestra.

Latencia propuesta: GET /api/tasks con hasta 1000 tareas, 5 clientes concurrentes, servicio caliente, 10 min de ensayo; p95 observado desde el cliente, cuerpo completo y fallos de red por separado. El ensayo local incluido es más breve (200 solicitudes) y no acredita esa ventana de 10 min ni el desempeño de Render. 5xx se calcula sobre respuestas API, separando 4xx de validación. En /metrics, p95 se calcula con el rango más reciente de hasta 1000 respuestas, no un histórico mensual. Una solicitud a /metrics se registra al finalizar, por lo que no está incluida en su propia respuesta.

RTO de 30 min: detectar y clasificar (5), identificar último commit sano (5), recuperar mediante versión anterior validada (15) y verificar SHA/salud (5). Es una meta sin ensayo remoto; un rollback de código no recupera datos perdidos. La pérdida de datos en Render gratuito impide proponer un RPO de cero. Aceptación de liberación: lint limpio, todos los tests correctos, cuatro coberturas ≥80 %, configuración/YAML válidos, artefacto trazable, Docker construido, sin secretos detectados y health check del commit publicado.

Render Free suspende servicios tras 15 min sin tráfico; el arranque puede tardar aproximadamente un minuto, el disco es efímero y existen cuotas de horas y compilación. Estas condiciones pueden impedir el objetivo de disponibilidad y p95; los SLO son aspiraciones del caso de estudio, no garantías del proveedor. No se usa tráfico artificial para evitar la suspensión. Para continuidad real se debe reevaluar arquitectura y alojamiento antes de comprometer niveles contractuales.
