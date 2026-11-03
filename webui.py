"""本地 Web 问答界面：浏览器里聊天（深色主题、流式输出、三模式切换、记忆与知识库命令）。

运行：python webui.py（或 启动.bat 选 [1]），自动打开 http://127.0.0.1:8765
依赖：starlette / uvicorn / sse-starlette（已随 langgraph-api 安装）
"""
import json
import sys
import threading
import time
import webbrowser
from collections import deque

import kb
import memory
import plugin_host
import stats
import tools as tools_mod
import uvicorn
from chat import command_reply
from core import (
    BASE_DIR,
    __version__,
    check_ollama,
    cloud_status,
    get_graph,
    get_titles,
    iter_agent,
    iter_ask,
    iter_vision,
    save_cloud_config,
    set_cloud_enabled,
    _rebuild_graphs,
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
  #cpanel{position:fixed;top:64px;right:28px;width:320px;background:var(--surface);
    border:1px solid var(--line);border-radius:16px;padding:18px;display:none;z-index:100;
    box-shadow:0 18px 50px rgba(0,0,0,.55);}
  #cpanel.open{display:block;animation:fade .25s ease;}
  #cpanel h3{font-size:11px;letter-spacing:.14em;color:var(--dim);font-weight:500;margin:14px 0 8px;}
  #cpanel h3:first-child{margin-top:0;}
  #cpanel label{display:block;font-size:11px;color:var(--dim);margin:10px 0 5px;letter-spacing:.04em;}
  #cpanel input[type=text],#cpanel input[type=password],#cpanel input[type=number]{
    width:100%;border-radius:9px;padding:8px 10px;font-size:12.5px;background:#0d0d0d;
    border:1px solid var(--line);color:var(--text);font-family:inherit;outline:none;}
  #cpanel input:focus{border-color:var(--accent);}
  .croles{display:flex;gap:14px;margin:6px 0;}
  .croles label{display:flex;align-items:center;gap:6px;font-size:12px;color:var(--dim);margin:0;cursor:pointer;}
  .croles input{accent-color:var(--accent);width:14px;height:14px;}
  .cnum{display:flex;gap:10px;}
  .cnum div{flex:1;}
  #csave{margin-top:16px;width:100%;border:none;background:var(--accent);color:var(--accent-text);
    padding:9px 0;border-radius:999px;cursor:pointer;font-size:12.5px;font-weight:600;letter-spacing:.1em;}
  #cmsg{margin-top:10px;font-size:11.5px;line-height:1.5;min-height:16px;word-break:break-word;}
  #cmsg.ok{color:var(--text);} #cmsg.err{color:#e08a8a;}
  #spanel{position:fixed;top:64px;right:28px;width:340px;background:var(--surface);
    border:1px solid var(--line);border-radius:16px;padding:18px;display:none;z-index:101;
    box-shadow:0 18px 50px rgba(0,0,0,.55);max-height:80vh;overflow-y:auto;}
  #spanel.open{display:block;animation:fade .25s ease;}
  #spanel h3{font-size:11px;letter-spacing:.14em;color:var(--dim);font-weight:500;margin:14px 0 8px;}
  #spanel h3:first-child{margin-top:0;}
  #spanel .srow{display:flex;justify-content:space-between;font-size:12px;color:var(--dim);margin:7px 0;gap:10px;}
  #spanel .srow b{color:var(--text);font-weight:600;text-align:right;}
  #spanel .sempty{font-size:12px;color:var(--dim);padding:10px 0;}
  #spanel .srec{font-size:11px;color:var(--dim);border-top:1px solid var(--line);padding:7px 0;line-height:1.5;}
  #spanel .srec b{color:var(--text);font-weight:600;}
  #wrap{flex:1;display:flex;min-height:0;}
  #sessions{width:196px;flex:none;border-right:1px solid var(--line);overflow-y:auto;
    padding:14px 12px;display:flex;flex-direction:column;gap:10px;background:var(--surface);}
  #newchat{border:1px solid var(--accent);color:var(--accent);background:transparent;
    padding:7px 0;border-radius:10px;cursor:pointer;font-size:12px;letter-spacing:.06em;}
  #slist{display:flex;flex-direction:column;gap:4px;}
  .sitem{display:flex;align-items:center;justify-content:space-between;gap:6px;
    padding:8px 10px;border-radius:9px;cursor:pointer;font-size:12px;color:var(--dim);
    border:1px solid transparent;transition:.15s;}
  .sitem:hover{color:var(--text);border-color:var(--line);}
  .sitem.on{color:var(--text);border-color:var(--line);background:var(--card);}
  .sitem .st{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .sitem .del{flex:none;width:16px;height:16px;line-height:14px;text-align:center;
    font-size:11px;color:var(--faint);border:1px solid var(--line);border-radius:6px;cursor:pointer;
    background:transparent;padding:0;}
  .sitem .del:hover{color:var(--text);border-color:var(--accent);}
  .sviews{display:flex;gap:6px;}
  .sview{flex:1;border:1px solid var(--line);background:transparent;color:var(--dim);font-size:11px;
    padding:4px 0;border-radius:999px;cursor:pointer;letter-spacing:.05em;}
  .sview.on{color:var(--text);border-color:var(--accent);}
  .sgroup{font-size:10.5px;color:var(--faint);letter-spacing:.12em;padding:9px 4px 4px;cursor:pointer;user-select:none;}
  .gwrap{display:flex;flex-direction:column;gap:4px;}
  .sitem.pinned .st{font-weight:600;}
  .sic{flex:none;width:15px;text-align:center;cursor:pointer;font-size:11px;}
  .sitem.drag{opacity:.5;}
  .sitem.tree{border:1px solid transparent;}
  .sitem.tree.arch{opacity:.45;}
  #ctxmenu{position:fixed;z-index:200;min-width:150px;background:var(--surface);border:1px solid var(--line);
    border-radius:10px;padding:6px;display:none;box-shadow:0 14px 40px rgba(0,0,0,.5);}
  #ctxmenu button{display:block;width:100%;text-align:left;background:transparent;border:none;color:var(--text);
    font-size:12px;padding:6px 10px;border-radius:7px;cursor:pointer;}
  #ctxmenu button:hover{background:var(--card);color:var(--accent);}
  #ssearch{width:100%;border:1px solid var(--line);background:#0d0d0d;color:var(--text);
    border-radius:9px;padding:6px 10px;font-size:11.5px;outline:none;font-family:inherit;}
  #ssearch:focus{border-color:var(--accent);}
  .ntoolbar{display:flex;gap:6px;margin:2px 0 8px;}
  .ntoolbar button{flex:1;border:1px solid var(--line);background:transparent;color:var(--dim);
    font-size:11px;padding:5px 0;border-radius:999px;cursor:pointer;}
  .ntoolbar button:hover{color:var(--text);border-color:var(--accent);}
  #nstyle{display:none;flex-direction:column;gap:6px;margin-bottom:8px;}
  .ncard{border:1px solid var(--line);border-radius:10px;padding:9px 10px;margin-bottom:8px;
    cursor:pointer;position:relative;overflow:hidden;font-size:12px;}
  .ncard .nt{white-space:pre-wrap;word-break:break-word;line-height:1.55;
    max-height:72px;overflow:hidden;color:var(--text);}
  .ncard .nmeta{font-size:10px;color:var(--faint);margin-top:5px;letter-spacing:.03em;}
  .ncard .npin{position:absolute;right:8px;top:6px;font-size:10px;color:var(--accent);}
  .ncard .ncbar{position:absolute;left:0;top:0;bottom:0;width:3px;}
  .nc{display:inline-block;width:18px;height:18px;border-radius:50%;border:1px solid var(--line);
    cursor:pointer;margin-right:5px;}
  .modal{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:center;
    justify-content:center;z-index:300;}
  .modal.open{display:flex;animation:fade .2s ease;}
  .mbox{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px;
    width:380px;max-width:92vw;box-shadow:0 24px 70px rgba(0,0,0,.6);}
  .mbox.wide{width:720px;}
  .mbox h3{font-size:11px;letter-spacing:.14em;color:var(--dim);font-weight:500;margin-bottom:12px;}
  .mbox textarea{width:100%;background:#0d0d0d;border:1px solid var(--line);color:var(--text);
    border-radius:10px;padding:10px;font-family:inherit;font-size:13px;outline:none;resize:vertical;}
  .mbox textarea:focus{border-color:var(--accent);}
  .mrow{display:flex;align-items:center;gap:8px;margin:10px 0;font-size:11.5px;color:var(--dim);}
  .mrow2{display:flex;gap:8px;margin-top:12px;flex-wrap:wrap;align-items:center;}
  .mrow2 button{flex:1;border:1px solid var(--line);background:transparent;color:var(--dim);
    padding:7px 0;border-radius:999px;cursor:pointer;font-size:12px;}
  .mrow2 button:hover{color:var(--text);border-color:var(--accent);}
  .mrow2 button.primary{background:var(--accent);color:var(--accent-text);border:none;font-weight:600;}
  #atpick{position:absolute;display:none;z-index:150;background:var(--surface);border:1px solid var(--line);
    border-radius:12px;width:420px;max-width:90vw;max-height:260px;overflow-y:auto;
    box-shadow:0 16px 46px rgba(0,0,0,.55);}
  #atpick .ap{border-top:1px solid var(--line);font-size:11px;color:var(--faint);
    padding:3px 12px;letter-spacing:.08em;}
  #atpick .aitem{padding:8px 12px;cursor:pointer;font-size:12px;color:var(--text);line-height:1.5;}
  #atpick .aitem:hover{background:var(--card);}
  #atpick .aitem .asrc{font-size:10px;color:var(--faint);}
  #tpanel{position:fixed;top:64px;right:28px;width:320px;max-height:80vh;overflow-y:auto;background:var(--surface);
    border:1px solid var(--line);border-radius:16px;padding:18px;display:none;z-index:105;
    box-shadow:0 18px 50px rgba(0,0,0,.55);}
  #tpanel.open{display:block;animation:fade .25s ease;}
  #tpanel h3{font-size:11px;letter-spacing:.14em;color:var(--dim);font-weight:500;margin:0 0 10px;}
  .titem{display:flex;justify-content:space-between;align-items:center;gap:8px;
    border:1px solid var(--line);border-radius:10px;padding:8px 12px;margin-bottom:8px;
    cursor:pointer;font-size:12px;color:var(--text);}
  .titem:hover{border-color:var(--accent);}
  .titem .td{flex:none;border:none;background:transparent;color:var(--faint);cursor:pointer;font-size:11px;}
  .titem .td:hover{color:var(--text);}
  #gsvg{width:100%;min-height:380px;border:1px solid var(--line);border-radius:12px;overflow:hidden;background:#0d0d0d;}
  #gsvg svg{width:100%;height:100%;display:block;}
  .glabel{font-size:11px;color:var(--dim);display:flex;align-items:center;gap:4px;}
  #gpanel select{background:#0d0d0d;border:1px solid var(--line);color:var(--text);
    border-radius:999px;padding:6px 12px;font-size:12px;outline:none;}
  .sres{border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin-bottom:8px;
    cursor:pointer;font-size:12px;color:var(--text);line-height:1.5;}
  .sres:hover{border-color:var(--accent);}
  .sres .ssrc{font-size:10px;color:var(--faint);letter-spacing:.06em;margin-bottom:3px;}
  .sres .sqt{max-height:48px;overflow:hidden;color:var(--dim);}
  #main{flex:1;display:flex;flex-direction:column;min-width:0;}
  #mpanel{position:fixed;top:64px;right:28px;width:340px;max-height:80vh;overflow-y:auto;background:var(--surface);
    border:1px solid var(--line);border-radius:16px;padding:18px;display:none;z-index:102;
    box-shadow:0 18px 50px rgba(0,0,0,.55);}
  #mpanel.open{display:block;animation:fade .25s ease;}
  #mpanel h3{font-size:11px;letter-spacing:.14em;color:var(--dim);font-weight:500;margin:12px 0 8px;}
  #mpanel h3:first-child{margin-top:0;}
  .tabs{display:flex;gap:8px;margin-bottom:10px;}
  .tab{flex:1;border:1px solid var(--line);background:transparent;color:var(--dim);
    padding:6px 0;border-radius:999px;cursor:pointer;font-size:12px;letter-spacing:.08em;}
  .tab.on{background:var(--accent);color:var(--accent-text);border-color:var(--accent);font-weight:600;}
  .addrow{display:flex;gap:6px;margin-bottom:10px;}
  .addrow input{flex:1;min-width:0;border-radius:9px;padding:7px 9px;font-size:12px;background:#0d0d0d;
    border:1px solid var(--line);color:var(--text);font-family:inherit;outline:none;}
  .addrow input:focus{border-color:var(--accent);}
  .addrow button{border:none;background:var(--accent);color:var(--accent-text);
    padding:0 12px;border-radius:9px;cursor:pointer;font-size:12px;font-weight:600;}
  .ditem{display:flex;flex-direction:column;gap:4px;border-top:1px solid var(--line);
    padding:9px 0;font-size:12px;color:var(--text);line-height:1.55;position:relative;padding-right:52px;}
  .ditem .dmeta{font-size:10.5px;color:var(--faint);letter-spacing:.03em;}
  .ditem .delbtn{position:absolute;right:0;top:9px;border:1px solid var(--line);background:transparent;
    color:var(--faint);font-size:10.5px;padding:2px 9px;border-radius:999px;cursor:pointer;}
  .ditem .delbtn:hover{color:var(--text);border-color:var(--accent);}
  #monpanel{position:fixed;top:64px;right:28px;width:300px;max-height:80vh;overflow-y:auto;background:var(--surface);
    border:1px solid var(--line);border-radius:16px;padding:18px;display:none;z-index:104;
    box-shadow:0 18px 50px rgba(0,0,0,.55);}
  #monpanel.open{display:block;animation:fade .25s ease;}
  #monpanel h3{font-size:11px;letter-spacing:.14em;color:var(--dim);font-weight:500;margin:12px 0 8px;}
  #monpanel h3:first-child{margin-top:0;}
  #monpanel .srow{display:flex;justify-content:space-between;font-size:12px;color:var(--dim);margin:6px 0;gap:10px;}
  #monpanel .srow b{color:var(--text);font-weight:600;text-align:right;}
  .gbar{height:6px;background:var(--line);border-radius:6px;overflow:hidden;margin:8px 0;}
  .gfill{height:100%;background:var(--accent);transition:width .4s;}
  #preload{width:100%;margin:6px 0 12px;border:1px solid var(--accent);color:var(--accent);background:transparent;
    padding:7px 0;border-radius:999px;cursor:pointer;font-size:12px;letter-spacing:.05em;}
  .dempty{font-size:12px;color:var(--dim);padding:10px 0;}
  #kbstats{font-size:11.5px;color:var(--dim);margin-bottom:8px;}
  .macts{display:flex;gap:8px;margin-top:6px;}
  .mact{border:1px solid var(--line);background:transparent;color:var(--dim);font-size:10.5px;
    padding:2px 10px;border-radius:999px;cursor:pointer;transition:.2s;}
  .mact:hover{color:var(--text);border-color:var(--accent);}
  #attz{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap;}
  #attdrop{border:1px dashed var(--line);border-radius:12px;padding:10px 16px;font-size:12px;
    color:var(--dim);cursor:pointer;transition:.2s;flex:1;min-width:200px;}
  #attdrop:hover{border-color:var(--accent);color:var(--text);}
  #attprev{max-height:96px;max-width:160px;border-radius:10px;border:1px solid var(--line);}
  #attclear{border:1px solid var(--line);background:transparent;color:var(--dim);font-size:11px;
    padding:4px 12px;border-radius:999px;cursor:pointer;}
  #attclear:hover{color:var(--text);border-color:var(--accent);}
  #kbup{margin-bottom:10px;font-size:11.5px;color:var(--dim);}
  #kbup input{border:1px solid var(--line);border-radius:8px;background:transparent;color:var(--dim);
    padding:5px 8px;font-size:11px;max-width:180px;}
  #kupbtn{border:1px solid var(--accent);color:var(--accent);background:transparent;font-size:11.5px;
    padding:5px 14px;border-radius:999px;cursor:pointer;margin-left:6px;}
  #epanel{position:fixed;top:64px;right:28px;width:250px;background:var(--surface);
    border:1px solid var(--line);border-radius:16px;padding:18px;display:none;z-index:103;
    box-shadow:0 18px 50px rgba(0,0,0,.55);}
  #epanel.open{display:block;animation:fade .25s ease;}
  #epanel h3{font-size:11px;letter-spacing:.14em;color:var(--dim);font-weight:500;margin:0 0 4px;}
  #epanel button{display:block;width:100%;margin:9px 0;border:1px solid var(--line);
    background:transparent;color:var(--text);padding:8px 0;border-radius:999px;cursor:pointer;
    font-size:12px;letter-spacing:.05em;transition:.2s;}
  #epanel button:hover{border-color:var(--accent);color:var(--accent);}
  @media print{
    header,#sessions,footer,#panel,#cpanel,#spanel,#mpanel,#epanel{display:none!important;}
    #wrap{display:block!important;}
    #main{display:block!important;}
    #chat{overflow:visible!important;padding:0!important;}
    body{background:#fff!important;color:#000!important;height:auto!important;}
    .msg{max-width:100%!important;}
    .bubble{border-color:#ddd!important;font-size:12px!important;}
    .user .bubble{background:#f2f2f2!important;color:#000!important;border:1px solid #ddd!important;}
    .bot .bubble{background:#fff!important;color:#000!important;}
    .chip{color:#555!important;border-color:#ccc!important;}
    .badge{color:#555!important;border-color:#ccc!important;}
  }
  @keyframes fade{from{opacity:0;transform:translateY(4px);}to{opacity:1;transform:none;}}
  ::-webkit-scrollbar{width:8px;} ::-webkit-scrollbar-thumb{background:rgba(255,255,255,.12);border-radius:6px;}</style>
<script>try{const o=JSON.parse(localStorage.getItem('zzdm-theme'));if(o&&o.vars){const r=document.documentElement.style;Object.keys(o.vars).forEach(k=>r.setProperty(k,o.vars[k]));}}catch(e){}</script>
</head>
<body>
<header>
  <div class="logo">谋</div>
  <div class="title">足智多谋 <small>v""" + __version__ + r""" · 全部数据本机运行 · 谋士 出品</small></div>
  <button class="tbtn" id="cbtn">云端：关</button>
  <button class="tbtn" id="cset">云端设置</button>
  <button class="tbtn" id="sbtn">统计</button>
  <button class="tbtn" id="mbtn">看板</button>
  <button class="tbtn" id="ebtn">导出</button>
  <span id="plugbtns"></span>
  <button class="tbtn" id="monbtn">监控</button>
  <button class="tbtn" id="tbtn">主题</button>
  <div class="status"><span id="dot" class="dot"></span><span id="stat">检测中…</span></div>
</header>
<div id="wrap">
  <aside id="sessions">
    <button id="newchat">＋ 新对话</button>
    <input id="ssearch" placeholder="搜索…（Ctrl+K）">
    <div class="sviews">
      <button class="sview on" id="vlist">列表</button>
      <button class="sview" id="vtree">结构</button>
      <button class="sview" id="vnotes">笔记</button>
      <button class="sview" id="vgraph">图谱</button>
    </div>
    <div id="slist"></div>
  </aside>
  <main id="main">
    <div id="chat"></div>
    <footer>
  <div class="modes">
    <div class="mode on" data-mode="general">通用问答</div>
    <div class="mode" data-mode="code">代码辅助</div>
    <div class="mode" data-mode="agent">Agent</div>
    <div class="mode" data-mode="vision">图片</div>
    <div class="mode" data-mode="social">文案</div>
  </div>
  <div class="quick">
    <button data-cmd="/帮助">/帮助</button>
    <button data-cmd="/记忆">/记忆</button>
    <button data-cmd="/知识 列表">/知识 列表</button>
    <button data-cmd="/记住 ">/记住 …</button>
    <button data-cmd="/回忆 ">/回忆 …</button>
    <button data-cmd="/知识 fetch ">/知识 fetch 网址</button>
    <button id="tplbtn">模板</button>
  </div>
  <div id="attz" style="display:none;">
    <input type="file" id="imgfile" accept="image/*" style="display:none;">
    <div id="attdrop">拖入图片，或点击选择（png/jpg/webp，≤8MB）</div>
    <img id="attprev" alt="预览" style="display:none;">
    <button id="attclear" style="display:none;">清除</button>
  </div>
  <div class="inputrow">
    <textarea id="q" placeholder="输入问题，Enter 发送，Shift+Enter 换行…"></textarea>
    <button id="send">发送</button>
  </div>
</footer>
  </main>
</div>
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
<div id="cpanel">
  <h3>云端大模型配置</h3>
  <label>接口地址 base_url</label>
  <input type="text" id="cc-url" placeholder="https://api.deepseek.com">
  <label>密钥 api_key <span style="float:right;cursor:pointer;" id="cc-eye">显示</span></label>
  <input type="password" id="cc-key" placeholder="sk-...">
  <label>模型名 model</label>
  <input type="text" id="cc-model" placeholder="deepseek-chat">
  <h3>走云端的岗位</h3>
  <div class="croles">
    <label><input type="checkbox" value="planner">规划</label>
    <label><input type="checkbox" value="executor">执行</label>
    <label><input type="checkbox" value="reviewer">审查</label>
  </div>
  <div class="cnum">
    <div><label>温度</label><input type="number" id="cc-temp" step="0.1" min="0" max="2"></div>
    <div><label>长度上限</label><input type="number" id="cc-np" step="1" min="1" max="32768"></div>
  </div>
  <button id="csave">保存配置</button>
  <div id="cmsg"></div>
</div>
<div id="spanel">
  <h3>运行统计</h3>
  <div id="sbody"><div class="sempty">加载中…</div></div>
</div>
<div id="mpanel">
  <h3>记忆 · 知识看板</h3>
  <div class="tabs">
    <button class="tab on" id="tab-mem">记忆</button>
    <button class="tab" id="tab-kb">知识库</button>
    <button class="tab" id="tab-plug">插件</button>
  </div>
  <div id="mem-view">
    <div class="addrow">
      <input id="mcontent" placeholder="新增记忆内容…">
      <input id="mtags" placeholder="标签" style="max-width:90px;">
      <button id="madd">添加</button>
    </div>
    <div id="mlist"></div>
  </div>
  <div id="kb-view" style="display:none;">
    <div id="kbstats"></div>
    <div id="kbup">
      <input type="file" id="kfile" accept=".pdf,.docx,.xlsx,.xlsm,.txt,.md">
      <button id="kupbtn">导入到知识库</button>
    </div>
    <div id="klist"></div>
  </div>
  <div id="plug-view" style="display:none;">
    <button id="preload">重载插件（拖入新插件后点击）</button>
    <div id="plist"></div>
  </div>
</div>
<div id="epanel">
  <h3>对话导出</h3>
  <button id="e-cur">导出当前会话 Markdown</button>
  <button id="e-pdf">打印当前会话为 PDF</button>
  <button id="e-all">导出全部会话 Markdown</button>
</div>
<div id="ctxmenu"></div>
<div id="atpick"></div>
<div id="tpanel">
  <h3>提示词模板</h3>
  <div id="tplist"></div>
  <div class="addrow"><input id="tpname" placeholder="模板名"><input id="tptext" placeholder="模板内容"><button id="tpadd">添加</button></div>
</div>
<div id="note-edit" class="modal">
  <div class="mbox">
    <h3>编辑笔记</h3>
    <textarea id="netext" rows="8"></textarea>
    <div class="mrow"><span class="nclabel">卡片色</span><span id="necolors"></span></div>
    <div class="mrow2">
      <button id="ne-pin">置顶</button>
      <button id="ne-mem">转存记忆</button>
      <button id="ne-del">删除</button>
      <button id="ne-save">保存</button>
    </div>
  </div>
</div>
<div id="gpanel" class="modal">
  <div class="mbox wide">
    <h3>对话图谱</h3>
    <div id="gsvg"></div>
    <div class="mrow2">
      <select id="g-preset">
        <option value="theme">跟随主题</option>
        <option value="bw">黑白</option>
        <option value="green">墨绿</option>
        <option value="sea">深海</option>
        <option value="paper">暖纸</option>
      </select>
      <label class="glabel">节点 <input type="range" id="g-size" min="8" max="22" value="13"></label>
      <label class="glabel"><input type="checkbox" id="g-labels" checked>标签</label>
      <label class="glabel"><input type="checkbox" id="g-arch" checked>归档</label>
    </div>
  </div>
</div>
<div id="monpanel">
  <h3>模型监控</h3>
  <div class="srow"><span>Ollama 状态</span><b id="mon-ok">…</b></div>
  <div class="srow"><span>已注册模型</span><b id="mon-total">…</b></div>
  <div id="mon-loaded"></div>
  <h3>GPU</h3>
  <div id="mon-gpu"></div>
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
// 多会话 v2（v1.8.0）：项目分组/命名/图标/置顶/拖拽排序/继续/分叉/归档/结构树
let sessions=[], sid=null, viewMode='list';
const ICONS=['','📌','★','💡','🚀','📚','✍️','🎯','🔍','🧠','📎','🗂️'];
function normSession(s){
 return {id:s.id,title:s.title||'新对话',html:s.html||'',group:s.group||'默认',
  icon:s.icon||'',pinned:!!s.pinned,archived:!!s.archived,parent:s.parent||null,
  t:s.t||(Number(String(s.id).slice(1))||Date.now())};
}
function loadSessions(){
 try{sessions=JSON.parse(localStorage.getItem('zzdm-sessions')||'[]');}catch(e){sessions=[];}
 sessions=(Array.isArray(sessions)?sessions:[]).map(normSession);
 if(!sessions.length){sessions=[normSession({id:'s'+Date.now()})];}
 sid=sessions[0].id; saveSessions(); renderSessions(); chat.innerHTML=curSession().html||''; scroll();
}
function saveSessions(){try{localStorage.setItem('zzdm-sessions',JSON.stringify(sessions));}catch(e){}}
function curSession(){return sessions.find(s=>s.id===sid);}
function snapSession(){const s=curSession(); if(!s) return;
 s.html=chat.innerHTML; s.t=Date.now();
 if(s.title==='新对话'){const b=chat.querySelector('.msg.user .bubble'); if(b) s.title=b.textContent.slice(0,16);}
 saveSessions();}
function switchSession(id){if(busy||id===sid) return; snapSession(); sid=id;
 chat.innerHTML=curSession().html||''; renderSessions(); scroll();}
function newSession(opts){if(busy) return; snapSession();
 const s=normSession(Object.assign({id:'s'+Date.now()},opts||{})); sessions.unshift(s); sid=s.id;
 chat.innerHTML=s.html||''; saveSessions(); renderSessions(); scroll();}
function delSession(id){sessions=sessions.filter(s=>s.id!==id);
 if(!sessions.length){sessions=[normSession({id:'s'+Date.now()})];}
 if(sid===id){sid=sessions[0].id; chat.innerHTML=curSession().html||'';}
 saveSessions(); renderSessions(); scroll();}
$('newchat').onclick=()=>newSession();
function ordered(){return sessions.slice().sort((a,b)=>(b.pinned-a.pinned)||(b.t-a.t));}
function itemEl(s){
 const it=document.createElement('div');it.className='sitem'+(s.id===sid?' on':'')+(s.pinned?' pinned':'');
 it.draggable=true;
 const ic=document.createElement('span');ic.className='sic';ic.textContent=s.icon||'·';ic.title='点击切换图标';
 ic.onclick=e=>{e.stopPropagation();cycleIcon(s.id);};
 const t=document.createElement('span');t.className='st';t.textContent=s.title;
 const m=document.createElement('button');m.className='del';m.textContent='⋮';m.title='更多';
 m.onclick=e=>{e.stopPropagation();openMenu(s.id,e.clientX,e.clientY);};
 it.appendChild(ic);it.appendChild(t);it.appendChild(m);
 it.onclick=()=>switchSession(s.id);
 it.addEventListener('dragstart',e=>{e.dataTransfer.setData('text/plain',s.id);it.classList.add('drag');});
 it.addEventListener('dragend',()=>it.classList.remove('drag'));
 it.addEventListener('dragover',e=>{e.preventDefault();});
 it.addEventListener('drop',e=>{e.preventDefault();const from=e.dataTransfer.getData('text/plain');
  if(from&&from!==s.id){moveBefore(from,s.id);}});
 it.addEventListener('dblclick',e=>{e.stopPropagation();renameSession(s.id);});
 return it;
}
function addGroup(el,name,arr){
 const head=document.createElement('div');head.className='sgroup';head.textContent=name+' ('+arr.length+')';
 head.onclick=()=>{head.classList.toggle('fold');const w=head.nextElementSibling;if(w)w.style.display=head.classList.contains('fold')?'none':'';};
 el.appendChild(head);
 const wrap=document.createElement('div');wrap.className='gwrap';
 arr.forEach(s=>wrap.appendChild(itemEl(s)));
 el.appendChild(wrap);
}
function renderSessions(){
 const el=$('slist'); el.innerHTML='';
 if(viewMode==='tree'){renderTree(el); return;}
 if(viewMode==='notes'){renderNotes(el); return;}
 const gm={};
 ordered().forEach(s=>{if(s.archived)return;(gm[s.group]=gm[s.group]||[]).push(s);});
 Object.keys(gm).forEach(g=>addGroup(el,g,gm[g]));
 const arch=ordered().filter(s=>s.archived);
 if(arch.length) addGroup(el,'归档',arch);
}
function renderTree(el){
 const roots=sessions.filter(s=>!s.parent||!sessions.some(x=>x.id===s.parent));
 function walk(s,dep){
  const line=document.createElement('div');
  line.className='sitem tree'+(s.id===sid?' on':'')+(s.archived?' arch':'');
  line.style.paddingLeft=(6+dep*14)+'px';
  const pre=document.createElement('span');pre.className='sic';pre.textContent=(s.icon||'·');
  const t=document.createElement('span');t.className='st';t.textContent=s.title;
  line.appendChild(pre);line.appendChild(t);
  line.onclick=()=>switchSession(s.id);
  el.appendChild(line);
  sessions.filter(x=>x.parent===s.id).forEach(c=>walk(c,dep+1));
 }
 roots.forEach(r=>walk(r,0));
}
function cycleIcon(id){const s=sessions.find(x=>x.id===id);if(!s)return;
 s.icon=ICONS[(ICONS.indexOf(s.icon||'')+1)%ICONS.length];saveSessions();renderSessions();}
function renameSession(id){const s=sessions.find(x=>x.id===id);if(!s)return;
 const name=prompt('对话名称',s.title);if(name&&name.trim()){s.title=name.trim().slice(0,40);saveSessions();renderSessions();}}
function moveBefore(fromId,toId){
 const fi=sessions.findIndex(x=>x.id===fromId),ti=sessions.findIndex(x=>x.id===toId);
 if(fi<0||ti<0)return;
 const [s]=sessions.splice(fi,1);
 sessions.splice(sessions.findIndex(x=>x.id===toId),0,s);
 saveSessions();renderSessions();
}
// 会话上下文菜单
let menuFor=null;
function openMenu(id,x,y){
  const target = id;  // 立即捕获目标ID，避免闭包问题
  menuFor = id;
  const m=$('ctxmenu');m.innerHTML='';
  const items=[
    ['置顶 / 取消置顶',()=>{const s=sessions.find(v=>v.id===target);if(s){s.pinned=!s.pinned;saveSessions();renderSessions();}}],
    ['重命名',()=>renameSession(target)],
    ['标记图标',()=>cycleIcon(target)],
    ['在新对话中继续',()=>{const s=sessions.find(v=>v.id===target);if(s)newSession({html:s.html,group:s.group});}],
    ['分叉对话',()=>{const s=sessions.find(v=>v.id===target);if(s)newSession({html:s.html,parent:s.id,group:s.group,icon:s.icon});}],
    ['移动到项目…',()=>{const g=prompt('项目名（例如：工作 / 学习 / 灵感）');if(g&&g.trim()){const s=sessions.find(v=>v.id===target);if(s){s.group=g.trim().slice(0,20);saveSessions();renderSessions();}}],
    ['归档',()=>{const s=sessions.find(v=>v.id===target);if(s){s.archived=true;saveSessions();renderSessions();}}],
    ['恢复（取消归档）',()=>{const s=sessions.find(v=>v.id===target);if(s){s.archived=false;saveSessions();renderSessions();}}],
    ['删除',()=>delSession(target)],
  ];
  items.forEach(([label,fn])=>{const b=document.createElement('button');b.textContent=label;b.onclick=()=>{closeMenu();fn();};m.appendChild(b);});
 m.style.display='block';
 m.style.left=Math.min(x,window.innerWidth-180)+'px';
 m.style.top=Math.min(y,window.innerHeight-items.length*32-24)+'px';
}
function closeMenu(){$('ctxmenu').style.display='none';menuFor=null;}
document.addEventListener('click',e=>{if(!$('ctxmenu').contains(e.target))closeMenu();});
function setView(v){
 viewMode=v;
 ['list','tree','notes'].forEach(n=>{const b=$('v'+n);if(b)b.className='sview'+(n===v?' on':'');});
 if(v==='graph'){openGraph();return;}
 renderSessions();
}
$('vlist').onclick=()=>setView('list');
$('vtree').onclick=()=>setView('tree');
$('vnotes').onclick=()=>setView('notes');
$('vgraph').onclick=()=>setView('graph');
loadSessions();
const dots=document.querySelectorAll('.mode');
dots.forEach(d=>d.onclick=()=>{dots.forEach(x=>x.classList.remove('on'));d.classList.add('on');mode=d.dataset.mode;
  $('attz').style.display=mode==='vision'?'flex':'none';});
// 图片上传（v1.5.0）
let imgData=null;
function setImage(file){
 if(!file) return;
 if(file.size>8*1024*1024){$('attdrop').textContent='图片超过 8MB，请压缩后重试';return;}
 const rd=new FileReader();
 rd.onload=()=>{const s=String(rd.result);imgData={b64:s.slice(s.indexOf(',')+1),mime:file.type||'image/png'};
  $('attprev').src=s;$('attprev').style.display='block';$('attclear').style.display='inline-block';
  $('attdrop').textContent=file.name+'（'+Math.round(file.size/1024)+'KB）';};
 rd.readAsDataURL(file);
}
$('attdrop').onclick=()=>$('imgfile').click();
$('imgfile').onchange=e=>{setImage(e.target.files[0]);e.target.value='';};
$('attdrop').addEventListener('dragover',e=>{e.preventDefault();$('attdrop').style.borderColor='var(--accent)';});
$('attdrop').addEventListener('dragleave',()=>{$('attdrop').style.borderColor='';});
$('attdrop').addEventListener('drop',e=>{e.preventDefault();$('attdrop').style.borderColor='';setImage(e.dataTransfer.files[0]);});
$('attclear').onclick=()=>{imgData=null;$('attprev').style.display='none';$('attprev').src='';
 $('attclear').style.display='none';$('attdrop').textContent='拖入图片，或点击选择（png/jpg/webp，≤8MB）';};
document.querySelectorAll('.quick button[data-cmd]').forEach(b=>b.onclick=()=>{q.value=b.dataset.cmd;q.focus();});
function scroll(){chat.scrollTop=chat.scrollHeight;}
function addUser(t){const m=document.createElement('div');m.className='msg user';
  m.innerHTML='<div class="bubble"></div>';m.firstChild.textContent=t;chat.appendChild(m);scroll();snapSession();}
function newBot(chipTitle){const m=document.createElement('div');m.className='msg bot';m.dataset.raw='';
  m.innerHTML='<div class="chip">'+chipTitle+'</div><div class="bubble"></div>';chat.appendChild(m);cur=m;
  const acts=document.createElement('div');acts.className='macts';
  const cp=document.createElement('button');cp.className='mact';cp.textContent='复制';
  cp.onclick=()=>{const raw=m.dataset.raw||m.querySelector('.bubble').textContent;
    navigator.clipboard.writeText(raw).then(()=>{cp.textContent='已复制';setTimeout(()=>cp.textContent='复制',1200);});};
  acts.appendChild(cp);m.appendChild(acts);return m;}
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
  case 'pp': if(!cur) newBot('回答'); cur.dataset.raw=d.text||'';
    const b3=cur.querySelector('.bubble'); b3.textContent=cur.dataset.raw; scroll(); break;
  case 'error': closeBot(); const er=newBot('出错'); er.classList.add('err');
    er.dataset.raw=d.message||'未知错误'; closeBot(); break;
  case 'done': break;}snapSession();}
async function streamFetch(url,payload){
  const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify(payload)});
  if(!r.ok) throw new Error('HTTP '+r.status);
  const rd=r.body.getReader(),dec=new TextDecoder(); let buf='';
  while(true){const {done,value}=await rd.read(); if(done) break;
    buf+=dec.decode(value,{stream:true});
    buf=buf.replace(/\r\n/g,'\n');
    let i; while((i=buf.indexOf('\n\n'))>=0){
      const blk=buf.slice(0,i); buf=buf.slice(i+2);
      let ev='message',data='';
      blk.split('\n').forEach(l=>{if(l.startsWith('event: '))ev=l.slice(7);else if(l.startsWith('data: '))data+=l.slice(6);});
      if(ev==='done'){return;} try{botEvent(ev,JSON.parse(data||'{}'));}catch(_){}
    }
  }
}
async function submit(){
  const text=q.value.trim(); if(!text||busy) return;
  if(mode==='vision'){
    if(!imgData){q.placeholder='请先拖入或选择一张图片';setTimeout(()=>{q.placeholder='输入问题，Enter 发送，Shift+Enter 换行…';},1800);return;}
    busy=true; send.disabled=true; q.value=''; addUser(text||'（图片提问）');
    try{await streamFetch('/api/vision',{question:text,image_b64:imgData.b64,mime:imgData.mime});}
    catch(err){closeBot();const m=newBot('网络错误');m.classList.add('err');m.dataset.raw=String(err);closeBot();}
    busy=false; send.disabled=false; q.focus(); snapSession();
    return;
  }
  busy=true; send.disabled=true; q.value=''; addUser(text);
  try{
    await streamFetch('/api/chat',{question:text,mode});
  }catch(err){closeBot();const m=newBot('网络错误');m.classList.add('err');m.dataset.raw=String(err);closeBot();}
  busy=false; send.disabled=false; q.focus(); snapSession();
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
// 云端配置面板（v1.3.1）
function fillCloudForm(st){
 $('cc-url').value=st.base_url||'';
 $('cc-model').value=st.model||'';
 $('cc-key').value='';
 $('cc-key').type='password'; $('cc-eye').textContent='显示';
 $('cc-key').placeholder=st.configured?'已配置密钥，留空保持不变':'未配置，填入 sk-...';
 document.querySelectorAll('#cpanel .croles input').forEach(cb=>{
  cb.checked=(st.roles||[]).includes(cb.value);});
 $('cc-temp').value=(st.temperature!==undefined)?st.temperature:0.3;
 $('cc-np').value=(st.num_predict!==undefined)?st.num_predict:4096;
 $('cmsg').textContent=''; $('cmsg').className='';
}
$('cset').onclick=async()=>{
 const panel=$('cpanel');
 const willOpen=!panel.classList.contains('open');
 $('panel').classList.remove('open');
 panel.classList.toggle('open',willOpen);
 if(willOpen){try{const r=await fetch('/api/cloud');fillCloudForm(await r.json());}catch(e){}}
};
$('cc-eye').onclick=()=>{
 const k=$('cc-key');
 if(k.type==='password'){k.type='text';$('cc-eye').textContent='隐藏';}
 else{k.type='password';$('cc-eye').textContent='显示';}
};
$('csave').onclick=async()=>{
 const payload={
  base_url:$('cc-url').value,
  model:$('cc-model').value,
  roles:Array.from(document.querySelectorAll('#cpanel .croles input:checked')).map(x=>x.value),
  temperature:$('cc-temp').value,
  num_predict:$('cc-np').value
 };
 if($('cc-key').value.trim()!==''){payload.api_key=$('cc-key').value;}
 $('cmsg').className=''; $('cmsg').textContent='保存中…';
 try{
  const r=await fetch('/api/cloud/config',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify(payload)});
  const d=await r.json();
  if(d.ok){$('cmsg').className='ok';$('cmsg').textContent='已保存并生效';renderCloud(d);fillCloudForm(d);}
  else{$('cmsg').className='err';$('cmsg').textContent='保存失败：'+(d.error||'未知错误');}
 }catch(e){$('cmsg').className='err';$('cmsg').textContent='网络错误：'+String(e);}
};
// 运行统计面板（可观测性）
function renderStats(d){
 const body=$('sbody');
 if(!d.total){body.innerHTML='<div class="sempty">暂无记录，先进行几次问答。</div>';return;}
 const src=d.by_source||{};
 const srcText=Object.keys(src).map(k=>k+' '+src[k]).join(' · ')||'-';
 let h='';
 h+='<h3>问答概览</h3>';
 h+='<div class="srow"><span>总问答</span><b>'+d.total+'</b></div>';
 h+='<div class="srow"><span>通过 / 失败</span><b>'+d.passed+' / '+d.failed+'</b></div>';
 h+='<div class="srow"><span>平均耗时</span><b>'+d.avg_duration_ms+' ms</b></div>';
 h+='<div class="srow"><span>来源分布</span><b>'+srcText+'</b></div>';
 h+='<h3>Token 估算（本地估算，非真实计费）</h3>';
 h+='<div class="srow"><span>累计输入</span><b>'+d.est_prompt_tokens+'</b></div>';
 h+='<div class="srow"><span>累计输出</span><b>'+d.est_completion_tokens+'</b></div>';
 h+='<h3>命中率</h3>';
 h+='<div class="srow"><span>记忆命中率</span><b>'+Math.round(d.memory_hit_rate*100)+'%</b></div>';
 h+='<div class="srow"><span>知识命中率</span><b>'+Math.round(d.knowledge_hit_rate*100)+'%</b></div>';
 h+='<h3>最近记录</h3>';
 (d.recent||[]).forEach(r=>{
  h+='<div class="srec"><b>#'+r.id+' '+r.source+'</b> · '+r.mode+' · '+r.duration_ms+'ms · '
   +'输入'+r.est_prompt_tokens+' / 输出'+r.est_completion_tokens+'</div>';
 });
 body.innerHTML=h;
}
$('sbtn').onclick=async()=>{
 const panel=$('spanel');
 const willOpen=!panel.classList.contains('open');
 $('panel').classList.remove('open'); $('cpanel').classList.remove('open');
 panel.classList.toggle('open',willOpen);
 if(willOpen){try{const r=await fetch('/api/stats');renderStats(await r.json());}catch(e){
  $('sbody').innerHTML='<div class="sempty">统计加载失败。</div>';}}
};
// 记忆 · 知识看板（v1.4.0）
function ditemRow(meta, bodyText, onDel){
 const div=document.createElement('div'); div.className='ditem';
 const b=document.createElement('div'); b.textContent=bodyText;
 const m=document.createElement('div'); m.className='dmeta'; m.textContent=meta;
 const del=document.createElement('button'); del.className='delbtn'; del.textContent='删除'; del.onclick=onDel;
 div.appendChild(del); div.appendChild(b); div.appendChild(m);
 return div;
}
async function refreshMem(){
 try{
  const r=await fetch('/api/memory'); const d=await r.json();
  const el=$('mlist'); el.innerHTML='';
  if(!(d.items&&d.items.length)){el.innerHTML='<div class="dempty">暂无记忆，可在上方添加，或问几轮复杂问题让系统自动提炼。</div>'; return;}
  d.items.forEach(it=>{
   const body=(it.kind==='auto'?'[自动] ':'')+it.content+(it.tags?'  · '+it.tags:'');
   el.appendChild(ditemRow('#'+it.id+' · '+it.ts, body, async()=>{
    await fetch('/api/memory/'+it.id,{method:'DELETE'}); refreshMem();}));
  });
 }catch(e){$('mlist').innerHTML='<div class="dempty">加载失败</div>';}
}
async function refreshKb(){
 try{
  const r=await fetch('/api/kb'); const d=await r.json();
  $('kbstats').textContent='共 '+d.chunks+' 个片段 · '+((d.sources||[]).length)+' 个来源';
  const el=$('klist'); el.innerHTML='';
  if(!(d.items&&d.items.length)){el.innerHTML='<div class="dempty">暂无知识片段，可用 /知识 add 或 /知识 fetch 导入。</div>'; return;}
  d.items.forEach(it=>{
   el.appendChild(ditemRow('#'+it.id+' · '+it.ts+' · '+it.source, it.snippet||'', async()=>{
    await fetch('/api/kb/'+it.id,{method:'DELETE'}); refreshKb();}));
  });
 }catch(e){$('klist').innerHTML='<div class="dempty">加载失败</div>';}
}
$('tab-mem').onclick=()=>{setTab('mem');refreshMem();};
$('tab-kb').onclick=()=>{setTab('kb');refreshKb();};
$('tab-plug').onclick=()=>{setTab('plug');refreshPlug();};
function setTab(which){
 $('tab-mem').className='tab'+(which==='mem'?' on':'');
 $('tab-kb').className='tab'+(which==='kb'?' on':'');
 $('tab-plug').className='tab'+(which==='plug'?' on':'');
 $('mem-view').style.display=which==='mem'?'':'none';
 $('kb-view').style.display=which==='kb'?'':'none';
 $('plug-view').style.display=which==='plug'?'':'none';
}
async function refreshPlug(){
 try{
  const d=await (await fetch('/api/plugins')).json();
  const el=$('plist');el.innerHTML='';
  (d.manifests||[]).forEach(m=>{
   const div=document.createElement('div');div.className='ditem';
   const b=document.createElement('div');b.textContent=m.name+' v'+(m.version||'?')+(m.description?' — '+m.description:'');
   const meta=document.createElement('div');meta.className='dmeta';meta.textContent='id: '+m.id;
   div.appendChild(b);div.appendChild(meta);
   el.appendChild(div);
  });
  if(!(d.manifests||[]).length){el.innerHTML='<div class="dempty">暂无插件。把插件文件夹放进 plugins/ 后点"重载插件"。</div>';}
 }catch(e){$('plist').innerHTML='<div class="dempty">加载失败</div>';}
}
$('preload').onclick=async()=>{
 try{
  const r=await fetch('/api/plugins/reload',{method:'POST'});
  const d=await r.json();
  if(d.ok){refreshPlug();}
 }catch(e){}
};
$('madd').onclick=async()=>{
 const c=$('mcontent').value.trim(); if(!c) return;
 try{
  const r=await fetch('/api/memory',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({content:c,tags:$('mtags').value})});
  const d=await r.json();
  if(d.ok){$('mcontent').value='';$('mtags').value='';refreshMem();}
 }catch(e){}
};
$('kupbtn').onclick=async()=>{
 const f=$('kfile').files[0];
 if(!f){alert('请先选择文件（pdf/docx/xlsx/txt/md）');return;}
 if(f.size>30*1024*1024){alert('文件超过 30MB 限制');return;}
 const rd=new FileReader();
 rd.onload=async()=>{
  const s=String(rd.result);
  try{
   const r=await fetch('/api/files',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({name:f.name,content_b64:s.slice(s.indexOf(',')+1)})});
   const d=await r.json();
   if(d.ok){$('kfile').value='';refreshKb();}
   else{alert('导入失败：'+(d.error||'未知错误'));}
  }catch(e){alert('网络错误：'+String(e));}
 };
 rd.readAsDataURL(f);
};
$('mbtn').onclick=()=>{
 const p=$('mpanel'); const willOpen=!p.classList.contains('open');
 $('panel').classList.remove('open'); $('cpanel').classList.remove('open'); $('spanel').classList.remove('open');
 p.classList.toggle('open',willOpen);
 if(willOpen){refreshMem();}
};
// 对话导出（v1.4.2）：纯前端，DOM→Markdown / 打印为 PDF，不碰服务端
function domToMd(el){
 let out='';
 el.childNodes.forEach(n=>{
  if(n.nodeType===3){out+=n.textContent;}
  else if(n.tagName==='PRE'){out+='\n```\n'+n.textContent.replace(/\n+$/,'')+'\n```\n';}
  else if(n.tagName==='CODE'){out+='`'+n.textContent+'`';}
  else if(n.tagName==='B'){out+='**'+n.textContent+'**';}
  else if(n.tagName==='BR'){out+='\n';}
  else{out+=domToMd(n);}
 });
 return out;
}
function msgToMd(msg){
 const chip=msg.querySelector('.chip');
 const bubble=msg.querySelector('.bubble');
 if(!bubble) return '';
 const who=msg.classList.contains('user')?'用户':(chip?chip.textContent:'助手');
 const body=bubble.dataset.raw?bubble.dataset.raw:domToMd(bubble);
 const badge=msg.querySelector('.badge');
 let tail=badge?'\n\n> '+badge.textContent+'\n':'';
 return '## '+who+'\n\n'+body.trim()+tail+'\n';
}
function sessionToMd(html){
 const t=document.createElement('template'); t.innerHTML=html||'';
 return Array.from(t.content.querySelectorAll('.msg')).map(msgToMd).filter(Boolean).join('\n');
}
function currentMd(){
 const title=(curSession()?curSession().title:'对话').replace(/[\\/:*?"<>|]/g,'_');
 return {title,md:'# '+title+'\n\n> 导出时间：'+new Date().toLocaleString()+'\n\n'+sessionToMd(chat.innerHTML)};
}
function download(name,text,mime){
 const blob=new Blob([text],{type:mime+';charset=utf-8'});
 const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download=name;
 document.body.appendChild(a); a.click(); setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},300);
}
function allMd(){
 let out='';
 sessions.forEach(s=>{out+='# '+s.title.replace(/[\\/:*?"<>|]/g,'_')+'\n\n'+sessionToMd(s.html)+'\n\n---\n\n';});
 return out;
}
$('ebtn').onclick=()=>{
 const p=$('epanel'); const willOpen=!p.classList.contains('open');
 $('panel').classList.remove('open'); $('cpanel').classList.remove('open'); $('spanel').classList.remove('open'); $('mpanel').classList.remove('open');
 p.classList.toggle('open',willOpen);
};
$('e-cur').onclick=()=>{const {title,md}=currentMd(); download('足智多谋-'+title+'.md',md,'text/markdown'); $('epanel').classList.remove('open');};
$('e-pdf').onclick=()=>{$('epanel').classList.remove('open'); setTimeout(()=>window.print(),100);};
$('e-all').onclick=()=>{download('足智多谋-全部会话.md',allMd(),'text/markdown'); $('epanel').classList.remove('open');};
// 插件桥（v1.6.0）：插件 JS 通过 window.ZZDM 挂载 UI
window.ZZDM={
 addHeaderButton:function(label,onclick){const b=document.createElement('button');b.className='tbtn';b.textContent=label;b.onclick=onclick;$('plugbtns').appendChild(b);return b;},
 api:async function(url,opts){const r=await fetch(url,opts);return r.json();}
};
async function loadPluginJS(){
 try{const r=await fetch('/api/plugins');const d=await r.json();
  (d.manifests||[]).forEach(m=>{const s=document.createElement('script');s.src='/plugins/'+m.id+'/plugin.js';s.onerror=()=>{};document.body.appendChild(s);});
 }catch(e){}
}
loadPluginJS();
// 模型监控面板（v1.7.0）
async function refreshMon(){
 try{
  const d=await (await fetch('/api/monitor')).json();
  $('mon-ok').textContent=d.ok?'正常':'未启动';
  $('mon-total').textContent=d.models_total+' 个';
  const le=$('mon-loaded');le.innerHTML='';
  (d.loaded||[]).forEach(m=>{
   const div=document.createElement('div');div.className='srow';
   const s=document.createElement('span');s.textContent=m.name;
   const b=document.createElement('b');b.textContent=m.size_vram?(m.size_vram+' MB 显存'):'CPU';
   div.appendChild(s);div.appendChild(b);
   le.appendChild(div);
  });
  if(!(d.loaded||[]).length){le.innerHTML='<div class="dempty">当前没有加载中的模型</div>';}
  const g=$('mon-gpu');
  if(d.gpu){
   const pct=Math.min(100,Math.round(d.gpu.mem_used/d.gpu.mem_total*100));
   g.innerHTML='<div class="srow"><span>'+d.gpu.name+'</span><b>'+pct+'%</b></div>'
    +'<div class="gbar"><div class="gfill" style="width:'+pct+'%"></div></div>'
    +'<div class="srow"><span>显存 '+d.gpu.mem_used+' / '+d.gpu.mem_total+' MB</span><b>'+d.gpu.temp+'°C · 负载 '+d.gpu.util+'%</b></div>';
  }else{g.innerHTML='<div class="dempty">未检测到 NVIDIA GPU（nvidia-smi）</div>';}
 }catch(e){$('mon-ok').textContent='读取失败';}
}
let monTimer=null;
$('monbtn').onclick=()=>{
 const p=$('monpanel'); const willOpen=!p.classList.contains('open');
 $('panel').classList.remove('open'); $('cpanel').classList.remove('open'); $('spanel').classList.remove('open'); $('mpanel').classList.remove('open'); $('epanel').classList.remove('open');
 p.classList.toggle('open',willOpen);
 if(willOpen){refreshMon();monTimer=setInterval(refreshMon,5000);}
 else{clearInterval(monTimer);monTimer=null;}
};
// ============ 笔记（v1.9.0） ============
let notes=[], editingNote=null, noteStyle={bg:'#141414',radius:10,fs:12};
const NCOLORS=['#0a0a0a','#ffffff','#8a8a86','#d8c9a3','#8ee6b0','#7fd4ff','#e0b060','#d98a8a'];
function loadNotes(){try{const o=JSON.parse(localStorage.getItem('zzdm-notes')||'{}');
 notes=(o.items||[]).map(n=>({id:n.id||'n'+Date.now(),text:n.text||'',pinned:!!n.pinned,color:n.color||'',t:n.t||Date.now()}));
 noteStyle=Object.assign(noteStyle,o.style||{});}catch(e){notes=[];}}
function saveNotes(){try{localStorage.setItem('zzdm-notes',JSON.stringify({items:notes,style:noteStyle}));}catch(e){}}
function renderNotes(el){
 el.innerHTML='';
 const tb=document.createElement('div');tb.className='ntoolbar';
 const add=document.createElement('button');add.textContent='＋ 笔记';add.onclick=()=>openNoteEditor(null);
 const st=document.createElement('button');st.textContent='样式';st.onclick=()=>{const ns=el.querySelector('#nstyle');if(ns)ns.style.display=ns.style.display==='flex'?'none':'flex';};
 tb.appendChild(add);tb.appendChild(st);el.appendChild(tb);
 const ns=document.createElement('div');ns.id='nstyle';
 ns.innerHTML='<div class="row"><span>底色</span><input type="color" id="ns-bg" value="'+noteStyle.bg+'"></div>'
  +'<div class="row"><span>圆角 <b id="ns-rv"></b></span><input type="range" id="ns-r" min="0" max="20" value="'+noteStyle.radius+'"></div>'
  +'<div class="row"><span>字号 <b id="ns-fv"></b></span><input type="range" id="ns-f" min="11" max="17" value="'+noteStyle.fs+'"></div>';
 el.appendChild(ns);
 $('ns-bg').oninput=e=>{noteStyle.bg=e.target.value;saveNotes();renderNotes(el);};
 $('ns-r').oninput=e=>{noteStyle.radius=+e.target.value;saveNotes();renderNotes(el);};
 $('ns-f').oninput=e=>{noteStyle.fs=+e.target.value;saveNotes();renderNotes(el);};
 notes.slice().sort((a,b)=>(b.pinned-a.pinned)||(b.t-a.t)).forEach(n=>{
  const c=document.createElement('div');c.className='ncard';
  c.style.background=noteStyle.bg;c.style.borderRadius=noteStyle.radius+'px';
  const bar=document.createElement('div');bar.className='ncbar';bar.style.background=n.color||'transparent';c.appendChild(bar);
  if(n.pinned){const p=document.createElement('span');p.className='npin';p.textContent='◆';c.appendChild(p);}
  const t=document.createElement('div');t.className='nt';t.style.fontSize=noteStyle.fs+'px';t.textContent=n.text||'(空笔记)';c.appendChild(t);
  const m=document.createElement('div');m.className='nmeta';m.textContent=new Date(n.t).toLocaleString();c.appendChild(m);
  c.onclick=()=>openNoteEditor(n.id);
  el.appendChild(c);
 });
}
function openNoteEditor(id){
 editingNote=id;
 const n=notes.find(x=>x.id===id)||{text:'',color:'',pinned:false};
 $('netext').value=n.text||'';
 const nc=$('necolors');nc.innerHTML='';
 NCOLORS.forEach(col=>{const d=document.createElement('span');d.className='nc';d.style.background=col;
  d.onclick=()=>{const t=notes.find(x=>x.id===editingNote);if(t){t.color=col;saveNotes();}};nc.appendChild(d);});
 $('note-edit').classList.add('open');$('netext').focus();
}
$('ne-save').onclick=()=>{
 const txt=$('netext').value.trim();if(!txt)return;
 let n=notes.find(x=>x.id===editingNote);
 if(n){n.text=txt;n.t=Date.now();}else{n={id:'n'+Date.now(),text:txt,pinned:false,color:'',t:Date.now()};notes.unshift(n);}
 saveNotes();$('note-edit').classList.remove('open');renderSessions();
};
$('ne-pin').onclick=()=>{const n=notes.find(x=>x.id===editingNote);if(n){n.pinned=!n.pinned;saveNotes();}};
$('ne-del').onclick=()=>{notes=notes.filter(x=>x.id!==editingNote);saveNotes();$('note-edit').classList.remove('open');renderSessions();};
$('ne-mem').onclick=async()=>{
 const n=notes.find(x=>x.id===editingNote);if(!n)return;
 try{await fetch('/api/memory',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:n.text,tags:'笔记'})});alert('已转存为长期记忆');}catch(e){alert('转存失败');}
};
$('note-edit').addEventListener('click',e=>{if(e.target===$('note-edit'))$('note-edit').classList.remove('open');});

// ============ 提示词模板（v1.9.0） ============
let prompts=[];
const DEFAULT_PROMPTS=[
 {name:'总结要点',text:'请把下面内容总结成 3-5 条要点：'},
 {name:'润色改写',text:'请润色下面的文字，保持原意，更流畅专业：'},
 {name:'翻译成英文',text:'请翻译成地道的英文：'},
 {name:'找bug',text:'请找出下面代码的问题并给出修正：'},
 {name:'小红书文案',text:'写一篇小红书笔记：主题「」，活泼语气，300 字，带标题和话题标签。'},
 {name:'头脑风暴',text:'围绕「」做头脑风暴，给出 10 个创意点子。'},
];
function loadPrompts(){try{const p=JSON.parse(localStorage.getItem('zzdm-prompts')||'null');prompts=(Array.isArray(p)&&p.length)?p:[...DEFAULT_PROMPTS];}catch(e){prompts=[...DEFAULT_PROMPTS];}}
function savePrompts(){try{localStorage.setItem('zzdm-prompts',JSON.stringify(prompts));}catch(e){}}
function renderPrompts(){
 const el=$('tplist');el.innerHTML='';
 prompts.forEach((p,i)=>{
  const d=document.createElement('div');d.className='titem';
  const s=document.createElement('span');s.textContent=p.name;
  const del=document.createElement('button');del.className='td';del.textContent='×';
  del.onclick=e=>{e.stopPropagation();prompts.splice(i,1);savePrompts();renderPrompts();};
  d.appendChild(s);d.appendChild(del);
  d.onclick=()=>{q.value=p.text;q.focus();$('tpanel').classList.remove('open');};
  el.appendChild(d);
 });
}
$('tplbtn').onclick=()=>{const p=$('tpanel');const w=!p.classList.contains('open');
 $('panel').classList.remove('open');$('cpanel').classList.remove('open');$('spanel').classList.remove('open');$('mpanel').classList.remove('open');$('epanel').classList.remove('open');$('monpanel').classList.remove('open');
 p.classList.toggle('open',w);if(w)renderPrompts();};
$('tpadd').onclick=()=>{const n=$('tpname').value.trim(),t=$('tptext').value.trim();
 if(!n||!t)return;prompts.push({name:n.slice(0,16),text:t});savePrompts();$('tpname').value='';$('tptext').value='';renderPrompts();};

// ============ 全局搜索（v1.9.0，Ctrl+K） ============
let searchMode=false;
function addSearchResult(el,src,label,onclick){
 const d=document.createElement('div');d.className='sres';
 d.innerHTML='<div class="ssrc">'+src+'</div><div class="sqt">'+label+'</div>';
 d.onclick=onclick;el.appendChild(d);
}
async function doSearch(q){
 const kw=q.trim();
 if(!kw){searchMode=false;renderSessions();return;}
 searchMode=true;
 const el=$('slist');el.innerHTML='';
 const low=kw.toLowerCase();
 sessions.forEach(s=>{if(s.title.toLowerCase().includes(low))addSearchResult(el,'对话',s.title,()=>{searchMode=false;$('ssearch').value='';switchSession(s.id);});});
 notes.forEach(n=>{if((n.text||'').toLowerCase().includes(low))addSearchResult(el,'笔记',(n.text||'').slice(0,90),()=>{searchMode=false;$('ssearch').value='';setView('notes');});});
 try{
  const [mr,kr]=await Promise.all([fetch('/api/memory'),fetch('/api/kb')]);
  const [md,kd]=await Promise.all([mr.json(),kr.json()]);
  (md.items||[]).forEach(it=>{if((it.content||'').toLowerCase().includes(low))addSearchResult(el,'记忆','#'+it.id+' '+(it.content||'').slice(0,90),()=>{});});
  (kd.items||[]).forEach(it=>{if((it.snippet||'').toLowerCase().includes(low))addSearchResult(el,'知识','#'+it.id+' · '+it.source+' '+(it.snippet||'').slice(0,80),()=>{});});
 }catch(e){}
 if(!el.children.length){el.innerHTML='<div class="dempty">没有匹配结果</div>';}
}
$('ssearch').addEventListener('input',e=>{const v=e.target.value;if(v.trim())doSearch(v);else{searchMode=false;renderSessions();}});
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();$('ssearch').focus();$('ssearch').select();}});

