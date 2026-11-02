# 版本迭代记录（CHANGELOG）

> 系统名称：本地多模型多 Agent 系统（定名"足智多谋"）
> 当前版本：v1.1.4（分工框架 v3；含 GitHub 行尾治理修复）
> 记录区间：2026-10-31 至 2026-11-02
> 参与方：豆包（初始部署、GitHub 发布与行尾治理）、DeepSeek deepseek-v4-pro（检修与框架升级）
> 说明：本文件为详细迭代归档；版本号与简表见 VERSION.md，使用方法见 系统说明书.md。

---

## 版本总览

| 版本 | 日期 | 责任方 | 主题 |
|---|---|---|---|
| v0.1 | 2026-10-31 | 豆包 | 环境搭建与三模型流水线跑通 |
| 检修版 | 2026-11-01 | DeepSeek | 执行策略、权限持久化与缓存清理 |
| 框架 v2 | 2026-11-01 | DeepSeek | 路由分类、快答、多轮上下文、团队身份 |
| 框架 v2+ | 2026-11-01 | DeepSeek | 模型仓库目录化、规划师换型 |
| 框架 v2++ | 2026-11-01 | DeepSeek | 执行者升级 InternLM3、长期记忆库 |
| 框架 v3 | 2026-11-01 | DeepSeek | 三模式分离、代码模型、Agent 工具 |
| v1.0.0 | 2026-11-01 | DeepSeek | 插件空间、联网搜索、打包发布 |
| v1.1.0 | 2026-11-01 | DeepSeek | RAG 知识库、Web 界面、启动器菜单 |
| v1.1.1 | 2026-11-01 | DeepSeek | 查缺补漏、系统定名"足智多谋" |
| v1.1.2 | 2026-11-01 | DeepSeek | bat 中文化、位置自检、无模型库教程 |
| v1.1.3 | 2026-11-01 | DeepSeek | 本地 bat 统一 CRLF、一键卸载 |
| v1.1.4 | 2026-11-01 | DeepSeek | 懒人部署、winget 环境自检 |
| 行尾治理修复 | 2026-11-02 | 豆包 | .gitattributes 强制 CRLF，修复他人下载报错 |

---

## v0.1（2026-10-31，豆包）—— 初始部署

### 新增

- 完成环境核查：i9-13900H、32GB 内存、RTX 4070 Laptop 8GB 显存、F 盘空间确认。
- 建立 Python 虚拟环境 .venv（Python 3.13.5）。
- 安装核心依赖：langgraph、langchain-ollama、langchain-core、pyyaml、modelscope。
- 编写单模型验证脚本 test_single.py，确认 LangGraph→Ollama→模型链路可用。
- 编写三模型协作图 multi_agent.py：规划→执行→审查，含条件退回与最大修订次数。
- 编写交互式流式程序 chat.py（初版）：手动输入、逐字输出、连续提问。
- 编写系统说明书（初版）。
- 首批三个模型：qwen2.5:7b（执行）、spark-x2.5:4b（规划）、deepseek-r1:8b（审查）。

### 问题与修复

- 命令误用：pip 等系统命令被误写进 .py 触发 SyntaxError。
  - 修复：明确系统命令只能在终端执行，.py 只放 Python 代码。
- ollama pull 卡死：主分片停滞、产生 0 字节临时分块。
  - 定位：境外服务器大文件长连接静默停滞。
  - 修复：改用魔搭 ModelScope 国内源，编写 robust_download.ps1（curl 断点续传 + 慢速重连 + 重试循环）。
- 分片 GGUF 导入报错：invalid split GGUF, expected 2。
  - 修复（依据 Ollama 官方文档）：Modelfile 改用通配符 FROM ./模型名-*.gguf。

### 验证

- 单模型返回正常中文；/api/ps 显示 size_vram 全量在显存，nvidia-smi 确认 GPU 占用。
- 三模型协作一次审查通过。

---

## 检修版（2026-11-01，DeepSeek）—— 环境加固

### 修复

- 执行策略未持久化：PowerShell 默认 Restricted 禁止运行脚本。
  - 处理：Set-ExecutionPolicy -Scope CurrentUser RemoteSigned，本地脚本可运行。
