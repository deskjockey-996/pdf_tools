from flask import Blueprint, request, jsonify, send_file, render_template
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import os
from werkzeug.utils import secure_filename
import tempfile

pdf_merge_bp = Blueprint('pdf_merge', __name__)

@pdf_merge_bp.route('/pdf-merge')
def pdf_merge_page():
    return render_template('pdf_merge.html')

@pdf_merge_bp.route('/merge', methods=['POST'])
def merge_pdfs():
    print('request.files:', request.files)
    print('request.form:', request.form)
    print('request.files keys:', list(request.files.keys()))
    files = []
    # 支持多种字段名
    for key in ['files[]', 'file', 'pdfFiles']:
        files += request.files.getlist(key)
    # 只过滤空文件名
    files = [f for f in files if f and f.filename]
    print('有效 files:', files)
    for f in files:
        print('filename:', f.filename, 'content_length:', f.content_length)
    if not files:
        return jsonify({'error': '没有上传文件（支持字段 files[]/file/pdfFiles，均为空）'}), 400

    # 获取页面顺序和旋转信息
    page_numbers = request.form.getlist('pageNumbers[]')
    rotations = request.form.getlist('rotations[]')

    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 只在单文件且页面参数齐全时做页面重组
        if len(files) == 1 and page_numbers and rotations and len(page_numbers) == len(rotations):
            file = files[0]
            filename = secure_filename(file.filename)
            filepath = os.path.join(temp_dir, filename)
            file.save(filepath)
            reader = PdfReader(filepath)
            writer = PdfWriter()
            for idx, (page_str, rot_str) in enumerate(zip(page_numbers, rotations)):
                page_index = int(page_str) - 1  # 前端是1-based
                rotation = int(rot_str)
                if 0 <= page_index < len(reader.pages):
                    page = reader.pages[page_index]
                    if rotation != 0:
                        page = page.rotate(rotation)
                    writer.add_page(page)
            output_path = os.path.join(temp_dir, 'edited.pdf')
            with open(output_path, 'wb') as f_out:
                writer.write(f_out)
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"{filename.replace('.pdf', '')}_edited.pdf",
                mimetype='application/pdf'
            )
        else:
            # 多文件合并或无页面参数时，直接合并所有 files[]
            print('走合并分支，files数量:', len(files), 'page_numbers:', page_numbers, 'rotations:', rotations)
            merger = PdfMerger()
            for file in files:
                if file.filename == '':
                    continue
                if not file.filename.lower().endswith('.pdf'):
                    return jsonify({'error': '只支持PDF文件'}), 400
                filename = secure_filename(file.filename)
                filepath = os.path.join(temp_dir, filename)
                file.save(filepath)
                merger.append(filepath)
            output_path = os.path.join(temp_dir, 'merged.pdf')
            merger.write(output_path)
            merger.close()
            return send_file(
                output_path,
                as_attachment=True,
                download_name=f"{files[0].filename.replace('.pdf', '')}_merge.pdf",
                mimetype='application/pdf'
            ) 