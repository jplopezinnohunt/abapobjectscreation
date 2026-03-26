"""Save full docx content to text files to avoid truncation."""
import zipfile, xml.etree.ElementTree as ET, sys, os
sys.stdout.reconfigure(encoding='utf-8')

NS = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def read_docx(path):
    paragraphs = []
    with zipfile.ZipFile(path) as z:
        xml_bytes = z.read('word/document.xml')
    root = ET.fromstring(xml_bytes)
    for para in root.iter(NS + 'p'):
        texts = []
        for node in para.iter():
            if node.tag == NS + 't' and node.text:
                texts.append(node.text)
        line = ''.join(texts).strip()
        if line:
            paragraphs.append(line)
    return paragraphs

dl = os.path.expanduser('~/Downloads')
out_dir = os.getcwd()

for fn, out_fn in [
    ('SAP_Transport_Intelligence_Reference.docx', 'doc_reference.txt'),
    ('SAP_Transport_Intelligence_Modules_Supplement.docx', 'doc_supplement.txt'),
]:
    path = os.path.join(dl, fn)
    lines = read_docx(path)
    out_path = os.path.join(out_dir, out_fn)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(f'=== {fn} ===\n')
        f.write(f'Total paragraphs: {len(lines)}\n\n')
        for line in lines:
            f.write(line + '\n')
    print(f'Saved {len(lines)} paragraphs → {out_fn}')
