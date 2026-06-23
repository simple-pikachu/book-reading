import re, zlib
from pathlib import Path

path = Path(r"U:\Github\book-reading\high-performance-mysql-4th\high-performance-mysql-4th.pdf")
data = path.read_bytes()

def decode_pdf_string(s):
    out = []
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i+1 < len(s):
            n = s[i+1]
            mapping = {'n':'\n','r':'\r','t':'\t','b':'\b','f':'\f','(': '(', ')': ')','\\':'\\'}
            out.append(mapping.get(n, n))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)

def extract_strings_from_stream(dec):
    parts = []
    for m in re.finditer(rb'\((?:\\.|[^\\)])*\)\s*Tj', dec):
        inner = m.group(0)[:-3].strip()
        if inner.startswith(b'(') and inner.endswith(b')'):
            parts.append(decode_pdf_string(inner[1:-1].decode('latin1', errors='ignore')))
    for m in re.finditer(rb'<([0-9A-Fa-f\s]+)>\s*TJ', dec):
        hexs = re.sub(rb'\s+', b'', m.group(1))
        for i in range(0, len(hexs)-3, 4):
            code = int(hexs[i:i+4], 16)
            if 32 <= code < 127:
                parts.append(chr(code))
            elif code == 10:
                parts.append('\n')
    return ''.join(parts)

def decompress_stream(stream_bytes):
    for fn in (lambda b: zlib.decompress(b), lambda b: zlib.decompress(b[2:])):
        try:
            return fn(stream_bytes)
        except Exception:
            pass
    return None

# Build object map: num -> raw bytes content
obj_re = re.compile(rb'(\d+) (\d+) obj(.*?)endobj', re.DOTALL)
objects = {}
for m in obj_re.finditer(data):
    objects[int(m.group(1))] = m.group(3)

# find page tree
page_texts = {}
page_nums = sorted([k for k,v in objects.items() if b'/Type/Page' in v and b'/Parent' in v])

# For each page, follow Contents reference and extract text
for pnum in page_nums:
    obj = objects[pnum]
    cm = re.search(rb'/Contents\s+(\d+) 0 R', obj)
    if not cm:
        continue
    cnum = int(cm.group(1))
    cobj = objects.get(cnum, b'')
    texts = []
    # could be array of content streams
    refs = re.findall(rb'(\d+) 0 R', cobj)
    if refs and b'/Contents' in obj and b'[' in cobj:
        stream_refs = refs
    elif cm:
        stream_refs = [str(cnum).encode()]
    else:
        stream_refs = refs or [str(cnum).encode()]
    for ref in stream_refs:
        onum = int(ref.split()[0])
        sobj = objects.get(onum, b'')
        sm = re.search(rb'stream\r?\n', sobj)
        if not sm:
            continue
        start = sm.end()
        em = re.search(rb'endstream', sobj[start:])
        if not em:
            continue
        stream = sobj[start:start+em.start()]
        if b'/FlateDecode' in sobj:
            dec = decompress_stream(stream)
            if dec:
                t = extract_strings_from_stream(dec)
                if t:
                    texts.append(t)
        else:
            t = stream.decode('latin1', errors='ignore')
            if t.strip():
                texts.append(t)
    if texts:
        page_texts[pnum] = '\n'.join(texts)

print('pages with text:', len(page_texts))
# sample pages around middle
keys = sorted(page_texts.keys())
for k in keys[120:130]:
    t = page_texts[k]
    print(f'--- PDF obj page {k} ---')
    print(t[:500].replace('\n',' '))
    print('printed page guess:', re.findall(r'\b(12[0-9]|13[0-9]|14[0-9]|15[0-9])\b', t[-100:]))
