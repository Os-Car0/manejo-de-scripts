"""Verifica Word y PDF y renderiza todas las páginas para revisión visual."""
from pathlib import Path
from datetime import datetime, timezone
import json
import zipfile
import xml.etree.ElementTree as ET
import subprocess
import sys
import hashlib
from docx import Document
from pypdf import PdfReader
import pypdfium2 as pdfium
from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent.parent
docx_path = root / 'docs/Manejo-de-Scripts.docx'
pdf_path = root / 'docs/Manejo-de-Scripts.pdf'
out = root / 'evidence/document-qa'
out.mkdir(exist_ok=True)
assert out.resolve().is_relative_to(root.resolve())
def body_hash(image):
    return hashlib.sha256(image.convert('RGB').crop((0, 0, image.width, image.height-100)).tobytes()).hexdigest()
previous_bodies = {body_hash(Image.open(file)): file.stem for file in out.glob('page-*.png')}
for pattern in ['page-*.png', 'contact-*.png']:
    for stale in out.glob(pattern):
        assert stale.resolve().parent == out.resolve()
        stale.unlink()
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

poppler = Path(sys.executable).resolve().parent.parent / 'native/poppler/Library/bin/pdftoppm.exe'
if poppler.exists():
    subprocess.run([str(poppler), '-r', '120', '-png', str(pdf_path), str(out / 'page')], check=True, capture_output=True, timeout=180)
    pdf = None
else:
    pdf = pdfium.PdfDocument(str(pdf_path))
page_records = []
thumbnails = []
for index in range(len(reader.pages)):
    filename = out / f'page-{index+1:02d}.png'
    if pdf is None:
        image = Image.open(filename).convert('RGB')
    else:
        page = pdf[index]
        image = page.render(scale=1.7).to_pil().convert('RGB')
        image.save(filename)
        page.close()
    thumbnail = image.copy(); thumbnail.thumbnail((306, 396))
    tile = Image.new('RGB', (326, 430), '#e6e8ee')
    tile.paste(thumbnail, ((326-thumbnail.width)//2, 6))
    ImageDraw.Draw(tile).text((12, 409), f'Página {index+1}', fill='black')
    thumbnails.append(tile)
    page_text = reader.pages[index].extract_text()
    assert len(page_text.strip()) > 20, f'Página {index+1} aparentemente vacía.'
    digest = body_hash(image)
    page_records.append({'page': index+1, 'textCharacters': len(page_text), 'image': str(filename.relative_to(root)), 'bodySha256': digest, 'identicalBodyInPreviousRender': previous_bodies.get(digest)})
for start in range(0, len(thumbnails), 8):
    group = thumbnails[start:start+8]
    sheet = Image.new('RGB', (326*4, 430*((len(group)+3)//4)), 'white')
    for offset, tile in enumerate(group): sheet.paste(tile, ((offset % 4)*326, (offset//4)*430))
    sheet.save(out / f'contact-{start//8+1}.png')
if pdf is not None: pdf.close()
(out / 'extracted-text.txt').write_text(text, encoding='utf-8')
export = json.loads((root / 'evidence/document-export.json').read_text(encoding='utf-8-sig'))
result = {'timestamp': datetime.now(timezone.utc).isoformat(), 'status': 'estructura y render PDF correctos; revisión visual registrada por separado', 'docxBytes': docx_path.stat().st_size, 'pdfBytes': pdf_path.stat().st_size, 'pages': len(reader.pages), 'tables': len(document.tables), 'format': {'font': 'Arial', 'bodyPt': 12, 'headingPt': 14, 'lineSpacing': 1.5, 'marginsCm': 2.54}, 'editableDocx': True, 'pdfMatchesWordExport': 'Microsoft Word' in export['converter'], 'docxVisualReview': 'Limitada: Word abrió y repaginó el editable, pero no finalizó su exportación PDF. El PDF de ReportLab se inspecciona por separado.', 'pageRecords': page_records}
(root / 'evidence/document-validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({key: result[key] for key in ['status', 'pages', 'tables', 'docxBytes', 'pdfBytes']}, ensure_ascii=False))