// ============ 对话图谱（v1.9.0，径向树 + 自定义风格） ============
let graphStyle={preset:'theme',size:13,labels:true,arch:true};
try{graphStyle=Object.assign(graphStyle,JSON.parse(localStorage.getItem('zzdm-graph')||'{}'));}catch(e){}
const GRAPH_PRESETS={
 theme:{node:'#ffffff',edge:'rgba(255,255,255,.18)',label:'#f2f2f0',bg:'transparent'},
 bw:{node:'#ffffff',edge:'rgba(255,255,255,.22)',label:'#ffffff',bg:'#0a0a0a'},
 green:{node:'#8ee6b0',edge:'rgba(142,230,176,.25)',label:'#e6ece8',bg:'#0d1210'},
 sea:{node:'#7fd4ff',edge:'rgba(127,212,255,.25)',label:'#e8eef5',bg:'#0b1420'},
 paper:{node:'#26241f',edge:'rgba(0,0,0,.2)',label:'#26241f',bg:'#f5f1e8'},
};
function openGraph(){
 $('gpanel').classList.add('open');
 $('g-preset').value=graphStyle.preset;$('g-size').value=graphStyle.size;
 $('g-labels').checked=graphStyle.labels;$('g-arch').checked=graphStyle.arch;
 drawGraph();
}
function drawGraph(){
 const box=$('gsvg');
 const W=Math.max(box.clientWidth||620,620),H=380;
 const P=GRAPH_PRESETS[graphStyle.preset]||GRAPH_PRESETS.theme;
 const nodes=sessions.filter(s=>graphStyle.arch||!s.archived);
 if(!nodes.length){box.innerHTML='<svg width="100%" height="'+H+'"></svg>';return;}
 const roots=nodes.filter(s=>!s.parent||!nodes.some(x=>x.id===s.parent));
 const pos={};const edges=[];
 const R=Math.min(W,H)/2-46,CX=W/2,CY=H/2;
 function place(s,level,a0,a1){
  const ang=(a0+a1)/2;
  const rr=R*Math.min(1,level*0.38+0.12);
  pos[s.id]={x:CX+Math.cos(ang)*rr,y:CY+Math.sin(ang)*rr};
  const kids=nodes.filter(x=>x.parent===s.id);
  kids.forEach((k,i)=>{edges.push([s.id,k.id]);
   place(k,level+1,a0+(a1-a0)*i/Math.max(1,kids.length),a0+(a1-a0)*(i+1)/Math.max(1,kids.length));});
 }
 roots.forEach((r,i)=>place(r,0,-Math.PI/2+2*Math.PI*i/Math.max(1,roots.length),-Math.PI/2+2*Math.PI*(i+1)/Math.max(1,roots.length)));
 const esc=s=>String(s.title||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
 let svg='<svg width="'+W+'" height="'+H+'" viewBox="0 0 '+W+' '+H+'" style="background:'+P.bg+'">';
 edges.forEach(([a,b])=>{const pa=pos[a],pb=pos[b];if(!pa||!pb)return;
  svg+='<line x1="'+pa.x+'" y1="'+pa.y+'" x2="'+pb.x+'" y2="'+pb.y+'" stroke="'+P.edge+'" stroke-width="1"/>';});
 nodes.forEach(s=>{const p=pos[s.id];if(!p)return;
  const r=(s.id===sid)?graphStyle.size+3:graphStyle.size;
  svg+='<circle cx="'+p.x+'" cy="'+p.y+'" r="'+r+'" fill="none" stroke="'+P.node+'" stroke-width="'+(s.id===sid?2.5:1.4)+'" data-id="'+s.id+'"/>';
  if(graphStyle.labels){svg+='<text x="'+p.x+'" y="'+(p.y+r+12)+'" text-anchor="middle" font-size="9" fill="'+P.label+'">'+esc(s).slice(0,8)+'</text>';}});
 svg+='</svg>';
 box.innerHTML=svg;
 box.querySelectorAll('circle').forEach(c=>{c.style.cursor='pointer';
  c.onclick=()=>{switchSession(c.dataset.id);drawGraph();};});
}
function saveGraph(){try{localStorage.setItem('zzdm-graph',JSON.stringify(graphStyle));}catch(e){}}
$('g-preset').onchange=e=>{graphStyle.preset=e.target.value;saveGraph();drawGraph();};
$('g-size').oninput=e=>{graphStyle.size=+e.target.value;saveGraph();drawGraph();};
$('g-labels').onchange=e=>{graphStyle.labels=e.target.checked;saveGraph();drawGraph();};
$('g-arch').onchange=e=>{graphStyle.arch=e.target.checked;saveGraph();drawGraph();};
$('gpanel').addEventListener('click',e=>{if(e.target===$('gpanel'))$('gpanel').classList.remove('open');});

// ============ @引用（v1.9.0） ============
let atData=null;
function atPos(){
 const v=q.value,i=q.selectionStart||0;
 const nl=v.lastIndexOf('\n',i-1);
 const at=v.lastIndexOf('@',i-1);
 if(at<0||at<nl)return null;
 return {start:at,query:v.slice(at+1,i).toLowerCase()};
}
async function openAtPicker(){
 const p=atPos();if(!p)return;
 if(!atData){
  atData={mem:[],kb:[]};
  try{const [mr,kr]=await Promise.all([fetch('/api/memory'),fetch('/api/kb')]);
   atData.mem=((await mr.json()).items||[]).slice(0,30);
   atData.kb=((await kr.json()).items||[]).slice(0,30);}catch(e){}
 }
 const pk=$('atpick');pk.innerHTML='';
 let cnt=0;
 const add=(src,txt)=>{const d=document.createElement('div');d.className='aitem';
  d.innerHTML='<div class="asrc">'+src+'</div>'+txt;
  d.onclick=()=>{const cur=q.value;
   q.value=cur.slice(0,p.start)+'【'+src+'引用】'+txt.replace(/\s+/g,' ').slice(0,400)+'\n'+cur.slice(p.start+1+p.query.length);
   pk.style.display='none';q.focus();};
  pk.appendChild(d);cnt++;};
 const hit=(s)=>(s||'').toLowerCase().includes(p.query)||!p.query;
 notes.slice(0,30).forEach(n=>{if(hit(n.text))add('笔记',(n.text||'').slice(0,120));});
 atData.mem.forEach(it=>{if(hit(it.content))add('记忆','#'+it.id+' '+(it.content||'').slice(0,120));});
 atData.kb.forEach(it=>{if(hit(it.snippet))add('知识','#'+it.id+' '+(it.snippet||'').slice(0,120));});
 if(!cnt){pk.style.display='none';return;}
 const r=q.getBoundingClientRect();
 pk.style.left=r.left+'px';
 pk.style.bottom=(window.innerHeight-r.top+10)+'px';
 pk.style.display='block';
}
q.addEventListener('input',()=>{if(mode==='vision')return;if(atPos())openAtPicker();else $('atpick').style.display='none';});
q.addEventListener('blur',()=>setTimeout(()=>$('atpick').style.display='none',200));
document.addEventListener('keydown',e=>{if(e.key==='Escape')$('atpick').style.display='none';});
loadNotes();loadPrompts();
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
        t0 = time.perf_counter()
        memory_hits = len(memory.search(question))
        knowledge_hits = len(kb.search(question))
        cloud_nodes = local_nodes = 0
        answer_parts = []
        run_passed = True
        run_error = ""

        def _record():
            source = ("cloud" if cloud_nodes and not local_nodes else
                      "hybrid" if cloud_nodes else "local")
            prompt_text = "\n".join([question, mem_ctx or "", kb_ctx or ""])
            try:
                stats.record_run(mode, source, (time.perf_counter() - t0) * 1000,
                                 cloud_nodes, local_nodes, memory_hits, knowledge_hits,
                                 prompt_text, "".join(answer_parts), run_passed, run_error)
            except Exception as e:
                print(f"[stats] 记录失败：{e}")

        if mode == "code":
            eviter = iter_ask(get_graph("code"), get_titles("code"), question, list(HISTORY), mem_ctx, kb_ctx)
        elif mode == "agent":
            eviter = iter_agent(question, mem_ctx, kb_ctx)
        elif mode == "social":
            eviter = iter_ask(get_graph("social"), get_titles("social"), question, list(HISTORY), mem_ctx, kb_ctx)
        else:
            eviter = iter_ask(get_graph("general"), get_titles("general"), question, list(HISTORY), mem_ctx, kb_ctx)
        for ev, data in eviter:
            if ev == "banner":
                if "（云端）" in data:
                    cloud_nodes += 1
                else:
                    local_nodes += 1
                yield {"event": "banner", "data": json.dumps({"title": data})}
            elif ev == "text":
                answer_parts.append(data)
                yield {"event": "text", "data": json.dumps({"text": data})}
            elif ev == "tool":
                yield {"event": "tool", "data": json.dumps({"text": data})}
            elif ev == "error":
                run_passed = False
                run_error = data
                yield {"event": "error", "data": json.dumps({"message": data})}
                _record()
                yield {"event": "done", "data": "{}"}
                return
            elif ev == "final":
                if data:
                    draft = data.get("draft") or ""
                    path_label = mode if mode in ("code", "agent", "social") else data.get("mode", mode)
                    run_passed = data.get("passed", True)
                    if draft:
                        filtered = plugin_host.apply_postprocess(draft)
                        if filtered and filtered != draft:
                            yield {"event": "pp", "data": json.dumps({"text": filtered})}
                    yield {"event": "final", "data": json.dumps({
                        "path": path_label,
                        "revisions": data.get("revisions", 0),
                        "passed": data.get("passed", True),
                    })}
                    if draft:
                        HISTORY.append(f"用户：{question}\n助手：{draft[:600]}")
                        memory.log_turn(data.get("mode", mode), question, draft)
        _record()
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


async def api_cloud_config(request):
    """保存云端配置（POST）：入参为 cloud 字段子集，校验后写回 models.yaml。"""
    try:
        body = await request.json()
        status = save_cloud_config(body)
    except Exception as e:
        return HTMLResponse(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False), media_type="application/json")
    return HTMLResponse(json.dumps({"ok": True, **status}, ensure_ascii=False), media_type="application/json")


