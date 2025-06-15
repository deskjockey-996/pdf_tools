from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from routes import rotate_bp, image2pdf_bp
from routes.pdf_rotate import pdf_rotate_bp
from routes.pdf2image import pdf2image_bp
from routes.pdf_watermark import pdf_watermark_bp
from routes.pdf_merge import pdf_merge_bp
import os
from PyPDF2 import PdfMerger, PdfReader, PdfWriter
import tempfile
import shutil
from werkzeug.utils import secure_filename
import io
from PyPDF2.generic import NameObject, NumberObject

app = Flask(__name__)

# 设置 secret_key
app.secret_key = 'your-secret-key'  # 在生产环境中应该使用更安全的密钥

# 注册蓝图
app.register_blueprint(rotate_bp)
app.register_blueprint(image2pdf_bp)
app.register_blueprint(pdf_rotate_bp)
app.register_blueprint(pdf2image_bp)
app.register_blueprint(pdf_watermark_bp)
app.register_blueprint(pdf_merge_bp)

# 确保上传目录存在
os.makedirs('uploads', exist_ok=True)
os.makedirs('uploads/pdf', exist_ok=True)
os.makedirs('uploads/pics', exist_ok=True)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/merge')
def merge_page():
    return render_template('pdf_merge.html')

@app.route('/merge', methods=['POST'])
def merge_pdfs():
    if 'files[]' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    files = request.files.getlist('files[]')
    if not files or files[0].filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    merger = PdfMerger()
    temp_files = []

    try:
        for file in files:
            if file and file.filename.endswith('.pdf'):
                # 保存上传的文件到临时文件
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                file.save(temp_file.name)
                temp_files.append(temp_file.name)
                
                # 添加到合并器
                merger.append(temp_file.name)

        # 创建临时文件用于保存合并后的PDF
        output_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        merger.write(output_temp.name)
        merger.close()

        # 读取合并后的文件并返回
        with open(output_temp.name, 'rb') as f:
            pdf_data = f.read()

        # 清理临时文件
        for temp_file in temp_files:
            os.unlink(temp_file)
        os.unlink(output_temp.name)

        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=False
        )

    except Exception as e:
        # 清理临时文件
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        if 'output_temp' in locals() and os.path.exists(output_temp.name):
            os.unlink(output_temp.name)
        return jsonify({'error': str(e)}), 500

@app.route('/rotate', methods=['POST'])
def rotate_pdf():
    if 'file' not in request.files:
        return jsonify({'error': '没有选择文件'}), 400
    
    file = request.files['file']
    if not file or not file.filename.endswith('.pdf'):
        return jsonify({'error': '无效的PDF文件'}), 400

    try:
        # 获取页面顺序和旋转信息
        page_numbers = request.form.getlist('pageNumbers[]')
        rotations = request.form.getlist('rotations[]')
        
        # 保存上传的文件到临时文件
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        file.save(temp_input.name)
        
        # 创建PDF写入器
        writer = PdfWriter()
        reader = PdfReader(temp_input.name)
        
        # 按照指定的顺序和旋转角度处理页面
        for page_num, rotation in zip(page_numbers, rotations):
            page = reader.pages[int(page_num) - 1]
            page_rotation = int(rotation) % 360
            page[NameObject("/Rotate")] = NumberObject(page_rotation)
            writer.add_page(page)
        
        # 保存处理后的文件
        output_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        with open(output_temp.name, 'wb') as output_file:
            writer.write(output_file)
        
        # 读取处理后的文件并返回
        with open(output_temp.name, 'rb') as f:
            pdf_data = f.read()
        
        # 清理临时文件
        os.unlink(temp_input.name)
        os.unlink(output_temp.name)
        
        return send_file(
            io.BytesIO(pdf_data),
            mimetype='application/pdf',
            as_attachment=False
        )
        
    except Exception as e:
        # 清理临时文件
        if 'temp_input' in locals() and os.path.exists(temp_input.name):
            os.unlink(temp_input.name)
        if 'output_temp' in locals() and os.path.exists(output_temp.name):
            os.unlink(output_temp.name)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000,debug=True) 