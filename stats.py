"""运行统计（可观测性）：记录每次问答的耗时、来源、记忆/知识命中与 token 估算。

表 runs：一次模型问答一条，含模式、来源（local/cloud/hybrid）、耗时、
云端/本地节点数、记忆与知识命中条数、估算输入/输出 token、是否通过。

口径说明：token 为本地 tiktoken（cl100k_base）估算，不是云端真实计费，
仅用于量级参考；stats.db 已被 .gitignore 的 *.db 规则排除，不入库。
"""
import re
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "stats.db"


def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS runs ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, mode TEXT, source TEXT,"
            "duration_ms INTEGER, cloud_nodes INTEGER, local_nodes INTEGER,"
            "memory_hits INTEGER, knowledge_hits INTEGER,"
            "est_prompt_tokens INTEGER, est_completion_tokens INTEGER,"
            "passed INTEGER, error TEXT)"
        )


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def count_tokens(text):
    """估算 token：优先 tiktoken；不可用时用中英文字符兜底，保证不崩。"""
    if not text:
        return 0
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
        words = len(re.findall(r"[a-zA-Z0-9]+", text))
        return cjk + words


def record_run(mode, source, duration_ms, cloud_nodes, local_nodes,
               memory_hits, knowledge_hits, prompt_text, answer_text,
               passed=True, error=""):
    """写入一次问答统计，返回新记录 id。"""
    init_db()
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO runs (ts, mode, source, duration_ms, cloud_nodes, local_nodes,"
            "memory_hits, knowledge_hits, est_prompt_tokens, est_completion_tokens,"
            "passed, error) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (_now(), mode, source, int(duration_ms), int(cloud_nodes), int(local_nodes),
             int(memory_hits), int(knowledge_hits),
             count_tokens(prompt_text), count_tokens(answer_text),
             1 if passed else 0, error),
        )
        return cur.lastrowid


def summary(limit=10):
    """汇总：总量、平均耗时、成败、来源分布、估算 token、记忆/知识命中率、最近记录。"""
    init_db()
    with _conn() as c:
        total = c.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
        if total == 0:
            return {"total": 0, "recent": []}
        avg_ms = c.execute("SELECT AVG(duration_ms) FROM runs").fetchone()[0]
        n_pass = c.execute("SELECT COUNT(*) FROM runs WHERE passed=1").fetchone()[0]
        n_fail = c.execute("SELECT COUNT(*) FROM runs WHERE passed=0").fetchone()[0]
        src_rows = c.execute("SELECT source, COUNT(*) AS n FROM runs GROUP BY source").fetchall()
        sum_pt = c.execute("SELECT SUM(est_prompt_tokens) FROM runs").fetchone()[0]
        sum_ct = c.execute("SELECT SUM(est_completion_tokens) FROM runs").fetchone()[0]
        mem_runs = c.execute("SELECT COUNT(*) FROM runs WHERE memory_hits>0").fetchone()[0]
        kb_runs = c.execute("SELECT COUNT(*) FROM runs WHERE knowledge_hits>0").fetchone()[0]
        recent = [dict(r) for r in c.execute(
            "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,))]
    return {
        "total": total,
        "avg_duration_ms": round(avg_ms or 0),
        "passed": n_pass,
        "failed": n_fail,
        "by_source": {r["source"]: r["n"] for r in src_rows},
        "est_prompt_tokens": sum_pt or 0,
        "est_completion_tokens": sum_ct or 0,
        "memory_hit_rate": round(mem_runs / total, 3),
        "knowledge_hit_rate": round(kb_runs / total, 3),
        "recent": recent,
    }
