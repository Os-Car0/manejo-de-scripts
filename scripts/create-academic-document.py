"""Genera la entrega editable con evidencias existentes; usar Python del runtime de Codex."""
from pathlib import Path
import json
import platform
from datetime import datetime, timezone
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'
EVIDENCE = ROOT / 'evidence'
DOCS.mkdir(exist_ok=True)

def read(name):
    return json.loads((EVIDENCE / name).read_text(encoding='utf-8-sig'))

tests = read('tests.json')
coverage = read('coverage/coverage-summary.json')['total']
load = read('load-test.json')
browser = read('browser-check.json')
health = read('health-response.json')
metrics = read('metrics-response.json')
build = read('build.json')
artifact = read('artifact.json')
audit = read('npm-audit.json')
lint = read('eslint.json')
versions = read('tool-availability.json')
lint_errors = sum(item['errorCount'] for item in lint)
lint_warnings = sum(item['warningCount'] for item in lint)
result_line = (f"Se aprobaron {tests['numPassedTests']} de {tests['numTotalTests']} pruebas en "
               f"{tests['numPassedTestSuites']} suites. La cobertura fue de "
               f"{coverage['lines']['pct']:.2f} % en líneas, {coverage['functions']['pct']:.2f} % en funciones, "
               f"{coverage['branches']['pct']:.2f} % en ramas y {coverage['statements']['pct']:.2f} % en sentencias.")

matrix = [
    ['D1', 'Justificación del pipeline', 'CUMPLE', 'README.md; documento §7', 'Workflow y explicación de dependencias'],
    ['D2', 'Entorno de liberación y despliegue', 'CUMPLE', 'Dockerfile; .env.example; documento §8', 'tool-availability.json; release-environment.json'],
    ['D3', 'Niveles de servicio acordados o propuestos', 'CUMPLE', 'README.md; documento §9', 'load-test.json; metas diferenciadas de resultados'],
    ['D4', 'Métricas para el monitoreo', 'CUMPLE', 'src/metrics.js; src/app.js; documento §10', 'metrics-response.json; health-response.json; tests.json'],
    ['D5', 'Parámetros de herramientas', 'CUMPLE', 'package.json; jest.config.js; eslint.config.js; documento §11', 'package-lock.json; yaml-validation.json'],
    ['I1', 'Herramienta de liberación configurada y vinculada al despliegue', 'PARCIAL', '.github/workflows/ci-cd.yml; render.yaml; scripts/deploy.js', 'YAML local válido; faltan repositorio y servicio remotos autorizados'],
    ['R1', 'Scripts del pipeline', 'CUMPLE', '.github/workflows/ci-cd.yml; scripts/lib.js', 'local-validation.json; pruebas del verificador'],
    ['R2', 'Scripts del entorno de liberación', 'CUMPLE', 'scripts/prepare-release.js; install-deps.js; validate-env.js', 'release-environment.json; local-validation.log'],
    ['R3', 'Scripts de pruebas de liberación', 'CUMPLE', 'scripts/test-release.js; tests/', 'tests.json; coverage/; eslint.json'],
    ['R4', 'Scripts de generación del despliegue', 'CUMPLE', 'scripts/deploy.js; deployment.js; health-check.js', 'deployment-plan.json; pruebas de rechazo de SHA anterior'],
    ['A1', 'Proyecto independiente y Git main local', 'CUMPLE', 'C:/dev/manejo-de-scripts; .git/', 'git-status.json; commit local en español'],
    ['A2', 'CRUD, validaciones y mensajes de interfaz', 'CUMPLE', 'src/app.js; src/store.js; public/', 'endpoints.json; browser-check.json; screenshots/'],
    ['A3', 'Persistencia local y límites documentados', 'CUMPLE', 'src/store.js; README.md', 'Tests de reinicio, corrupción y escritura atómica'],
    ['A4', 'Pruebas y cuatro coberturas mínimas de 80 %', 'CUMPLE', 'tests/; jest.config.js', 'tests.json; coverage/coverage-summary.json'],
    ['A5', 'Dependencias reproducibles y análisis estático', 'CUMPLE', 'package-lock.json; eslint.config.js', 'local-validation.log; eslint.json; npm-audit.json'],
    ['A6', 'Artefacto de liberación trazable', 'CUMPLE', 'scripts/create-artifact.js; dist/', 'artifact.json con commit y SHA-256'],
    ['A7', 'Construcción y ejecución de imagen Docker local', 'PENDIENTE', 'Dockerfile; .dockerignore; scripts/build-docker.js', 'docker.json: Docker no está instalado'],
    ['A8', 'Pipeline ejecutado en GitHub Actions', 'PENDIENTE', '.github/workflows/ci-cd.yml', 'Sin repositorio remoto; validación local solamente'],
    ['A9', 'Despliegue real en Render y commit verificado', 'PENDIENTE', 'render.yaml; scripts/deploy.js; health-check.js', 'Sin servicio ni URL pública; ejecución remota no autorizada'],
    ['A10', 'Documento académico Word y PDF', 'CUMPLE', 'docs/Manejo-de-Scripts.docx; docs/Manejo-de-Scripts.pdf', 'document-validation.json; revisión de páginas renderizadas'],
    ['A11', 'Evidencias reales y matriz de cumplimiento', 'CUMPLE', 'evidence/; docs/matriz-cumplimiento.md', 'Registros de ejecución y capturas locales'],
    ['A12', 'Medición mensual de disponibilidad y ensayo de recuperación', 'PENDIENTE', 'Objetivos y protocolo en documento §9', 'Sin mes de observación ni incidente remoto ensayado'],
    ['A13', 'Protección de secretos y despliegue exclusivo de main', 'PARCIAL', '.gitignore; workflow; scripts/check-secrets.js', 'secret-scan.json; protecciones y Secrets remotos pendientes'],
]
(DOCS / 'matriz-cumplimiento.json').write_text(json.dumps(matrix, ensure_ascii=False, indent=2), encoding='utf-8')
matrix_md = '# Matriz de cumplimiento\n\nLa evidencia indicada sin prefijo se encuentra en evidence/. CUMPLE evalúa el entregable local; no equivale a una ejecución remota. Los diez primeros registros evalúan individualmente los requisitos originales de la profesora.\n\n| ID | Requisito | Estado | Archivos | Evidencia y alcance |\n|---|---|---|---|---|\n'
matrix_md += '\n'.join('| ' + ' | '.join(row) + ' |' for row in matrix) + '\n'
(DOCS / 'matriz-cumplimiento.md').write_text(matrix_md, encoding='utf-8')

FONT = 'C:/Windows/Fonts/arial.ttf'
BOLD = 'C:/Windows/Fonts/arialbd.ttf'
diagram = Image.new('RGB', (1400, 1550), 'white')
draw = ImageDraw.Draw(diagram)
stages = [
    ('Código y entorno', 'Checkout · Node.js 24 · npm ci'),
    ('Validación obligatoria', 'Configuración · ESLint · Jest y cobertura ≥80 %'),
    ('Preparación de la liberación', 'Construcción · Artefacto SHA-256 · Imagen Docker'),
    ('Condición de despliegue', 'Validación correcta · push a main · enabled=true'),
    ('Solicitud a Render', 'AutoDeploy off · hook HTTPS con ref=commit'),
    ('Comprobación de la versión', '/health sano · commit publicado = commit esperado'),
]
for i, (title, detail) in enumerate(stages):
    y = 30 + i * 255
    draw.rounded_rectangle((25, y, 1375, y + 185), radius=18, fill='#f4f5f9' if i != 3 else '#eeebf8', outline='#aab0c3', width=3)
    draw.text((700, y + 51), title, font=ImageFont.truetype(BOLD, 46), fill='#111111', anchor='mm')
    draw.text((700, y + 120), detail, font=ImageFont.truetype(FONT, 38), fill='#252638', anchor='mm')
    if i < 5:
        draw.line((700, y + 186, 700, y + 243), fill='#626a82', width=5)
        draw.polygon([(688, y + 229), (712, y + 229), (700, y + 248)], fill='#626a82')