async def api_stats(request):
    """运行统计：GET 返回汇总（平均耗时、来源分布、token 估算、记忆/知识命中率）。"""
    return HTMLResponse(json.dumps(stats.summary(), ensure_ascii=False), media_type="application/json")


async def api_memory(request):
    """记忆看板：GET 列表 / POST 新增（v1.4.0）。"""
    if request.method == "POST":
        try:
            body = await request.json()
            content = (body.get("content") or "").strip()
            if not content:
                return HTMLResponse(json.dumps({"ok": False, "error": "内容不能为空"}, ensure_ascii=False),
                                    media_type="application/json")
            mid = memory.add_memory(content, kind="manual", tags=(body.get("tags") or "").strip())
            return HTMLResponse(json.dumps({"ok": True, "id": mid}, ensure_ascii=False),
                                media_type="application/json")
        except Exception as e:
            return HTMLResponse(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
                                media_type="application/json")
    try:
        return HTMLResponse(json.dumps({"ok": True, "items": memory.list_recent(200)}, ensure_ascii=False),
                            media_type="application/json")
    except Exception as e:
        return HTMLResponse(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
                            media_type="application/json")


async def api_memory_item(request):
    """删除一条记忆（v1.4.0）。"""
    try:
        memory.delete_memory(int(request.path_params["mid"]))
        return HTMLResponse(json.dumps({"ok": True}, ensure_ascii=False), media_type="application/json")
    except Exception as e:
        return HTMLResponse(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
                            media_type="application/json")


