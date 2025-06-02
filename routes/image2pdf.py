from flask import Blueprint, render_template, request, jsonify, send_file, current_app, session
import os
from PIL import Image
import tempfile
import shutil
import logging
from werkzeug.utils import secure_filename
import time
import uuid
import PyPDF2
import io

image2pdf_bp = Blueprint('image2pdf', __name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
ALLOWED_PDF_EXTENSIONS = {'.pdf'}

def allowed_file(filename):
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXTENSIONS

def allowed_pdf_file(filename):
    return os.path.splitext(filename.lower())[1] in ALLOWED_PDF_EXTENSIONS

def get_batch_id():
    """获取或创建批次ID"""
    if 'batch_id' not in session:
        session['batch_id'] = str(uuid.uuid4())
    return session['batch_id']

def get_unique_filename(original_filename, index):
    """生成唯一的文件名，包含批次ID和序号"""
    ext = os.path.splitext(original_filename)[1].lower()
    batch_id = get_batch_id()
    return f"{batch_id}_{index}{ext}"

def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        os.path.join(current_app.root_path, 'uploads'),
        os.path.join(current_app.root_path, 'uploads', 'pics'),
        os.path.join(current_app.root_path, 'uploads', 'pdf')
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

@image2pdf_bp.route('/image2pdf')
def image2pdf():
    try:
        # 创建新的批次ID
        session['batch_id'] = str(uuid.uuid4())
        # 确保目录存在
        ensure_directories()
        return render_template('image2pdf.html')
    except Exception as e:
        logger.error(f"初始化页面失败: {str(e)}")
        return jsonify({'error': '初始化失败'}), 500

@image2pdf_bp.route('/upload_image', methods=['POST'])
def upload_image():
    logger.info("开始处理图片上传请求")
    
    try:
        if 'file' not in request.files:
            logger.error("请求中没有文件")
            return jsonify({'error': '没有文件被上传'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("没有选择文件")
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_file(file.filename):
            logger.error(f"不支持的文件类型: {file.filename}")
            return jsonify({'error': '不支持的文件类型'}), 400
        
        # 确保目录存在
        ensure_directories()
        
        # 获取当前批次的文件数量
        batch_id = get_batch_id()
        upload_folder = os.path.join(current_app.root_path, 'uploads', 'pics')
        existing_files = [f for f in os.listdir(upload_folder) if f.startswith(batch_id)]
        next_index = len(existing_files) + 1
        
        # 生成唯一文件名
        filename = get_unique_filename(file.filename, next_index)
        filepath = os.path.join(upload_folder, filename)
        
        logger.info(f"保存文件到: {filepath}")
        file.save(filepath)
        
        # 验证图片
        with Image.open(filepath) as img:
            width, height = img.size
            logger.info(f"图片尺寸: {width}x{height}")
            
            return jsonify({
                'success': True,
                'filename': filename,
                'width': width,
                'height': height,
                'batch_id': batch_id
            })
    except Exception as e:
        logger.error(f"处理图片时出错: {str(e)}")
        return jsonify({'error': f'图片处理失败: {str(e)}'}), 500

@image2pdf_bp.route('/get_batch_images', methods=['GET'])
def get_batch_images():
    """获取当前批次的所有图片"""
    try:
        batch_id = get_batch_id()
        upload_folder = os.path.join(current_app.root_path, 'uploads', 'pics')
        
        # 获取当前批次的所有图片
        batch_files = [f for f in os.listdir(upload_folder) 
                      if f.startswith(batch_id) and f.endswith(tuple(ALLOWED_EXTENSIONS))]
        
        # 按序号排序
        batch_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
        
        return jsonify({
            'success': True,
            'filenames': batch_files,
            'batch_id': batch_id
        })
    except Exception as e:
        logger.error(f"获取批次图片失败: {str(e)}")
        return jsonify({'error': f'获取图片失败: {str(e)}'}), 500

@image2pdf_bp.route('/process_images', methods=['POST'])
def process_images():
    """处理图片操作（旋转、删除）"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        operation = data.get('operation')
        selected_images = data.get('selected_images', [])
        batch_id = get_batch_id()
        
        if not selected_images:
            return jsonify({'error': '没有选择图片'}), 400
        
        upload_folder = os.path.join(current_app.root_path, 'uploads', 'pics')
        
        # 获取当前批次的所有图片
        batch_files = [f for f in os.listdir(upload_folder) 
                      if f.startswith(batch_id) and f.endswith(tuple(ALLOWED_EXTENSIONS))]
        batch_files.sort(key=lambda x: int(x.split('_')[1].split('.')[0]))
        
        if operation == 'rotate':
            angle = int(data.get('angle', 90))
            logger.info(f"开始旋转图片，选中图片: {selected_images}, 角度: {angle}")
            
            # 处理选中的图片
            for img_name in selected_images:
                # 移除可能的时间戳参数
                img_name = img_name.split('?')[0]
                img_path = os.path.join(upload_folder, img_name)
                if not os.path.exists(img_path):
                    logger.error(f"图片不存在: {img_path}")
                    continue
                    
                try:
                    # 检查文件扩展名
                    ext = os.path.splitext(img_name)[1].lower()
                    if ext not in ALLOWED_EXTENSIONS:
                        logger.error(f"不支持的文件类型: {ext}")
                        continue
                        
                    with Image.open(img_path) as img:
                        # 如果是RGBA模式，转换为RGB
                        if img.mode == 'RGBA':
                            img = img.convert('RGB')
                        # 创建旋转后的图片
                        rotated_img = img.rotate(angle, expand=True)
                        # 保存旋转后的图片
                        rotated_img.save(img_path, format=img.format, quality=95)
                        logger.info(f"成功旋转图片: {img_name}, 角度: {angle}")
                except Exception as e:
                    logger.error(f"旋转图片 {img_name} 失败: {str(e)}")
                    continue
            
            # 返回当前批次的所有图片
            return jsonify({
                'success': True,
                'filenames': batch_files,
                'batch_id': batch_id
            })
                
        elif operation == 'delete':
            logger.info(f"开始删除图片，选中图片: {selected_images}")
            
            # 只删除选中的图片
            for img_name in selected_images:
                # 移除可能的时间戳参数
                img_name = img_name.split('?')[0]
                img_path = os.path.join(upload_folder, img_name)
                if os.path.exists(img_path):
                    try:
                        os.remove(img_path)
                        logger.info(f"成功删除图片: {img_name}")
                    except Exception as e:
                        logger.error(f"删除图片 {img_name} 失败: {str(e)}")
            
            # 获取剩余的文件
            remaining_files = [f for f in batch_files if f not in selected_images]
            
            return jsonify({
                'success': True,
                'filenames': remaining_files,
                'batch_id': batch_id
            })
        else:
            return jsonify({'error': '不支持的操作'}), 400
        
    except Exception as e:
        logger.error(f"处理图片失败: {str(e)}")
        return jsonify({'error': f'处理图片失败: {str(e)}'}), 500

@image2pdf_bp.route('/convert_to_pdf', methods=['POST'])
def convert_to_pdf():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        selected_images = data.get('selected_images', [])
        batch_id = get_batch_id()
        
        if not selected_images:
            logger.error("没有选择图片")
            return jsonify({'error': '没有可用的图片'}), 400
        
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        temp_output = os.path.join(temp_dir, 'output.pdf')
        upload_folder = os.path.join(current_app.root_path, 'uploads', 'pics')
        pdf_folder = os.path.join(current_app.root_path, 'uploads', 'pdf')
        
        logger.info(f"选中的图片: {selected_images}")
        
        # 获取所有选中的图片
        images = []
        for img_name in selected_images:
            img_path = os.path.join(upload_folder, img_name)
            logger.info(f"处理图片: {img_path}")
            img = Image.open(img_path)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            images.append(img)
        
        if not images:
            raise Exception("没有有效的图片")
        
        # 保存为PDF
        logger.info(f"保存PDF到: {temp_output}")
        images[0].save(
            temp_output,
            save_all=True,
            append_images=images[1:]
        )
        
        # 生成唯一的输出文件名
        output_filename = f"{batch_id}_converted.pdf"
        output_path = os.path.join(pdf_folder, output_filename)
        
        # 移动临时文件到PDF目录
        shutil.move(temp_output, output_path)
        
        # 返回成功响应
        return jsonify({
            'success': True,
            'filename': output_filename
        })
    
    except Exception as e:
        logger.error(f"PDF转换失败: {str(e)}")
        return jsonify({'error': f'PDF转换失败: {str(e)}'}), 500
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

@image2pdf_bp.route('/download/<filename>')
def download_file(filename):
    """提供PDF文件下载"""
    try:
        pdf_folder = os.path.join(current_app.root_path, 'uploads', 'pdf')
        return send_file(
            os.path.join(pdf_folder, filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        logger.error(f"下载文件失败: {str(e)}")
        return jsonify({'error': '文件不存在'}), 404

@image2pdf_bp.route('/uploads/pics/<filename>')
def serve_image(filename):
    """提供上传的图片文件"""
    try:
        upload_folder = os.path.join(current_app.root_path, 'uploads', 'pics')
        return send_file(os.path.join(upload_folder, filename))
    except Exception as e:
        logger.error(f"提供图片文件时出错: {str(e)}")
        return jsonify({'error': '文件不存在'}), 404

@image2pdf_bp.route('/rotate')
def rotate():
    """PDF旋转页面"""
    try:
        # 创建新的批次ID
        session['batch_id'] = str(uuid.uuid4())
        # 确保目录存在
        ensure_directories()
        return render_template('pdf_rotate.html')
    except Exception as e:
        logger.error(f"初始化页面失败: {str(e)}")
        return jsonify({'error': '初始化失败'}), 500

@image2pdf_bp.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    """处理PDF文件上传"""
    logger.info("开始处理PDF上传请求")
    
    try:
        if 'file' not in request.files:
            logger.error("请求中没有文件")
            return jsonify({'error': '没有文件被上传'}), 400
        
        file = request.files['file']
        if file.filename == '':
            logger.error("没有选择文件")
            return jsonify({'error': '没有选择文件'}), 400
        
        if not allowed_pdf_file(file.filename):
            logger.error(f"不支持的文件类型: {file.filename}")
            return jsonify({'error': '只支持PDF文件'}), 400
        
        # 确保目录存在
        ensure_directories()
        
        # 生成唯一文件名
        filename = secure_filename(file.filename)
        batch_id = get_batch_id()
        unique_filename = f"{batch_id}_{filename}"
        pdf_folder = os.path.join(current_app.root_path, 'uploads', 'pdf')
        filepath = os.path.join(pdf_folder, unique_filename)
        
        logger.info(f"保存PDF文件到: {filepath}")
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'batch_id': batch_id
        })
        
    except Exception as e:
        logger.error(f"处理PDF上传时出错: {str(e)}")
        return jsonify({'error': f'PDF上传失败: {str(e)}'}), 500

@image2pdf_bp.route('/rotate_pdf', methods=['POST'])
def rotate_pdf():
    """处理PDF旋转请求"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        filename = data.get('filename')
        angle = int(data.get('angle', 90))
        
        if not filename:
            return jsonify({'error': '未指定文件名'}), 400
            
        # 移除可能的时间戳参数
        filename = filename.split('?')[0]
        pdf_folder = os.path.join(current_app.root_path, 'uploads', 'pdf')
        input_path = os.path.join(pdf_folder, filename)
        
        if not os.path.exists(input_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 创建临时文件
        temp_dir = tempfile.mkdtemp()
        output_filename = f"rotated_{filename}"
        output_path = os.path.join(pdf_folder, output_filename)
        
        try:
            # 读取PDF文件
            with open(input_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                writer = PyPDF2.PdfWriter()
                
                # 旋转每一页
                for page in reader.pages:
                    page.rotate(angle)
                    writer.add_page(page)
                
                # 保存旋转后的文件
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
            
            return jsonify({
                'success': True,
                'filename': output_filename
            })
            
        except Exception as e:
            logger.error(f"旋转PDF失败: {str(e)}")
            return jsonify({'error': f'PDF旋转失败: {str(e)}'}), 500
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        logger.error(f"处理PDF旋转请求失败: {str(e)}")
        return jsonify({'error': f'处理请求失败: {str(e)}'}), 500

@image2pdf_bp.route('/uploads/pdf/<filename>')
def serve_pdf(filename):
    """提供PDF文件"""
    try:
        pdf_folder = os.path.join(current_app.root_path, 'uploads', 'pdf')
        return send_file(
            os.path.join(pdf_folder, filename),
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"提供PDF文件时出错: {str(e)}")
        return jsonify({'error': '文件不存在'}), 404 