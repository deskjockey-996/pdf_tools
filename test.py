from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

can = canvas.Canvas("test_bookmark_with_toc.pdf", pagesize=A4)

# 目录页
can.setFont("Helvetica-Bold", 18)
can.drawCentredString(297, 800, "content")
can.setFont("Helvetica", 14)
can.drawString(80, 770, "封面1 ...... 2")
can.linkRect('', 'cover1', (80, 768, 300, 784), relative=0, thickness=0)
can.showPage()

# 封面页
can.setFont("Helvetica-Bold", 32)
can.drawCentredString(297, 420, "封面1")
can.bookmarkPage("cover1")
can.addOutlineEntry("封面1", "cover1", level=0)
can.showPage()

can.save()