async def api_kb(request):
    """知识看板：GET 统计与片段列表（v1.4.0）。"""
    try:
        n, sources = kb.stats()
        return HTMLResponse(json.dumps({"ok": True, "chunks": n, "sources": sources,
                                        "items": kb.list_recent(200)}, ensure_ascii=False),
                            media_type="application/json")
    except Exception as e:
        return HTMLResponse(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
                            media_type="application/json")


async def api_kb_item(request):
    """删除一个知识片段（v1.4.0）。"""
    try:
        kb.delete_chunk(int(request.path_params["cid"]))
        return HTMLResponse(json.dumps({"ok": True}, ensure_ascii=False), media_type="application/json")
    except Exception as e:
        return HTMLResponse(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
                            media_type="application/json")


async def api_vision(request):
    """图片理解（v1.5.0）：{question, image_b64, mime} → SSE 流。"""
    try:
        body = await request.json()
    except Exception:
        return HTMLResponse(json.dumps({"error": "请求体非法"}, ensure_ascii=False),
                            media_type="application/json", status_code=400)
    b64 = (body.get("image_b64") or "").strip()
    if not b64:
        return HTMLResponse(json.dumps({"error": "缺少图片数据"}, ensure_ascii=False),
                            media_type="application/json", status_code=400)
    if len(b64) > 12_000_000:
        return HTMLResponse(json.dumps({"error": "图片过大（限 8MB）"}, ensure_ascii=False),
                            media_type="application/json", status_code=400)
    question = body.get("question") or ""
    mime = body.get("mime") or "image/png"

    async def gen():
        for ev, data in iter_vision(b64, question, mime):
            if ev == "banner":
                yield {"event": "banner", "data": json.dumps({"title": data})}
            elif ev == "text":
                yield {"event": "text", "data": json.dumps({"text": data})}
            elif ev == "error":
                yield {"event": "error", "data": json.dumps({"message": data})}
            elif ev == "final":
                yield {"event": "final", "data": json.dumps(data)}
        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(gen())