diagram.save(DOCS / 'pipeline.png')

doc = Document()
section = doc.sections[0]
section.top_margin = section.bottom_margin = section.left_margin = section.right_margin = Inches(1)
section.page_width = Inches(8.5)
section.page_height = Inches(11)
section.header_distance = section.footer_distance = Inches(.5)
for style_name in ['Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2', 'Heading 3', 'Caption']:
    style = doc.styles[style_name]
    style.font.name = 'Arial'
    style.font.color.rgb = RGBColor(0, 0, 0)
    style.font.size = Pt(14 if style_name in ['Title', 'Heading 1', 'Heading 2', 'Heading 3'] else 12)
    style.font.bold = style_name in ['Title', 'Heading 1', 'Heading 2', 'Heading 3']
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.space_after = Pt(8)
    style.paragraph_format.widow_control = True
normal = doc.styles['Normal']
normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
for level in ['Heading 1', 'Heading 2']:
    doc.styles[level].paragraph_format.keep_with_next = True
    doc.styles[level].paragraph_format.space_before = Pt(12)
footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
footer.add_run('Página ')
field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
doc.core_properties.title = 'Manejo de Scripts: Implementación de un Pipeline de Liberación y Despliegue Continuo'
doc.core_properties.author = 'Oscar Martínez Martínez'
doc.core_properties.subject = 'Gestión del Proceso de Desarrollo de Software'
doc.core_properties.keywords = 'DevOps, CI/CD, scripts, pruebas, Render, GitHub Actions'

def p(text, bold=False):
    para = doc.add_paragraph()
    para.add_run(text).bold = bold
    return para

def heading(text, level=1, new_page=False):
    if new_page: doc.add_page_break()
    return doc.add_heading(text, level)

def table(headers, rows, widths=None):
    t = doc.add_table(rows=1, cols=len(headers))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    if widths:
        for col, width in zip(t.columns, widths): col.width = Inches(width)
    for cell, title in zip(t.rows[0].cells, headers): cell.text = str(title)
    repeat = OxmlElement('w:tblHeader'); repeat.set(qn('w:val'), 'true'); t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for row in rows:
        for cell, value in zip(t.add_row().cells, row): cell.text = str(value)
    for row_index, row in enumerate(t.rows):
        tr_pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement('w:cantSplit'); tr_pr.append(cant_split)
        for col_index, cell in enumerate(row.cells):
            if widths: cell.width = Inches(widths[col_index])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tc_pr = cell._tc.get_or_add_tcPr()
            borders = OxmlElement('w:tcBorders')
            for side in ['top', 'left', 'bottom', 'right']:
                edge = OxmlElement('w:' + side); edge.set(qn('w:val'), 'single'); edge.set(qn('w:sz'), '5'); edge.set(qn('w:color'), 'D9D9D9'); borders.append(edge)
            tc_pr.append(borders)
            margins = OxmlElement('w:tcMar')
            for side in ['top', 'left', 'bottom', 'right']:
                edge = OxmlElement('w:' + side); edge.set(qn('w:w'), '100'); edge.set(qn('w:type'), 'dxa'); margins.append(edge)
            tc_pr.append(margins)
            if row_index == 0 or row_index % 2 == 0:
                shade = OxmlElement('w:shd'); shade.set(qn('w:fill'), 'DFE5EF' if row_index == 0 else 'F5F6F9'); tc_pr.append(shade)
            for para in cell.paragraphs:
                para.alignment = WD_ALIGN_PARAGRAPH.LEFT
                para.paragraph_format.space_after = Pt(3)
                para.paragraph_format.line_spacing = 1.5
                for run in para.runs:
                    run.font.name = 'Arial'; run.font.size = Pt(12); run.bold = row_index == 0
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

def caption(text):
    para = doc.add_paragraph(text, style='Caption')
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return para

def figure(file, width, text):
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.keep_with_next = True
    para.add_run().add_picture(str(file), width=Inches(width))
    caption(text)

def code_excerpt(file, start, end):
    lines = (ROOT / file).read_text(encoding='utf-8').splitlines()
    caption(f'Extracto real de {file}, líneas {start} a {end}.')
    for line in lines[start-1:end]:
        para = doc.add_paragraph(line)
        para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.line_spacing = 1.5

# 1 Portada
for _ in range(2): doc.add_paragraph()
cover = doc.add_paragraph('Manejo de Scripts: Implementación de un Pipeline de Liberación y Despliegue Continuo', style='Title')
cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph()
for line in ['Sistema de Gestión de Tareas', 'Actividad académica de implementación y validación local']:
    para = p(line); para.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph()
for line in ['Alumno: Oscar Martínez Martínez', 'Matrícula: 3523110806', 'Grupo: 10B', 'Materia: Gestión del Proceso de Desarrollo de Software', 'Docente: Julieta E. H. Guzmán', 'Actividad: Manejo de Scripts', 'Fecha: 22 de noviembre de 2026']:
    para = p(line); para.alignment = WD_ALIGN_PARAGRAPH.CENTER
doc.add_paragraph()
p('Entrega local verificable. La vinculación a GitHub y el despliegue público requieren autorización posterior.').alignment = WD_ALIGN_PARAGRAPH.CENTER

# 2 Índice
doc.add_page_break()
index_title = doc.add_paragraph('2 Índice')
index_title.runs[0].bold = True; index_title.runs[0].font.size = Pt(14)
p('La portada corresponde al apartado 1. El índice incluye los apartados del desarrollo y sus páginas; sus entradas se pueden actualizar en Word con la opción Actualizar tabla.')
toc = doc.add_paragraph()
begin = OxmlElement('w:fldChar'); begin.set(qn('w:fldCharType'), 'begin')
instruction = OxmlElement('w:instrText'); instruction.set(qn('xml:space'), 'preserve'); instruction.text = ' TOC \\o "1-1" \\h \\z \\u '
separate = OxmlElement('w:fldChar'); separate.set(qn('w:fldCharType'), 'separate')
end = OxmlElement('w:fldChar'); end.set(qn('w:fldCharType'), 'end')
for item in [begin, instruction, separate]: toc.add_run()._r.append(item)
toc.add_run('Índice actualizable de los apartados 3 a 21.')
toc.add_run()._r.append(end)

heading('3 Introducción', new_page=True)
p('La liberación de software exige convertir el código fuente en una versión identificable, verificar que conserva su comportamiento y comprobar que esa misma versión llega al entorno de ejecución. Esta actividad implementa ese recorrido mediante un Sistema de Gestión de Tareas, con scripts ejecutables, pruebas automatizadas y una configuración de integración y despliegue continuo. El resultado local puede revisarse sin depender de una cuenta de alojamiento.')
p('El proyecto se creó de forma independiente en C:/dev/manejo-de-scripts. La aplicación utiliza Node.js y Express para la API, y HTML, CSS y JavaScript para la interfaz. Jest y Supertest verifican el comportamiento del servidor; ESLint analiza el código; Git conserva versiones; Docker describe una unidad de ejecución; GitHub Actions coordina el pipeline y Render se define como destino de despliegue futuro. Las decisiones se relacionan con archivos concretos, en lugar de limitarse a una descripción conceptual de las herramientas.')
p('El alcance realizado comprende creación, instalación, análisis estático, pruebas, mediciones HTTP, comprobación visual y generación del artefacto. No se creó repositorio remoto, no se efectuó push y no se aprovisionó un servicio público. Docker no está instalado en el equipo, por lo que su construcción local se registra como pendiente. Estas condiciones separan una configuración preparada de una operación demostrada y evitan presentar resultados que todavía no existen.')
p(result_line)
p('La organización del documento sigue el flujo de una liberación: describe el caso, establece objetivos y condiciones de operación, explica los scripts y la configuración, muestra el diagrama y analiza las evidencias disponibles. La matriz final permite evaluar cada requisito original de la actividad, incluida la vinculación remota que aún requiere intervención autorizada.')

