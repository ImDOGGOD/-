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
    __version__,
    check_ollama,
    cloud_status,
    get_graph,
    get_titles,
    iter_agent,
    iter_ask,
    set_cloud_enabled,
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
<style>:root{
    --bg:#0a0a0a; --surface:#101010; --card:#131313; --line:rgba(255,255,255,.08);
    --text:#f2f2f0; --dim:#8a8a86; --faint:#55554f; --inv:#ffffff; --inv-text:#0a0a0a;
    --accent:#ffffff; --accent-text:#0a0a0a; --fs:14px; --radius:14px;
  }
  *{box-sizing:border-box; margin:0; padding:0;}
  body{
    height:100vh; display:flex; flex-direction:column;
    background:var(--bg); color:var(--text);
    font-family:"Segoe UI",-apple-system,"Microsoft YaHei",sans-serif;
    font-weight:400; letter-spacing:.01em;
  }
  header{
    display:flex; align-items:center; gap:16px; padding:16px 28px;
    border-bottom:1px solid var(--line);
  }
  .logo{
    width:34px;height:34px;border-radius:8px; flex:none;
    background:var(--inv); color:var(--inv-text);
    display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:600;
  }
  .title{font-size:15px;font-weight:500;letter-spacing:.02em;}
  .title small{display:block;font-size:11px;color:var(--dim);font-weight:400;margin-top:3px;letter-spacing:.05em;}
  .status{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:11px;color:var(--dim);letter-spacing:.06em;}
  .dot{width:6px;height:6px;border-radius:50%;background:var(--faint);}
  .dot.ok{background:var(--accent);}
  .dot.bad{background:var(--faint);}
  #chat{flex:1;overflow-y:auto;padding:34px 28px;display:flex;flex-direction:column;gap:20px;}
  .msg{max-width:80%;animation:fade .3s ease;}
  .user{align-self:flex-end;}
  .user .bubble{background:var(--inv);color:var(--inv-text);
    border-radius:var(--radius) var(--radius) 4px var(--radius);padding:11px 15px;
    white-space:pre-wrap;word-break:break-word;font-size:var(--fs);}
  .bot{align-self:flex-start;width:86%;}
  .chip{display:inline-block;font-size:10px;color:var(--dim);margin-bottom:8px;
    letter-spacing:.14em;border:1px solid var(--line);padding:3px 10px;border-radius:999px;}
  .chip.tool{color:var(--text);background:rgba(255,255,255,.04);}
  .bubble{background:var(--card);border:1px solid var(--line);border-radius:var(--radius) var(--radius) var(--radius) 4px;
    padding:13px 16px;line-height:1.7;white-space:pre-wrap;word-break:break-word;font-size:var(--fs);}
  .bubble pre{background:#0d0d0d;border:1px solid var(--line);border-radius:10px;
    padding:12px;overflow-x:auto;margin:8px 0;font-size:13px;font-family:"JetBrains Mono",Consolas,monospace;}
  .bubble code{font-family:Consolas,monospace;background:rgba(255,255,255,.06);padding:1px 6px;border-radius:5px;font-size:13px;}
  .bubble pre code{background:none;padding:0;}
  .bubble b{color:#fff;font-weight:600;}
  .badge{display:inline-block;margin-top:10px;font-size:10px;padding:3px 12px;border-radius:999px;
    border:1px solid var(--line);color:var(--dim);letter-spacing:.1em;}
  .badge.ok{color:var(--text);border-color:rgba(255,255,255,.32);}
  .err .bubble{border-color:rgba(255,255,255,.35);}
  footer{padding:16px 28px 20px;border-top:1px solid var(--line);background:var(--bg);}
  .modes{display:flex;gap:8px;margin-bottom:12px;}
  .mode{flex:1;max-width:150px;text-align:center;padding:9px 0;border-radius:999px;cursor:pointer;
    border:1px solid var(--line);color:var(--dim);font-size:12.5px;letter-spacing:.08em;transition:.2s;background:transparent;}
  .mode.on{background:var(--accent);color:var(--accent-text);border-color:var(--accent);font-weight:600;}
  .quick{display:flex;gap:8px;margin-bottom:12px;flex-wrap:wrap;}
  .quick button{font-size:11px;color:var(--dim);background:transparent;border:1px solid var(--line);
    padding:4px 12px;border-radius:999px;cursor:pointer;transition:.2s;letter-spacing:.04em;}
  .quick button:hover{color:var(--text);border-color:rgba(255,255,255,.35);}
  .inputrow{display:flex;gap:10px;}
  textarea{flex:1;resize:none;border-radius:var(--radius);padding:13px 16px;font-size:var(--fs);
    background:#0d0d0d;border:1px solid var(--line);color:var(--text);
    font-family:inherit;outline:none;height:50px;transition:.2s;}
  textarea:focus{border-color:var(--accent);}
  #send{width:110px;border:none;border-radius:var(--radius);cursor:pointer;font-size:14px;color:var(--accent-text);
    background:var(--accent);font-weight:600;letter-spacing:.12em;}
  #send:disabled{opacity:.3;cursor:wait;}
  .tbtn{margin-left:12px;font-size:11px;color:var(--dim);border:1px solid var(--line);
    background:transparent;padding:4px 12px;border-radius:999px;cursor:pointer;letter-spacing:.06em;transition:.2s;}
  .tbtn:hover{color:var(--text);border-color:var(--accent);}
  #cbtn.on{color:var(--accent);border-color:var(--accent);}
  #panel{position:fixed;top:64px;right:28px;width:280px;background:var(--surface);
    border:1px solid var(--line);border-radius:16px;padding:18px;display:none;z-index:99;
    box-shadow:0 18px 50px rgba(0,0,0,.55);}
  #panel.open{display:block;animation:fade .25s ease;}
  #panel h3{font-size:11px;letter-spacing:.14em;color:var(--dim);font-weight:500;margin:14px 0 10px;}
  #panel h3:first-child{margin-top:0;}
  .presets{display:flex;gap:8px;flex-wrap:wrap;}
  .preset{border:1px solid var(--line);background:transparent;color:var(--text);font-size:12px;
    padding:6px 12px;border-radius:999px;cursor:pointer;transition:.2s;}
  .preset.on{border-color:var(--accent);color:var(--accent);}
  .row{display:flex;align-items:center;justify-content:space-between;margin:9px 0;font-size:12px;color:var(--dim);}
  .row input[type=color]{width:34px;height:24px;border:1px solid var(--line);border-radius:6px;background:transparent;cursor:pointer;padding:0;}
  .row input[type=range]{width:118px;accent-color:var(--accent);}
  #reset{margin-top:14px;width:100%;border:1px solid var(--line);background:transparent;color:var(--dim);
    padding:7px 0;border-radius:999px;cursor:pointer;font-size:12px;letter-spacing:.08em;}
  #reset:hover{color:var(--text);border-color:var(--accent);}
  @keyframes fade{from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:none;}}
  ::-webkit-scrollbar{width:8px;} ::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:6px;}</style>