async def api_files(request):
    """文件导入知识库（v1.5.0）：{name, content_b64} → 提取文本 → kb。"""
    try:
        import base64 as _b64
        body = await request.json()
        name = (body.get("name") or "upload.bin").strip().replace("\\", "_").replace("/", "_")
        raw = _b64.b64decode(body.get("content_b64") or "")
        if not raw:
            return HTMLResponse(json.dumps({"ok": False, "error": "文件内容为空"}, ensure_ascii=False),
                                media_type="application/json")
        if len(raw) > 30_000_000:
            return HTMLResponse(json.dumps({"ok": False, "error": "文件过大（限 30MB）"}, ensure_ascii=False),
                                media_type="application/json")
        tmpdir = BASE_DIR / ".uploads"
        tmpdir.mkdir(exist_ok=True)
        path = tmpdir / name
        path.write_bytes(raw)
        try:
            text = kb.read_document_text(str(path))
        except Exception as e:
            path.unlink(missing_ok=True)
            return HTMLResponse(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
                                media_type="application/json")
        n = kb.ingest_text(name, text)
        path.unlink(missing_ok=True)
        return HTMLResponse(json.dumps({"ok": True, "chunks": n, "source": name}, ensure_ascii=False),
                            media_type="application/json")
    except Exception as e:
        return HTMLResponse(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
                            media_type="application/json")


