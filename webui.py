"""本地 Web 问答界面：浏览器里聊天（深色主题、流式输出、三模式切换、记忆与知识库命令）。

运行：python webui.py（或 启动.bat 选 [1]），自动打开 http://127.0.0.1:8765
依赖：starlette / uvicorn / sse-starlette（已随 langgraph-api 安装）
"""
import json
import threading
import webbrowser
from collections import deque

import kb
import memory
import uvicorn
from chat import command_reply
from core import (
    CODE_GRAPH,
    CODE_TITLES,
    GENERAL_GRAPH,
    GENERAL_TITLES,
    __version__,
    check_ollama,
    iter_agent,
    iter_ask,
)
from sse_starlette.sse import EventSourceResponse
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

HOST, PORT = "127.0.0.1", 8765
HISTORY = deque(maxlen=4)  # 会话内最近 4 轮（与终端版一致）

HTML = r"""<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>足智多谋 · Web 界面</title>
<style>
  :root{
    --bg1:#0d0f1e; --bg2:#171233; --card:rgba(255,255,255,.045);
    --border:rgba(255,255,255,.10); --text:#e8e9f4; --dim:#9aa0c0;
    --acc1:#7c5cff; --acc2:#00d4ff; --ok:#3ddc97; --bad:#ff6b7a; --tool:#ffb454;
  }
  *{box-sizing:border-box; margin:0; padding:0;}
  body{
    height:100vh; display:flex; flex-direction:column;
    background:linear-gradient(160deg,var(--bg1),var(--bg2) 70%);
    color:var(--text); font-family:"Segoe UI","Microsoft YaHei",sans-serif;
  }
  header{
    display:flex; align-items:center; gap:14px; padding:14px 22px;
    background:linear-gradient(90deg,rgba(124,92,255,.16),rgba(0,212,255,.10));
    border-bottom:1px solid var(--border);
  }
  .logo{
    width:38px;height:38px;border-radius:11px; flex:none;
    background:linear-gradient(135deg,var(--acc1),var(--acc2));
    display:flex;align-items:center;justify-content:center;font-weight:800;color:#fff;font-size:18px;
    box-shadow:0 4px 18px rgba(124,92,255,.45);
  }
  .title{font-size:17px;font-weight:700;}
  .title small{display:block;font-size:11px;color:var(--dim);font-weight:400;margin-top:2px;}
  .status{margin-left:auto;display:flex;align-items:center;gap:7px;font-size:12px;color:var(--dim);}
  .dot{width:8px;height:8px;border-radius:50%;background:#666;box-shadow:0 0 8px currentColor;}
  .dot.ok{background:var(--ok);color:var(--ok);} .dot.bad{background:var(--bad);color:var(--bad);}
  #chat{flex:1;overflow-y:auto;padding:22px;display:flex;flex-direction:column;gap:14px;}
  .msg{max-width:82%;animation:pop .25s ease;}
  .user{align-self:flex-end;}
  .user .bubble{background:linear-gradient(135deg,#6d4dff,#4a2fd6);color:#fff;
    border-radius:18px 18px 4px 18px;padding:11px 15px;white-space:pre-wrap;word-break:break-word;}
  .bot{align-self:flex-start;width:88%;}
  .chip{display:inline-block;font-size:11px;color:var(--acc2);margin-bottom:6px;
    border:1px solid rgba(0,212,255,.35);padding:2px 9px;border-radius:999px;
    background:rgba(0,212,255,.08);}
  .chip.tool{color:var(--tool);border-color:rgba(255,180,84,.4);background:rgba(255,180,84,.08);}
  .bubble{background:var(--card);border:1px solid var(--border);border-radius:18px 18px 18px 4px;
    padding:12px 16px;line-height:1.65;white-space:pre-wrap;word-break:break-word;font-size:14.5px;}
  .bubble pre{background:rgba(0,0,0,.35);border:1px solid var(--border);border-radius:10px;
    padding:10px 12px;overflow-x:auto;margin:8px 0;font-size:13px;font-family:Consolas,monospace;}
  .bubble code{font-family:Consolas,monospace;background:rgba(0,0,0,.3);padding:1px 5px;border-radius:5px;}
  .bubble pre code{background:none;padding:0;}
  .bubble b{color:#fff;}
  .badge{display:inline-block;margin-top:8px;font-size:11px;padding:3px 10px;border-radius:999px;
    border:1px solid var(--border);color:var(--dim);}
  .badge.ok{border-color:rgba(61,220,151,.4);color:var(--ok);background:rgba(61,220,151,.08);}
  .badge.no{border-color:rgba(255,107,122,.4);color:var(--bad);background:rgba(255,107,122,.08);}
  .err .bubble{border-color:rgba(255,107,122,.5);color:#ffb3bc;}
  footer{padding:14px 22px 18px;border-top:1px solid var(--border);
    background:rgba(13,15,30,.6);backdrop-filter:blur(6px);}
  .modes{display:flex;gap:8px;margin-bottom:10px;}
  .mode{flex:1;max-width:150px;text-align:center;padding:8px 0;border-radius:12px;cursor:pointer;
    border:1px solid var(--border);color:var(--dim);font-size:13px;transition:.2s;background:transparent;}
  .mode.on{background:linear-gradient(135deg,rgba(124,92,255,.28),rgba(0,212,255,.18));
    color:#fff;border-color:rgba(124,92,255,.55);box-shadow:0 0 14px rgba(124,92,255,.25);}
  .quick{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;}
  .quick button{font-size:11.5px;color:var(--dim);background:var(--card);border:1px solid var(--border);
    padding:4px 11px;border-radius:999px;cursor:pointer;transition:.2s;}
  .quick button:hover{color:#fff;border-color:var(--acc1);}
  .inputrow{display:flex;gap:10px;}
  textarea{flex:1;resize:none;border-radius:14px;padding:12px 14px;font-size:14px;
    background:rgba(0,0,0,.28);border:1px solid var(--border);color:var(--text);
    font-family:inherit;outline:none;height:48px;transition:.2s;}
  textarea:focus{border-color:rgba(124,92,255,.6);box-shadow:0 0 12px rgba(124,92,255,.18);}
  #send{width:110px;border:none;border-radius:14px;cursor:pointer;font-size:14px;color:#fff;
    background:linear-gradient(135deg,var(--acc1),var(--acc2));font-weight:700;}
  #send:disabled{opacity:.5;cursor:wait;}
  @keyframes pop{from{opacity:0;transform:translateY(6px);}to{opacity:1;transform:none;}}
  ::-webkit-scrollbar{width:9px;} ::-webkit-scrollbar-thumb{background:rgba(255,255,255,.14);border-radius:6px;}
</style>
</head>
<body>
<header>
  <div class="logo">AI</div>
  <div class="title">足智多谋 <small>v""" + __version__ + r""" · 全部数据本机运行 · DeepSeek 出品</small></div>
  <div class="status"><span id="dot" class="dot"></span><span id="stat">检测中…</span></div>
</header>
<div id="chat"></div>
<footer>
  <div class="modes">
    <div class="mode on" data-mode="general">💬 通用问答</div>
    <div class="mode" data-mode="code">💻 代码辅助</div>
    <div class="mode" data-mode="agent">🤖 Agent</div>
  </div>
  <div class="quick">
    <button data-cmd="/帮助">/帮助</button>
    <button data-cmd="/记忆">/记忆</button>
    <button data-cmd="/知识 列表">/知识 列表</button>
    <button data-cmd="/记住 ">/记住 …</button>
    <button data-cmd="/回忆 ">/回忆 …</button>
    <button data-cmd="/知识 fetch ">/知识 fetch 网址</button>
  </div>
  <div class="inputrow">
    <textarea id="q" placeholder="输入问题，Enter 发送，Shift+Enter 换行…"></textarea>
    <button id="send">发送</button>
  </div>
</footer>
<script>
let mode='general', cur=null, busy=false;
const $=id=>document.getElementById(id), chat=$('chat'), q=$('q'), send=$('send');
const dots=document.querySelectorAll('.mode');
dots.forEach(d=>d.onclick=()=>{dots.forEach(x=>x.classList.remove('on'));d.classList.add('on');mode=d.dataset.mode;});
document.querySelectorAll('.quick button').forEach(b=>b.onclick=()=>{q.value=b.dataset.cmd;q.focus();});
function scroll(){chat.scrollTop=chat.scrollHeight;}
function addUser(t){const m=document.createElement('div');m.className='msg user';
  m.innerHTML='<div class="bubble"></div>';m.firstChild.textContent=t;chat.appendChild(m);scroll();}
function newBot(chipTitle){const m=document.createElement('div');m.className='msg bot';m.dataset.raw='';
  m.innerHTML='<div class="chip">'+chipTitle+'</div><div class="bubble"></div>';chat.appendChild(m);cur=m;return m;}
function md(s){let t=s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  t=t.replace(/```([\s\S]*?)```/g,(_,c)=>'<pre><code>'+c.replace(/^\\n|\\n$/g,'')+'</code></pre>');
  t=t.replace(/`([^`]+)`/g,'<code>$1</code>');
  t=t.replace(/\*\*([^*]+)\*\*/g,'<b>$1</b>');
  return t;}
function closeBot(badge){if(cur){cur.querySelector('.bubble').innerHTML=md(cur.dataset.raw||'');
  if(badge){const d=document.createElement('span');d.className='badge '+badge.cls;d.textContent=badge.txt;
    cur.appendChild(d);}cur=null;scroll();}}
function botEvent(e,d){switch(e){
  case 'banner': closeBot(); newBot(d.title||'系统'); break;
  case 'text': if(!cur) newBot('回答'); cur.dataset.raw+=d.text||'';
    const b=cur.querySelector('.bubble'); b.textContent=cur.dataset.raw; scroll(); break;
  case 'tool': if(!cur) newBot('工具'); const m=document.createElement('div');
    m.className='chip tool'; m.textContent='🔧 '+d.text; cur.appendChild(m); break;
  case 'final': const ok=(d.passed===true);
    closeBot({cls:ok?'ok':'no',txt:'路径：'+(d.path||'?')+' · 修订 '+(d.revisions||0)+' 次 · '+(ok?'通过 ✓':'未通过 ✗')}); break;
  case 'error': closeBot(); const er=newBot('出错'); er.classList.add('err');
    er.dataset.raw=d.message||'未知错误'; closeBot(); break;
  case 'done': break;}}
async function submit(){
  const text=q.value.trim(); if(!text||busy) return;
  busy=true; send.disabled=true; q.value=''; addUser(text);
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({question:text,mode})});
    if(!r.ok) throw new Error('HTTP '+r.status);
    const rd=r.body.getReader(),dec=new TextDecoder(); let buf='';
    while(true){const {done,value}=await rd.read(); if(done) break;
      buf+=dec.decode(value,{stream:true});
      buf=buf.replace(/\r\n/g,'\n');
      let i; while((i=buf.indexOf('\n\n'))>=0){
        const blk=buf.slice(0,i); buf=buf.slice(i+2);
        let ev='message',data='';
        blk.split('\n').forEach(l=>{if(l.startsWith('event: '))ev=l.slice(7);else if(l.startsWith('data: '))data+=l.slice(6);});
        if(ev==='done'){break;} try{botEvent(ev,JSON.parse(data||'{}'));}catch(_){}
      }
    }
  }catch(err){closeBot();const m=newBot('网络错误');m.classList.add('err');m.dataset.raw=String(err);closeBot();}
  busy=false; send.disabled=false; q.focus();
}
send.onclick=submit;
q.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();submit();}});
async function ping(){try{const r=await fetch('/api/ping');const d=await r.json();
  $('dot').className='dot '+(d.ok?'ok':'bad'); $('stat').textContent=d.ok?('Ollama 正常 · 模型 '+(d.models||0)+' 个'):'Ollama 未启动';}
  catch(_){$('dot').className='dot bad';$('stat').textContent='服务连接失败';}}
ping(); setInterval(ping,30000);
</script>
</body></html>"""