heading('4 Descripción del caso de estudio', new_page=True)
p('El Sistema de Gestión de Tareas permite que una persona registre sus pendientes en un espacio web compartido. Cada tarea contiene id, title, description, completed, createdAt y updatedAt. El identificador se genera con randomUUID; las fechas se almacenan en formato ISO 8601. El título es obligatorio, mientras que descripción y estado tienen valores predeterminados. La interfaz muestra totales, pendientes y completadas calculados a partir de los registros devueltos por la API.')
p('El usuario puede crear una tarea, editar su título y descripción, marcarla como completada, reabrirla y eliminarla después de confirmar la acción. La búsqueda local consulta título y descripción, y los filtros separan todas, pendientes y completadas. Los mensajes de éxito y error informan el resultado. El formulario conserva su contenido si una operación falla para facilitar una corrección o un reintento consciente.')
table(['Capa', 'Implementación y responsabilidad'], [
    ['Presentación', 'public/index.html, styles.css y app.js; formularios, filtros, contadores y diálogos.'],
    ['HTTP y negocio', 'src/app.js; rutas REST, validación, salud, métricas y errores.'],
    ['Datos', 'src/store.js; JSON, límite de 1000 tareas y reemplazo atómico del archivo.'],
    ['Operación', 'src/server.js y src/config.js; puerto, entorno, versión y cierre ordenado.'],
], [1.35, 5.15])
p('El archivo data/tasks.json se crea vacío en la primera ejecución. La persistencia depende de conservar ese archivo y su directorio. Cada escritura prepara un temporal y lo renombra en el mismo filesystem. El diseño admite un proceso y una instancia: no implementa coordinación entre servidores, autenticación ni aislamiento por usuario. Es adecuado para datos de demostración del caso académico, no para información personal o tareas confidenciales.')
p('Una lectura corrupta produce un error y no reemplaza silenciosamente el archivo con una lista vacía. Esta decisión conserva evidencia del fallo y evita ocultar pérdida de datos. La comprobación de salud inspecciona formato y permisos del almacenamiento, por lo que un proceso activo puede reportar salud degradada cuando su dependencia local falla.')

heading('5 Objetivo general', new_page=True)
p('Implementar y verificar localmente un Sistema de Gestión de Tareas con scripts de liberación y una configuración de CI/CD que condicione el despliegue en Render a validaciones automáticas, conserve evidencias y compruebe que la versión publicada coincide con el commit evaluado.')
p('El objetivo se considera alcanzado en su alcance local cuando el proyecto puede instalarse desde el lockfile, ofrece operaciones CRUD válidas, supera el análisis estático y las pruebas con los cuatro umbrales de cobertura y genera una liberación identificable. Su dimensión remota permanece parcial hasta disponer de un repositorio y un servicio autorizados, secretos reales y una ejecución verificable del workflow.')
p('Esta delimitación hace evaluable el trabajo: la existencia de render.yaml no demuestra un despliegue, una respuesta HTTP 200 no demuestra que se publicó el cambio esperado y una cobertura elevada no acredita disponibilidad mensual. Cada afirmación se vincula a una evidencia del nivel que realmente prueba. La evaluación combina comportamiento funcional, automatización operativa y trazabilidad documental.')

heading('6 Objetivos específicos', new_page=True)
for text in [
    'Desarrollar una interfaz adaptable y una API REST para crear, consultar, editar, completar y eliminar tareas, con validación del contrato y manejo explícito de errores.',
    'Implementar persistencia JSON sencilla y explicar su comportamiento ante reinicios, corrupción, concurrencia y filesystem efímero de alojamiento.',
    'Automatizar preparación, instalación reproducible, configuración, análisis, pruebas, empaquetado, construcción Docker, solicitud de despliegue y verificación posterior mediante comandos npm compatibles con Windows y Linux.',
    'Definir un único pipeline de GitHub Actions para PR y main, con dependencias que impidan desplegar una versión con pruebas fallidas o cobertura inferior al 80 %.',
    'Calcular indicadores operativos con respuestas finalizadas y recursos del proceso; separar tráfico de API, errores 4xx, errores 5xx y sondeos de monitoreo.',
    'Proponer niveles de servicio medibles, explicitar las condiciones de carga y distinguir los resultados del ensayo local de compromisos contractuales y capacidades del proveedor.',
    'Conservar resultados y capturas reales e integrarlos en una entrega editable, una versión PDF y una matriz que señale los componentes locales completos y las acciones remotas pendientes.'
]: p(text)
p('Estos objetivos se verifican mediante archivos y ejecuciones identificadas. Los requisitos originales de documentación y scripts se evalúan por separado de la vinculación efectiva a un proveedor. Esta separación permite reconocer los avances sin dar por terminada una etapa que depende de autorizaciones y recursos aún inexistentes.')

heading('7 Justificación del flujo de trabajo para la liberación y despliegue continuo', new_page=True)
p('El pipeline convierte las condiciones de aceptación en dependencias ejecutables. Instalar con npm ci antes del análisis reduce diferencias derivadas de resolver versiones nuevas; el lockfile fija el árbol instalado. Validar el entorno antes de las pruebas identifica puertos, modos o commits incorrectos. ESLint detecta problemas de código sin arrancar la aplicación, mientras que Jest y Supertest comprueban el contrato HTTP y el almacenamiento. Estas etapas responden a fallos distintos y por ello se conservan como pasos explícitos (npm, s. f.; OpenJS Foundation, s. f.).')
p('El job validate agrupa configuración, lint, pruebas, cobertura, construcción, validación YAML, revisión de secretos, artefacto e imagen Docker. El job deploy declara needs: validate. No se usa continue-on-error para suavizar una condición de aceptación. Si falla cualquier etapa anterior, GitHub no satisface la dependencia de despliegue. En un pull request se evalúa el cambio, pero no se ejecuta deploy ni se requieren credenciales del proveedor.')
p('Los cambios enviados a main pueden desplegarse solo si RENDER_DEPLOY_ENABLED es true. El diseño utiliza un único mecanismo de activación: Render mantiene autoDeployTrigger en off y recibe un hook desde Actions. Activar simultáneamente autodeploy por push y hook permitiría dos liberaciones y podría iniciar una antes de las pruebas; por eso la desactivación forma parte de la configuración y de la lista de vinculación (Render, s. f.-a, s. f.-d).')
p('Cada solicitud de despliegue especifica ref con el SHA completo de GitHub. La verificación posterior espera que /health confirme ese mismo SHA, salud ok y almacenamiento disponible. Una instancia anterior puede seguir respondiendo durante la construcción; aceptarla solo por devolver 200 produciría un falso positivo. Las pruebas del verificador reproducen ese caso para exigir identidad de versión y no únicamente conectividad.')
p('El control concurrency evita ejecuciones simultáneas del mismo flujo y referencia sin cancelar una liberación ya iniciada (GitHub, s. f.). Además, el script consulta si el commit esperado ya está sano antes de emitir otro POST. Si la respuesta del hook es ambigua, detiene la operación y exige revisar el proveedor antes de repetirla. La protección de main y del environment sigue siendo una configuración remota necesaria; el código local no puede imponerla a administradores externos.')

