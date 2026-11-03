"""知识库（RAG）：把下载/导入的资料切成片段、向量化存 SQLite，提问时语义检索并注入回答。

表：kb_chunks(id, ts, source, text, embedding)  embedding 为 JSON 字符串向量
嵌入模型：models.yaml 的 knowledge.embed_model（默认 bge-m3）；嵌入模型未就绪时自动退回关键词检索。

聊天命令（chat.py，别名 /kb）：
  /知识 add <文件路径>   导入本地 txt/md 文件
  /知识 fetch <网址>     下载网页文字并导入
  /知识 查 <关键词>      检索知识库
  /知识 列表             统计与最近来源
  /知识 删除 <编号>      删除一条片段
  /知识 清空             清空全部知识
"""
import html
import json
import math
import re
import sqlite3
import time
import urllib.request
from pathlib import Path

from langchain_ollama import OllamaEmbeddings

from core import cfg

DB_PATH = Path(__file__).resolve().parent / "knowledge.db"
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def _kcfg():
    return cfg.get("knowledge") or {}


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS kb_chunks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, source TEXT, "
            "text TEXT, embedding TEXT)"
        )


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _embedder():
    model = _kcfg().get("embed_model", "bge-m3")
    try:
        # 注意：本版本 keep_alive 必须是整数（秒）
        return OllamaEmbeddings(model=model, base_url="http://127.0.0.1:11434", keep_alive=1800)
    except Exception:
        return OllamaEmbeddings(model=model, base_url="http://127.0.0.1:11434")


def _chunks(text):
    t = (text or "").strip()
    if not t:
        return []
    size = int(_kcfg().get("chunk_size", CHUNK_SIZE))
    overlap = int(_kcfg().get("chunk_overlap", CHUNK_OVERLAP))
    step = max(1, size - overlap)
    return [t[i:i + size] for i in range(0, len(t), step) if t[i:i + size].strip()]


def ingest_text(source, text):
    """切块并向量化后写入知识库；返回新增片段数。"""
    pieces = _chunks(text)
    if not pieces:
        return 0
    try:
        embs = _embedder().embed_documents(pieces)
    except Exception:
        embs = None
    init_db()
    ts = _now()
    with _conn() as c:
        for i, p in enumerate(pieces):
            emb = json.dumps(embs[i]) if embs else None
            c.execute(
                "INSERT INTO kb_chunks(ts, source, text, embedding) VALUES (?,?,?,?)",
                (ts, source, p, emb),
            )
    return len(pieces)


def read_document_text(path):
    """从 pdf/docx/xlsx/txt/md 提取纯文本；不支持的格式抛 ValueError。"""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError("读取 PDF 需要 pypdf：pip install pypdf") from None
        reader = PdfReader(str(p))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    elif suffix == ".docx":
        try:
            import docx
        except ImportError:
            raise ValueError("读取 Word 需要 python-docx：pip install python-docx") from None
        d = docx.Document(str(p))
        text = "\n".join(par.text for par in d.paragraphs)
    elif suffix in (".xlsx", ".xlsm"):
        try:
            import openpyxl
        except ImportError:
            raise ValueError("读取 Excel 需要 openpyxl：pip install openpyxl") from None
        wb = openpyxl.load_workbook(str(p), read_only=True, data_only=True)
        rows = []
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                rows.append("\t".join("" if c is None else str(c) for c in row))
        text = "\n".join(rows)
    elif suffix in (".txt", ".md", ".markdown"):
        text = p.read_text(encoding="utf-8", errors="replace")
    else:
        raise ValueError(f"暂不支持 {suffix} 格式（支持 pdf/docx/xlsx/txt/md）")
    if not (text and text.strip()):
        raise ValueError("未能从文件中提取到文本（扫描版 PDF 请用图片识别功能）")
    return text