- 工作区权限问题修正。
- 清理早期下载遗留的废弃缓存与未完成临时文件。

---

## 框架 v2（2026-11-01，DeepSeek）—— 智能路由

### 新增

- 问题分类路由：元问题 / 简单问题 / 复杂问题区分处理。
- 元问题直达：关于系统自身的问题由编排层直接回答，不调用模型。
- 简单问题快答：跳过审查，缩短响应路径。
- 多轮上下文：保留最近对话供执行者参考。
- 团队身份：动态生成团队介绍，换模型后自动同步。

---

## 框架 v2+（2026-11-01，DeepSeek）—— 仓库目录化

### 变更

- 建立"模型仓库"目录，一个模型一个子目录，各自包含 GGUF、Modelfile、日志。
- 规划师由 spark-x2.5:4b 更换为 qwen2.5:7b。

---

## 框架 v2++（2026-11-01，DeepSeek）—— 执行者升级与长期记忆

### 新增

- 新模型 internlm3:8b，执行者升级为 InternLM3-8B-Instruct。
- 长期记忆库：
  - memory.py：SQLite 存储、关键词检索、模型自动提炼。
  - memory.db：memories（长期记忆）与 turns（问答存档）两张表。
  - 支持 /记住、/回忆、/忘记、/记忆 命令。
  - 复杂问题回答后自动提炼长期记忆。

---

## 框架 v3（2026-11-01，DeepSeek）—— 三模式分离

### 新增

- 三种工作模式分离：
  - general 通用问答：规划→执行→审查闭环。
  - code 代码辅助：使用代码专用提示词与特化模型。
  - agent 工具模式：工具调用循环 + 审查回路，双模型协作。
- 新模型 qwen2.5-coder-7b:q4_k_m，代码辅助专用。
- 工具集 tools.py：计算器、当前时间、读文件、列目录、联网搜索共 5 个工具。
  - 计算器采用 AST 白名单，文件访问限定 F:\AI 目录内。
- 核心逻辑整合至 core.py，统一三模式图构建与流式输出。

### 变更

- 模型角色在 models.yaml 中按模式重新映射。
- 增加 num_ctx、num_predict、max_tool_steps 等参数控制。

---

## v1.0.0（2026-11-01，DeepSeek）—— 发布版本

### 新增

- 插件空间 my_tools.py：自定义工具写入后自动加载，无需改动其他代码；含掷骰子示例。
- 联网搜索接口：接入博查（bocha）搜索，API key 与地址集中在 models.yaml 的 search 段。
- 打包发布：
  - 发布\本地多智能体系统_v1.0.0_便携包.zip（代码、配置、文档、部署脚本）。
  - 安装部署.bat：自动建虚拟环境、装依赖、导入五个模型。
  - 启动.bat：一键运行 chat.py。
- requirements.txt：目标机器依赖清单。
- README.md：跨机器移植与打包说明。
- VERSION.md：版本信息与升级简史。

---

## 模型引入时点

| 模型 | 引入版本 | 最终角色 | 大小 |
|---|---|---|---|
| qwen2.5:7b | v0.1 | 通用规划 / Agent 执行 | 4.36GB |
| spark-x2.5:4b | v0.1 | 早期规划（后调整） | 2.42GB |
| deepseek-r1:8b | v0.1 | 通用与代码审查 | 4.68GB |
| internlm3:8b | 框架 v2++ | 通用执行 / Agent 审查 | 4.99GB |
| qwen2.5-coder-7b:q4_k_m | 框架 v3 | 代码执行 | 4.36GB |

---

## 关键问题解决索引

| 问题 | 解决版本 | 方案 |
|---|---|---|
| 系统命令误写进 .py | v0.1 | 终端与 .py 职责分离 |
| ollama pull 大文件停滞 | v0.1 | ModelScope + curl 断点续传脚本 |
| 分片 GGUF 无法导入 | v0.1 | Modelfile 通配符匹配全部分片 |
| PowerShell 禁止运行脚本 | 检修版 | CurrentUser 设为 RemoteSigned |
| 无长期记忆 | 框架 v2++ | SQLite 记忆库 + 自动提炼 |
| 无法调用外部能力 | 框架 v3 | 工具集 + Agent 工具模式 |
| 无法迁移到其他机器 | v1.0.0 | 便携包 + 部署脚本 |
| 他人下载后 bat 报"不是内部或外部命令" | 行尾治理修复（2026-11-02） | .gitattributes 强制 bat CRLF |

