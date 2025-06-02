from flask import Blueprint, render_template, request, jsonify, send_file, current_app, session
import os
import tempfile
import shutil
import logging
from werkzeug.utils import secure_filename
import uuid
import PyPDF2
import re

pdf_rotate_bp = Blueprint('pdf_rotate', __name__, url_prefix='/pdf')

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {'.pdf'}

def allowed_file(filename):
    return os.path.splitext(filename.lower())[1] in ALLOWED_EXTENSIONS

def sanitize_filename(filename):
    """清理文件名，只保留字母、数字、下划线和点"""
    # 移除所有非字母数字字符，但保留点和下划线
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)
    # 确保文件名以.pdf结尾
    if not filename.lower().endswith('.pdf'):
        filename += '.pdf'
    return filename

def get_batch_id():
    """获取或创建批次ID"""
    if 'batch_id' not in session:
        session['batch_id'] = str(uuid.uuid4())
    return session['batch_id']

def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        os.path.join(current_app.root_path, 'uploads'),
        os.path.join(current_app.root_path, 'uploads', 'pdf')
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

@pdf_rotate_bp.route('/')
def rotate():
    """PDF旋转页面"""
    try:
        # 创建新的批次ID
        session['batch_id'] = str(uuid.uuid4())
        # 确保目录存在
        ensure_directories()
        return render_template('rotate.html')
    except Exception as e:
        logger.error(f"初始化页面失败: {str(e)}")
        return jsonify({'error': '初始化失败'}), 500

@pdf_rotate_bp.route('/upload', methods=['POST'])
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
        
        if not allowed_file(file.filename):
            logger.error(f"不支持的文件类型: {file.filename}")
            return jsonify({'error': '只支持PDF文件'}), 400
        
        # 确保目录存在
        ensure_directories()
        
        # 生成唯一文件名
        original_filename = secure_filename(file.filename)
        sanitized_filename = sanitize_filename(original_filename)
        batch_id = get_batch_id()
        unique_filename = f"{batch_id}_{sanitized_filename}"
        pdf_folder = os.path.join(current_app.root_path, 'uploads', 'pdf')
        filepath = os.path.join(pdf_folder, unique_filename)
        
        logger.info(f"保存PDF文件到: {filepath}")
        file.save(filepath)
        
        # 验证文件是否成功保存
        if not os.path.exists(filepath):
            raise Exception("文件保存失败")
            
        return jsonify({
            'success': True,
            'filename': unique_filename,
            'batch_id': batch_id
        })
        
    except Exception as e:
        logger.error(f"处理PDF上传时出错: {str(e)}")
        if 'filepath' in locals() and os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        return jsonify({'error': f'PDF上传失败: {str(e)}'}), 500

@pdf_rotate_bp.route('/rotate', methods=['POST'])
def rotate_pdf():
    """处理PDF旋转请求"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        filename = data.get('filename')
        angle = int(data.get('angle', 90))
        pages = data.get('pages', [])  # 获取要旋转的页面列表
        
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
                
                # 遍历所有页面
                for i in range(len(reader.pages)):
                    page = reader.pages[i]
                    # 如果页面在选中列表中，则旋转
                    if i + 1 in pages:  # 页面索引从0开始，但页面号从1开始
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

@pdf_rotate_bp.route('/delete', methods=['POST'])
def delete_pages():
    """处理PDF页面删除请求"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        filename = data.get('filename')
        pages = data.get('pages', [])  # 获取要删除的页面列表
        
        if not filename:
            return jsonify({'error': '未指定文件名'}), 400
            
        if not pages:
            return jsonify({'error': '未指定要删除的页面'}), 400
            
        # 移除可能的时间戳参数
        filename = filename.split('?')[0]
        pdf_folder = os.path.join(current_app.root_path, 'uploads', 'pdf')
        input_path = os.path.join(pdf_folder, filename)
        
        if not os.path.exists(input_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 创建临时文件
        temp_dir = tempfile.mkdtemp()
        output_filename = f"deleted_{filename}"
        output_path = os.path.join(pdf_folder, output_filename)
        
        try:
            # 读取PDF文件
            with open(input_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                writer = PyPDF2.PdfWriter()
                
                # 遍历所有页面，跳过要删除的页面
                for i in range(len(reader.pages)):
                    if i + 1 not in pages:  # 页面索引从0开始，但页面号从1开始
                        writer.add_page(reader.pages[i])
                
                # 保存删除后的文件
                with open(output_path, 'wb') as output_file:
                    writer.write(output_file)
            
            return jsonify({
                'success': True,
                'filename': output_filename
            })
            
        except Exception as e:
            logger.error(f"删除PDF页面失败: {str(e)}")
            return jsonify({'error': f'删除页面失败: {str(e)}'}), 500
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                
    except Exception as e:
        logger.error(f"处理PDF删除请求失败: {str(e)}")
        return jsonify({'error': f'处理请求失败: {str(e)}'}), 500

@pdf_rotate_bp.route('/file/<filename>')
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

@pdf_rotate_bp.route('/save', methods=['POST'])
def save_changes():
    """处理PDF保存请求"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400
            
        filename = data.get('filename')
        if not filename:
            return jsonify({'error': '未指定文件名'}), 400
            
        # 移除可能的时间戳参数
        filename = filename.split('?')[0]
        pdf_folder = os.path.join(current_app.root_path, 'uploads', 'pdf')
        input_path = os.path.join(pdf_folder, filename)
        
        if not os.path.exists(input_path):
            return jsonify({'error': '文件不存在'}), 404
            
        # 创建新的文件名
        output_filename = f"final_{filename}"
        output_path = os.path.join(pdf_folder, output_filename)
        
        try:
            # 复制文件
            shutil.copy2(input_path, output_path)
            
            return jsonify({
                'success': True,
                'filename': output_filename
            })
            
        except Exception as e:
            logger.error(f"保存PDF失败: {str(e)}")
            return jsonify({'error': f'保存失败: {str(e)}'}), 500
                
    except Exception as e:
        logger.error(f"处理保存请求失败: {str(e)}")
        return jsonify({'error': f'处理请求失败: {str(e)}'}), 500 