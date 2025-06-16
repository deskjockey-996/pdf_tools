import os
import json
from flask import Blueprint, request, jsonify, send_file, render_template
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
import tempfile
from pdf2image import convert_from_path
import base64
from io import BytesIO

pdf_split = Blueprint('pdf_split', __name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@pdf_split.route('/pdf_split')
def split_page():
    return render_template('pdf_split.html')

@pdf_split.route('/pdf_split/preview', methods=['POST'])
def preview_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': '请上传PDF文件'}), 400

    split_type = request.form.get('splitType', 'all')
    page_range = request.form.get('pageRange', '')

    # 保存上传的文件
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # 读取PDF
        reader = PdfReader(filepath)
        total_pages = len(reader.pages)
        # 解析页码
        if split_type == 'all' or not page_range.strip():
            page_indices = list(range(total_pages))
        else:
            page_indices = []
            ranges = page_range.split(',')
            for r in ranges:
                r = r.strip()
                if '-' in r:
                    start, end = r.split('-')
                    start = int(start) - 1
                    end = int(end)
                    page_indices.extend(list(range(start, end)))
                else:
                    idx = int(r) - 1
                    page_indices.append(idx)
            # 去重并排序
            page_indices = sorted(set([i for i in page_indices if 0 <= i < total_pages]))
        # 只生成指定页码的缩略图
        images = convert_from_path(filepath, dpi=200)
        thumbnails = []
        for i in page_indices:
            img = images[i]
            img.thumbnail((200, 200))
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            thumbnails.append(f"data:image/png;base64,{img_str}")
        return jsonify({
            'thumbnails': thumbnails,
            'total_pages': len(page_indices)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@pdf_split.route('/pdf_split/preview_selected', methods=['POST'])
def preview_selected_pages():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    pages = json.loads(request.form.get('pages', '[]'))

    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': '请上传PDF文件'}), 400

    if not pages:
        return jsonify({'error': '请选择要预览的页面'}), 400

    # 保存上传的文件
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # 读取PDF文件
        reader = PdfReader(filepath)
        writer = PdfWriter()

        # 添加选中的页面
        for page_num in pages:
            if 0 <= page_num < len(reader.pages):
                writer.add_page(reader.pages[page_num])

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            writer.write(temp_file.name)
            return send_file(
                temp_file.name,
                mimetype='application/pdf',
                as_attachment=False
            )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # 清理临时文件
        if os.path.exists(filepath):
            os.remove(filepath)

@pdf_split.route('/pdf_split/split', methods=['POST'])
def split_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    pages = json.loads(request.form.get('pages', '[]'))
    original_name = request.form.get('originalName')

    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': '请上传PDF文件'}), 400

    if not pages:
        return jsonify({'error': '请选择要保存的页面'}), 400

    # 保存上传的文件
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    try:
        # 读取PDF文件
        reader = PdfReader(filepath)
        writer = PdfWriter()

        # 添加选中的页面
        for page_num in pages:
            if 0 <= page_num < len(reader.pages):
                writer.add_page(reader.pages[page_num])

        # 生成导出文件名
        if original_name:
            base, ext = os.path.splitext(secure_filename(original_name))
        else:
            base, ext = os.path.splitext(filename)
        export_name = f"{base}_split.pdf"

        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            writer.write(temp_file.name)
            return send_file(
                temp_file.name,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=export_name
            )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        # 清理临时文件
        if os.path.exists(filepath):
            os.remove(filepath) 