from flask import Blueprint, render_template, request, send_file, jsonify
import os
import tempfile
import zipfile
from werkzeug.utils import secure_filename
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

pdf_batch_merge_bp = Blueprint('pdf_batch_merge', __name__)

@pdf_batch_merge_bp.route('/pdf-batch-merge')
def pdf_batch_merge_page():
    return render_template('pdf_batch_merge.html')

@pdf_batch_merge_bp.route('/batch-merge-preview', methods=['POST'])
def batch_merge_preview():
    return _batch_merge_core(preview=True)

@pdf_batch_merge_bp.route('/batch-merge', methods=['POST'])
def batch_merge():
    return _batch_merge_core(preview=False)

def _batch_merge_core(preview=False):
    files = request.files.getlist('files[]')
    toc_list = request.form.getlist('tocList[]')
    font_path = os.path.join('static', 'fonts')
    font_file = None
    # 优先选择 TTF 字体，避免 OTF
    for f in os.listdir(font_path):
        if f.lower().endswith(('.ttf', '.ttc')):  # 只选 ttf/ttc
            font_file = os.path.join(font_path, f)
            break
    font_name = 'CustomCNFont'
    if font_file:
        pdfmetrics.registerFont(TTFont(font_name, font_file))
    # 生成目录、封面、正文
    merger = PdfWriter()
    toc_entries = []
    cover_page_indices = []
    temp_pages = []
    bookmark_names = []
    # 先生成所有封面和正文，记录封面页索引
    for idx, file in enumerate(files):
        if file.filename == '':
            continue
        filename = secure_filename(file.filename)
        toc_name = toc_list[idx] if idx < len(toc_list) else filename
        # 生成唯一书签名，避免中文或特殊字符导致PDF跳转异常
        bookmark_name = f"toc_title_{idx+1}"
        bookmark_names.append(bookmark_name)
        # 封面页
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=A4)
        if font_file:
            can.setFont(font_name, 32)
        else:
            can.setFont('Helvetica-Bold', 32)
        # 封面标题自动换行，最多两行，每行15字，超出省略
        title = toc_name
        if len(title) > 30:
            title = title[:29] + '…'
        if len(title) > 15:
            line1 = title[:15]
            line2 = title[15:30]
            can.drawCentredString(297, 440, line1)
            can.drawCentredString(297, 390, line2)
        else:
            can.drawCentredString(297, 420, title)
        can.showPage()
        can.save()
        packet.seek(0)
        cover_pdf = PdfReader(packet)
        cover_page = cover_pdf.pages[0]
        temp_pages.append(cover_page)
        cover_page_indices.append(len(temp_pages)-1)
        toc_entries.append({'title': toc_name, 'page': len(temp_pages), 'bookmark': bookmark_name})
        # 正文页
        file_stream = io.BytesIO(file.read())
        reader = PdfReader(file_stream)
        for page in reader.pages:
            temp_pages.append(page)
    # 目录页
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    if font_file:
        can.setFont(font_name, 18)
    else:
        can.setFont('Helvetica', 18)
    # 标题居中
    can.drawCentredString(297, 800, "目录")
    if font_file:
        can.setFont(font_name, 14)
    else:
        can.setFont('Helvetica', 14)
    y = 770
    for entry in toc_entries:
        toc_text = f"{entry['title']} ...... {entry['page']+1}"
        can.drawString(80, y, toc_text)
        y -= 24
    can.showPage()
    can.save()
    packet.seek(0)
    toc_pdf = PdfReader(packet)
    merger.add_page(toc_pdf.pages[0])
    # 添加封面和正文页，并加书签
    bookmark_page_offset = 1  # 目录页占1页
    for idx, page in enumerate(temp_pages):
        merger.add_page(page)
    # 添加书签（PyPDF2 3.x: add_outline_item，2.x: addBookmark）
    try:
        # 兼容新版 PyPDF2
        for i, entry in enumerate(toc_entries):
            merger.add_outline_item(entry['title'], entry['page'] + bookmark_page_offset)
    except Exception:
        # 兼容旧版 PyPDF2
        for i, entry in enumerate(toc_entries):
            merger.addBookmark(entry['title'], entry['page'] + bookmark_page_offset)
    # 页码覆盖
    output_stream = io.BytesIO()
    # 重新加页码（遍历 merger.pages）
    temp_writer = PdfWriter()
    for idx, page in enumerate(merger.pages):
        mediabox = page.mediabox
        page_width = float(mediabox.width)
        page_height = float(mediabox.height)
        packet2 = io.BytesIO()
        can2 = canvas.Canvas(packet2, pagesize=(page_width, page_height))
        if font_file:
            can2.setFont(font_name, 16)
        else:
            can2.setFont('Helvetica', 16)
        # 获取旋转角度，标准化为0-3
        rotate = int(page.get('/Rotate', 0))
        rotate = (rotate // 90) % 4
        page_num_str = str(idx+1)
        if rotate == 0:
            # 正常方向
            can2.drawRightString(page_width - 20, 20, page_num_str)
        elif rotate == 1:
            # 顺时针90°
            can2.saveState()
            can2.translate(page_width, 0)
            can2.rotate(90)
            can2.drawRightString(page_height - 20, 20, page_num_str)
            can2.restoreState()
        elif rotate == 2:
            # 180°
            can2.saveState()
            can2.translate(page_width, page_height)
            can2.rotate(180)
            can2.drawRightString(page_width - 20, 20, page_num_str)
            can2.restoreState()
        elif rotate == 3:
            # 270°
            can2.saveState()
            can2.translate(0, page_height)
            can2.rotate(270)
            can2.drawRightString(page_height - 20, 20, page_num_str)
            can2.restoreState()
        can2.save()
        packet2.seek(0)
        overlay_pdf = PdfReader(packet2)
        page.merge_page(overlay_pdf.pages[0])
        temp_writer.add_page(page)
    temp_writer.write(output_stream)
    output_stream.seek(0)
    if preview:
        return send_file(output_stream, as_attachment=False, mimetype='application/pdf')
    else:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, '批量合并结果.pdf')
            with open(pdf_path, 'wb') as f_out:
                f_out.write(output_stream.read())
            return send_file(
                pdf_path,
                as_attachment=True,
                download_name='批量合并结果.pdf',
                mimetype='application/pdf'
            ) 