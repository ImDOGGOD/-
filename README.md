<div align="center">

简体中文 | [English](README.en.md)

<img src="docs/banner.png" alt="足智多谋 本地多模型多Agent系统" width="100%">

# 足智多谋（ZuZhiDuoMou）

### 一个完全本地运行的多模型 · 多 Agent 系统

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13-green.svg)](https://www.python.org/)
[![Ollama](https://img.shields.io/badge/Ollama-required-orange.svg)](https://ollama.com/)
[![100% Local](https://img.shields.io/badge/100%25-Local-success.svg)()

数据不出本机 · 六模型协作 · 三模式编排 · 记忆与知识库 · 终端与 Web 双前端

</div>

---

## 目录

1. [项目简介](#1-项目简介)
2. [核心特性](#2-核心特性)
3. [系统架构](#3-系统架构)
4. [模型清单](#4-模型清单)
5. [快速开始](#5-快速开始)
6. [使用指南](#6-使用指南)
7. [配置说明](#7-配置说明)
8. [目录结构](#8-目录结构)
9. [二次开发](#9-二次开发)
10. [卸载](#10-卸载)
11. [常见问题](#11-常见问题)
12. [许可证与署名](#12-许可证与署名)

---

## 1. 项目简介

**足智多谋**是一套基于 [Ollama](https://ollama.com/) 与 [LangGraph](https://langchain-ai.github.io/langgraph/) 搭建、可在普通消费级笔记本上运行的本地多模型多智能体系统。

它解决的核心问题是：**在单张 8GB 显存的机器上，让多个能力各异的开源大模型像一个团队一样分工协作**——有的负责规划、有的负责执行、有的负责审查、有的负责写代码、有的负责调用工具，而不是依赖单一模型一次给出答案。

设计理念有两条：

- **能写死成规则的交给代码，只有需要"理解与判断"的才交给模型**。路由、分类、安全校验、工具执行都由确定性代码完成，模型只负责真正的推理。
- **数据与代码分离**。长期记忆、知识库各自存于独立数据库，升级代码不丢数据；全部推理在本机完成，不向任何云端发送内容。

> 适用场景：注重隐私的个人知识助手、离线环境问答、代码辅助、本地 RAG 知识库、以及学习多 Agent 编排与开源工程落地的完整参考实现。

---

## 2. 核心特性

### 2.1 三种工作模式

| 模式 | 触发方式 | 机制 |
|---|---|---|
| 通用问答 | 直接提问 | 规划 → 执行 → 审查 闭环；元问题直达、简单问题快答 |
| 代码辅助 | `/code 问题` | 同一闭环，使用代码特化模型与专用提示词 |
| Agent 工具 | `/agent 任务` | 工具调用循环 + 独立审查，可计算、读写文件、联网搜索 |

### 2.2 长期记忆库

- 手动记忆：`/记住`、`/回忆`、`/忘记`、`/记忆`；
- 自动提炼：复杂问答结束后，规划模型自动从对话中提炼要点存入记忆；
- 检索时按中英文分词加权打分，相关记忆自动注入提示词。

### 2.3 知识库（RAG）

- 支持导入本地 txt/md 文件、抓取网页内容；
- bge-m3 嵌入模型做语义检索，嵌入不可用时自动降级为关键词检索；
- 检索到的资料优先注入回答，审查环节据此核对事实。

### 2.4 双前端，同一套编排

- **Web 界面**：深色主题、SSE 流式输出、三模式切换、记忆与知识库快捷命令；
- **终端界面**：交互式命令行，逐字流式输出；
- 两者消费同一个事件生成器，改逻辑只需动一处。

### 2.5 工程与可复刻性

- 一键部署、一键卸载、U 盘打包、六模型一键下载器；
- 内置 `.gitattributes` / `.gitignore` 治理行尾编码与敏感文件，他人下载即可部署；
- 插件化工具空间，写一个函数即可扩展 Agent 能力。

### 2.6 云端混合模式（v1.3.0 新增）

- 客户端提供"启动云端大模型"开关：打开后，指定岗位（planner/executor/reviewer）走兼容 OpenAI 接口的云端大模型，其余岗位仍走本地 Ollama，即"混合"。
- 支持自定义 base_url/api_key/model/roles，适配 DeepSeek、通义千问、智谱 GLM、OpenAI 等；默认关闭、默认全本地，密钥不入库。
- 未配置密钥或开关关闭时自动回退本地，不报错；已用真实 DeepSeek 密钥实测全云端与混合问答正常。
- v1.3.1 起新增"云端设置"网页面板：可直接在浏览器编辑 base_url/密钥/模型/岗位/温度/长度，服务端校验、自动备份 models.yaml.bak，密钥不回显、留空保持不变，仅改 cloud 段不动其他配置。

### 2.7 运行统计与自动化回归（v1.4.0 新增）

- 网页"统计"面板：查看总问答数、通过/失败、平均耗时、本地/云端/混合来源分布、累计估算 token、记忆与知识命中率及最近记录。
- 每次走模型的问答自动记录到 stats.db（不入库）；token 为本地 tiktoken 估算，非真实计费，仅作量级参考。
- 内置 pytest 最小回归用例（tests/，12 个），覆盖云端配置校验、cloud 段替换、配置保存、计算器白名单等不依赖 GPU 的纯逻辑。
- GitHub Actions 持续集成：push/PR 自动在 Ubuntu + Python 3.13 装依赖、从 example 生成 models.yaml 并跑 pytest；开发依赖见 requirements-dev.txt。

---

## 3. 系统架构

系统自上而下分为五层，各层职责单一、边界清晰：

```
┌─────────────────────────────────────────────────────────────┐
│ 前端层   webui.py（浏览器深色UI, SSE流式）  chat.py（终端）     │
├─────────────────────────────────────────────────────────────┤
│ 编排层   core.py：LangGraph 三张图                            │
│          GENERAL_GRAPH / CODE_GRAPH（流水线）                 │
│          AGENT_GRAPH（工具循环）                              │
│          事件流 iter_ask / iter_agent（前端共享）             │
├──────────────────┬──────────────────────────────────────────┤
│ 数据层           │  工具层 tools.py（内置5工具）+ my_tools.py  │
│ memory.py 记忆库  │       （插件空间，自动加载 TOOLS_EXTRA）     │
│ kb.py 知识库 RAG │                                           │
├──────────────────┴──────────────────────────────────────────┤
│ 模型层   Ollama 服务（127.0.0.1:11434）+ model_warehouse      │
├─────────────────────────────────────────────────────────────┤
│ 部署层   启动 / 安装部署 / 打包到U盘 / 一键卸载 .bat           │
└─────────────────────────────────────────────────────────────┘
```

**编排核心**由三张 LangGraph 状态图组成：

- **流水线图**：`router`（规则预判元问题 + 规划模型分类）→ `executor`（执行）→ `reviewer`（审查），不通过则带修订意见回到执行环节，最多循环固定次数；
- **Agent 图**：执行模型绑定工具，有工具调用则执行工具、无工具调用则进入审查；内置"工具风暴防线"，每轮只执行第一个工具调用，防止小模型生成上百个重复调用；
- **事件流**：产出 `banner / text / tool / final / error` 五类事件，终端与 Web 共用。

完整的机制、数据流与调参坑位见 [技术架构.md](技术架构.md)。

---

## 4. 模型清单

系统共使用 6 个本地模型（含 1 个嵌入模型），全部为 Q4 量化，模型由 Ollama 按需串行加载，8GB 显存同一时刻只运行一个 7–9B 模型。

| Ollama 注册名 | 来源 | 大小 | 岗位 |
|---|---|---|---|
| qwen2.5:7b | Qwen2.5-7B-Instruct | 4.7GB | 规划/路由 + Agent 执行（原生支持工具） |
| internlm3:8b | InternLM3-8B-Instruct | 5.4GB | 通用执行 + Agent 审查 |
| qwen2.5-coder-7b:q4_k_m | Qwen2.5-Coder-7B | 4.7GB | 代码模式执行（特化） |
| deepseek-r1:8b | DeepSeek-R1-0528-Qwen3-8B | 5.0GB | 通用/代码审查（推理模型） |
| spark-x2.5:4b | Spark-X2.5-4B | 2.6GB | 备用 |
| bge-m3 | BAAI bge-m3 | 634MB | 知识库嵌入（语义检索） |

**显存账**：模型权重 ≤5.4GB + 8K 上下文 KV 缓存（8B 约 1.2GB）≈ 6.6GB < 8GB，可在 8GB 显存内运行。

---

## 5. 快速开始

### 5.1 硬件与环境要求

| 项 | 推荐配置 | 最低配置 |
|---|---|---|
| 显卡 | NVIDIA 8GB 显存 | 无独显（纯 CPU，速度慢约一个数量级） |
| 内存 | 32GB | 16GB |
| 磁盘 | 代码约 1MB + 模型约 13GB + 导入副本约 16GB | 同左 |
| 软件 | Python 3.13、Ollama | 安装部署脚本可自动安装 |

### 5.2 方式一：一键部署（推荐）

1. 下载本仓库（`Code → Download ZIP`）并解压；
2. 双击 **`安装部署.bat`**：脚本自动检测环境——缺 Python 或 Ollama 时尝试 winget 自动安装，装不了会打开下载页并给出链接；环境齐全后自动创建虚拟环境、安装依赖、导入六个模型；
3. 双击 **`启动.bat`**，选择 `[1]` Web 界面（推荐）或 `[2]` 终端版。

> 对方电脑上唯一需要交代的只有一句：**"双击 安装部署.bat，跟着提示走"**。

### 5.3 方式二：从 GitHub 手动部署

GitHub 仓库只含代码与文档，**不含模型文件**（单文件 100MB 限制）。

```bash
# 1. 克隆仓库
git clone https://github.com/ImDOGGOD/-.git
cd -

# 2. 创建虚拟环境并安装依赖
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. 下载六个模型（断点续传、自动重试，约 13GB）
.venv\Scripts\python.exe download_models.py

# 4. 准备配置（或由安装部署.bat 自动完成）
copy models.yaml.example models.yaml

# 5. 启动
.venv\Scripts\python.exe webui.py
```

### 5.4 获取模型的两条路径

1. **一键下载器**（推荐）：`python download_models.py`，自动从魔搭 ModelScope 下载六个模型并归位到 `model_warehouse`，断点续传、日志在 `gguf\download_all.log`；
2. **离线拷贝**：从已有机器用 `打包到U盘.bat` 复制 `model_warehouse` 文件夹，无需重新下载。

> 手头没有模型库、想在新电脑上在线下载的完整图文步骤，见 [无模型库部署教程.md](无模型库部署教程.md)。

---

## 6. 使用指南

### 6.1 斜杠命令一览

| 命令 | 作用 |
|---|---|
| 直接提问 | 进入通用问答模式 |
| `/code 问题`（`/代码`） | 代码辅助模式 |
| `/agent 任务`（`/智能体`） | Agent 工具模式，可计算/读文件/联网搜索 |
| `/记住 内容`（`/remember`） | 手动存入长期记忆 |
| `/回忆 关键词`（`/recall`） | 检索记忆与历史问答 |
| `/忘记 编号`（`/forget`） | 删除一条记忆 |
| `/记忆`（`/memory`） | 查看统计与最近记忆 |
| `/云端 开/关`（`/cloud`） | 切换云端大模型开关，不带参数查看状态 |
| `/帮助`（`/help`） | 查看完整命令帮助 |

### 6.2 知识库命令

```
/知识 add <文件路径>      导入 txt/md 文件（也可用 添加/导入）
/知识 fetch <网址>        抓取网页内容入库（也可用 下载）
/知识 查 <关键词>         语义检索片段（也可用 search/搜索）
/知识 列表                查看条目数与来源
/知识 删除 <编号>          删除片段
/知识 清空                清空知识库
```

### 6.3 内置工具（Agent 模式）

| 工具 | 能力 |
|---|---|
| calculator | 数学计算，AST 白名单安全求值 |
| current_time | 获取当前时间 |
| read_file | 读取文件（限项目根目录内、有大小上限） |
| list_directory | 列出目录内容 |
| web_search | 联网搜索（博查 API，密钥在 models.yaml 配置） |

---

## 7. 配置说明

### 7.1 models.yaml

仓库只跟踪公开模板 **`models.yaml.example`**；含真实密钥的 `models.yaml` 被 `.gitignore` 排除，首次运行由脚本自动复制生成。

```yaml
provider: bocha
base_url: https://api.bochaai.com/v1/web-search
api_key: 你的密钥在这里填写
count: 5
```

云端混合模式在同一文件的 `cloud` 段配置（公开模板里 api_key 为空）：

```yaml
cloud:
  enabled: false
  base_url: https://api.deepseek.com
  api_key: ""          # 填自己的云端密钥，仅本地保留
  model: deepseek-chat
  roles: [planner, executor, reviewer]
```

### 7.2 行尾与编码治理

- `.gitattributes` 规定 `*.bat` / `*.cmd` 按二进制处理（`-text`），Git 绝不改动其编码与换行，避免他人下载后 cmd 解析失败；
- `*.py` / `*.md` / `*.yaml` 统一 LF，`*.ps1` 用 CRLF；
- 不要用编辑器另存 bat 文件，以免破坏编码与换行。

### 7.3 更换模型与参数

- 模型的提示词、生成长度、循环上限等集中在 `core.py`，各角色均配置了 `num_predict` 上限防止生成失控；
- 各模型的导入配方在 `model_warehouse/<模型>/Modelfile`，更换 GGUF 后重新 `ollama create` 即可。

---

## 8. 目录结构

```
足智多谋/
├─ core.py / chat.py / webui.py        # 编排核心 / 终端入口 / Web 入口
├─ tools.py / my_tools.py              # 内置工具 / 插件空间
├─ memory.py / kb.py                   # 长期记忆 / 知识库 RAG
├─ download_models.py                  # 六模型一键下载器
├─ models.yaml.example / requirements.txt
├─ model_warehouse/                    # 模型源文件与导入配方（权重不入库）
│   ├─ bge-m3/ deepseek-r1-8b/ internlm3-8b/
│   ├─ qwen2.5-7b/ qwen2.5-coder-7b/ spark-x2.5-4b/
│   └─ import_model.ps1 等辅助文件
├─ docs/banner.png                     # 文档配图
├─ 启动.bat / 安装部署.bat / 打包到U盘.bat / 一键卸载.bat
├─ README.md / README.en.md / VERSION.md
├─ 系统说明书.md / 技术架构.md / 无模型库部署教程.md / CHANGELOG.md
├─ .gitattributes / .gitignore / LICENSE
└─ release/                            # 发布产物（不入库）
```

---

## 9. 二次开发

### 9.1 增加一个新工具

在 `my_tools.py` 中编写一个 `@tool` 装饰的函数，加入 `TOOLS_EXTRA` 列表，保存即自动生效，无需改动核心代码；函数的 docstring 就是给模型看的使用说明。

### 9.2 增加一个新模型

1. 把 GGUF 放入 `model_warehouse/<新目录>/`，参照现有 Modelfile 写好导入配方；
2. 运行 `ollama create` 注册；
3. 在 `core.py` 中把对应岗位指向新模型名。
- 注意 8GB 显存约束：同一时刻只加载一个 7–9B Q4 模型，多模型靠 Ollama 串行切换。

### 9.3 训练与升级

- 本系统定位为**本地推理与编排**，8GB 显存不支持从零预训练或全参微调；
- 升级模型的实际做法是替换为更高版本或更强量化的开源 GGUF，再重新导入；
- 若需领域适配，可在显存允许时考虑 LoRA 等参数高效微调，或直接用知识库 RAG 注入领域资料（成本更低、可随时更新）。

---

## 10. 卸载

双击项目目录中的 **`一键卸载.bat`**，输入 `YES` 确认：删除 Ollama 中本系统的六个模型与整个项目文件夹，但**不会**卸载 Python 和 Ollama 本身；输入其他任何内容则取消。

---

## 11. 常见问题

| 问题 | 解决办法 |
|---|---|
| `ollama create` 报找不到模型文件 | 确认 GGUF 已放入 `model_warehouse` 对应子目录 |
| 激活虚拟环境报"禁止运行脚本" | 执行 `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force` |
| Web 界面打不开 | 确认 8765 端口未被占用，或改用终端版 |
| 双击 bat 报"不是内部或外部命令" | 确认仓库含 `.gitattributes`，不要用编辑器另存 bat |
| 模型生成失控、输出不停 | 检查 `core.py` 中各角色 `num_predict` 上限 |
| 联网搜索无结果 | 确认 `models.yaml` 中 API 密钥正确 |

更多排障细节见 [系统说明书.md](系统说明书.md) 与 [CHANGELOG.md](CHANGELOG.md)。

---

## 12. 许可证与署名

本项目代码采用 **[MIT 许可证](LICENSE)**，可自由使用、修改与分发；各模型另有独立许可，分发前请分别确认。

| 参与方 | 昵称 | 职责 |
|---|---|---|
| DeepSeek | 谋士（MoShi） | 系统架构、框架与代码原作、维护 |
| 豆包 | 匠师（JiangShi） | 初始部署、故障诊断、GitHub 发布与行尾/可复刻治理 |

<div align="center">

仓库地址：https://github.com/ImDOGGOD/-

—— 足智多谋团队，2026-11-02

</div>