heading('8 Entorno requerido para la liberación y despliegue continuo', new_page=True)
p('Se distinguen desarrollo, liberación y producción porque tienen datos, permisos y criterios de salida diferentes. Desarrollo permite recargar la aplicación y usar datos de demostración. Liberación instala el árbol bloqueado, ejecuta las validaciones y genera evidencias. Producción ejecuta únicamente el servidor y sus dependencias necesarias, con un commit identificable. La separación evita que una prueba escriba sobre el archivo del usuario o que un secreto termine en un paquete distribuible.')
table(['Entorno', 'Configuración y propósito'], [
    ['Desarrollo local', 'Windows; Node 24–26; npm ≥10; Git; puerto 3000; JSON en data/tasks.json; npm run dev o npm start.'],
    ['Liberación local', 'Mismo código; npm ci; pruebas aisladas en temporales; evidence, coverage y dist; no se invoca Render.'],
    ['Integración', 'GitHub Actions ubuntu-latest; Node 24 LTS; NODE_ENV=test; APP_COMMIT=github.sha; Docker del runner.'],
    ['Producción propuesta', 'Render web Docker, plan free, main, PORT=10000 y /app/data/tasks.json efímero.'],
], [1.5, 5])
p(f"La inspección real detectó {versions['node']}, npm {versions['npm']} y {versions['git']}. Docker no está disponible. El sistema dispone de Chrome para la prueba de interfaz y Microsoft Word para exportar el documento. El acceso al ejecutor restringido presentó un error de inicialización; las validaciones se continuaron mediante las autorizaciones del entorno de ejecución, sin modificar otros proyectos.")
p('Como referencia de desarrollo se proponen dos núcleos, 4 GB de RAM y 1 GB libre para código, dependencias y evidencias. Para Docker se recomiendan 8 GB y virtualización habilitada. Son requisitos orientativos de trabajo, no mediciones del proveedor. Se necesita conexión para instalar dependencias y, en una etapa futura, acceder a GitHub y Render. Las herramientas seleccionadas permiten realizar el alcance académico sin contratar servicios.')
p('La versión de referencia del pipeline y del contenedor es Node.js 24 LTS; el equipo local tiene Node 26. Esta diferencia se declara porque las pruebas locales no sustituyen una ejecución en el runtime del contenedor. Las etiquetas mayores de la imagen y de las acciones favorecen actualización, pero no fijan un digest inmutable; el lockfile sí establece las versiones de bibliotecas. Una operación productiva deberá revisar y actualizar ambos niveles con cambios comprobados (Node.js, s. f.; Docker, s. f.).')

heading('9 Niveles de servicio acordados o propuestos para el caso de estudio', new_page=True)
p('Un SLI es un indicador cuantitativo definido con un método de medición; un SLO es el umbral que se desea alcanzar; un SLA formaliza compromisos y consecuencias entre partes. En esta actividad se proponen SLO académicos, sin afirmar que existe un SLA firmado ni atribuir al proveedor garantías que no se han contratado. Los objetivos guían las comprobaciones y permiten discutir qué arquitectura sería necesaria para sostenerlos (Beyer et al., 2016).')
table(['Indicador', 'Objetivo propuesto', 'Método y ventana'], [
    ['Disponibilidad', '≥99 % mensual', 'Sondeo externo cada minuto; respuestas sanas / sondeos programados. Registrar fallos de red y arranques fríos.'],
    ['Latencia', 'p95 <500 ms', 'GET /api/tasks; hasta 1000 tareas; 5 clientes; 10 min; servicio caliente; cuerpo completo desde cliente.'],
    ['Errores de servidor', '<1 % de respuestas API', 'Respuestas 5xx / respuestas API finalizadas ×100, en la ventana acordada. Los 4xx se presentan por separado.'],
    ['Recuperación', 'RTO ≤30 min', 'Desde detección del incidente hasta salud y commit de recuperación confirmados; ensayo aún pendiente.'],
], [1.3, 1.7, 3.5])
p('Para un mes de 30 días, 99 % permite 432 minutos de indisponibilidad. El uptime del proceso no permite calcular ese porcentaje: puede reiniciarse sin indicar cuánto duró el corte y no registra problemas de red, plataforma o DNS. Por ello la disponibilidad mensual exige un observador externo con registros persistentes. Los sondeos ausentes deben investigarse; no pueden contarse como éxito sin evidencia.')
p('El protocolo de rendimiento completo exige diez minutos bajo las condiciones definidas. El ensayo implementado aquí es más corto: 200 solicitudes con cinco clientes, después de diez solicitudes de calentamiento. Sus resultados solo describen ese equipo, muestra y tamaño real de datos. Los fallos de red se registran separados de los códigos HTTP, ya que un timeout no es una respuesta 5xx y no debe ocultarse dentro de su denominador.')
p('La recuperación propuesta distribuye 5 minutos para detectar y clasificar, 5 para elegir un commit previo validado, 15 para restaurar la versión y 5 para verificar salud y SHA. No se ha ensayado en Render. Un rollback de código no restaura tareas borradas por el filesystem efímero; por tanto no se compromete un RPO de cero ni una recuperación garantizada de datos. Un uso real requiere respaldos y almacenamiento duradero.')
p('La aceptación de una versión exige lint sin errores, todas las pruebas aprobadas, cobertura mínima en las cuatro dimensiones, configuración y YAML válidos, artefacto trazable, construcción Docker correcta, ausencia de credenciales detectadas y health check del commit esperado. Una construcción Docker pendiente impide afirmar aceptación productiva completa aunque el alcance local de la aplicación funcione.')
p('El plan gratuito puede suspender el servicio después de inactividad y requiere un arranque posterior. Estas condiciones y las cuotas del servicio pueden afectar la disponibilidad y la latencia. No se genera tráfico artificial para impedir la suspensión. Los SLO deberán revisarse frente al comportamiento observado y las condiciones vigentes del alojamiento antes de transformarse en un acuerdo contractual (Render, s. f.-b).')

heading('10 Métricas para el monitoreo de la aplicación', new_page=True)
p('El middleware de medición se instala antes del parser JSON para incluir también respuestas inválidas. Al recibir una solicitud registra process.hrtime.bigint y, en el evento finish de la respuesta, calcula la diferencia en milisegundos. Solo se contabilizan respuestas finalizadas. Una conexión abortada antes de finish no aparece como respuesta HTTP completada; el cliente de carga registra sus propios fallos de transporte.')
table(['Campo de /metrics', 'Cálculo y significado'], [
    ['requests.total y byStatus', 'Contador real desde el inicio del proceso y distribución por código HTTP.'],
    ['responseTimeMs.average', 'Suma de duraciones / respuestas finalizadas; null si no existen observaciones.'],
    ['responseTimeMs.p95', 'Ordenar últimas ≤1000 duraciones; índice ceil(n×0.95)−1; sin datos devuelve null.'],
    ['errors', 'Conteos 4xx y 5xx, porcentaje total ≥400 y porcentaje 5xx con denominador global.'],
    ['api', 'Respuestas de /api/tasks y subrutas; p95 y porcentaje 5xx excluyen monitoreo y archivos estáticos.'],
    ['uptimeSeconds', 'process.uptime; segundos de vida del proceso, no disponibilidad mensual.'],
    ['health y memoryBytes', 'Estado comprobado del almacenamiento y process.memoryUsage: RSS, heap y buffers.'],
], [2.35, 4.15])
p('Los contadores no están precargados ni usan valores aleatorios. Las métricas de API separan el trabajo del usuario de las consultas de salud y recursos estáticos. El porcentaje global de errores incluye validaciones 4xx deliberadas; por ello no debe compararse directamente con el objetivo de 5xx. El campo api.serverErrorPercentage es el indicador pertinente para ese objetivo.')
p('El p95 usa una ventana acotada para limitar memoria. No representa el percentil de todo el mes ni un histograma distribuido; sus observaciones se pierden al reiniciar. El promedio abarca todas las respuestas del proceso, por lo que tiene una ventana distinta del p95 y debe interpretarse con esa diferencia. La respuesta de /metrics no incluye su propia solicitud, porque su registro ocurre al finalizar el envío.')
p('GET /health devuelve 503 cuando no puede leer o validar el archivo o comprobar sus permisos, e informa commit, estado, timestamp y uptime. La comprobación no garantiza espacio libre futuro ni ausencia de fallos inmediatamente después del sondeo. Ambas rutas usan Cache-Control: no-store para reducir respuestas reutilizadas. Para disponibilidad histórica se necesita exportar los indicadores a un observador persistente externo.')
p(f"En la captura real de monitoreo había {metrics['requests']['total']} respuestas previas y {metrics['errors']['total']} errores HTTP, incluidos errores de validación provocados por el smoke. Su porcentaje total fue {metrics['errors']['percentage']:.2f} %. La memoria RSS observada fue {metrics['memoryBytes']['rss']} bytes. Estos números describen ese instante y no se presentan como métricas de un servidor remoto.")

