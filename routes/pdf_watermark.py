from flask import Blueprint, render_template, request, send_file
from werkzeug.utils import secure_filename
import PyPDF2
import io
import os
import tempfile
import zipfile
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color
from reportlab.pdfbase.pdfmetrics import stringWidth

pdf_watermark_bp = Blueprint('pdf_watermark', __name__)

# 字体路径
FONT_PATH = os.path.join(os.path.dirname(__file__), '..', 'static', 'fonts', 'NotoSansSCMedium.ttf')
if not pdfmetrics.getRegisteredFontNames() or 'NotoSansSC' not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(TTFont('NotoSansSC', FONT_PATH))

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_watermark_pdf(text, font_size, color, opacity, rotation, is_tiled, position, page_width, page_height, tiled_spacing_x=1.2, tiled_spacing_y=1.5):
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=(page_width, page_height))
    r, g, b = [v/255 for v in color]
    c.setFillColor(Color(r, g, b, alpha=opacity))
    c.setFont('NotoSansSC', font_size)
    if is_tiled:
        text_width = stringWidth(text, 'NotoSansSC', font_size)
        text_height = font_size

        # 更密集的平铺
        step_x = text_width * tiled_spacing_x
        step_y = text_height * tiled_spacing_y

        x_start = -text_width
        y_start = -text_height

        y = y_start
        row = 0
        while y < page_height + text_height:
            x_offset = 0 if row % 2 == 0 else step_x / 2
            x = x_start + x_offset
            while x < page_width + text_width:
                c.saveState()
                c.translate(x, y)
                c.rotate(rotation)
                c.drawCentredString(0, 0, text)
                c.restoreState()
                x += step_x
            y += step_y
            row += 1
    else:
        # 计算位置
        if position == 'center':
            x = page_width / 2
            y = page_height / 2
        elif position == 'top-left':
            x = 100
            y = page_height - 100
        elif position == 'top-right':
            x = page_width - 100
            y = page_height - 100
        elif position == 'bottom-left':
            x = 100
            y = 100
        elif position == 'bottom-right':
            x = page_width - 100
            y = 100
        c.saveState()
        c.translate(x, y)
        c.rotate(rotation)
        c.drawCentredString(0, 0, text)
        c.restoreState()
    c.save()
    packet.seek(0)
    return packet

@pdf_watermark_bp.route('/pdf_watermark', methods=['GET', 'POST'])
def pdf_watermark():
    if request.method == 'POST':
        if 'pdfFiles' not in request.files:
            return '没有选择文件', 400
        
        files = request.files.getlist('pdfFiles')
        if not files or files[0].filename == '':
            return '没有选择文件', 400

        watermark_type = request.form.get('watermarkType', 'text')
        opacity = float(request.form.get('opacity', 0.5))
        position = request.form.get('position', 'center')
        color = hex_to_rgb(request.form.get('color', '#000000'))
        rotation = float(request.form.get('rotation', 0))
        is_tiled = request.form.get('isTiled') in ['true', 'on', '1']
        font_size = int(request.form.get('fontSize', 36))
        text = request.form.get('watermarkText', '水印文字')
        tiled_spacing_x = float(request.form.get('tiledSpacingX', 1.2))
        tiled_spacing_y = float(request.form.get('tiledSpacingY', 1.5))
        print('is_tiled:', is_tiled, 'raw:', request.form.get('isTiled'))

        # 只支持文字水印，图片水印可后续扩展
        def process_one_pdf(file):
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                file.save(temp_pdf.name)
                try:
                    reader = PyPDF2.PdfReader(temp_pdf.name)
                    writer = PyPDF2.PdfWriter()
                    for page in reader.pages:
                        width = float(page.mediabox.width)
                        height = float(page.mediabox.height)
                        # 生成与当前页尺寸一致的水印PDF
                        watermark_pdf = create_watermark_pdf(
                            text, font_size, color, opacity, rotation, is_tiled, position, width, height, tiled_spacing_x, tiled_spacing_y
                        )
                        watermark_reader = PyPDF2.PdfReader(watermark_pdf)
                        page.merge_page(watermark_reader.pages[0])
                        writer.add_page(page)
                    output = io.BytesIO()
                    writer.write(output)
                    output.seek(0)
                    return output.read()
                finally:
                    os.unlink(temp_pdf.name)

        # 预览
        if request.form.get('preview') == 'true':
            file = files[0]
            pdf_bytes = process_one_pdf(file)
            return send_file(
                io.BytesIO(pdf_bytes),
                mimetype='application/pdf',
                as_attachment=False
            )

        # 批量处理并打包
        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, 'w') as zf:
            for file in files:
                if file and file.filename.endswith('.pdf'):
                    pdf_bytes = process_one_pdf(file)
                    filename = secure_filename(file.filename)
                    zf.writestr(filename, pdf_bytes)
        memory_zip.seek(0)
        return send_file(
            memory_zip,
            mimetype='application/zip',
            as_attachment=True,
            download_name='watermarked_pdfs.zip'
        )

    return render_template('pdf_watermark.html')