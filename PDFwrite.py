import fitz
from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage

def pdf_copy(input_pdf_path, output_pdf_path):
    doc = fitz.open(input_pdf_path)

    # 遍历每一页
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # 提取页面中的所有文本块
        text_instances = page.get_text("blocks")

        # 删除找到的所有文本块
        for inst in text_instances:
            if inst[6] == 0:  # 如果这个块是文本块
                rect = fitz.Rect(inst[:4])
                page.add_redact_annot(rect)  # 添加遮盖注释
        page.apply_redactions()  # 应用遮盖

    # 将修改后的PDF保存到新的文件中
    doc.save(output_pdf_path)
    return output_pdf_path

def read_pdf(file_path):
    document = fitz.open(file_path)
    blocks = []
    for page_num in range(document.page_count):
        page = document.load_page(page_num)
        text_dict = page.get_text("dict")

        for block in text_dict.get("blocks", []):
            # 检查 block 是否包含 'lines' 键
            if "lines" in block:
                for line in block["lines"]:
                    dir = line['dir']
                    for span in line.get("spans", []):
                        blocks.append({
                            "page": page_num,
                            "size": span.get("size"),
                            "bbox": span.get("bbox"),
                            "text": span.get("text", ""),
                            "dir": line['dir']
                        })
            else:
                continue

    return blocks

def should_merge(previous_block,current_block):
    next_text = current_block['text']
    current_text = previous_block['text']
    t = min(abs((current_block['bbox'][1]-previous_block['bbox'][3])),(abs(current_block['bbox'][3]-previous_block['bbox'][3])),
    (abs(current_block['bbox'][1]-previous_block['bbox'][1])),(abs(current_block['bbox'][3]-previous_block['bbox'][1])))

    return ((next_text[0].islower()) or (next_text[0] in ' (,-，–:：)[]{}') or (current_text[-1] in '–[')) and \
            (current_block['dir'] == previous_block['dir']) and (t<10)


# 合并块的函数
def merge_blocks(blocks):
    merged_blocks = []
    previous_block = blocks[0]

    for i in range(1, len(blocks)):
        current_block = blocks[i]

        if should_merge(previous_block, current_block):
            # 合并text字段
            previous_block['text'] += ' ' + current_block['text']
            # 合并bbox（取两者的最小/最大值）
            previous_block['bbox'] = (
                min(previous_block['bbox'][0], current_block['bbox'][0]),
                min(previous_block['bbox'][1], current_block['bbox'][1]),
                max(previous_block['bbox'][2], current_block['bbox'][2]),
                max(previous_block['bbox'][3], current_block['bbox'][3]),
            )
        else:
            # 如果不合并，则将previous_block添加到结果中
            merged_blocks.append(previous_block)
            previous_block = current_block

    # 将最后一个块添加到结果中
    merged_blocks.append(previous_block)
    return merged_blocks

def spark_translate(r):
    SPARKAI_URL = 'wss://spark-api.xf-yun.com/v4.0/chat'
    SPARKAI_APP_ID = '*****'
    SPARKAI_API_SECRET = '******'
    SPARKAI_API_KEY = '******'
    SPARKAI_DOMAIN = '4.0Ultra'
    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )

    messages = [ChatMessage(
        role="user",
        content=f'''
        请你用中文翻译一下论文里面的一部分,要使用专业术语。\
        如果没有充足的内容也要尽量翻译,你只需要返回翻译的结果，不要输出其他内容\
        遇到专属名次的话提供专属名词的翻译，而不是解释这个词\
        如果是单个字母或者其他无法翻译的，输出原文。\
        你要翻译的内容：："""{r}"""'\
        如果没法翻译，输出：'e_RRor'\
        '''
    )]
    handler = ChunkPrintHandler()
    a = spark.generate([messages], callbacks=[handler])
    a_translate = a.generations[0][0].text
    return a_translate