async def api_plugins(request):
    """插件：GET 清单与后处理器状态；POST /api/plugins/{pid} 切换开关（v1.6.0）。"""
    if request.method == "POST":
        try:
            body = await request.json()
            pid = request.path_params["pid"]
            cfg = plugin_host.write_config(pid, {"enabled": bool(body.get("enabled"))})
            return HTMLResponse(json.dumps({"ok": True, "id": pid, **cfg}, ensure_ascii=False),
                                media_type="application/json")
        except Exception as e:
            return HTMLResponse(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
                                media_type="application/json")
    return HTMLResponse(json.dumps({"ok": True, "manifests": plugin_host.list_manifests(),
                                    "processors": plugin_host.processor_states()}, ensure_ascii=False),
                        media_type="application/json")


async def serve_plugin_js(request):
    """插件前端脚本（plugins/<id>/plugin.js）。"""
    pid = request.path_params["pid"]
    p = plugin_host.PLUGIN_DIR / pid / "plugin.js"
    if not p.is_file():
        return HTMLResponse("// plugin.js not found", status_code=404,
                            media_type="application/javascript")
    return HTMLResponse(p.read_text(encoding="utf-8"), media_type="application/javascript")


async def api_plugins_reload(request):
    """重载插件（拖入新插件文件夹后点击；v1.7.0）。"""
    try:
        plugin_host.reload_plugins()
        tools_mod.refresh_plugin_tools()
        _rebuild_graphs()
        return HTMLResponse(json.dumps({"ok": True, "manifests": plugin_host.list_manifests(),
                                        "processors": plugin_host.processor_states(),
                                        "tool_count": len(tools_mod.TOOLS)}, ensure_ascii=False),
                            media_type="application/json")
    except Exception as e:
        return HTMLResponse(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False),
                            media_type="application/json")


