from flask import Blueprint, request, send_file, render_template
import os
import tempfile
import zipfile
from docx import Document
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
from werkzeug.utils import secure_filename
import io

word2pdf = Blueprint('word2pdf', __name__)

# 注册中文字体
FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'fonts')

def register_chinese_font():
    """注册中文字体"""
    try:
        # 获取static/fonts目录下的所有字体文件
        font_files = [f for f in os.listdir(FONT_PATH) if f.endswith(('.ttf', '.ttc', '.otf'))]
        if not font_files:
            print("未找到字体文件")
            return False
            
        # 使用第一个找到的字体文件
        font_file = font_files[0]
        font_path = os.path.join(FONT_PATH, font_file)
        print(f"使用字体文件: {font_path}")
        
        # 注册字体
        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
        return True
    except Exception as e:
        print(f"注册字体失败: {str(e)}")
        return False

@word2pdf.route('/')
def word2pdf_page():
    return render_template('word2pdf.html')

def convert_docx_to_pdf(docx_path, pdf_path):
    """将.docx文档转换为PDF"""
    try:
        # 注册中文字体
        if not register_chinese_font():
            return False

        # 读取Word文档
        doc = Document(docx_path)
        
        # 创建PDF文档
        pdf = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # 创建支持中文的样式
        styles = getSampleStyleSheet()
        style = ParagraphStyle(
            'ChineseStyle',
            parent=styles['Normal'],
            fontName='ChineseFont',
            fontSize=12,
            leading=14
        )
        
        # 准备内容
        story = []
        
        # 处理每个段落
        for para in doc.paragraphs:
            if para.text.strip():  # 只处理非空段落
                p = Paragraph(para.text, style)
                story.append(p)
                story.append(Spacer(1, 12))
        
        # 处理表格
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text for cell in row.cells)
                if row_text.strip():
                    p = Paragraph(row_text, style)
                    story.append(p)
                    story.append(Spacer(1, 12))
        
        # 生成PDF
        pdf.build(story)
        return True
    except Exception as e:
        print(f"转换错误: {str(e)}")
        return False

@word2pdf.route('', methods=['POST'])
def convert_word_to_pdf():
    if 'wordFiles' not in request.files:
        return {'error': '未找到文件'}, 400
    
    files = request.files.getlist('wordFiles')
    if not files or files[0].filename == '':
        return {'error': '未选择文件'}, 400

    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建ZIP文件
            zip_path = os.path.join(temp_dir, 'converted_pdfs.zip')
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for file in files:
                    if not file.filename.lower().endswith('.docx'):
                        continue

                    # 保存上传的Word文件
                    word_path = os.path.join(temp_dir, secure_filename(file.filename))
                    file.save(word_path)

                    # 设置输出PDF路径
                    base_name = os.path.splitext(secure_filename(file.filename))[0]
                    pdf_filename = f"{base_name}.pdf"
                    pdf_path = os.path.join(temp_dir, pdf_filename)

                    # 转换文档
                    if convert_docx_to_pdf(word_path, pdf_path):
                        # 添加到ZIP文件
                        zipf.write(pdf_path, pdf_filename)
                    else:
                        return {'error': f'转换文件 {file.filename} 失败'}, 500
                    
                    # 删除临时文件
                    os.remove(word_path)
                    os.remove(pdf_path)

            # 返回ZIP文件
            return send_file(
                zip_path,
                as_attachment=True,
                download_name='converted_pdfs.zip',
                mimetype='application/zip'
            )

    except Exception as e:
        return {'error': f'转换失败: {str(e)}'}, 500 