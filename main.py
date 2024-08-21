from PDFwrite import *
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io
import fitz
import re

input_pdf = "/Users/niufan/Desktop/2406.08426v3（拖移项目）.pdf"
output_pdf = "output1.pdf"
blocks = read_pdf(input_pdf)
pdf_copy(input_pdf, output_pdf)
merged_blocks = merge_blocks(blocks)


# 注册中文字体
pdfmetrics.registerFont(TTFont('HeitiSC', '/System/Library/Fonts/STHeiti Medium.ttc'))  # macOS 系统字体路径

t = merged_blocks

for block in t:
    # 读取现有的PDF文件
    existing_pdf_path = "output1.pdf"
    document = fitz.open(existing_pdf_path)
    reader = PdfReader(existing_pdf_path)
    page = document.load_page(0)
    width, height = page.rect.width, page.rect.height

    # 创建一个字节流
    packet = io.BytesIO()

    # 使用 reportlab 生成新的 PDF 内容
    can = canvas.Canvas(packet, pagesize=letter)

    # 设置文本
    if bool(re.search(r'\b[a-zA-Z]+\b', block['text'])):
        translate_text = spark_translate(block['text'])
        if 'e_RRor' in translate_text:
            translate_text = spark_translate(block['text'])
            if 'e_RRor' in translate_text:
                block['text'] = block['text']
            else:
                block['text'] = block['text']
        else:
            block['text'] = translate_text
    else:
        block['text'] = block['text']
    text = block['text']

    font_name = "HeitiSC"  # 使用系统字体
    font_size = block['size'] - 1
    can.setFont(font_name, font_size)

    direction = block.get('dir', (1, 0))  # 默认是水平 (1, 0)

    if direction == (1, 0):  # 水平方向
        x_start = block['bbox'][0]
        y_start = height - block['bbox'][1]
        max_width = block['bbox'][2] - block['bbox'][0]  # 最大行宽

        # 手动控制文本换行
        lines = []
        current_line = ""
        for char in text:
            if can.stringWidth(current_line + char, font_name, font_size) <= max_width:
                current_line += char
            else:
                lines.append(current_line)
                current_line = char
        if current_line:
            lines.append(current_line)

        for line in lines:
            can.drawString(x_start, y_start, line)
            y_start -= font_size  # 根据字体大小调整行间距

    elif direction == (0, -1):  # 竖直向下
        x_start = block['bbox'][0]
        y_start = height - block['bbox'][3]
        can.saveState()  # 保存当前状态
        can.translate(x_start, y_start)  # 移动到起始点
        can.rotate(90)  # 旋转90度
        can.drawString(0, 0, text)
        can.restoreState()  # 恢复状态
    elif direction == (-1, 0):  # 水平向左
        can.saveState()  # 保存当前状态
        can.translate(x_start, y_start)  # 移动到起始点
        can.rotate(180)  # 旋转180度
        can.drawString(0, 0, text)
        can.restoreState()  # 恢复状态
    elif direction == (0, 1):  # 竖直向上
        x_start = block['bbox'][0]
        y_start = height - block['bbox'][1]

        can.saveState()  # 保存当前状态
        can.translate(x_start, y_start)  # 移动到起始点
        can.rotate(270)  # 旋转270度
        can.drawString(0, 0, text)
        can.restoreState()  # 恢复状态

    can.save()

    # 将字节流指针移动到开始位置
    packet.seek(0)

    # 读取生成的PDF内容
    overlay_pdf = PdfReader(packet)

    # 使用PyPDF2将生成的内容附加到指定的PDF页面
    writer = PdfWriter()

    i = block['page']  # 设置要添加内容的页码，PyPDF2 页码从 0 开始

    # 处理每一页
    for page_number, page in enumerate(reader.pages):
        if page_number == i:
            page.merge_page(overlay_pdf.pages[0])
        writer.add_page(page)

    # 保存新的PDF文件
    output_pdf_path = "output1.pdf"
    with open(output_pdf_path, "wb") as output_pdf:
        writer.write(output_pdf)

    print(f"PDF已保存到 {output_pdf_path}")