async def api_monitor(request):
    """模型监控（v1.7.0）：Ollama 状态、已注册/已加载模型、GPU 显存占用。"""
    gpu = None
    try:
        import subprocess
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total,utilization.gpu,temperature.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5,
        )
        if out.returncode == 0 and out.stdout.strip():
            parts = [x.strip() for x in out.stdout.strip().split(",")]
            gpu = {"name": parts[0], "mem_used": float(parts[1]), "mem_total": float(parts[2]),
                   "util": float(parts[3]), "temp": float(parts[4])}
    except Exception:
        gpu = None
    ok = check_ollama()
    loaded, models_total = [], 0
    if ok:
        try:
            import urllib.request as _u
            import json as _j
            with _u.urlopen("http://127.0.0.1:11434/api/ps", timeout=3) as r:
                for m in _j.loads(r.read()).get("models", []):
                    loaded.append({"name": m.get("name"),
                                   "size_vram": round((m.get("size_vram") or 0) / 1048576),
                                   "expires_at": m.get("expires_at")})
            with _u.urlopen("http://127.0.0.1:11434/api/tags", timeout=3) as r:
                models_total = len(_j.loads(r.read()).get("models", []))
        except Exception:
            pass
    return HTMLResponse(json.dumps({"ok": ok, "models_total": models_total,
                                    "loaded": loaded, "gpu": gpu}, ensure_ascii=False),
                        media_type="application/json")


