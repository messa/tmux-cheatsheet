#!/usr/bin/env python3
"""Kontrola interních odkazů v README.md.

Z nadpisů vygeneruje kotvy stejným algoritmem jako GitHub (backticky pryč,
interpunkce pryč, lowercase, mezery na pomlčky, duplicity s příponou -1,
-2, …) a ověří, že každý odkaz tvaru ](#kotva) na nějakou existující míří.
"""

import re
import sys
from pathlib import Path


def anchor_for(heading: str) -> str:
    a = heading.strip().lower()
    a = a.replace('`', '')
    a = re.sub(r'[^\w\s-]', '', a)
    a = re.sub(r'\s', '-', a)
    return a


def main() -> int:
    text = (Path(__file__).parent / 'README.md').read_text(encoding='utf-8')

    anchors = set()
    counts = {}
    in_code = False
    for line in text.splitlines():
        if line.startswith('```'):
            in_code = not in_code
            continue
        m = re.match(r'#{1,6}\s+(.*)', line)
        if m and not in_code:
            base = anchor_for(m.group(1))
            n = counts.get(base, 0)
            counts[base] = n + 1
            anchors.add(base if n == 0 else f'{base}-{n}')

    links = re.findall(r'\]\(#([^)]+)\)', text)
    broken = [link for link in links if link not in anchors]

    print(f'{len(links)} odkazů, {len(broken)} rozbitých')
    for link in broken:
        print(f'  rozbitý: #{link}')
    return 1 if broken else 0


if __name__ == '__main__':
    sys.exit(main())
