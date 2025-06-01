import os
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import json
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 用于flash消息
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_pdf_info(filepath):
    reader = PdfReader(filepath)
    return {
        'num_pages': len(reader.pages),
        'filename': os.path.basename(filepath)
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/rotate')
def rotate():
    return render_template('rotate.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'pdf_file' not in request.files:
        return jsonify({'success': False, 'error': '没有文件'})
    
    file = request.files['pdf_file']
    if file.filename == '':
        return jsonify({'success': False, 'error': '没有选择文件'})
    
    if file and file.filename.endswith('.pdf'):
        filename = str(uuid.uuid4()) + '.pdf'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        return jsonify({
            'success': True,
            'filename': filename,
            'pages': len(PdfReader(filepath).pages)
        })
    
    return jsonify({'success': False, 'error': '只支持PDF文件'})

@app.route('/preview/<filename>')
def preview_pdf(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route('/process', methods=['POST'])
def process_pdf():
    data = request.json
    operation = data.get('operation')
    filename = data.get('filename')
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': '文件不存在'})
    
    reader = PdfReader(filepath)
    writer = PdfWriter()
    
    if operation == 'rotate':
        angle = data.get('angle', 90)
        pages = data.get('pages', [])
        
        for i in range(len(reader.pages)):
            page = reader.pages[i]
            if i + 1 in pages:  # 因为页面索引从1开始
                page.rotate(angle)
            writer.add_page(page)
            
    elif operation == 'delete':
        pages_to_delete = set(data.get('pages', []))
        for i in range(len(reader.pages)):
            if i + 1 not in pages_to_delete:  # 因为页面索引从1开始
                writer.add_page(reader.pages[i])
                
    elif operation == 'reorder':
        new_order = data.get('new_order', [])
        for page_num in new_order:
            writer.add_page(reader.pages[page_num - 1])  # 因为页面索引从1开始
            
    else:
        return jsonify({'success': False, 'error': '不支持的操作'})
    
    # 保存处理后的文件
    output_filename = str(uuid.uuid4()) + '.pdf'
    output_path = os.path.join(UPLOAD_FOLDER, output_filename)
    
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    
    # 删除原文件
    os.remove(filepath)
    
    return jsonify({
        'success': True,
        'filename': output_filename
    })

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(
        os.path.join(UPLOAD_FOLDER, filename),
        as_attachment=True,
        download_name=filename
    )

if __name__ == '__main__':
    app.run(debug=True) 