routes = [
    Route("/", homepage),
    Route("/api/ping", api_ping),
    Route("/api/chat", api_chat, methods=["POST"]),
    Route("/api/cloud", api_cloud, methods=["GET", "POST"]),
    Route("/api/cloud/config", api_cloud_config, methods=["POST"]),
    Route("/api/stats", api_stats),
    Route("/api/memory", api_memory, methods=["GET", "POST"]),
    Route("/api/memory/{mid}", api_memory_item, methods=["DELETE"]),
    Route("/api/kb", api_kb, methods=["GET"]),
    Route("/api/kb/{cid}", api_kb_item, methods=["DELETE"]),
    Route("/api/vision", api_vision, methods=["POST"]),
    Route("/api/files", api_files, methods=["POST"]),
    Route("/api/plugins/reload", api_plugins_reload, methods=["POST"]),
    Route("/api/plugins", api_plugins, methods=["GET"]),
    Route("/api/plugins/{pid}", api_plugins, methods=["POST"]),
    Route("/plugins/{pid}/plugin.js", serve_plugin_js),
    Route("/api/monitor", api_monitor),
]
app = Starlette(routes=routes)


def _open_browser():
    webbrowser.open(f"http://{HOST}:{PORT}")


def _port_in_use(host, port):
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0


if __name__ == "__main__":
    if _port_in_use(HOST, PORT):
        print(f"端口 {PORT} 已被占用，可能已有一个 Web 界面在运行。")
        print(f"直接打开浏览器访问 http://{HOST}:{PORT}")
        _open_browser()
        sys.exit(0)
    print(f"足智多谋 Web 界面 v{__version__} 已启动：http://{HOST}:{PORT}")
    print("浏览器未自动打开时，请手动访问上面的地址。Ctrl+C 退出。")
    threading.Timer(1.2, _open_browser).start()
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
