from flask import Blueprint, request, jsonify, send_file, render_template
import os
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
import tempfile
import pandas as pd
from datetime import datetime

pdf_count = Blueprint('pdf_count', __name__)

@pdf_count.route('/')
def pdf_count_page():
    return render_template('pdf_count.html')

@pdf_count.route('/analyze', methods=['POST'])
def analyze_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '未找到文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': '请上传PDF文件'}), 400

    try:
        # 创建临时文件来保存上传的PDF
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            reader = PdfReader(temp_file.name)
            num_pages = len(reader.pages)
        
        # 删除临时文件
        os.unlink(temp_file.name)
        
        return jsonify({
            'pages': num_pages
        })
    except Exception as e:
        return jsonify({'error': f'处理PDF文件时出错: {str(e)}'}), 500

@pdf_count.route('/preview', methods=['POST'])
def preview_pdf():
    if 'file' not in request.files:
        return '未找到文件', 400
    
    file = request.files['file']
    if file.filename == '':
        return '未选择文件', 400
    
    if not file.filename.lower().endswith('.pdf'):
        return '请上传PDF文件', 400

    try:
        # 创建临时文件来保存上传的PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            file.save(temp_file.name)
            return send_file(
                temp_file.name,
                mimetype='application/pdf',
                as_attachment=False,
                download_name=secure_filename(file.filename)
            )
    except Exception as e:
        return f'处理PDF文件时出错: {str(e)}', 500

@pdf_count.route('/export', methods=['POST'])
def export_excel():
    try:
        data = request.get_json()
        if not data or 'files' not in data:
            return jsonify({'error': '没有数据可导出'}), 400

        # 创建DataFrame
        df = pd.DataFrame(data['files'])
        
        # 添加时间戳到文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_filename = f'pdf_pages_count_{timestamp}.xlsx'
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_file:
            # 将DataFrame保存为Excel文件
            df.to_excel(temp_file.name, index=False, engine='openpyxl')
            
            # 发送文件
            return send_file(
                temp_file.name,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name=excel_filename
            )
    except Exception as e:
        return jsonify({'error': f'导出Excel时出错: {str(e)}'}), 500 