<script>try{const o=JSON.parse(localStorage.getItem('zzdm-theme'));if(o&&o.vars){const r=document.documentElement.style;Object.keys(o.vars).forEach(k=>r.setProperty(k,o.vars[k]));}}catch(e){}</script>
</head>
<body>
<header>
  <div class="logo">谋</div>
  <div class="title">足智多谋 <small>v""" + __version__ + r""" · 全部数据本机运行 · 谋士 出品</small></div>
  <button class="tbtn" id="cbtn">云端：关</button>
  <button class="tbtn" id="tbtn">主题</button>
  <div class="status"><span id="dot" class="dot"></span><span id="stat">检测中…</span></div>
</header>
<div id="chat"></div>
<footer>
  <div class="modes">
    <div class="mode on" data-mode="general">通用问答</div>
    <div class="mode" data-mode="code">代码辅助</div>
    <div class="mode" data-mode="agent">Agent</div>
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
<div id="panel">
  <h3>预设主题</h3>
  <div class="presets" id="presets"></div>
  <h3>自定义</h3>
  <div class="row"><span>背景色</span><input type="color" id="c-bg" value="#0a0a0a"></div>
  <div class="row"><span>强调色</span><input type="color" id="c-ac" value="#ffffff"></div>
  <div class="row"><span>字号 <b id="v-fs"></b></span><input type="range" id="r-fs" min="12" max="18" step="1"></div>
  <div class="row"><span>圆角 <b id="v-ra"></b></span><input type="range" id="r-ra" min="0" max="24" step="2"></div>
  <button id="reset">恢复默认（黑白极简）</button>
