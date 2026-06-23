import re, zlib, sys
from pathlib import Path

path = Path(r"U:\Github\book-reading\high-performance-mysql-4th\high-performance-mysql-4th.pdf")
data = path.read_bytes()
text = data.decode('latin1')

# extract all flate streams with length
pattern = re.compile(rb'/Length\s+(\d+)\s*/Filter\s*/FlateDecode.*?stream\r?\n', re.DOTALL)
# simpler: find stream/endstream pairs after FlateDecode nearby
results = []
pos = 0
while True:
    idx = data.find(b'/FlateDecode', pos)
    if idx < 0: break
    chunk = data[idx:idx+200]
    m = re.search(rb'/Length\s+(\d+)', chunk)
    if not m:
        pos = idx + 10; continue
    length = int(m.group(1))
    sidx = data.find(b'stream', idx)
    if sidx < 0 or sidx > idx + 500:
        pos = idx + 10; continue
    start = sidx + 6
    if data[start:start+1] == b'\r': start += 1
    if data[start:start+1] == b'\n': start += 1
    stream = data[start:start+length]
    try:
        dec = zlib.decompress(stream)
        s = dec.decode('latin1', errors='ignore')
        if 'Tj' in s or 'TJ' in s or 'BT' in s:
            # extract strings
            for sm in re.findall(r'\((?:\\.|[^\\)])*\)\s*Tj', s):
                inner = sm[:-3].strip()
                if inner.startswith('('): inner = inner[1:]
                results.append(inner)
    except Exception:
        pass
    pos = idx + 10

out = '\n'.join(results)
print('strings', len(results), 'chars', len(out))
for term in ['CHAPTER 6', 'Schema Design', 'CHAPTER 7', 'Indexing', 'CHAPTER 8', 'Query Performance', 'Normalization', 'B-Tree']:
    print(term, out.find(term))
print('---PREVIEW---')
print(out[:3000])