heading('11 Parámetros de configuración de las herramientas utilizadas', new_page=True)
p('package.json reúne comandos portables y declara Node >=24 <27 y npm >=10. package-lock.json fija la resolución exacta. La instalación omite scripts de paquetes mediante --ignore-scripts porque la aplicación y sus herramientas no los necesitan. El primer análisis identificó avisos transitivos; se actualizó ESLint y se declararon overrides para glob y minimatch. La suite se ejecutó después para verificar compatibilidad, sin reducir umbrales ni excluir módulos de src. ESLint utiliza el formato plano documentado para definir reglas y entornos por archivo (ESLint, s. f.).')
packages = json.loads((ROOT / 'package-lock.json').read_text(encoding='utf-8'))['packages']
table(['Herramienta', 'Versión instalada', 'Configuración utilizada'], [
    [name, packages['node_modules/' + name]['version'], detail] for name, detail in [
        ('express', 'Rutas REST; JSON de hasta 16 KB; errores centralizados.'),
        ('jest', 'Entorno Node; ejecución serial; todos los módulos src; cuatro umbrales de 80 %.'),
        ('supertest', 'Solicitudes HTTP al servidor Express real dentro de pruebas aisladas.'),
        ('eslint', 'Configuración plana; recommended; globals de Node, navegador y Jest por archivo.'),
        ('helmet', 'Encabezados de seguridad y política de contenido sin scripts externos.'),
        ('playwright', 'Chrome local headless; 1440 px y 390 px; capturas y acciones reales.'),
    ]
], [1.2, 1.05, 4.25])
p('Las variables se validan en src/config.js. PORT acepta enteros de 1 a 65535; NODE_ENV solo development, test o production; DATA_FILE debe apuntar a JSON. La prioridad de versión es RENDER_GIT_COMMIT, después APP_COMMIT y finalmente local. Producción rechaza local. Esta regla impide arrancar una liberación productiva sin identidad verificable y permite que Render suministre el commit real de su checkout.')
p('El workflow limita GITHUB_TOKEN a contents: read. Los secretos del hook y del origen público se inyectan únicamente en el job deploy. No se escribe el hook en registros. El archivo .env se excluye de Git y del contexto Docker. La búsqueda de secretos se limita a patrones reconocibles; un reporte sin coincidencias no sustituye una revisión humana ni demuestra que todo formato de secreto posible haya sido detectado.')
p('Docker usa node:24-bookworm-slim, instala dependencias productivas, cambia al usuario node y expone el puerto de ejecución. Render utiliza runtime docker, plan free, main, healthCheckPath /health y autoDeployTrigger off. El YAML local se parsea con claves únicas y comprobaciones propias; esta validación no constituye aprobación del esquema remoto ni acredita que la imagen haya sido ejecutada.')

heading('12 Configuración de la herramienta de liberación continua', new_page=True)
p('La herramienta coordinadora es GitHub Actions y su configuración está en .github/workflows/ci-cd.yml. Los eventos son pull_request hacia main y push sobre main. No se usa pull_request_target ni se ejecuta un workflow separado que despliegue sin depender de las pruebas. El timeout del job de validación es de quince minutos y los reportes se conservan mediante upload-artifact con retención de catorce días.')
p('validate descarga el código, configura Node 24, instala con npm ci, prepara el entorno, valida variables, ejecuta ESLint, Jest y cobertura, comprueba construcción y YAML, revisa secretos, genera el paquete y construye Docker. La carga de reportes usa always para conservar información incluso cuando un paso falla, pero esto no cambia la conclusión del job ni habilita deploy.')
p('deploy depende de validate y exige push, refs/heads/main y la variable RENDER_DEPLOY_ENABLED=true. Recupera el artefacto generado por el mismo SHA, valida el entorno de despliegue, genera el plan, solicita la liberación y ejecuta health:check. Si la variable no existe, el despliegue queda deshabilitado. Esta decisión permite conectar el repositorio sin publicar de forma accidental durante su configuración.')
p('La vinculación futura requiere crear el repositorio remoto, asociar Render a main, revisar que el despliegue automático esté apagado y guardar dos Secrets: RENDER_DEPLOY_HOOK_URL y DEPLOY_BASE_URL. Después se crea el environment production y se exige el job de validación en la protección de main cuando las opciones del repositorio lo permitan. Esas acciones no se realizaron por la restricción expresa de no crear remotos ni publicar sin autorización.')
p('La primera creación del servicio de alojamiento puede iniciar una construcción del proveedor; deberá registrarse como configuración inicial y distinguirse del flujo posterior gobernado por Actions. El plan académico no supone que el YAML elimine por sí solo ese comportamiento de aprovisionamiento. Una vez vinculado, se comprobarán el registro de Actions, la versión de /health y las evidencias del commit publicado.')
p('La imagen construida en CI funciona como prueba de empaquetado. Render construye desde el mismo commit con el Dockerfile del repositorio, en lugar de descargar el tar.gz o una imagen publicada por este proyecto. Esta diferencia de función evita atribuir al artefacto una participación que no tiene. Para reproducibilidad binaria más estricta habría que fijar digest y publicar una imagen inmutable en una etapa adicional autorizada.')

heading('13 Descripción de los scripts del flujo de trabajo', new_page=True)
p('Los scripts se implementan en JavaScript con APIs de Node para ejecutarse desde Windows y desde un runner Linux. scripts/lib.js concentra ejecución, códigos de error, identidad de commit y escritura de evidencias. Los procesos se lanzan con argumentos estructurados sin componer comandos de shell a partir de datos del usuario. Los errores se capturan, se muestran con el prefijo ERROR y producen exitCode 1.')
script_rows = [
    ['release:prepare', 'Verifica Node y archivos necesarios; crea carpetas sin borrar tareas.'],
    ['deps:ci', 'Ejecuta npm ci, bloquea instalación ante desacuerdo de package y lock.'],
    ['config:validate', 'Comprueba valores locales; --deploy exige origen, hook y SHA.'],
    ['test:release', 'Ejecuta Jest y cobertura; copia reportes solo si la verificación pasa.'],
    ['build', 'Comprueba sintaxis y existencia de recursos; registra cantidad de archivos.'],
    ['release:artifact', 'Empaqueta lista permitida, obtiene SHA-256 y genera manifest.'],
    ['docker:build', 'Exige Docker Engine; construye con etiqueta y argumento del commit.'],
    ['deploy:plan / deploy:render', 'Genera plan sin red o solicita publicación en contexto autorizado de Actions.'],
    ['health:check', 'Sondea estado y commit esperado; termina en error si vence la espera.'],
    ['smoke / load:test / test:ui', 'Verifican HTTP local, muestra de carga y comportamiento del navegador.'],
]
table(['Comando npm', 'Responsabilidad'], script_rows, [2.3, 4.2])
p('La validación local registra tanto éxitos como rechazos esperados. La ausencia de Docker produce salida 1 y un estado PENDIENTE, y un intento de despliegue fuera de Actions debe fallar. Esos resultados no equivalen a ejecutar Docker o Render correctamente; demuestran que los scripts reconocen una limitación y no la convierten en un éxito ficticio. El orquestador conserva la salida observada y el código esperado de cada comprobación.')
p('El plan de despliegue es un JSON sin credenciales que contiene proveedor, rama, commit y pasos. La generación del plan no envía solicitudes al hook. Esto permite revisar el comportamiento previsto antes de autorizar servicios remotos. Los scripts de carga y smoke rechazan destinos externos para evitar modificar o someter a carga una aplicación publicada por accidente.')