</div>
<script>
let mode='general', cur=null, busy=false;
const $=id=>document.getElementById(id), chat=$('chat'), q=$('q'), send=$('send');
const THEMES={
 '黑白极简':{'--bg':'#0a0a0a','--surface':'#101010','--card':'#131313','--line':'rgba(255,255,255,.08)','--text':'#f2f2f0','--dim':'#8a8a86','--faint':'#55554f','--accent':'#ffffff','--accent-text':'#0a0a0a','--fs':'14px','--radius':'14px'},
 '暖纸':{'--bg':'#f5f1e8','--surface':'#fffdf6','--card':'#fffdf6','--line':'rgba(0,0,0,.12)','--text':'#26241f','--dim':'#8b8577','--faint':'#b9b2a0','--accent':'#26241f','--accent-text':'#f5f1e8','--fs':'15px','--radius':'10px'},
 '深海':{'--bg':'#0b1420','--surface':'#101c2c','--card':'#12233a','--line':'rgba(255,255,255,.10)','--text':'#e8eef5','--dim':'#7f93ad','--faint':'#46566e','--accent':'#7fd4ff','--accent-text':'#0b1420','--fs':'14px','--radius':'14px'},
 '墨绿':{'--bg':'#0d1210','--surface':'#111815','--card':'#14201b','--line':'rgba(255,255,255,.08)','--text':'#e6ece8','--dim':'#7f8f86','--faint':'#4b5a51','--accent':'#8ee6b0','--accent-text':'#0d1210','--fs':'14px','--radius':'12px'}
};
let curPreset='自定义', curVars={};
function setVars(v){const r=document.documentElement.style;Object.keys(v).forEach(k=>r.setProperty(k,v[k]));}
function saveTheme(){localStorage.setItem('zzdm-theme',JSON.stringify({preset:curPreset,vars:curVars}));}
function applyVars(v){setVars(v);curVars=v;saveTheme();syncUI();}
function rgb2hex(c){if(c.startsWith('#'))return c;const m=c.match(/[\d.]+/g);if(!m)return '#000000';return '#'+m.slice(0,3).map(x=>('0'+parseInt(x).toString(16)).slice(-2)).join('');}
function syncUI(){
 const cs=getComputedStyle(document.documentElement);
 $('c-bg').value=rgb2hex(cs.getPropertyValue('--bg').trim());
 $('c-ac').value=rgb2hex(cs.getPropertyValue('--accent').trim());
 $('r-fs').value=parseInt(cs.getPropertyValue('--fs'));$('v-fs').textContent=$('r-fs').value+'px';
 $('r-ra').value=parseInt(cs.getPropertyValue('--radius'));$('v-ra').textContent=$('r-ra').value+'px';
 document.querySelectorAll('.preset').forEach(p=>p.classList.toggle('on',p.dataset.name===curPreset));
}
function initTheme(){try{const o=JSON.parse(localStorage.getItem('zzdm-theme'));if(o&&o.vars){setVars(o.vars);curPreset=o.preset||'自定义';curVars=o.vars||{};}}catch(e){}}
initTheme();
const ps=$('presets');
Object.keys(THEMES).forEach(name=>{const b=document.createElement('button');b.className='preset';b.dataset.name=name;b.textContent=name;b.onclick=()=>{curPreset=name;applyVars(THEMES[name]);};ps.appendChild(b);});
$('tbtn').onclick=()=>{syncUI();$('panel').classList.toggle('open');};
$('c-bg').oninput=e=>{curPreset='自定义';applyVars({...curVars,'--bg':e.target.value});};
$('c-ac').oninput=e=>{curPreset='自定义';applyVars({...curVars,'--accent':e.target.value});};
$('r-fs').oninput=e=>{curPreset='自定义';applyVars({...curVars,'--fs':e.target.value+'px'});};
$('r-ra').oninput=e=>{curPreset='自定义';applyVars({...curVars,'--radius':e.target.value+'px'});};
$('reset').onclick=()=>{curPreset='黑白极简';applyVars(THEMES['黑白极简']);};
syncUI();
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
    m.className='chip tool'; m.textContent='· '+d.text; cur.appendChild(m); break;
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
// 云端大模型开关（混合模式）
function renderCloud(st){
 const on=st.enabled===true;
 $('cbtn').classList.toggle('on',on);
 $('cbtn').textContent=on?'云端：开':'云端：关';
 $('cbtn').title=st.configured
   ?('服务商 '+st.base_url+' · 模型 '+st.model+' · 云端岗位 '+st.roles.join('/'))
   :'未配置 api_key，打开也会回退本地（在 models.yaml 的 cloud 段配置）';
}
async function syncCloud(enabled){
 try{
  const r=await fetch('/api/cloud',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({enabled})});
  renderCloud(await r.json());
 }catch(e){}
}
$('cbtn').onclick=async()=>{
 const willOn=$('cbtn').classList.contains('on')===false;
 await syncCloud(willOn);
 localStorage.setItem('zzdm-cloud',willOn?'1':'0');
};
(async function initCloud(){
 try{
  if(localStorage.getItem('zzdm-cloud')==='1'){await syncCloud(true);}
  else{const r=await fetch('/api/cloud');renderCloud(await r.json());}
 }catch(e){}
})();
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
            eviter = iter_ask(get_graph("code"), get_titles("code"), question, list(HISTORY), mem_ctx, kb_ctx)
        elif mode == "agent":
            eviter = iter_agent(question, mem_ctx, kb_ctx)
        else:
            eviter = iter_ask(get_graph("general"), get_titles("general"), question, list(HISTORY), mem_ctx, kb_ctx)
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


async def api_cloud(request):
    """云端开关：GET 返回状态，POST 切换（入参 {"enabled": true/false}）。"""
    if request.method == "POST":
        try:
            body = await request.json()
            status = set_cloud_enabled(bool(body.get("enabled")))
        except Exception as e:
            return HTMLResponse(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), media_type="application/json")
        return HTMLResponse(json.dumps({"ok": True, **status}, ensure_ascii=False), media_type="application/json")
    return HTMLResponse(json.dumps({"ok": True, **cloud_status()}, ensure_ascii=False), media_type="application/json")


routes = [
    Route("/", homepage),
    Route("/api/ping", api_ping),
    Route("/api/chat", api_chat, methods=["POST"]),
    Route("/api/cloud", api_cloud, methods=["GET", "POST"]),
]
app = Starlette(routes=routes)


def _open_browser():
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    print(f"足智多谋 Web 界面 v{__version__} 已启动：http://{HOST}:{PORT}")
    print("浏览器未自动打开时，请手动访问上面的地址。Ctrl+C 退出。")
    threading.Timer(1.2, _open_browser).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
