from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from routes import rotate_bp, image2pdf_bp
from routes.pdf_rotate import pdf_rotate_bp
from routes.pdf2image import pdf2image_bp
from routes.pdf_watermark import pdf_watermark_bp
from routes.pdf_merge import pdf_merge_bp
from routes.pdf_split import pdf_split
from routes.pdf_count import pdf_count
from routes.pdf2ppt import pdf2ppt
from routes.word2pdf import word2pdf
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
app.register_blueprint(pdf_split)
app.register_blueprint(pdf_count, url_prefix='/pdf_count')
app.register_blueprint(pdf2ppt, url_prefix='/pdf2ppt')
app.register_blueprint(word2pdf, url_prefix='/word2pdf')

# 确保上传目录存在
os.makedirs('uploads', exist_ok=True)
os.makedirs('uploads/pdf', exist_ok=True)
os.makedirs('uploads/pics', exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000,debug=True) 