def ingest_file(path):
    """导入本地文件（v1.5.0 起支持 pdf/docx/xlsx/txt/md）。"""
    p = Path(path).expanduser()
    if not p.is_file():
        return f"文件不存在：{p}"
    try:
        text = read_document_text(p)
    except Exception as e:
        return f"读取失败：{e}"
    n = ingest_text(p.name, text)
    return f"已导入 {n} 个片段（来源：{p.name}）"


def _strip_html(html_text):
    html_text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html_text)
    title = ""
    m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html_text)
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()
    html_text = re.sub(r"(?is)<br\s*/?>", "\n", html_text)
    html_text = re.sub(r"(?is)</p>", "\n", html_text)
    text = re.sub(r"(?is)<[^>]+>", " ", html_text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return (title + "\n" + text).strip() if title else text.strip()


def ingest_url(url):
    """下载网页正文并导入知识库。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read()
        for enc in ("utf-8", "gbk"):
            try:
                text = _strip_html(raw.decode(enc))
                break
            except UnicodeDecodeError:
                continue
        else:
            text = _strip_html(raw.decode("utf-8", errors="replace"))
        if len(text) < 50:
            return "网页内容太少，可能无法访问或需要登录。"
        n = ingest_text(url, text)
        return f"已导入 {n} 个片段（来源：{url}）"
    except Exception as e:
        return f"抓取失败：{e}"


# ---------------- 检索 ----------------

def _tokens(text):
    t = (text or "").lower()
    words = set(re.findall(r"[a-z0-9]+", t))
    cjk = re.findall(r"[\u4e00-\u9fff]", t)
    return words | {cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1)} | set(cjk)


def _cos(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = ab = bb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        ab += x * x
        bb += y * y
    if ab == 0 or bb == 0:
        return 0.0
    return dot / (math.sqrt(ab) * math.sqrt(bb))


def search(query, topk=None):
    """语义检索；嵌入模型不可用时自动退回关键词检索。"""
    topk = topk or int(_kcfg().get("topk", 4))
    init_db()
    with _conn() as c:
        rows = [dict(r) for r in c.execute("SELECT id, ts, source, text, embedding FROM kb_chunks")]
    if not rows:
        return []
    q_emb = None
    if any(r["embedding"] for r in rows):
        try:
            q_emb = _embedder().embed_query(query)
        except Exception:
            q_emb = None
    scored = []
    for r in rows:
        if q_emb is not None and r["embedding"]:
            r["score"] = _cos(q_emb, json.loads(r["embedding"]))
            r["method"] = "semantic"
        else:
            r["score"] = len(_tokens(query) & _tokens(r["text"]))
            r["method"] = "keyword"
        if r["score"] > 0:
            scored.append(r)
    scored.sort(key=lambda r: -r["score"])
    return scored[:topk]


def build_context(query, topk=None):
    """检索并拼成注入提示词的上下文文本。"""
    topk = topk or int(_kcfg().get("topk", 4))
    parts = []
    for r in search(query, topk):
        parts.append(f"- [知识{r['id']}]（来源：{r['source']}）{r['text'][:300]}")
    return "\n".join(parts) if parts else ""


def stats():
    init_db()
    with _conn() as c:
        n = c.execute("SELECT COUNT(*) FROM kb_chunks").fetchone()[0]
        sources = [dict(r) for r in c.execute(
            "SELECT source, COUNT(*) AS n, MAX(ts) AS ts FROM kb_chunks "
            "GROUP BY source ORDER BY ts DESC LIMIT 10"
        )]
    return n, sources


def list_recent(limit=100):
    """最近片段列表（知识看板用）。"""
    init_db()
    with _conn() as c:
        rows = [dict(r) for r in c.execute(
            "SELECT id, ts, source, substr(text, 1, 120) AS snippet FROM kb_chunks "
            "ORDER BY id DESC LIMIT ?", (int(limit),))]
    return rows


def delete_chunk(cid):
    init_db()
    with _conn() as c:
        cur = c.execute("DELETE FROM kb_chunks WHERE id=?", (cid,))
        return cur.rowcount > 0


def clear_all():
    init_db()
    with _conn() as c:
        c.execute("DELETE FROM kb_chunks")
