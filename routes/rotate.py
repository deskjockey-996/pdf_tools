from flask import Blueprint, render_template, request, jsonify, send_file
import os
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import shutil

rotate_bp = Blueprint('rotate', __name__)

@rotate_bp.route('/rotate')
def rotate():
    return render_template('rotate.html')

@rotate_bp.route('/upload_rotate', methods=['POST'])
def upload_rotate():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件被上传'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': '请上传PDF文件'}), 400
    
    # 保存上传的文件
    filename = os.path.join('uploads', file.filename)
    file.save(filename)
    
    # 读取PDF文件信息
    try:
        pdf = PdfReader(filename)
        num_pages = len(pdf.pages)
        return jsonify({
            'success': True,
            'filename': file.filename,
            'num_pages': num_pages
        })
    except Exception as e:
        return jsonify({'error': f'PDF文件处理失败: {str(e)}'}), 500

@rotate_bp.route('/rotate_page', methods=['POST'])
def rotate_page():
    data = request.get_json()
    filename = data.get('filename')
    page_num = data.get('page_num')
    rotation = data.get('rotation')
    
    if not all([filename, page_num, rotation]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    input_path = os.path.join('uploads', filename)
    if not os.path.exists(input_path):
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        # 创建临时文件
        temp_dir = tempfile.mkdtemp()
        temp_output = os.path.join(temp_dir, 'output.pdf')
        
        # 读取PDF
        pdf = PdfReader(input_path)
        writer = PdfWriter()
        
        # 处理每一页
        for i in range(len(pdf.pages)):
            page = pdf.pages[i]
            if i == page_num - 1:  # 页码从1开始
                page.rotate(rotation)
            writer.add_page(page)
        
        # 保存结果
        with open(temp_output, 'wb') as output_file:
            writer.write(output_file)
        
        # 发送文件
        return send_file(
            temp_output,
            as_attachment=True,
            download_name=f'rotated_{filename}',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        return jsonify({'error': f'旋转页面失败: {str(e)}'}), 500
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@rotate_bp.route('/rotate_selected', methods=['POST'])
def rotate_selected():
    data = request.get_json()
    filename = data.get('filename')
    selected_pages = data.get('selected_pages', [])
    rotation = data.get('rotation')
    
    if not all([filename, selected_pages, rotation]):
        return jsonify({'error': '缺少必要参数'}), 400
    
    input_path = os.path.join('uploads', filename)
    if not os.path.exists(input_path):
        return jsonify({'error': '文件不存在'}), 404
    
    try:
        # 创建临时文件
        temp_dir = tempfile.mkdtemp()
        temp_output = os.path.join(temp_dir, 'output.pdf')
        
        # 读取PDF
        pdf = PdfReader(input_path)
        writer = PdfWriter()
        
        # 处理每一页
        for i in range(len(pdf.pages)):
            page = pdf.pages[i]
            if i + 1 in selected_pages:  # 页码从1开始
                page.rotate(rotation)
            writer.add_page(page)
        
        # 保存结果
        with open(temp_output, 'wb') as output_file:
            writer.write(output_file)
        
        # 发送文件
        return send_file(
            temp_output,
            as_attachment=True,
            download_name=f'rotated_{filename}',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        return jsonify({'error': f'旋转页面失败: {str(e)}'}), 500
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir) 