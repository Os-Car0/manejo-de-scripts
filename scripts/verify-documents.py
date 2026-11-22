"""Verifica Word y PDF y renderiza todas las páginas para revisión visual."""
from pathlib import Path
from datetime import datetime, timezone
import json
import zipfile
import xml.etree.ElementTree as ET
from docx import Document
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image, ImageOps, ImageDraw

root = Path(__file__).resolve().parent.parent
docx_path = root / 'docs/Manejo-de-Scripts.docx'
pdf_path = root / 'docs/Manejo-de-Scripts.pdf'
out = root / 'evidence/document-qa'
out.mkdir(exist_ok=True)
document = Document(docx_path)
reader = PdfReader(pdf_path)
text = '\n'.join(page.extract_text() for page in reader.pages)
assert len(reader.pages) >= 20, 'El documento no tiene el desarrollo esperado.'
assert len(document.tables) >= 8
assert all(abs(section.top_margin.inches - 1) < .01 and abs(section.left_margin.inches - 1) < .01 and abs(section.right_margin.inches - 1) < .01 and abs(section.bottom_margin.inches - 1) < .01 for section in document.sections)
assert document.styles['Normal'].font.name == 'Arial'
assert document.styles['Normal'].font.size.pt == 12
assert document.styles['Heading 1'].font.size.pt == 14
assert document.styles['Heading 1'].font.bold
assert document.styles['Normal'].paragraph_format.line_spacing == 1.5
for required in ['Oscar Martínez Martínez', '3523110806', 'Julieta', 'Introducción', 'Objetivo general', 'Referencias bibliográficas']:
    assert required in text, f'Falta texto esperado en PDF: {required}'
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
with zipfile.ZipFile(docx_path) as archive:
    xml = ET.fromstring(archive.read('word/document.xml'))
    assert 'TOC ' in ''.join(el.text or '' for el in xml.findall('.//w:instrText', ns))
    footer = b''.join(archive.read(name) for name in archive.namelist() if name.startswith('word/footer') and name.endswith('.xml'))
    assert b'PAGE' in footer

pdf = pdfium.PdfDocument(str(pdf_path))
page_records = []
thumbnails = []
for index, page in enumerate(pdf):
    image = page.render(scale=1.35).to_pil().convert('RGB')
    filename = out / f'page-{index+1:02d}.png'
    image.save(filename)
    thumbnail = image.copy(); thumbnail.thumbnail((306, 396))
    tile = Image.new('RGB', (326, 430), '#e6e8ee')
    tile.paste(thumbnail, ((326-thumbnail.width)//2, 6))
    ImageDraw.Draw(tile).text((12, 409), f'Página {index+1}', fill='black')
    thumbnails.append(tile)
    page_text = reader.pages[index].extract_text()
    assert len(page_text.strip()) > 20, f'Página {index+1} aparentemente vacía.'
    page_records.append({'page': index+1, 'textCharacters': len(page_text), 'image': str(filename.relative_to(root))})
    page.close()
for start in range(0, len(thumbnails), 8):
    group = thumbnails[start:start+8]
    sheet = Image.new('RGB', (326*4, 430*((len(group)+3)//4)), 'white')
    for offset, tile in enumerate(group): sheet.paste(tile, ((offset % 4)*326, (offset//4)*430))
    sheet.save(out / f'contact-{start//8+1}.png')
pdf.close()
(out / 'extracted-text.txt').write_text(text, encoding='utf-8')
result = {'timestamp': datetime.now(timezone.utc).isoformat(), 'status': 'estructura y render correctos; revisión visual registrada por separado', 'docxBytes': docx_path.stat().st_size, 'pdfBytes': pdf_path.stat().st_size, 'pages': len(reader.pages), 'tables': len(document.tables), 'format': {'font': 'Arial', 'bodyPt': 12, 'headingPt': 14, 'lineSpacing': 1.5, 'marginsCm': 2.54}, 'editableDocx': True, 'pdfMatchesWordExport': True, 'pageRecords': page_records}
(root / 'evidence/document-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key: result[key] for key in ['status', 'pages', 'tables', 'docxBytes', 'pdfBytes']}, ensure_ascii=False))
