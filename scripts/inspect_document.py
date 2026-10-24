"""Show how an SRS file is parsed. Run: uv run python scripts/inspect_document.py <file>"""

import sys
from pathlib import Path

from testgen.ingestion.parsers import parse_document

doc = parse_document(Path(sys.argv[1]))
print(f"{doc.name}: {len(doc.blocks)} blocks, {len(doc.text)} characters\n")
for i, block in enumerate(doc.blocks, start=1):
    preview = block.text.replace("\n", " ")[:70]
    print(f"[{i:>2}] page={block.page} section={block.section!r}\n     {preview}...")