---

## 故障修复：他人下载后 bat 报"不是内部或外部命令"（2026-11-02，豆包）

### 问题现象

他人从 GitHub 下载 ZIP 后双击 bat，cmd 窗口连续报：
`'_python' 不是内部或外部命令`、`'rlevel' 不是内部或外部命令`、`'winget' 不是内部或外部命令` 等，命令被拆成碎片，脚本无法执行。

### 问题为什么产生（根因）

1. 本机 Git 配置 `core.autocrlf=true`：提交时 Git 会把工作区文件的 CRLF 行尾转换成 LF，再写入仓库。
2. 项目首次发布时缺少 `.gitattributes`，没有针对 bat 强制规定行尾。
3. 两者叠加的结果：
   - 本地磁盘工作区的 bat 是 CRLF（v1.1.3 已在本地统一），所以本机运行正常；
   - 但仓库 blob 里实际存的是 LF，GitHub 的 Download ZIP 直接取仓库内容，他人拿到的就是 LF 版本；
   - Windows cmd 无法可靠解析 LF 行尾的批处理，配合括号块、标签和 set /p 时把命令拆碎，产生报错。
4. 责任界定：这不是 DeepSeek 的业务代码逻辑错误，也不是用户操作失误，而是首次发布时 Git 行尾治理（.gitattributes）缺失，属于发布工程问题。

### 操作更改记录（豆包执行）

1. 诊断：用 `git ls-files --eol`、`git show HEAD:文件` 确认仓库 blob 为 LF、工作区为 CRLF，定位行尾不一致。
2. 新建 `.gitattributes`：
   - `*.bat`、`*.cmd` 强制 `text eol=crlf`；
   - `.ps1/.py/.md/.txt/.yaml/.example` 统一 LF；
   - 其余文件 `* text=auto`。
3. 重新规范化并提交、推送（提交 b50e145）。
4. 实证验证：重新下载 GitHub 实际提供的 ZIP，检查四个 bat 全部为 CRLF、无孤立 LF，编码仍为 GBK（启动.bat 为 UTF-8），与各自 chcp 匹配。

### 署名

- 系统框架与 bat 原始作者：DeepSeek（deepseek-v4-pro）
- 本次故障诊断、.gitattributes 编写、发布与验证：豆包
- 修复后无论他人的 Git 客户端如何配置，下载到的 bat 行尾都由 .gitattributes 保证，不再依赖客户端设置。

---

## 后续可扩展方向（未实现，备忘）

- 视觉能力：接入视觉模型，新增读图 / OCR 工具。
- 文档解析：支持 PDF、Office 文件读取与总结。
- 状态持久化升级：基于检查点的中断恢复与回溯。
- 人机协同：高风险节点人工确认后再继续。
- 模型微调：QLoRA 领域微调后转 GGUF 导入。
- 视频生成等重能力：以工具形式封装外部 API，本地不承载。

---

## 可复刻性修复（2026-11-02，豆包）—— 提交 9c58e45

### 背景

核查"他人能否仅凭仓库文件复刻整套系统"，发现若干写死路径与文件误排问题，会导致他人部署失败。

### 发现的问题

1. 致命：`.gitignore` 中 `模型仓库/` 整行把整个目录排除，导致 6 个 Modelfile（导入配方）、import_model.ps1 与说明文件未上传；而安装部署.bat 依赖这些文件，他人执行 `ollama create -f Modelfile` 会全部失败。
2. 跨机器硬伤：tools.py 写死 `ALLOWED_ROOT = Path(r"F:\AI")`，他人部署到其他路径时文件工具全部拒绝。
3. 下载脚本写死路径：download_coder/bge/internlm3/gguf.py 与 download_r1/spark/robust_download.ps1 的输出目录写死 `F:\AI\local\gguf`，换路径即失效。
4. 文档过时：无模型库教程便携包版本号停留在 v1.1.1；requirements.txt 注释版本号过时。

