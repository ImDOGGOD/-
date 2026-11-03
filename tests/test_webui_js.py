"""回归：webui.py 内嵌前端 JS 的语法完整性（花括号/圆括号配平 + 关键元素）。

背景：前端 JS 曾因一个缺失的 `}` 导致整个 <script> 语法错误，
浏览器解析失败 → 所有按钮失灵、状态卡"检测中"。后端测试无法覆盖此盲区，
故单独建立本用例，纳入 pytest / GitHub Actions CI 自动拦截。
"""
import ast
import pathlib
import re

BASE = pathlib.Path(__file__).resolve().parent.parent


def _webui_html():
    t = (BASE / "webui.py").read_text(encoding="utf-8")
    ast.parse(t)  # 先保证 Python 语法合法
    m = re.search(r'HTML = r"""<!doctype html>(.*)</body></html>"""', t, re.S)
    assert m, "webui.py 中未找到 HTML 内嵌块"
    return m.group(1), t


def test_webui_python_syntax():
    (BASE / "webui.py").read_text(encoding="utf-8")
    ast.parse((BASE / "webui.py").read_text(encoding="utf-8"))


def test_webui_js_braces_balanced():
    html, _ = _webui_html()
    scripts = re.findall(r'<script>(.*?)</script>', html, re.S)
    assert scripts, "未找到 <script> 块"
    for i, s in enumerate(scripts):
        assert s.count("{") - s.count("}") == 0, f"脚本块 {i} 花括号不平衡"
        assert s.count("(") - s.count(")") == 0, f"脚本块 {i} 圆括号不平衡"


def test_webui_key_elements_present():
    html, t = _webui_html()
    scripts = re.findall(r'<script>(.*?)</script>', html, re.S)
    s = scripts[-1]
    # 关键前端元素与后端路由都应存在（防误删）
    assert 'id="kill-btn"' in html
    assert "killBackend" in s
    assert '"/api/kill"' in t
    assert 'id="sessions"' in html
    assert 'data-mode="social"' in html