heading('14 Scripts para la generación del entorno de liberación', new_page=True)
p('prepare-release.js verifica la versión mayor de Node y la presencia de package-lock.json, Dockerfile y render.yaml. Crea dist, evidence y tmp sin eliminar datos existentes. El reporte release-environment.json registra plataforma, arquitectura, versión y commit. Esta preparación detecta requisitos ausentes antes de dedicar tiempo a pruebas o construcción.')
p('install-deps.js invoca npm ci con --ignore-scripts y --no-fund. A diferencia de una resolución libre durante cada ejecución, ci exige coherencia entre package.json y el lockfile. La instalación realizada mediante validate:local quedó registrada en local-validation.log. La presencia de node_modules por sí sola no se utiliza como evidencia de reproducibilidad (npm, s. f.).')
p('validate-env.js reutiliza exactamente la función getConfig del servidor, por lo que el criterio de aceptación del script coincide con el arranque de la aplicación. En modo de despliegue añade validación de origen HTTPS, formato del hook de Render y SHA completo. Los mensajes describen el campo incorrecto sin imprimir secretos. .env.example documenta valores seguros; .env no se genera con credenciales ni se incorpora al repositorio.')
p('create-artifact.js usa una lista explícita de archivos y carpetas. Incluye aplicación, recursos públicos, scripts y manifiestos; excluye por construcción el archivo de tareas, node_modules, .git y credenciales. El resultado es tar.gz más dist/manifest.json. El hash SHA-256 permite detectar cambios al archivo generado; no constituye por sí solo una firma de autor ni sustituye el control de acceso al repositorio.')
p(f"La liberación de evidencia se identificó con el commit {artifact['commit']}. Su SHA-256 fue {artifact['sha256']}. El nombre exacto del paquete está en evidence/artifact.json. Los commits posteriores que integran esta documentación no cambian retroactivamente el origen de esa evidencia: al liberar otra versión debe regenerarse el artefacto para su nuevo SHA.")
code_excerpt('scripts/prepare-release.js', 5, 10)

heading('15 Scripts de pruebas en el entorno de liberación', new_page=True)
p('test-release.js ejecuta Jest con --runInBand, --coverage y salida JSON. El orden serial reduce competencia por puertos y simplifica la evidencia local, mientras que cada prueba crea un directorio temporal propio para los datos. Supertest realiza peticiones HTTP al objeto Express; no se sustituye el CRUD por funciones vacías o respuestas prefabricadas. Los temporales se eliminan al terminar cada caso.')
p('La suite de API verifica creación, listado, consulta individual, PATCH, PUT, eliminación y persistencia al reabrir TaskStore. Comprueba campos desconocidos, título corto o demasiado largo, descripción inválida, booleanos incorrectos, JSON roto, tipo de contenido y cuerpos excesivos. Los recursos inexistentes se prueban con cada método relevante y se comprueba el código 404.')
p('Los escenarios de fallo incluyen corrupción real del archivo que provoca 500, salud 503 y métricas con errores; también simulan un fallo de rename para comprobar que se conserva el archivo anterior y se elimina el temporal. Esta última es una prueba controlada de un fallo del sistema operativo, claramente diferenciada de una observación de producción. El límite de 1000 tareas se comprueba con datos generados dentro del entorno aislado.')
p('Las métricas se verifican contra una secuencia conocida de peticiones. Se comprueban denominadores, códigos de respuesta, valores de memoria, ausencia de observaciones y recorte de la ventana a 1000 duraciones. La prueba de despliegue devuelve primero un commit anterior sano y después el esperado, y exige que el verificador no acepte el primero. Estas respuestas controladas prueban la lógica del verificador; no se registran como publicación real.')
p('La cobertura incluye todos los archivos src, incluso server.js. Jest exige 80 % en ramas, funciones, líneas y sentencias mediante coverageThreshold (Jest, s. f.). No se exige que cada archivo individual alcance 80 % porque el umbral configurado es global; el reporte permite examinar cada módulo. La cobertura del punto de entrada es menor que la de los módulos de negocio, debido a ramas de cierre y arranque del proceso. Esta limitación se conserva visible en lugar de excluir ese archivo.')
p(result_line)
p(f"La prueba adicional de Chrome realizó {len(browser['checks'])} comprobaciones de interfaz con Playwright (s. f.). Incluyó creación, edición, completar, persistencia tras recarga, búsqueda, filtros, validación del formulario, error HTTP controlado, diseño móvil y cancelación/confirmación de eliminación. Las tareas visibles en las capturas se crearon durante esa ejecución y se eliminaron al finalizar. Este recorrido no acredita por sí solo accesibilidad exhaustiva o compatibilidad con todos los navegadores.")

heading('16 Scripts para la generación del despliegue', new_page=True)
p('build-docker.js primero ejecuta docker info para comprobar cliente y daemon. Solo después construye la imagen con APP_COMMIT y una etiqueta del SHA. Si Docker falta, escribe docker.json con PENDIENTE y sale con error. El Dockerfile cambia al usuario node, instala exclusivamente dependencias productivas y configura un HEALTHCHECK que consulta el puerto del proceso. No se afirmó una construcción local porque la herramienta está ausente.')
p('deploy.js tiene dos modos explícitos. --plan produce un documento de intención sin contactar servicios; --execute exige GITHUB_ACTIONS=true, evento push y referencia main. También exige un manifest del artefacto cuyo commit coincida. Este control sirve dentro del workflow definido; un administrador con capacidad de alterar scripts o variables conserva poder de intervención, por lo que deben aplicarse protecciones de repositorio.')
p('El módulo deployment.js valida que el hook use HTTPS y api.render.com, y que el origen de aplicación no incluya contraseñas, rutas ni parámetros. Añade ref con el SHA validado y emite un único POST. Un error de comunicación no desencadena otra solicitud automática, porque el proveedor podría haber recibido la primera. La evidencia local omite la URL secreta. Los códigos 200 y 202 indican solicitud aceptada o en cola, no una aplicación ya publicada (Render, s. f.-c).')
p('health-check.js permite esperar hasta diez minutos. Cada consulta tiene un timeout individual y evita caché. La liberación solo se confirma cuando el cuerpo informa status ok, storage ok y el commit esperado. Durante la espera puede responder la versión anterior y el script continúa hasta que aparezca la correcta o venza el plazo. Una falla produce salida no cero y se refleja como despliegue no verificado.')
p('La reversión propuesta consiste en seleccionar un commit previamente validado y repetir el procedimiento de liberación para ese SHA con los controles aprobados. No existe un script que revierta automáticamente datos JSON, porque el servicio gratuito no conserva versiones del archivo. La recuperación de código y la recuperación de datos se documentan como problemas distintos y deben ensayarse antes de prometer un RTO contractual.')
p('No hay hooks, dominios ni claves reales en esta entrega. Las pruebas emplean example.invalid como dominio reservado y un hook deliberadamente no operativo para validar formato. La existencia de esas fixtures no representa una conexión con Render. La generación local del plan y el rechazo de ejecución fuera de Actions son las evidencias disponibles hasta contar con autorización remota.')

