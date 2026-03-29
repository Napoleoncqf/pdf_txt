# PDF 转 TXT

将 PDF 文件转换为 TXT 纯文本，自动修复中文 PDF 常见的硬换行问题。支持文字版和扫描版 PDF。

## 功能

- 使用 pdfplumber 逐页提取 PDF 文本
- 自动检测扫描版 PDF，自动切换 OCR 识别（RapidOCR + PyMuPDF）
- 自动识别中文句末标点（。！？；：等），智能合并被硬换行截断的段落
- 支持两种使用方式：命令行 和 Web 界面

## 安装

```bash
pip install -r requirements.txt
```

依赖：
- `pdfplumber` — 文字版 PDF 提取
- `flask` — Web 界面
- `PyMuPDF` — PDF 页面渲染为图片（OCR 用）
- `rapidocr-onnxruntime` — OCR 文字识别（扫描版 PDF 用）

## 使用方式

### 命令行

```bash
python pdf_to_txt.py input.pdf output.txt
```

### Web 界面

```bash
python app.py
```

启动后访问 http://localhost:5000 ，上传 PDF 文件即可在线转换并下载 TXT。

支持拖拽上传。

## 工作原理

1. 先用 pdfplumber 尝试提取文字
2. 如果每页平均字符数 < 10，判定为扫描版，自动启用 OCR
3. OCR 模式：PyMuPDF 将每页渲染为 300dpi 图片，RapidOCR 识别文字
4. 最后智能合并被硬换行截断的中文段落
