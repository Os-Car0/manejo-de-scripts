"""Alternativa local cuando Word no finaliza PDF: reconstruye el mismo contenido con ReportLab."""
from pathlib import Path
from io import BytesIO
from datetime import datetime, timezone
import json
from xml.sax.saxutils import escape
from docx import Document
from docx.text.paragraph import Paragraph as WordParagraph
from docx.table import Table as WordTable
from docx.oxml.ns import qn
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, PageBreak, Image, LongTable, TableStyle, KeepTogether
from reportlab.platypus.tableofcontents import TableOfContents

root = Path(__file__).resolve().parent.parent
source = root / 'docs/Manejo-de-Scripts.docx'
output = root / 'docs/Manejo-de-Scripts.pdf'
document = Document(source)
for name, font in [('Arial', 'arial.ttf'), ('Arial-Bold', 'arialbd.ttf'), ('Arial-Italic', 'ariali.ttf'), ('Arial-BoldItalic', 'arialbi.ttf')]:
    pdfmetrics.registerFont(TTFont(name, 'C:/Windows/Fonts/' + font))
pdfmetrics.registerFontFamily('Arial', normal='Arial', bold='Arial-Bold', italic='Arial-Italic', boldItalic='Arial-BoldItalic')
normal = ParagraphStyle('Normal', fontName='Arial', fontSize=12, leading=18, alignment=TA_JUSTIFY, spaceAfter=8, allowWidows=0, allowOrphans=0, splitLongWords=True)
center = ParagraphStyle('Center', parent=normal, alignment=TA_CENTER)
heading = ParagraphStyle('Heading1', parent=normal, fontName='Arial-Bold', fontSize=14, leading=21, spaceBefore=12, spaceAfter=8, keepWithNext=True, alignment=TA_LEFT)
heading2 = ParagraphStyle('Heading2', parent=heading)
title = ParagraphStyle('Title', parent=heading, alignment=TA_CENTER, spaceBefore=0)
caption = ParagraphStyle('Caption', parent=normal, alignment=TA_LEFT, spaceAfter=12)
cell = ParagraphStyle('Cell', parent=normal, alignment=TA_LEFT, spaceAfter=3)
cell_header = ParagraphStyle('CellHeader', parent=cell, fontName='Arial-Bold')
toc_style = ParagraphStyle('TOC', parent=normal, alignment=TA_LEFT, rightIndent=24, spaceBefore=0, spaceAfter=0)

class AcademicPdf(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=letter, leftMargin=72, rightMargin=72, topMargin=72, bottomMargin=72,
                         title='Manejo de Scripts: Implementación de un Pipeline de Liberación y Despliegue Continuo', author='Oscar Martínez Martínez')
        self.addPageTemplates(PageTemplate('Academic', frames=Frame(72, 72, 468, 648, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0), onPage=self.page_footer))
    def page_footer(self, canvas, _document):
        canvas.saveState(); canvas.setFont('Arial', 12)
        canvas.drawCentredString(letter[0]/2, 36, f'Página {self.page}')
        canvas.restoreState()
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and flowable.style.name == 'Heading1':
            text = flowable.getPlainText()
            key = 'section-' + text.split(' ')[0]
            self.canv.bookmarkPage(key)
            self.notify('TOCEntry', (0, text, self.page, key))

def inline(paragraph):
    values = []
    for run in paragraph.runs:
        text = escape(run.text).replace('\n', '<br/>')
        if run.bold: text = '<b>' + text + '</b>'
        if run.italic: text = '<i>' + text + '</i>'
        values.append(text)
    return ''.join(values) or escape(paragraph.text)