### 操作更改记录（增量，未删改历史内容）

1. `.gitignore`：删除 `模型仓库/` 整行，改由 `*.gguf` 排除权重、`*.log` 排除日志，目录内小文件正常纳入。
2. tools.py：`ALLOWED_ROOT` 改为 `Path(__file__).resolve().parent`，同步更新 docstring 与注释。
3. 4 个 Python 下载脚本：输出目录改为基于 `__file__` 的 `gguf` 子目录。
4. 3 个 PowerShell 脚本：`$outdir` 改为 `Join-Path $PSScriptRoot "gguf"`。
5. 无模型库教程便携包更新为 v1.1.4；requirements.txt 注释更新为 v1.1.4。

### 验证结果（实证）

- 全部改动 Python 文件通过 `py_compile` 语法检查。
- tools.py 路径逻辑验证：ALLOWED_ROOT 随项目位置动态推导，相对路径正确解析。
- 重新下载 GitHub 实际 ZIP：共 47 个条目，6 个 Modelfile 齐全、0 个 GGUF 权重、import_model.ps1 在位。

### 署名

- 系统框架与脚本原始作者：DeepSeek（deepseek-v4-pro）
- 本次可复刻性核查、修复与验证：豆包

---

## 技术架构文档与开源许可（2026-11-02）—— 提交 d5f4519

### 新增

1. 技术架构.md（开源复刻指南，DeepSeek 原作，共 12 章）：项目定位、分层架构、关键依赖、模型清单与角色、编排核心（三图机制与事件流）、调参坑位、数据层、工具与插件、Web 前端、一次提问数据流、从零复刻步骤、目录结构、开源许可提示。
2. 豆包增量追加第 13 章（原文未改动）：2 处勘误（文件工具路径动态化、models.yaml 仅 example 入库）与 3 项开源工程补充（LICENSE、.gitattributes/.gitignore、SSH 备用通道）。
3. LICENSE：采用 MIT 许可证，版权行署名"足智多谋 (ImDOGGOD)"，明确授权自由使用、修改与分发。
4. README.md 与系统说明书.md 加入对技术架构.md 的引用。

### 说明

- 期间 GitHub 直连多次临时阻断，最终在直连恢复后通过 HTTPS 推送成功；本地提交始终保存未丢失。

### 署名

- 技术架构文档原始作者：DeepSeek（deepseek-v4-pro）
- 第 13 章勘误补充、MIT LICENSE 创建与发布：豆包

---

## 署名 / 昵称对照（2026-11-02 增量标注，历史署名不删改）

自 v1.2.0 起，两位参与方启用昵称署名；历史文档中出现的旧称与新昵称为同一参与方，等价对照如下：

| 历史署名 | 新昵称 | 职责 |
|---|---|---|
| DeepSeek（deepseek-v4-pro） | 谋士（MoShi） | 系统架构、框架与代码原作、维护 |
| 豆包 | 匠师（JiangShi） | 初始部署、故障诊断、GitHub 发布与行尾/可复刻治理 |

说明：
- 本对照为增量标注，文档前文已有的"豆包""DeepSeek"字样一律保留原貌，不回填、不替换。
- 自本次提交起，新的更改记录中 DeepSeek 一方署"谋士（MoShi）"，豆包一方署"匠师（JiangShi）"。

---

## v1.2.0（2026-11-02）—— 分发工程加固与文档重构

### 变更（依据 VERSION.md）

1. v1.1.5 GitHub 分发修复：
   - 模型目录由中文"模型仓库"改为英文 `model_warehouse`，发布目录改英文 `release`；
   - bat 全部 ASCII 化，`.gitattributes` 将 bat 按二进制处理（`-text`，Git 绝不改其编码与换行）；
   - 部署脚本自动从 models.yaml.example 生成 models.yaml。
2. v1.1.6 六模型一键下载器：
   - 新增单文件 download_models.py，断点续传、自动重试、全程日志（gguf\download_all.log）；
   - 部署脚本检测到缺模型时交互询问是否立即下载。
