"""Web interface for PDF to TXT conversion."""

from flask import Flask, request, send_file, render_template_string
import tempfile
import os
from pdf_to_txt import smart_extract, fix_hard_line_breaks

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PDF 转 TXT</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, "Microsoft YaHei", sans-serif; background: #f0f2f5; min-height: 100vh; display: flex; align-items: center; justify-content: center; }
  .container { background: #fff; border-radius: 12px; box-shadow: 0 4px 24px rgba(0,0,0,.1); padding: 48px; max-width: 500px; width: 90%; text-align: center; }
  h1 { font-size: 28px; margin-bottom: 8px; color: #1a1a1a; }
  .subtitle { color: #888; margin-bottom: 32px; font-size: 14px; }
  .upload-area { border: 2px dashed #d0d0d0; border-radius: 8px; padding: 48px 24px; cursor: pointer; transition: .2s; position: relative; }
  .upload-area:hover, .upload-area.dragover { border-color: #4a90d9; background: #f7faff; }
  .upload-area input { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
  .upload-icon { font-size: 48px; color: #999; }
  .upload-text { margin-top: 12px; color: #666; font-size: 15px; }
  .file-name { margin-top: 16px; font-size: 14px; color: #4a90d9; word-break: break-all; display: none; }
  .btn { margin-top: 24px; background: #4a90d9; color: #fff; border: none; border-radius: 8px; padding: 14px 48px; font-size: 16px; cursor: pointer; transition: .2s; }
  .btn:hover { background: #3a7bc8; }
  .btn:disabled { background: #ccc; cursor: not-allowed; }
  .msg { margin-top: 16px; font-size: 14px; }
  .msg.error { color: #e74c3c; }
  .spinner { display: none; margin: 16px auto 0; width: 32px; height: 32px; border: 3px solid #e0e0e0; border-top-color: #4a90d9; border-radius: 50%; animation: spin .8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="container">
  <h1>PDF 转 TXT</h1>
  <p class="subtitle">上传 PDF 文件，自动修复中文硬换行，返回 TXT</p>
  <form id="form" action="/convert" method="post" enctype="multipart/form-data">
    <div class="upload-area" id="dropZone">
      <input type="file" name="file" id="fileInput" accept=".pdf">
      <div class="upload-icon">&#128196;</div>
      <div class="upload-text">点击或拖拽 PDF 文件到此处</div>
    </div>
    <div class="file-name" id="fileName"></div>
    <button class="btn" type="submit" id="btn" disabled>开始转换</button>
    <div class="spinner" id="spinner"></div>
    <div class="msg" id="msg"></div>
  </form>
</div>
<script>
  const fileInput = document.getElementById('fileInput');
  const fileName = document.getElementById('fileName');
  const btn = document.getElementById('btn');
  const form = document.getElementById('form');
  const spinner = document.getElementById('spinner');
  const msg = document.getElementById('msg');
  const dropZone = document.getElementById('dropZone');

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length) {
      fileName.textContent = fileInput.files[0].name;
      fileName.style.display = 'block';
      btn.disabled = false;
      msg.textContent = '';
    }
  });

  ['dragover','dragenter'].forEach(e => dropZone.addEventListener(e, ev => { ev.preventDefault(); dropZone.classList.add('dragover'); }));
  ['dragleave','drop'].forEach(e => dropZone.addEventListener(e, () => dropZone.classList.remove('dragover')));

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!fileInput.files.length) return;
    btn.disabled = true;
    spinner.style.display = 'block';
    msg.textContent = '';
    msg.className = 'msg';

    const data = new FormData();
    data.append('file', fileInput.files[0]);

    try {
      const resp = await fetch('/convert', { method: 'POST', body: data });
      if (!resp.ok) {
        const err = await resp.text();
        throw new Error(err || '转换失败');
      }
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      const baseName = fileInput.files[0].name.replace(/\.pdf$/i, '');
      a.href = url;
      a.download = baseName + '.txt';
      a.click();
      URL.revokeObjectURL(url);
      msg.textContent = '转换完成，已开始下载';
    } catch (err) {
      msg.textContent = err.message;
      msg.className = 'msg error';
    } finally {
      btn.disabled = false;
      spinner.style.display = 'none';
    }
  });
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return "未上传文件", 400
    file = request.files["file"]
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        return "请上传 PDF 文件", 400

    tmp_pdf = None
    tmp_txt = None
    try:
        tmp_pdf = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        file.save(tmp_pdf.name)
        tmp_pdf.close()

        raw = smart_extract(tmp_pdf.name)
        result = fix_hard_line_breaks(raw)

        tmp_txt = tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8")
        tmp_txt.write(result)
        tmp_txt.close()

        base_name = os.path.splitext(file.filename)[0] + ".txt"
        return send_file(tmp_txt.name, as_attachment=True, download_name=base_name, mimetype="text/plain; charset=utf-8")
    except Exception as e:
        return f"转换出错: {e}", 500
    finally:
        if tmp_pdf and os.path.exists(tmp_pdf.name):
            os.unlink(tmp_pdf.name)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
