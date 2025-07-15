import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PyPDF2 import PdfReader, PdfWriter

def add_toc_to_pdf(output_stream, toc_entries):
    # 重置流指针并读取原始PDF
    output_stream.seek(0)
    original_pdf = PdfReader(output_stream)
    
    # 创建目录页
    toc_page = io.BytesIO()
    c = canvas.Canvas(toc_page, pagesize=letter)
    width, height = letter
    
    # 设置样式
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 72, "Table of Contents")
    c.setFont("Helvetica", 12)
    
    # 计算起始位置
    y_position = height - 100
    
    # 添加目录条目（带超链接）
    for entry in toc_entries:
        # 目标页码 = 原始页码 + 1（因为添加了目录页）
        target_page = entry['page'] + 1
        title = entry['title']
        
        # 创建带页码的文本
        text = f"{title} ...... {target_page}"
        text_width = c.stringWidth(text, "Helvetica", 12)
        
        # 修复：移除 relative 参数
        c.linkAbsolute(
            text, 
            f"page{target_page}",  # 目标名称
            Rect=(72, y_position - 5, 72 + text_width, y_position + 10)
        )
        
        c.drawString(72, y_position, text)
        y_position -= 20
    
    c.save()
    
    # 合并目录页和原始PDF
    toc_page.seek(0)
    toc_pdf = PdfReader(toc_page)
    
    writer = PdfWriter()
    
    # 添加目录页
    writer.add_page(toc_pdf.pages[0])
    
    # 添加原始页面（页码偏移+1）
    for i, page in enumerate(original_pdf.pages):
        # 添加命名目标以便超链接工作
        if i == 0:
            # 第一页的特殊处理（添加书签）
            writer.add_page(page)
            writer.add_named_destination(f"page{entry['page'] + 1}", len(writer.pages) - 1)
        else:
            writer.add_page(page)
    
    # 将结果保存到新的BytesIO流
    new_pdf_stream = io.BytesIO()
    writer.write(new_pdf_stream)
    new_pdf_stream.seek(0)
    
    return new_pdf_stream

# 使用示例
if __name__ == "__main__":
    # 创建示例PDF
    sample_pdf = io.BytesIO()
    c = canvas.Canvas(sample_pdf, pagesize=letter)
    for i in range(1, 20):
        c.drawString(100, 700, f"Page {i} Content")
        c.showPage()
    c.save()
    sample_pdf.seek(0)
    
    # 目录条目数据
    toc_entries = [
        {'title': 'Section 1', 'page': 1, 'bookmark': 'toc_title_1'},
        {'title': 'Section 2', 'page': 14, 'bookmark': 'toc_title_2'}
    ]
    
    # 处理PDF
    new_pdf_stream = add_toc_to_pdf(sample_pdf, toc_entries)
    
    # 保存结果到文件
    with open("output_with_toc.pdf", "wb") as f:
        f.write(new_pdf_stream.getbuffer())
    
    print("PDF with TOC created successfully!")