3. v1.2.0 说明书大重构：按逻辑顺序重组为六部分加附录（认识 / 部署 / 使用 / 配置 / 技术内幕 / 维护），文末保留按时间版本历史，内容全面加深。
4. 目录结构：旧"模型仓库"整体重命名为 model_warehouse，Git 识别为重命名，历史可追溯；权重（*.gguf）与日志（*.log）继续排除，Modelfile 与说明文件正常纳入。

### 验证

- 全部 Python 文件通过 py_compile 语法检查。
- 暂存清单确认：6 个 Modelfile 随重命名保留，无权重、无日志入库。

### 署名

- 架构、代码与文档重构：谋士（MoShi）
- 发布核查、署名对照与本次发布：匠师（JiangShi）

---

## 发布通道治理：HTTPS 直连改 SSH 免密（2026-11-02）

### 问题

1. 直连 github.com:443 反复临时阻断：TCP 探测偶通，但实际 git push 多次在 21 秒后超时，无法可靠完成传输。
2. 旧私钥 id_ed25519 为加密状态（含 passphrase，用户已无设置印象），非交互环境无法弹出密码输入，导致认证停在最后一步。

### 处理（旧密钥保留不动）

1. 新生成无密码密钥 id_ed25519_np（空 passphrase，已验证私钥头部为 none、无 bcrypt 加密）。
2. 更新 ~/.ssh/config，IdentityFile 指向新密钥；通道仍为 ssh.github.com:443。
3. 将新公钥添加到 GitHub 账号；远程由 HTTPS 切换为 SSH（git@github.com:ImDOGGOD/-.git）。

### 验证

1. 推送成功：2cc00fc..f2fb50a main -> main；GitHub API 核对本地与远程 SHA 完全一致。
2. 重新下载远程实际 ZIP（50 个条目）：6 个 Modelfile、download_models.py、4 个 bat、LICENSE、.gitattributes/.gitignore 均在；权重与日志正确排除。
3. ZIP 内 4 个 bat 全部为 CRLF、无孤立 LF，cmd 可正常解析；.gitattributes 二进制处理策略生效。

### 署名

- 本次通道治理、验证与记录：匠师（JiangShi）

---

## README 重构、英文版与项目配图（2026-11-02）

### 变更

1. README.md 整体重构：扩充为 12 章，含项目简介、核心特性、分层架构、模型清单、快速开始（一键/手动）、使用指南、配置说明、目录结构、二次开发、卸载、FAQ、许可证与署名，逻辑按"认识 → 部署 → 使用 → 配置 → 开发 → 维护"组织。
2. 新增 README.en.md：与中文版对应的完整英文文档，两版互相链接。
3. 新增 docs/banner.png：科技感横幅配图（中央编排节点连接六个模型节点，无文字）；.gitignore 增加 docs 配图例外（`!docs/`、`!docs/*.png`），确保图片入库。

### 署名

- 文档重构、翻译、配图与发布：匠师（JiangShi）

---

## v1.2.1 / v1.2.2（2026-11-02）—— Web 界面改版与主题自定义

### 变更（依据 VERSION.md 与实际代码）

1. v1.2.1 Web 界面改版：黑白极简单色主题（墨黑底、纯白反色、发丝灰线，去除彩色与 emoji）。
2. v1.2.2 主题自定义空间：
   - 四套预设主题：黑白极简、暖纸、深海、墨绿，均由 CSS 变量驱动；
   - 支持背景色、强调色、字号、圆角自定义，通过 localStorage（键 zzdm-theme）持久化，刷新与重开浏览器保留；
   - 右上角"主题"按钮打开面板，含重置功能。
3. 版本号同步：core.py `__version__`、VERSION.md、四个 bat 标题、技术架构/说明书/无模型库教程头部统一更新为 v1.2.2。

### 检查与验证

- 全部 Python 文件通过 py_compile 语法检查。
- 磁盘四个 bat 全部 CRLF、无孤立 LF；.dsh-project-memory 目录自带 .gitignore（`*`）默认本地保留，不入库。
- 文档版本号与功能描述一致，无遗漏。

### 署名

- Web 界面改版与主题功能：谋士（MoShi）
- 发布前检查、记录与推送：匠师（JiangShi）

---

> 记录原则：所有条目以实际部署、文件与验证结果为准；后续每次改动应在此文件追加新版本，不回填、不臆测。
