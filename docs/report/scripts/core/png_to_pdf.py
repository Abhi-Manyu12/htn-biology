"""Wrap a PNG screenshot in a one-page PDF of the same aspect (used for the UI captures, whose Chrome
print-to-PDF renders the gradient title text with an outline box)."""
import sys
import pymupdf
png, pdf = sys.argv[1], sys.argv[2]
img = pymupdf.open(png)
r = img[0].rect
doc = pymupdf.open()
page = doc.new_page(width=r.width / 2, height=r.height / 2)   # 2x device scale -> CSS px as pt
page.insert_image(page.rect, filename=png)
doc.save(pdf, deflate=True, garbage=3)