heading('17 Diagrama del pipeline CI/CD', new_page=True)
p('El diagrama agrupa las etapas ejecutadas por validate y la condición que habilita deploy. En un PR el recorrido termina al conservar las evidencias de validación; únicamente un push a main con despliegue habilitado puede continuar hacia Render. Cada bloque depende del éxito de los anteriores.')
figure(DOCS / 'pipeline.png', 6.2, 'Figura 1. Pipeline implementado en .github/workflows/ci-cd.yml. Elaboración propia a partir de la configuración del proyecto.')

heading('18 Evidencias de implementación y pruebas', new_page=True)
p('Las evidencias se obtuvieron ejecutando el proyecto local. Los archivos JSON y el log permiten contrastar las afirmaciones del informe; las capturas corresponden al Chrome local, no a una maqueta ni a un servicio público. Su fecha de registro está dentro de cada reporte. Los resultados de pruebas del verificador utilizan datos controlados y se identifican como pruebas, no como hechos de despliegue.')
table(['Evidencia', 'Resultado observado'], [
    ['tests.json', f"{tests['numPassedTests']}/{tests['numTotalTests']} pruebas; {tests['numPassedTestSuites']} suites aprobadas."],
    ['coverage/coverage-summary.json', f"Líneas {coverage['lines']['pct']:.2f} %; funciones {coverage['functions']['pct']:.2f} %; ramas {coverage['branches']['pct']:.2f} %; sentencias {coverage['statements']['pct']:.2f} %."],
    ['eslint.json', f'{lint_errors} errores y {lint_warnings} advertencias.'],
    ['build.json', f"Sintaxis válida en {build['checkedJavaScriptFiles']} archivos JS y recursos estáticos comprobados."],
    ['npm-audit.json', f"{audit['metadata']['vulnerabilities']['total']} vulnerabilidades informadas por npm audit."],
    ['yaml-validation.json', 'Parseo correcto y controles locales de main, needs, plan free y autoDeploy off.'],
    ['docker.json', 'PENDIENTE; Docker no disponible. El script informó el fallo.'],
    ['endpoints.json', 'CRUD, validación 400, recurso 404, /health y /metrics con respuestas reales.'],
], [2.6, 3.9])
p('El reporte HTML de cobertura se encuentra en evidence/coverage/index.html y su información LCOV puede integrarse en herramientas de revisión. local-validation.log conserva la salida completa de los scripts. No existe un enlace de Actions ni una URL pública porque no se creó un remoto ni un servicio. Esas evidencias se deberán incorporar después de la autorización, conservando commit, fecha, resultado y correspondencia entre versión probada y publicada.')
heading('18.1 Captura de escritorio', level=2, new_page=True)
p('La captura muestra tres tareas creadas mediante la interfaz durante la prueba. Una fue editada y completada; los contadores reflejan la respuesta de la API. Los datos pertenecen exclusivamente a la verificación y fueron eliminados por su identificador al terminar.')
figure(EVIDENCE / 'screenshots/aplicacion-escritorio.png', 6.5, 'Figura 2. Aplicación local en Chrome con viewport de 1440 × 1040. Fuente: evidence/screenshots/aplicacion-escritorio.png.')
heading('18.2 Vista móvil y validación', level=2, new_page=True)
p('La vista de 390 píxeles se comprobó sin desbordamiento horizontal. El formulario rechazó un título compuesto únicamente por espacios y mostró el mensaje correspondiente. La ejecución también verificó un mensaje de fallo HTTP mediante una respuesta interceptada y declarada como escenario controlado.')
figure(EVIDENCE / 'screenshots/aplicacion-movil.png', 3, 'Figura 3. Captura real del viewport móvil de 390 × 844. La página completa también se conserva en evidence/screenshots/.')
heading('18.3 Validación del formulario', level=2, new_page=True)
p('Un título de solo espacios produce un mensaje de corrección sin enviar una tarea inválida al servidor. La API repite la validación para que no dependa exclusivamente del navegador. Esta captura corresponde a la interacción real del formulario y no al escenario HTTP interceptado.')
figure(EVIDENCE / 'screenshots/validacion-formulario.png', 5.5, 'Figura 4. Validación real del formulario. Fuente: evidence/screenshots/validacion-formulario.png.')
heading('18.4 Respuestas reales de monitoreo', level=2, new_page=True)
p(f"La respuesta de /health capturada el {health['timestamp']} informó status={health['status']}, storage={health['storage']} y commit={health['commit']}. El valor local señala el arranque de desarrollo; no se presenta como SHA de una versión publicada. Las pruebas del health check con commits completos se distinguen de esta captura local.")
table(['Indicador capturado', 'Valor real'], [
    ['Peticiones previas', metrics['requests']['total']],
    ['Errores 4xx / 5xx', f"{metrics['errors']['http4xx']} / {metrics['errors']['http5xx']}"],
    ['Porcentaje de errores HTTP global', f"{metrics['errors']['percentage']:.2f} %"],
    ['p95 del proceso', f"{metrics['responseTimeMs']['p95']:.3f} ms"],
    ['Uptime del proceso', f"{metrics['uptimeSeconds']:.3f} s"],
    ['Memoria RSS', f"{metrics['memoryBytes']['rss']} bytes"],
], [3.6, 2.9])
p('Los errores 4xx fueron provocados intencionalmente por el smoke para comprobar la validación y el manejo de rutas ausentes. No se eliminan del contador para mejorar el resultado. La ventana de este registro es corta y su p95 mide el servidor, mientras que el ensayo de carga mide desde el cliente; esos valores no son intercambiables.')

heading('19 Resultados obtenidos', new_page=True)
p(result_line)
p(f"ESLint terminó con {lint_errors} errores y {lint_warnings} advertencias. La construcción comprobó {build['checkedJavaScriptFiles']} archivos JavaScript. npm audit informó {audit['metadata']['vulnerabilities']['total']} vulnerabilidades tras actualizar las dependencias y verificar su compatibilidad. Los archivos YAML pasaron el parseo y las comprobaciones locales implementadas. Estos resultados están en evidence y no se atribuyen a GitHub Actions.")
p(f"El ensayo de carga completó {load['completed']} de {load['measuredRequests']} solicitudes medidas, con concurrencia {load['concurrency']}, p95 de {load['p95Ms']:.3f} ms, {load['http5xxPercentage']:.2f} % de respuestas 5xx y {load['networkFailures']} fallos de red. La duración de la muestra fue {load['elapsedMs']:.2f} ms y la tasa observada {load['requestsPerSecond']:.2f} solicitudes por segundo. Fue una prueba local breve sobre la lista vacía tras el smoke; no demuestra la meta bajo 1000 tareas ni la ventana propuesta de diez minutos.")
p('Los fallos de entorno se identificaron sin eliminar requisitos. npm.ps1 estaba bloqueado por la política de PowerShell y se utilizó npm.cmd. El ejecutor restringido falló al crear procesos y el acceso integrado al navegador tampoco pudo iniciarse; las ejecuciones se continuaron con los permisos del entorno y la interfaz se verificó con Playwright y Chrome local. Git detectó diferente propietario al cambiar de ejecutor y se aplicó safe.directory exclusivamente al comando y a la ruta del proyecto, sin cambiar ajustes globales.')
p('La construcción Docker quedó pendiente porque no existe Docker Engine. El pipeline tiene configuración local válida y scripts ejercitados, pero no cuenta con una ejecución remota. La vinculación Actions–Render permanece parcial y el despliegue público pendiente. Tampoco se ha medido un mes completo de disponibilidad ni se ha ensayado recuperación remota; esas metas no pueden darse por satisfechas con pruebas funcionales.')
heading('19.1 Matriz de requisitos originales', level=2)
p('Se evalúan individualmente los diez requisitos de la profesora. CUMPLE se refiere al entregable documental o de código verificado localmente; PARCIAL señala que la vinculación solicitada aún no se puede demostrar. La matriz ampliada incluye además Docker, despliegue, documentos y objetivos operativos en docs/matriz-cumplimiento.md.')
table(['ID y requisito', 'Estado', 'Archivo o evidencia principal'], [[f'{r[0]} {r[1]}', r[2], r[3] + '. ' + r[4]] for r in matrix[:10]], [2.25, 1.0, 3.25])

