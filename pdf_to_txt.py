"""PDF to TXT converter with Chinese hard line-break fixing and OCR fallback."""

import argparse
import re
import pdfplumber


# 中文句末标点（遇到这些结尾保留换行，视为段落结束）
SENTENCE_END_PUNCTUATION = set("。！？；：…""）》】」』!?;:")

# 每页平均少于此字符数时，判定为扫描版，启用 OCR
OCR_THRESHOLD = 10


def extract_text(pdf_path: str) -> str:
    """用 pdfplumber 逐页提取文本。"""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
    return "\n".join(pages_text)


def extract_text_ocr(pdf_path: str) -> str:
    """OCR 回退：用 PyMuPDF 渲染页面，再用 RapidOCR 识别文字。"""
    import fitz  # PyMuPDF
    from rapidocr_onnxruntime import RapidOCR

    ocr = RapidOCR()
    pages_text = []
    doc = fitz.open(pdf_path)
    total = len(doc)
    for i, page in enumerate(doc):
        print(f"\rOCR 识别中... {i + 1}/{total}", end="", flush=True)
        pix = page.get_pixmap(dpi=300)
        img_bytes = pix.tobytes("png")
        result, _ = ocr(img_bytes)
        if result:
            lines = [line[1] for line in result]
            pages_text.append("\n".join(lines))
    doc.close()
    print()  # 换行
    return "\n".join(pages_text)


def smart_extract(pdf_path: str) -> str:
    """先尝试文字提取，若为扫描版则自动切换 OCR。"""
    with pdfplumber.open(pdf_path) as pdf:
        num_pages = len(pdf.pages)

    raw = extract_text(pdf_path)
    avg_chars = len(raw.strip()) / max(num_pages, 1)

    if avg_chars >= OCR_THRESHOLD:
        return raw

    print(f"检测到扫描版 PDF（{num_pages} 页，平均 {avg_chars:.0f} 字符/页），启用 OCR...")
    return extract_text_ocr(pdf_path)


def fix_hard_line_breaks(raw_text: str) -> str:
    """修复中文 PDF 中常见的硬换行问题。

    规则：
    - 行尾是句末标点 → 保留换行（段落边界）
    - 行尾不是句末标点 → 去掉换行，与下一行拼接
    """
    lines = raw_text.splitlines()
    merged: list[str] = []
    buffer = ""

    for line in lines:
        stripped = line.strip()

        # 跳过空行：如果 buffer 有内容先落盘，再保留一个空行作为段落间距
        if not stripped:
            if buffer:
                merged.append(buffer)
                buffer = ""
            # 避免连续空行
            if merged and merged[-1] != "":
                merged.append("")
            continue

        if buffer:
            # 拼接到 buffer（去掉行间多余空格）
            buffer += stripped
        else:
            buffer = stripped

        # 判断当前行尾字符
        if buffer and buffer[-1] in SENTENCE_END_PUNCTUATION:
            merged.append(buffer)
            buffer = ""

    # 处理最后残留的 buffer
    if buffer:
        merged.append(buffer)

    # 去掉首尾空行
    text = "\n".join(merged).strip()
    # 压缩连续空行为单个空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def convert(pdf_path: str, txt_path: str) -> None:
    raw = smart_extract(pdf_path)
    result = fix_hard_line_breaks(raw)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"Done: {txt_path}  ({len(result)} chars)")


def main():
    parser = argparse.ArgumentParser(description="Convert PDF to TXT (Chinese line-break fix)")
    parser.add_argument("input", help="Input PDF file path")
    parser.add_argument("output", help="Output TXT file path")
    args = parser.parse_args()
    convert(args.input, args.output)


if __name__ == "__main__":
    main()