story = []
in_toc = False
toc_inserted = False
image_count = 0
for block in document.element.body:
    tag = block.tag.rsplit('}', 1)[-1]
    if tag == 'p':
        paragraph = WordParagraph(block, document)
        text = paragraph.text.strip()
        style_name = paragraph.style.name
        if text == '2 Índice':
            story.append(Paragraph(text, heading2)); in_toc = True
            continue
        if in_toc:
            if text.startswith('La portada corresponde'):
                story.append(Paragraph(escape(text), normal))
                toc = TableOfContents(); toc.levelStyles = [toc_style]; toc.dotsMinLevel = 0
                story.append(toc); toc_inserted = True
                continue
            if style_name == 'Heading 1' and text.startswith('3 Introducción'):
                in_toc = False; story.append(PageBreak())
            else:
                continue
        if block.xpath('.//w:br[@w:type="page"]'):
            if story and not isinstance(story[-1], PageBreak): story.append(PageBreak())
            continue
        drawings = block.xpath('.//a:blip')
        if drawings:
            embed = drawings[0].get(qn('r:embed'))
            blob = document.part.related_parts[embed].blob
            extent = block.xpath('.//wp:extent')[0]
            width = int(extent.get('cx')) / 12700
            height = int(extent.get('cy')) / 12700
            scale = min(1, 468/width, 570/height)
            image = Image(BytesIO(blob), width=width*scale, height=height*scale)
            image.hAlign = 'CENTER'; story.append(image); image_count += 1
            continue
        if not text:
            story.append(Spacer(1, 18))
            continue
        style = heading if style_name == 'Heading 1' else heading2 if style_name.startswith('Heading') else title if style_name == 'Title' else caption if style_name == 'Caption' else center if paragraph.alignment == 1 else normal
        if text.startswith(('Beyer,', 'Docker.', 'ESLint.', 'GitHub.', 'Jest.', 'Node.js.', 'npm.', 'OpenJS Foundation.', 'Playwright.', 'Render.')) and style_name == 'Normal':
            style = ParagraphStyle('Reference', parent=normal, leftIndent=36, firstLineIndent=-36)
        story.append(Paragraph(inline(paragraph), style))
    elif tag == 'tbl' and not in_toc:
        table = WordTable(block, document)
        widths = [column.width.pt for column in table.columns]
        total = sum(widths); widths = [width*468/total for width in widths]
        rows = []
        for index, row in enumerate(table.rows):
            rows.append([Paragraph('<br/>'.join(inline(para) for para in item.paragraphs), cell_header if index == 0 else cell) for item in row.cells])
        rendered = LongTable(rows, colWidths=widths, repeatRows=1, hAlign='CENTER')
        commands = [('GRID', (0, 0), (-1, -1), .5, colors.HexColor('#D9D9D9')), ('BACKGROUND', (0,0),(-1,0),colors.HexColor('#DFE5EF')), ('VALIGN', (0,0),(-1,-1),'MIDDLE'), ('LEFTPADDING',(0,0),(-1,-1),5), ('RIGHTPADDING',(0,0),(-1,-1),5), ('TOPPADDING',(0,0),(-1,-1),5), ('BOTTOMPADDING',(0,0),(-1,-1),5)]
        for index in range(2, len(rows), 2): commands.append(('BACKGROUND',(0,index),(-1,index),colors.HexColor('#F5F6F9')))
        rendered.setStyle(TableStyle(commands)); story.append(rendered); story.append(Spacer(1, 8))
assert toc_inserted
cleaned = []
for item in story:
    if isinstance(item, PageBreak):
        while cleaned and isinstance(cleaned[-1], Spacer): cleaned.pop()
        if cleaned and isinstance(cleaned[-1], PageBreak): continue
    cleaned.append(item)
story = cleaned
pdf = AcademicPdf(str(output)); pdf.multiBuild(story)
(root / 'evidence/document-export.json').write_text(json.dumps({
    'timestamp': datetime.now(timezone.utc).isoformat(), 'converter': 'ReportLab con contenido y figuras del DOCX',
    'pages': pdf.page, 'images': image_count, 'tocUpdated': True,
    'limitation': 'Word abrió, actualizó índice y repaginó el DOCX, pero la exportación PDF de Word no finalizó. El PDF se compuso desde el mismo contenido; sus saltos y páginas pueden diferir del editable.',
    'docx': 'docs/Manejo-de-Scripts.docx', 'pdf': 'docs/Manejo-de-Scripts.pdf'
}, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'PDF generado desde el contenido real del DOCX: {pdf.page} páginas y {image_count} imágenes.')
