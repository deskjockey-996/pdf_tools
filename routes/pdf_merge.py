from flask import Blueprint, request, jsonify, send_file, render_template
from PyPDF2 import PdfMerger
import os
from werkzeug.utils import secure_filename
import tempfile

pdf_merge_bp = Blueprint('pdf_merge', __name__)

@pdf_merge_bp.route('/pdf-merge')
def pdf_merge_page():
    return render_template('pdf_merge.html')

@pdf_merge_bp.route('/merge', methods=['POST'])
def merge_pdfs():
    if 'files[]' not in request.files:
        return jsonify({'error': '没有上传文件'}), 400
    
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': '没有选择文件'}), 400
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        merger = PdfMerger()
        
        # 保存并合并所有文件
        for file in files:
            if file.filename == '':
                continue
                
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'error': '只支持PDF文件'}), 400
                
            filename = secure_filename(file.filename)
            filepath = os.path.join(temp_dir, filename)
            file.save(filepath)
            merger.append(filepath)
        
        # 创建输出文件
        output_path = os.path.join(temp_dir, 'merged.pdf')
        merger.write(output_path)
        merger.close()
        
        # 发送合并后的文件
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f"{files[0].filename.replace('.pdf', '')}_merge.pdf",
            mimetype='application/pdf'
        ) 