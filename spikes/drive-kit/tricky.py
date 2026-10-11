# -*- coding: utf-8 -*-
def parse(rows):
	# tab-indented on purpose
	return [r.strip() for r in rows]   

GREETING = "שלום — ‘quotes’ “double” …"
EMOJI = "✓ ✗ →"
RAW = r'\d+\s*\\'
EMPTY_LINES_BELOW = True