heading('20 Conclusiones', new_page=True)
p('La actividad produjo un caso de estudio ejecutable en el que los scripts representan operaciones concretas de liberación. La instalación bloqueada, el análisis estático, las pruebas, el empaquetado y los controles de versión pueden revisarse en archivos y registros reales. La combinación de una API sencilla con errores de almacenamiento reproducibles permitió evaluar tanto el comportamiento esperado como las condiciones que deben impedir una liberación.')
p('La principal decisión operativa fue tratar la identidad del commit como parte de la verificación. El estado saludable de una instancia anterior no demuestra que se desplegó una nueva versión. El hook con ref y la comparación exacta en /health ofrecen un mecanismo documentado para resolver ese problema cuando se autorice la vinculación. Las dependencias del workflow impiden que la configuración normal despliegue tras una prueba fallida.')
p('La cobertura alcanzada supera los objetivos académicos, pero conserva límites: el frontend se verificó con un recorrido específico, no con una batería exhaustiva de navegadores; la latencia proviene de una muestra local breve; la disponibilidad y recuperación no se observaron durante las ventanas propuestas. Presentar esos límites permite utilizar los resultados para decidir el siguiente paso sin convertir un ensayo en una garantía.')
p('La persistencia JSON facilita comprender la automatización y reduce requisitos de instalación, a costa de restringir la aplicación a un proceso y de perder datos en alojamiento efímero. Por esta razón el sistema muestra una advertencia y se limita a información de demostración. Un servicio de uso real necesitaría almacenamiento duradero, permisos de usuario, respaldos y una política de recuperación de datos antes de adoptar un SLA.')
p('La siguiente etapa requiere autorización expresa para crear el remoto y el servicio Render. Después deberán configurarse protecciones de main, el environment, los Secrets y la variable de habilitación; ejecutar el pipeline completo; verificar Docker y el commit publicado; y actualizar las evidencias. Hasta ese momento la entrega se considera completa en su implementación local, con la vinculación remota identificada como parcial y las ejecuciones externas pendientes.')

heading('21 Referencias bibliográficas', new_page=True)
references = [
    'Beyer, B., Jones, C., Petoff, J., & Murphy, N. R. (Eds.). (2016). Site reliability engineering: How Google runs production systems. O’Reilly Media. https://sre.google/sre-book/service-level-objectives/',
    'Docker. (s. f.). Building best practices. Docker Docs. Recuperado el 22 de noviembre de 2026, de https://docs.docker.com/build/building/best-practices/',
    'ESLint. (s. f.). Configuration files. Recuperado el 22 de noviembre de 2026, de https://eslint.org/docs/latest/use/configure/configuration-files',
    'GitHub. (s. f.). Concurrency. GitHub Docs. Recuperado el 22 de noviembre de 2026, de https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency',
    'Jest. (s. f.). Configuring Jest. Recuperado el 22 de noviembre de 2026, de https://jestjs.io/docs/configuration',
    'Node.js. (s. f.). Node.js releases. Recuperado el 22 de noviembre de 2026, de https://nodejs.org/en/about/previous-releases',
    'npm. (s. f.). npm ci. npm Docs. Recuperado el 22 de noviembre de 2026, de https://docs.npmjs.com/cli/v11/commands/npm-ci/',
    'OpenJS Foundation. (s. f.). Routing. Express. Recuperado el 22 de noviembre de 2026, de https://expressjs.com/en/guide/routing/',
    'Playwright. (s. f.). Assertions. Recuperado el 22 de noviembre de 2026, de https://playwright.dev/docs/test-assertions',
    'Render. (s. f.-a). Blueprint YAML reference. Recuperado el 22 de noviembre de 2026, de https://render.com/docs/blueprint-spec',
    'Render. (s. f.-b). Deploy for free. Recuperado el 22 de noviembre de 2026, de https://render.com/docs/free',
    'Render. (s. f.-c). Deploy hooks. Recuperado el 22 de noviembre de 2026, de https://render.com/docs/deploy-hooks',
    'Render. (s. f.-d). Deploying on Render. Recuperado el 22 de noviembre de 2026, de https://render.com/docs/deploys',
]
for reference in references:
    para = p(reference)
    para.paragraph_format.left_indent = Inches(.5)
    para.paragraph_format.first_line_indent = Inches(-.5)
    # APA 7: título de obra o página en cursiva.
    title = reference.split('). ', 1)[1].split('. ', 1)[0]
    prefix, _, suffix = reference.partition(title)
    para.clear(); para.add_run(prefix); para.add_run(title).italic = True; para.add_run(suffix)

# Estilos del índice también respetan la tipografía solicitada.
for name in ['TOC 1', 'TOC 2']:
    try: style = doc.styles[name]
    except KeyError: style = doc.styles.add_style(name, 1)
    style.font.name = 'Arial'; style.font.size = Pt(12)
    style.paragraph_format.line_spacing = 1.5
    style.paragraph_format.space_after = Pt(4)
doc.save(DOCS / 'Manejo-de-Scripts.docx')

informe = f'''# Informe final de implementación local

Fecha académica: 22 de noviembre de 2026. Proyecto: C:/dev/manejo-de-scripts. Rama main local; no se creó remoto ni se realizó push.

## Resultado comprobado

{result_line}

ESLint: {lint_errors} errores, {lint_warnings} advertencias. Construcción: {build['checkedJavaScriptFiles']} archivos JS. Auditoría: {audit['metadata']['vulnerabilities']['total']} vulnerabilidades. YAML: parseo y controles básicos correctos. Docker: no instalado; construcción pendiente. GitHub Actions y Render: preparados, sin ejecución remota.

La muestra local completó {load['completed']} solicitudes, p95 {load['p95Ms']:.3f} ms, 5xx {load['http5xxPercentage']:.2f} %, errores de red {load['networkFailures']}. Es una muestra corta con lista vacía, no una medición mensual ni una prueba de Render. Chrome: {len(browser['checks'])} comprobaciones y {len(browser['screenshots'])} capturas reales.

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
'''
(DOCS / 'informe-final.md').write_text(informe, encoding='utf-8')
(EVIDENCE / 'document-source.json').write_text(json.dumps({
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'python': platform.python_version(),
    'sections': 21,
    'docx': 'docs/Manejo-de-Scripts.docx',
    'sources': ['tests.json', 'coverage/coverage-summary.json', 'eslint.json', 'load-test.json', 'browser-check.json', 'health-response.json', 'metrics-response.json', 'artifact.json', 'npm-audit.json'],
    'note': 'DOCX creado con python-docx. Exportar con Word y revisar PDF y PNG antes de entregar.'
}, ensure_ascii=False, indent=2), encoding='utf-8')
print('Documento Word, matriz, diagrama e informe generados con evidencias reales.')
