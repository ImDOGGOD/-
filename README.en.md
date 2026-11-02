<div align="center">

[简体中文](README.md) | English

<img src="docs/banner.png" alt="ZuZhiDuoMou Local Multi-Model Multi-Agent System" width="100%">

# ZuZhiDuoMou

### A Fully Local Multi-Model · Multi-Agent System

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13-green.svg)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Ollama-required-orange.svg)](https://ollama.com/)
[![100% Local](https://img.shields.io/badge/100%25-Local-success.svg)()

Data stays on your machine · Six models working together · Three orchestration modes · Memory & knowledge base · Terminal & Web frontends

</div>

---

## Table of Contents

1. [Overview](#1-overview)
2. [Key Features](#2-key-features)
3. [Architecture](#3-architecture)
4. [Model List](#4-model-list)
5. [Quick Start](#5-quick-start)
6. [Usage Guide](#6-usage-guide)
7. [Configuration](#7-configuration)
8. [Project Structure](#8-project-structure)
9. [Extending the System](#9-extending-the-system)
10. [Uninstallation](#10-uninstallation)
11. [FAQ](#11-faq)
12. [License & Credits](#12-license--credits)

---

## 1. Overview

**ZuZhiDuoMou** is a local multi-model multi-agent system built on [Ollama](https://ollama.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/) that runs on an ordinary consumer-grade laptop.

It addresses one core problem: **on a machine with a single 8GB GPU, making multiple open-source models with different strengths collaborate as a team** — some plan, some execute, some review, some write code, and some call tools — rather than relying on a single model to produce the answer in one shot.

Two design principles guide the project:

- **Anything that can be hard-coded as a rule is handled by code; only tasks requiring understanding and judgment go to the models.** Routing, classification, safety checks, and tool execution are done with deterministic code, while models handle the actual reasoning.
- **Data and code are separated.** Long-term memory and the knowledge base live in independent databases, so upgrading the code never loses data; all inference happens locally and no content is sent to the cloud.

> Use cases: a privacy-focused personal knowledge assistant, offline Q&A, coding assistance, local RAG knowledge bases, and a complete reference implementation for learning multi-agent orchestration and open-source engineering.

---

## 2. Key Features

### 2.1 Three Working Modes

| Mode | Trigger | Mechanism |
|---|---|---|
| General Q&A | Ask directly | Plan → Execute → Review loop; meta-questions bypass, simple questions answered fast |
| Code assistance | `/code <question>` | Same loop with a code-specialized model and dedicated prompts |
| Agent tools | `/agent <task>` | Tool-calling loop plus an independent review; can compute, read/write files, and search the web |

### 2.2 Long-Term Memory

- Manual memory: `/remember`, `/recall`, `/forget`, `/memory`;
- Automatic distillation: after complex Q&A, the planner model automatically extracts key points from the conversation into memory;
- Relevant memories are scored with Chinese/English tokenization and injected into prompts.

### 2.3 Knowledge Base (RAG)

- Import local txt/md files and fetch web pages;
- The bge-m3 embedding model performs semantic retrieval and automatically falls back to keyword search when embeddings are unavailable;
- Retrieved material is injected into answers with priority, and the review step verifies facts against it.

### 2.4 Two Frontends, One Orchestration

- **Web UI**: dark theme, SSE streaming, mode switching, memory and knowledge-base shortcuts;
- **Terminal UI**: interactive command line with token-by-token streaming;
- Both consume the same event generator, so logic changes happen in one place.

### 2.5 Engineering & Reproducibility

- One-click deployment, one-click uninstall, USB packaging, and a six-model downloader;
- Built-in `.gitattributes` / `.gitignore` govern line endings, encodings, and sensitive files so anyone can download and deploy;
- A plugin space lets you extend agent capabilities by writing a single function.

### 2.6 Cloud Hybrid Mode (New in v1.3.0)

- The client provides a "Enable cloud model" toggle: once on, the selected roles (planner/executor/reviewer) use an OpenAI-compatible cloud model, while the remaining roles stay on local Ollama — hence "hybrid".
- Customizable base_url/api_key/model/roles; works with DeepSeek, Qwen (DashScope), Zhipu GLM, OpenAI, etc. Off by default and fully local; the API key is never committed.
- Falls back to local automatically when no key is set or the toggle is off, without errors. Tested end-to-end with a real DeepSeek key for both full-cloud and hybrid Q&A.

---

## 3. Architecture

The system is organized into five layers, each with a single, well-defined responsibility:

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend   webui.py (dark browser UI, SSE)  chat.py (terminal)│
├─────────────────────────────────────────────────────────────┤
│ Orchestration  core.py: three LangGraph graphs               │
│                GENERAL_GRAPH / CODE_GRAPH (pipeline)          │
│                AGENT_GRAPH (tool loop)                        │
│                event streams iter_ask / iter_agent (shared)   │
├──────────────────┬──────────────────────────────────────────┤
│ Data             │  Tools tools.py (5 built-in) + my_tools.py │
│ memory.py store  │        (plugin space, loads TOOLS_EXTRA)   │
│ kb.py RAG        │                                           │
├──────────────────┴──────────────────────────────────────────┤
│ Models  Ollama service (127.0.0.1:11434) + model_warehouse   │
├─────────────────────────────────────────────────────────────┤
│ Deployment  start / install / USB-pack / uninstall .bat      │
└─────────────────────────────────────────────────────────────┘
```

The **orchestration core** consists of three LangGraph state graphs:

- **Pipeline graphs**: `router` (rule-based meta detection plus planner classification) → `executor` → `reviewer`; a failed review returns to the executor with revision notes, looping a fixed number of times;
- **Agent graph**: the executor binds tools; tool calls trigger tool execution, while no tool calls enter review. A "tool-storm guard" executes only the first tool call per turn, preventing small models from generating hundreds of duplicate calls;
- **Event streams**: emit five event types — `banner / text / tool / final / error` — shared by terminal and web.

See [技术架构.md](技术架构.md) for the full mechanisms, data flow, and tuning pitfalls.

---

## 4. Model List

The system uses six local models (including one embedding model), all Q4 quantized. Ollama loads them serially on demand, so only one 7–9B model runs at a time within 8GB of GPU memory.

| Ollama name | Source | Size | Role |
|---|---|---|---|
| qwen2.5:7b | Qwen2.5-7B-Instruct | 4.7GB | Planning/routing + Agent execution (native tool support) |
| internlm3:8b | InternLM3-8B-Instruct | 5.4GB | General execution + Agent review |
| qwen2.5-coder-7b:q4_k_m | Qwen2.5-Coder-7B | 4.7GB | Code-mode execution (specialized) |
| deepseek-r1:8b | DeepSeek-R1-0528-Qwen3-8B | 5.0GB | General/code review (reasoning model) |
| spark-x2.5:4b | Spark-X2.5-4B | 2.6GB | Backup |
| bge-m3 | BAAI bge-m3 | 634MB | Knowledge-base embeddings (semantic retrieval) |

**GPU budget**: model weights ≤5.4GB + 8K-context KV cache (about 1.2GB for 8B) ≈ 6.6GB < 8GB, so it fits within 8GB of VRAM.

---

## 5. Quick Start

### 5.1 Hardware & Environment

| Item | Recommended | Minimum |
|---|---|---|
| GPU | NVIDIA 8GB VRAM | No discrete GPU (CPU-only, roughly an order of magnitude slower) |
| RAM | 32GB | 16GB |
| Disk | About 1MB code + 13GB models + 16GB imported copies | Same |
| Software | Python 3.13, Ollama | The install script can set them up automatically |

### 5.2 Option 1: One-Click Deployment (Recommended)

1. Download this repository (`Code → Download ZIP`) and extract it;
2. Double-click **`安装部署.bat`**: it detects the environment — installing missing Python or Ollama via winget, or opening download pages with links if that fails — then creates a virtual environment, installs dependencies, and imports the six models;
3. Double-click **`启动.bat`** and choose `[1]` Web UI (recommended) or `[2]` terminal.

> The only instruction anyone needs is: **"Double-click 安装部署.bat and follow the prompts."**

### 5.3 Option 2: Manual Setup from GitHub

The GitHub repository contains only code and docs, **not model files** (the 100MB per-file limit).

```bash
# 1. Clone the repository
git clone https://github.com/ImDOGGOD/-.git
cd -

# 2. Create a virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Download the six models (resumable, auto-retry, about 13GB)
.venv\Scripts\python.exe download_models.py

# 4. Prepare the config (or let the install script do it)
copy models.yaml.example models.yaml

# 5. Launch
.venv\Scripts\python.exe webui.py
```

### 5.4 Two Ways to Get the Models

1. **Downloader** (recommended): `python download_models.py` downloads the six models from ModelScope and places them in `model_warehouse`, with resumable transfers and logs at `gguf\download_all.log`;
2. **Offline copy**: use `打包到U盘.bat` on an existing machine to copy the `model_warehouse` folder, no re-download needed.

> For the full illustrated online-download walkthrough on a fresh machine, see [无模型库部署教程.md](无模型库部署教程.md).

---

## 6. Usage Guide

### 6.1 Slash Commands

| Command | Purpose |
|---|---|
| Ask directly | Enter general Q&A mode |
| `/code <question>` | Code assistance mode |
| `/agent <task>` | Agent tool mode; can compute, read files, and search the web |
| `/remember <content>` | Store something in long-term memory |
| `/recall <keyword>` | Search memories and past Q&A |
| `/forget <id>` | Delete a memory |
| `/memory` | View statistics and recent memories |
| `/cloud on/off` | Toggle the cloud model; without an argument, show status |
| `/help` | Show the full command help |

### 6.2 Knowledge Base Commands

```
/kb add <file path>      Import a txt/md file
/kb fetch <url>          Fetch a web page into the knowledge base
/kb search <keyword>     Semantic retrieval of chunks
/kb list                 View entry counts and sources
/kb delete <id>           Delete a chunk
/kb clear                 Empty the knowledge base
```

### 6.3 Built-in Tools (Agent Mode)

| Tool | Capability |
|---|---|
| calculator | Math with safe AST-whitelist evaluation |
| current_time | Get the current time |
| read_file | Read files (within the project root, size-limited) |
| list_directory | List directory contents |
| web_search | Web search (Bocha API; key configured in models.yaml) |

---

## 7. Configuration

### 7.1 models.yaml

Only the public template **`models.yaml.example`** is tracked; `models.yaml` containing the real key is excluded by `.gitignore` and auto-generated on first run.

```yaml
provider: bocha
base_url: https://api.bochaai.com/v1/web-search
api_key: put-your-key-here
count: 5
```

The cloud hybrid mode is configured in the `cloud` section of the same file (empty api_key in the public template):

```yaml
cloud:
  enabled: false
  base_url: https://api.deepseek.com
  api_key: ""          # your own cloud key, kept locally only
  model: deepseek-chat
  roles: [planner, executor, reviewer]
```

### 7.2 Line Ending & Encoding Governance

- `.gitattributes` treats `*.bat` / `*.cmd` as binary (`-text`), so Git never changes their encoding or line endings, preventing cmd parse failures after download;
- `*.py` / `*.md` / `*.yaml` use LF; `*.ps1` uses CRLF;
- Do not re-save bat files in an editor, which can break encoding and line endings.

### 7.3 Changing Models and Parameters

- Prompts, generation lengths, and loop limits live in `core.py`; every role has a `num_predict` cap to prevent runaway generation;
- Import recipes are in `model_warehouse/<model>/Modelfile`; after replacing a GGUF, run `ollama create` again.

---

## 8. Project Structure

```
ZuZhiDuoMou/
├─ core.py / chat.py / webui.py        # Orchestration / terminal entry / web entry
├─ tools.py / my_tools.py              # Built-in tools / plugin space
├─ memory.py / kb.py                   # Long-term memory / knowledge-base RAG
├─ download_models.py                  # Six-model downloader
├─ multi_agent.py / test_single.py     # Early demo / single-model test
├─ models.yaml.example / requirements.txt
├─ model_warehouse/                    # Model sources and import recipes (weights not tracked)
│   ├─ bge-m3/ deepseek-r1-8b/ internlm3-8b/
│   ├─ qwen2.5-7b/ qwen2.5-coder-7b/ spark-x2.5-4b/
│   └─ import_model.ps1 and helper files
├─ docs/banner.png                     # Documentation image
├─ 启动.bat / 安装部署.bat / 打包到U盘.bat / 一键卸载.bat
├─ README.md / README.en.md / VERSION.md
├─ 系统说明书.md / 技术架构.md / 无模型库部署教程.md / CHANGELOG.md
├─ .gitattributes / .gitignore / LICENSE
└─ release/                            # Release artifacts (not tracked)
```

---

## 9. Extending the System

### 9.1 Adding a New Tool

Write a `@tool`-decorated function in `my_tools.py`, add it to the `TOOLS_EXTRA` list, and it takes effect automatically on save without touching the core code. The function's docstring is the usage instruction shown to the model.

### 9.2 Adding a New Model

1. Place the GGUF in `model_warehouse/<new folder>/` and write an import recipe following the existing Modelfiles;
2. Run `ollama create` to register it;
3. Point the relevant role to the new model name in `core.py`.
- Mind the 8GB constraint: only one 7–9B Q4 model loads at a time, and Ollama switches models serially.

### 9.3 Training & Upgrades

- The system is built for **local inference and orchestration**; 8GB VRAM does not support from-scratch pretraining or full fine-tuning;
- Upgrading in practice means replacing a model with a newer or better-quantized open-source GGUF and re-importing it;
- For domain adaptation, consider parameter-efficient methods like LoRA if VRAM allows, or simply inject domain material through the RAG knowledge base (lower cost and always updatable).

---

## 10. Uninstallation

Double-click **`一键卸载.bat`** in the project folder and type `YES` to confirm: it removes the six models from Ollama and the entire project folder, but **does not** uninstall Python or Ollama themselves. Typing anything else cancels the operation.

---

## 11. FAQ

| Problem | Solution |
|---|---|
| `ollama create` cannot find the model file | Make sure the GGUF is in the right `model_warehouse` subfolder |
| Activating the venv reports scripts are disabled | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force` |
| Web UI won't open | Check that port 8765 is free, or use the terminal instead |
| Bat files report "not recognized as a command" | Ensure `.gitattributes` is present and never re-save bat files in an editor |
| Model generation runs out of control | Check the `num_predict` caps for each role in `core.py` |
| Web search returns nothing | Verify the API key in `models.yaml` |

For more troubleshooting, see [系统说明书.md](系统说明书.md) and [CHANGELOG.md](CHANGELOG.md).

---

## 12. License & Credits

The code is released under the **[MIT License](LICENSE)** and may be freely used, modified, and distributed; the models carry their own separate licenses, which should be confirmed before redistribution.

| Party | Nickname | Responsibility |
|---|---|---|
| DeepSeek | MoShi (谋士) | System architecture, framework and original code, maintenance |
| Doubao | JiangShi (匠师) | Initial deployment, diagnostics, GitHub release, line-ending and reproducibility governance |

<div align="center">

Repository: https://github.com/ImDOGGOD/-

— The ZuZhiDuoMou Team, 2026-11-02

</div>