async def homepage(request):
    return HTMLResponse(HTML)


async def api_ping(request):
    models = 0
    ok = check_ollama()
    if ok:
        try:
            import urllib.request
            import json as _json
            with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as r:
                models = len(_json.loads(r.read()).get("models", []))
        except Exception:
            models = 0
    return HTMLResponse(json.dumps({"ok": ok, "models": models}), media_type="application/json")


async def api_chat(request):
    body = await request.json()
    question = (body.get("question") or "").strip()
    mode = body.get("mode") or "general"

    async def gen():
        if not question:
            yield {"event": "error", "data": json.dumps({"message": "问题为空"})}
            yield {"event": "done", "data": "{}"}
            return
        rep = command_reply(question)
        if rep is not None:
            yield {"event": "banner", "data": json.dumps({"title": "命令"})}
            yield {"event": "text", "data": json.dumps({"text": rep})}
            yield {"event": "done", "data": "{}"}
            return
        if not check_ollama():
            yield {"event": "error", "data": json.dumps({"message": "Ollama 服务未启动，请先启动 Ollama 再试。"})}
            yield {"event": "done", "data": "{}"}
            return
        mem_ctx = memory.build_context(question)
        kb_ctx = kb.build_context(question)
        if mode == "code":
            eviter = iter_ask(CODE_GRAPH, CODE_TITLES, question, list(HISTORY), mem_ctx, kb_ctx)
        elif mode == "agent":
            eviter = iter_agent(question, mem_ctx, kb_ctx)
        else:
            eviter = iter_ask(GENERAL_GRAPH, GENERAL_TITLES, question, list(HISTORY), mem_ctx, kb_ctx)
        for ev, data in eviter:
            if ev == "banner":
                yield {"event": "banner", "data": json.dumps({"title": data})}
            elif ev == "text":
                yield {"event": "text", "data": json.dumps({"text": data})}
            elif ev == "tool":
                yield {"event": "tool", "data": json.dumps({"text": data})}
            elif ev == "error":
                yield {"event": "error", "data": json.dumps({"message": data})}
                yield {"event": "done", "data": "{}"}
                return
            elif ev == "final":
                if data:
                    draft = data.get("draft") or ""
                    path_label = mode if mode in ("code", "agent") else data.get("mode", mode)
                    yield {"event": "final", "data": json.dumps({
                        "path": path_label,
                        "revisions": data.get("revisions", 0),
                        "passed": data.get("passed", True),
                    })}
                    if draft:
                        HISTORY.append(f"用户：{question}\n助手：{draft[:600]}")
                        memory.log_turn(data.get("mode", mode), question, draft)
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(gen())


routes = [
    Route("/", homepage),
    Route("/api/ping", api_ping),
    Route("/api/chat", api_chat, methods=["POST"]),
]
app = Starlette(routes=routes)


def _open_browser():
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    print(f"足智多谋 Web 界面 v{__version__} 已启动：http://{HOST}:{PORT}")
    print("浏览器未自动打开时，请手动访问上面的地址。Ctrl+C 退出。")
    threading.Timer(1.2, _open_browser).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
