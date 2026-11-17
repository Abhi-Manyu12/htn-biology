"""Extract the three figures of BTP_Checkpoint2.pdf losslessly into report/figures/orig/.

Figure 1 (p.8) and Figure 3 (p.12) are raster images embedded in the PDF: copied as PNG.
Figure 2 (p.9) was drawn with pgfplots: cropped as vector PDF (clip around plot + axis labels,
caption excluded) plus a 300-dpi PNG render.
Usage: python extract_figures.py <W>
"""
import shutil, sys
from pathlib import Path
import pymupdf as fitz

W = Path(sys.argv[1])
src_pdf = W / "report_src" / "BTP_Checkpoint2.pdf"
out = W / "report" / "figures" / "orig"
out.mkdir(parents=True, exist_ok=True)

shutil.copyfile(W / "report_src" / "images" / "p08_img1.png", out / "fig1_web_ui.png")
shutil.copyfile(W / "report_src" / "images" / "p12_img1.png", out / "fig3_success_vs_removal.png")

src = fitz.open(src_pdf)
page = src[8]
# bbox of all vector drawings and axis/tick label text of the plot (found from
# page.get_drawings() / page.get_text("blocks")): x 82.9..528.5, y 262.8..439.8
clip = fitz.Rect(81.5, 261.0, 530.0, 441.5)
# work on a one-page copy and remove (redact) everything outside the clip so that no
# hidden text/graphics of the rest of the page is carried into the figure PDF
tmp = fitz.open()
tmp.insert_pdf(src, from_page=8, to_page=8)
tp = tmp[0]
R = tp.rect
for r in (fitz.Rect(R.x0, R.y0, R.x1, clip.y0), fitz.Rect(R.x0, clip.y1, R.x1, R.y1),
          fitz.Rect(R.x0, clip.y0, clip.x0, clip.y1), fitz.Rect(clip.x1, clip.y0, R.x1, clip.y1)):
    tp.add_redact_annot(r)
tp.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE, graphics=fitz.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
doc = fitz.open()
p = doc.new_page(width=clip.width, height=clip.height)
p.show_pdf_page(p.rect, tmp, 0, clip=clip)
doc.save(out / "fig2_cumulative_energy.pdf", garbage=4, deflate=True)
p.get_pixmap(dpi=300).save(out / "fig2_cumulative_energy.png")
print("clip", clip, "width/linewidth", clip.width / 468.0)
