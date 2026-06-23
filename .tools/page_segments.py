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

def extract_strings(dec):
    parts = []
    for m in re.finditer(rb'\((?:\\.|[^\\)])*\)\s*Tj', dec):
        inner = m.group(0)[:-3].strip()
        if inner.startswith(b'('): inner = inner[1:]
        if inner.endswith(b')'): inner = inner[:-1]
        s = decode_pdf_string(inner.decode('latin1', errors='ignore'))
        parts.append(s)
    return parts

def decompress_stream(stream_bytes):
    for fn in (lambda b: zlib.decompress(b), lambda b: zlib.decompress(b[2:])):
        try: return fn(stream_bytes)
        except: pass
    return None

all_parts = []
pos = 0
while True:
    idx = data.find(b'/FlateDecode', pos)
    if idx < 0: break
    chunk = data[idx:idx+300]
    m = re.search(rb'/Length\s+(\d+)', chunk)
    if not m: pos = idx+12; continue
    length = int(m.group(1))
    sidx = data.find(b'stream', idx)
    if sidx < 0 or sidx > idx+400: pos = idx+12; continue
    start = sidx+6
    if data[start:start+1]==b'\r': start+=1
    if data[start:start+1]==b'\n': start+=1
    dec = decompress_stream(data[start:start+length])
    if dec: all_parts.extend(extract_strings(dec))
    pos = start+length

# build page-aware segments
current_page = None
segments = []
buf = []
for p in all_parts:
  p = p.replace('\u2019', "'").replace('\u2018', "'").replace('\u201c', '"').replace('\u201d', '"')
  if re.fullmatch(r'\d{1,3}', p.strip()) and 1 <= int(p.strip()) <= 999:
    pg = int(p.strip())
    if 100 <= pg <= 250:
      if buf:
        segments.append((current_page, ' '.join(buf)))
        buf = []
      current_page = pg
      continue
  buf.append(p)
if buf:
  segments.append((current_page, ' '.join(buf)))

# print sections for ch6-8
for ch, lo, hi in [(6,125,154),(7,155,189),(8,191,226)]:
    print(f'\n===== CHAPTER {ch} ({lo}-{hi}) =====')
  # find headings - lines that look like section titles
    text = ' '.join(t for pg,t in segments if pg and lo <= pg <= hi)
    # major headings from book
    headings = []
    for pat in [
        r'Choosing Optimal Data Types', r'Whole Numbers', r'Real Numbers', r'String Types',
        r'BLOB and TEXT', r'Using ENUM', r'Bit-Packed', r'JSON Data', r'Choosing Identifiers',
        r'Schema Design Gotchas', r'Too Many Columns', r'Schema Management',
        r'Indexing Basics', r'Types of Indexes', r'B-tree indexes', r'Benefits of Indexes',
        r'Indexing Strategies', r'Prefix Indexes', r'Multicolumn Indexes', r'Clustered Indexes',
        r'Covering Indexes', r'Redundant and Duplicate', r'Unused Indexes', r'Index and Table Maintenance',
        r'Why Are Queries Slow', r'Slow Query Basics', r'Ways to Restructure', r'Query Execution Basics',
        r'Query Optimization Process', r'Query Execution Engine', r'Limitations of the MySQL',
        r'Optimizing COUNT', r'Optimizing JOIN', r'Optimizing GROUP BY', r'Optimizing LIMIT',
    ]:
        i = text.find(pat)
        if i>=0: headings.append((i, pat, segments_at(text, pat, segments, lo, hi)))
    # simpler: list page segments with first 80 chars
    for pg,t in segments:
        if pg and lo <= pg <= hi:
            print(f'p{pg}: {t[:120]}...' if len(t)>120 else f'p{pg}: {t}')

def segments_at(text, pat, segments, lo, hi):
    for pg,t in segments:
        if pg and lo<=pg<=hi and pat in t:
            return pg
    return None
