from flask import Blueprint, render_template, request, send_file, jsonify
from werkzeug.utils import secure_filename
from pdf2image import convert_from_path
import zipfile
import io
import tempfile
import os
from PIL import Image

pdf2image_bp = Blueprint('pdf2image', __name__)

@pdf2image_bp.route('/pdf2image', methods=['GET', 'POST'])
def pdf2image():
    if request.method == 'POST':
        if 'pdfFiles' not in request.files:
            return '没有选择文件', 400
        
        files = request.files.getlist('pdfFiles')
        if not files or files[0].filename == '':
            return '没有选择文件', 400

        image_format = request.form.get('imageFormat', 'png')
        dpi = int(request.form.get('dpi', 300))

        # 创建内存中的 ZIP 文件
        memory_zip = io.BytesIO()
        with zipfile.ZipFile(memory_zip, 'w') as zf:
            total_files = len([f for f in files if f.filename.endswith('.pdf')])
            processed_files = 0
            
            for file in files:
                if file and file.filename.endswith('.pdf'):
                    # 创建临时文件保存 PDF
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                        file.save(temp_pdf.name)
                        
                        try:
                            # 转换 PDF 为图片
                            images = convert_from_path(temp_pdf.name, dpi=dpi)
                            
                            # 获取原始文件名（不含扩展名）
                            base_name = os.path.splitext(secure_filename(file.filename))[0]
                            
                            # 将每个页面保存为图片并添加到 ZIP
                            for i, image in enumerate(images):
                                img_byte_arr = io.BytesIO()
                                # 处理图片格式
                                if image_format.lower() in ['jpg', 'jpeg']:
                                    # 对于 JPG/JPEG 格式，需要将图片转换为 RGB 模式
                                    if image.mode in ('RGBA', 'LA'):
                                        background = Image.new('RGB', image.size, (255, 255, 255))
                                        background.paste(image, mask=image.split()[-1])
                                        image = background
                                    elif image.mode != 'RGB':
                                        image = image.convert('RGB')
                                    image.save(img_byte_arr, format='JPEG', quality=95)
                                else:
                                    image.save(img_byte_arr, format=image_format.upper())
                                
                                img_byte_arr.seek(0)
                                
                                # 在 ZIP 中创建以 PDF 文件名命名的文件夹
                                zip_path = f"{base_name}/page_{i+1}.{image_format}"
                                zf.writestr(zip_path, img_byte_arr.getvalue())
                            
                            processed_files += 1
                            
                        finally:
                            # 清理临时文件
                            os.unlink(temp_pdf.name)

        memory_zip.seek(0)
        return send_file(
            memory_zip,
            mimetype='application/zip',
            as_attachment=True,
            download_name='converted_images.zip'
        )

    return render_template('pdf2image.html') 