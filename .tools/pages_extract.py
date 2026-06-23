import re, zlib, json
from pathlib import Path

path = Path(r"U:\Github\book-reading\high-performance-mysql-4th\high-performance-mysql-4th.pdf")
data = path.read_bytes()

def decode_pdf_string(s):
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i + 1]
            mapping = {'n': '\n', 'r': '\r', 't': '\t', 'b': '\b', 'f': '\f', '(': '(', ')': ')', '\\': '\\'}
            out.append(mapping.get(n, n))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)

def extract_strings(dec):
    parts = []
    for m in re.finditer(rb'\((?:\\.|[^\\)])*\)\s*Tj', dec):
        inner = m.group(0)[:-3].strip()
        if inner.startswith(b'('):
            inner = inner[1:]
        if inner.endswith(b')'):
            inner = inner[:-1]
        parts.append(decode_pdf_string(inner.decode('latin1', errors='ignore')))
    return parts

def decompress_stream(stream_bytes):
    for fn in (lambda b: zlib.decompress(b), lambda b: zlib.decompress(b[2:])):
        try:
            return fn(stream_bytes)
        except Exception:
            pass

all_parts = []
pos = 0
while True:
    idx = data.find(b'/FlateDecode', pos)
    if idx < 0:
        break
    chunk = data[idx:idx + 300]
    m = re.search(rb'/Length\s+(\d+)', chunk)
    if not m:
        pos = idx + 12
        continue
    length = int(m.group(1))
    sidx = data.find(b'stream', idx)
    if sidx < 0 or sidx > idx + 400:
        pos = idx + 12
        continue
    start = sidx + 6
    if data[start:start + 1] == b'\r':
        start += 1
    if data[start:start + 1] == b'\n':
        start += 1
    dec = decompress_stream(data[start:start + length])
    if dec:
        all_parts.extend(extract_strings(dec))
    pos = start + length

current_page = None
pages = {}
buf = []
for p in all_parts:
    p = p.replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
    if re.fullmatch(r'\d{1,3}', p.strip()):
        pg = int(p.strip())
        if 100 <= pg <= 250:
            if current_page is not None and buf:
                pages[current_page] = pages.get(current_page, '') + ' ' + ' '.join(buf)
            current_page = pg
            buf = []
            continue
    if current_page is not None:
        buf.append(p)

if current_page and buf:
    pages[current_page] = pages.get(current_page, '') + ' ' + ' '.join(buf)

out = Path(r"U:\Github\book-reading\.tools\pages.json")
json.dump(
    {str(k): v[:2500] for k, v in sorted(pages.items()) if 125 <= k <= 226},
    open(out, 'w', encoding='utf-8'),
    ensure_ascii=False,
    indent=1,
)
print('pages', sorted(k for k in pages if 125 <= k <= 226))
