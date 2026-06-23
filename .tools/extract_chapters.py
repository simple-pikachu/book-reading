import re, zlib, json
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

def extract_strings(dec):
    parts = []
    for m in re.finditer(rb'\((?:\\.|[^\\)])*\)\s*Tj', dec):
        inner = m.group(0)
        inner = inner[:-3].strip()
        if inner.startswith(b'('):
            inner = inner[1:]
            if inner.endswith(b')'):
                inner = inner[:-1]
        s = decode_pdf_string(inner.decode('latin1', errors='ignore'))
        if s.strip():
            parts.append(s)
    return parts

def decompress_stream(stream_bytes):
    for fn in (lambda b: zlib.decompress(b), lambda b: zlib.decompress(b[2:])):
        try:
            return fn(stream_bytes)
        except Exception:
            pass
    return None

# walk all flate streams in order
all_parts = []
pos = 0
while True:
    idx = data.find(b'/FlateDecode', pos)
    if idx < 0:
        break
    chunk = data[idx:idx+300]
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
    if data[start:start+1] == b'\r': start += 1
    if data[start:start+1] == b'\n': start += 1
    stream = data[start:start+length]
    dec = decompress_stream(stream)
    if dec:
        parts = extract_strings(dec)
        if parts:
            all_parts.extend(parts)
    pos = start + length

full = ' '.join(all_parts)
# normalize whitespace
full = re.sub(r'\s+', ' ', full)

markers = ['CHAPTER 6', 'CHAPTER 7', 'CHAPTER 8', 'CHAPTER 9']
for m in markers:
    print(m, full.find(m))

# extract chapter 6 snippet
i6 = full.find('CHAPTER 6')
i7 = full.find('CHAPTER 7')
i8 = full.find('CHAPTER 8')
i9 = full.find('CHAPTER 9')
ch6 = full[i6:i7]
ch7 = full[i7:i8]
ch8 = full[i8:i9]

# find printed page numbers in chapters - look for " 125 " pattern near start
for name, ch in [('ch6', ch6[:3000]), ('ch6end', ch6[-2000:]), ('ch7start', ch7[:3000]), ('ch8start', ch8[:3000])]:
    pages = re.findall(r' (?:(?:1[2-9][0-9])|(?:2[0-2][0-9])) ', ' ' + ch + ' ')
    print(name, 'pages found:', sorted(set(int(p.strip()) for p in pages))[:20], '... total', len(set(pages)))

# dump chapters for analysis
outdir = Path(r"U:\Github\book-reading\.tools")
outdir.mkdir(exist_ok=True)
for name, content in [('ch6', ch6), ('ch7', ch7), ('ch8', ch8)]:
    (outdir / f'{name}.txt').write_text(content, encoding='utf-8')
print('lengths', len(ch6), len(ch7), len(ch8))
print('ch6 start:', ch6[:800])
