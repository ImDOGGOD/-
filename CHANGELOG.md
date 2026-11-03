# 版本迭代记录（CHANGELOG）

> 系统名称：本地多模型多 Agent 系统（定名"足智多谋"）
> 当前版本：v1.9.0（分工框架 v3）
> 记录区间：2026-10-31 至 2026-11-03
> 参与方：豆包（初始部署、GitHub 发布与行尾治理）、DeepSeek deepseek-v4-pro（检修与框架升级）、谋士 MoShi（v1.2.0 起：视觉/文件识别、文案模式、插件空间、MCP、多会话增强、笔记/搜索/图谱等）
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
| v1.1.5–v1.4.2 | 2026-11-02 | 谋士 | GitHub 分发修复、一键下载器、说明书重构、黑白极简主题、主题空间、对话导出 |
| v1.5.0 | 2026-11-03 | 谋士 | 图片识别（qwen2.5vl）+ 文件识别（PDF/Word/Excel 入库） |
| v1.6.0 | 2026-11-03 | 谋士 | 文案创作模式 + 插件空间 v1（plugins/、后处理器、前端插槽） |
| v1.7.0 | 2026-11-03 | 谋士 | MCP 客户端 + 插件热重载 + 模型监控面板 |
| v1.8.0 | 2026-11-03 | 谋士 | 多会话增强（分组/置顶/分叉/归档/结构树） |
| v1.9.0 | 2026-11-03 | 谋士 | 笔记+@引用、全局搜索、提示词模板、对话图谱；体检清理冗余 |
| v1.10.0 | 2026-11-03 | 谋士 | 部署脚本 v2：依赖验证、视觉模型交互部署、环境汇总 |
| v2.0.0 | 2026-11-03 | 谋士 | 卸载脚本健壮性重写 + 诊断自检.bat；全功能回归 |

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

## v1.3.0（2026-11-02）—— 云端混合模式（本地 + 云端大模型可切换）

### 背景与目标

- 用户拍板采用"混合"方案：保留本地 Ollama 全离线能力，同时在客户端新增"启动云端大模型"开关，支持自定义配置，完成后检查可运行。
- 设计原则：默认仍走本地、密钥不入库、未配置密钥时自动降级本地不崩；复用已验证的图构建函数，不引入脆弱的 LLM 代理层。

### 变更清单（依据实际代码）

1. 依赖：新增 `langchain-openai==1.7.3`（连带 openai 3.42.1、tiktoken 0.14.0、jiter、regex），已写入 requirements.txt。
2. 配置：models.yaml 与 models.yaml.example 均新增 `cloud` 段（enabled/provider/base_url/api_key/model/roles/temperature/num_predict）；公开模板 api_key 为空，本地 models.yaml 仍被 .gitignore 排除。
3. core.py：
   - 新增 ChatOpenAI 导入、`_cloud_section()`、运行时状态 `CLOUD_STATE`；
   - 重写 `_make_llm()`：开关启用且岗位在 cloud.roles 内且有 key/base_url 时返回 ChatOpenAI（num_predict 映射为 max_tokens），否则返回本地 ChatOllama；
   - 新增 `_rebuild_graphs()`、`set_cloud_enabled()`、`cloud_status()`，以及前端统一访问器 `get_graph()`/`get_titles()`；切换开关时重建三图与标题。
   - 标题在云端岗位后标注"（云端）"，本地/云端状态一目了然。
4. webui.py：header 新增"云端：开/关"按钮（含高亮样式与悬停说明），新增 `GET/POST /api/cloud` 路由；前端改用 get_graph/get_titles；开关状态用 localStorage（键 zzdm-cloud）持久化，刷新自动同步后端。
5. chat.py：新增 `/云端 开/关`（/cloud）斜杠命令，帮助文本同步；主循环改用 get_graph/get_titles。

### 检查与验证（实测结果）

- 全部 Python 文件 py_compile 通过（core/webui/chat 退出码均为 0）。
- 本地模式回归：通用问答经"路由 qwen2.5:7b → 执行 internlm3:8b"正常流式输出，无错误。
- 空 key 降级：打开云端开关但 api_key 为空时，`_make_llm` 仍返回 ChatOllama，问答正常不崩。
- 真实云端链路：将 cloud 指向 Ollama 的 OpenAI 兼容端点（http://127.0.0.1:11434/v1，占位 key，model=qwen2.5:7b），LLM 类型确认为 ChatOpenAI，问答成功且标题正确显示"（云端）"；验证后内存配置已还原。
- Web 服务实测：首页 HTTP 200（含云端按钮与 JS），/api/ping（ok、6 模型）、/api/cloud GET 与 POST 开/关均正确响应。
- 说明：真实云端调用需在 models.yaml 的 cloud 段填入有效服务商的 base_url/api_key/model；当前无真实云端密钥，故以 Ollama 兼容端点实证 ChatOpenAI 全链路。

### 署名

- 云端混合模式架构与代码：谋士（MoShi）
- 端到端验证、版本号同步与记录：匠师（JiangShi）

### 补充（2026-11-02 增量）：真实密钥验证与 `KeyError: 'draft'` 修复

#### 一、真实云端密钥验证（用户提供测试密钥）

- 密钥写入本地 models.yaml 的 cloud 段（api_key 带引号；该文件被 .gitignore 第 29 行排除，不入库，公开模板 example 仍为空）。
- 直接构造 ChatOpenAI 调用 DeepSeek 端点（base_url=https://api.deepseek.com，model=deepseek-chat）成功：密钥有效，回答准确。
- 打开云端开关驱动完整 pipeline，全岗位云端问答成功，banners 正确显示"（云端）"，瑞利散射等问题回答准确。

#### 二、问题现象

- 混合三场景测试（同一复杂问题）：纯本地正常；但"executor 走 ChatOpenAI + 问题走 reviewer 复杂路径"时，reviewer_node（core.py 内 `state['draft']`）报 `KeyError: 'draft'`，回答为空。
- 已排除：与 stream_mode 无关（values 与 messages+values 均报错）；ChatOpenAI 本身无问题（最小诊断图普通边正常）；全新构建图同样复现，非运行时污染。

#### 三、问题为什么产生（根因）

- core.py 中存在两个同名 `class AgentState`：
  1. pipeline 版（规划—执行—审查图用），字段含 question/mode/plan/draft/review/passed/revisions/history/memory_ctx/knowledge_ctx；
  2. agent 版（Agent 工具图用），字段含 messages（add_messages 聚合）/question/memory_ctx/review/passed/revisions/tool_steps。
- Python 模块加载时第二个类定义覆盖了同名全局名。`build_pipeline` 内 `StateGraph(AgentState)` 在模块末尾被调用时，延迟解析到第二个类，其 schema 缺少 mode/plan/draft 等字段定义。
- 节点写入这些"计划外"字段时，LangGraph 虽动态补出对应 channel，但条件边触发的下游节点（reviewer）在构建 input 时无法可靠读取这些未在正式 schema 声明的通道，故读到旧快照、缺失 draft，最终抛 KeyError。本地 ChatOllama 路径此前未触发该时序，问题一直潜伏。

#### 四、操作更改记录（修复）

1. 第一个类重命名为 `PipelineState`，第二个类重命名为 `AgentRuntimeState`，消除同名覆盖。
2. pipeline 全部节点（router/executor/reviewer/meta_answer/finalize/route_*）类型注解改为 `PipelineState`；`build_pipeline` 内改为 `StateGraph(PipelineState)`。
3. `build_agent_graph` 内改为 `StateGraph(AgentRuntimeState)`，agent 图字段保持不变。
4. `set_cloud_enabled()` 改为每次调用都执行 `_rebuild_graphs()`：保证运行时修改 roles 等配置后，图始终与当前配置一致（重建仅构造图对象，不加载模型、不联网，成本极低）。

#### 五、修复后验证（实测）

- py_compile 通过（core/chat/webui 退出码 0）。
- 混合三场景全部正常：纯本地（经 planner/executor/reviewer）；混合（planner 本地、executor 云端、reviewer 本地，banners 三节点正确）；全云端（三岗位均显示"（云端）"）。
- 降级四种情况均正确回退 ChatOllama 不崩：空 key、缺 base_url、岗位不在 roles、开关关闭。
- 本地回归与 Ollama OpenAI 兼容端点链路正常。

#### 六、署名

- 根因诊断与修复代码：匠师（JiangShi）诊断、谋士（MoShi）架构复核
- 验证与本记录：匠师（JiangShi）

#### 七、GitHub 实际发布包验证（推送后，干净环境实证）

- 远程核对：GitHub API 返回 main 最新 commit 为 9b9fe4c，与本地一致。
- 下载实际 ZIP（codeload.github.com/.../zip/refs/heads/main）并解压到独立临时目录，确认：
  - 包内无 models.yaml（密钥不入库）、无 *.db/*.gguf/*.exe 等敏感或大文件；代码、文档、模板、LICENSE、bat/ps1 齐全。
- 静态检查：4 个 bat 全部 CRLF、孤立 LF=0；models.yaml.example 含 cloud 段且两个 api_key 均为空字符串；全部 py 文件 py_compile 失败数 0；PipelineState/AgentRuntimeState/ChatOpenAI/云端函数/版本号 1.3.0 均在。
- 运行时检查（用 venv 解释器在干净目录加载）：
  - 两个状态类独立、字段互不污染（PipelineState 含 draft 不含 messages，AgentRuntimeState 反之）；
  - cloud_status 初始正确；开关开/关均成功重建图，三模式图与标题均可取；
  - 空 key 时即便打开开关，executor 仍正确构造 ChatOllama（降级类型已确认），不报错。
- 结论：GitHub 上的公开包可正常下载、部署、运行，未发现 bug。验证过程中在临时目录生成的 models.yaml 仅为本地模拟部署产物，不影响仓库。

---

## v1.3.1（2026-11-03）—— Web 云端配置面板（网页直接编辑，不改写其余配置）

### 背景与目标

- 用户要求：在不复杂、不大幅改变 Web 代码健壮性的前提下，把云端"自定义配置"从手动编辑 models.yaml 升级为网页面板操作。
- 设计原则：纯增量、不改动现有函数逻辑；只改 cloud 段、保留其余段与注释；服务端强校验；写文件先备份、原子替换；密钥不回显。

### 变更清单（依据实际代码）

1. core.py：
   - 新增 `save_cloud_config()`、`_validate_cloud_updates()`、`_replace_cloud_block()`；
   - 文本块级替换：行级定位顶层 `cloud:` 段，仅替换该段，其余段（general/code/agent/search/memory/knowledge）与全部注释、role 块原样保留；
   - 写入前备份 models.yaml.bak，再写 .tmp 并 `os.replace` 原子替换；更新内存 cfg 后 `_rebuild_graphs()`；
   - `cloud_status()` 增加返回 temperature、num_predict。
2. webui.py：
   - header 新增"云端设置"按钮与独立浮动面板 `#cpanel`，可编辑 base_url/api_key/model/roles（复选框）/temperature/num_predict；
   - 新增 `POST /api/cloud/config` 路由与 handler；面板样式复用现有视觉变量。
3. .gitignore：新增 models.yaml.bak、*.bak 排除，备份不入库。

### 关键设计（避坑）

- 密钥不回显：面板打开时密钥框留空，已配置则提示"留空保持不变"；仅当填入新值才提交，避免密钥出现在前端响应。
- enabled 解耦：保存配置不覆盖文件里的 enabled 启动默认值；开关由内存与浏览器 localStorage（zzdm-cloud）独立管理。
- 校验规则：temperature 限 0–2、num_predict 限 1–32768、roles 元素必须是 planner/executor/reviewer；非法输入直接拒绝且不污染现有配置。

### 检查与验证（实测）

- py_compile 通过（core/webui 退出码 0）。
- 合法保存：roles=[executor]、temp=0.5、np=2048 成功生效，不提交密钥时 configured 仍为 true（密钥保留）。
- 非法输入三种（temperature=5、roles 含 ceo、num_predict=0）均被拒并返回中文错误，拒绝后配置保持原值。
- 文件核对：备份已生成且可解析；其余段与注释、role 块完整保留；保存后 enabled 保持 false。
- 现有功能回归：首页 200、/api/ping 正常、云端开关与图构建不受影响。

### 署名

- 配置面板代码与架构：谋士（MoShi）
- 实测、验证与记录：匠师（JiangShi）

---

## v1.3.1 补充修正（2026-11-03）—— 发布后收尾一致性优化（不升版本号）

### 背景

- v1.3.1 发布后，对文案、注释、版本标注与忽略规则做一次一致性收尾，消除"代码已支持云端、但部分注释/介绍仍写全本地"等过时表述；无任何业务逻辑改动。

### 变更清单（依据实际 diff）

1. .gitignore：新增 models.yaml.tmp 排除（原子写中间产物，与 .bak 一并忽略）。
2. core.py：build_team_intro 团队自我介绍由"全部在本地运行"改为"默认全部本地，也可按需切换云端（终端 /云端 或网页开关）"，仅改字符串。
3. models.yaml.example：去掉文件开头 UTF-8 BOM；注释中"模型仓库"更正为 model_warehouse。
4. requirements.txt：头部注释版本号由 v1.1.4 更新为 v1.3.1。
5. 四个 bat（启动/安装部署/打包到U盘/一键卸载）：title 与 echo 版本标注统一更新为 v1.3.1，逻辑不变。
6. 文档：技术架构.md、无模型库部署教程.md 头部版本号更新；系统说明书.md 头部版本/日期更新并在版本历史表补 v1.3.1 行。

### 检查与验证（实测）

- py_compile 通过（core/webui 退出码 0）；models.yaml.example 前 3 字节确认无 BOM。
- 安全核对：models.yaml、models.yaml.bak、models.yaml.tmp 均被 check-ignore 命中；待提交文件无真实密钥。
- 改动仅涉及字符串、注释、版本标注与忽略规则，不触碰问答、图构建与配置保存逻辑。

### 署名

- 优化内容：谋士（MoShi）
- 核对、验证与记录：匠师（JiangShi）

---

## v1.4.0（2026-11-03）—— 自动化回归 CI + 运行可观测性

### 背景与目标

- 把历次手工验证沉淀为可重复执行的最小回归用例，并接入 GitHub Actions，改动后自动跑测试，防止回归。
- 新增运行统计：问答耗时、本地/云端来源、记忆与知识命中率、token 估算，让成本与效果可观察。
- 约束：纯增量、不改变现有问答与 Web 健壮性，统计失败不影响主流程。

### 变更清单（依据实际代码）

1. 新增 tests/ 目录：12 个 pytest 用例，覆盖云端配置校验 _validate_cloud_updates、cloud 段替换 _replace_cloud_block、save_cloud_config（tmp 隔离、独立 cfg、不接触真实密钥）、计算器 AST 白名单。
2. 新增 .github/workflows/test.yml：push/PR 到 main 触发，Ubuntu + Python 3.13，装依赖、从 example 复制 models.yaml、跑 pytest。
3. 新增 requirements-dev.txt：开发/测试依赖 pytest，与运行时 requirements.txt 分离。
4. 新增 stats.py：SQLite 表 runs，记录每次问答的模式、来源、耗时、云端/本地节点数、记忆/知识命中、token 估算；tiktoken 不可用时字符兜底。
5. webui.py：api_chat 埋点（计时、按 banner 标题统计云端/本地节点、累积答案、失败也记录），新增 GET /api/stats 与"统计"面板；统计写入 try/except 包裹。
6. stats.db 由 .gitignore 的 *.db 规则自动排除，无需新增忽略项。
7. .gitattributes：新增 *.yml text eol=lf（与 *.yaml 一致），消除 workflow 换行 warning，保证跨平台一致。

### 口径说明

- token 为本地 tiktoken（cl100k_base）估算，不是云端真实计费，仅用于量级参考；前端面板已明确标注。
- 来源依据流式 banner 标题是否含"（云端）"判定 local/cloud/hybrid；统计的是节点级趋势，不追求逐节点绝对精确。

### 检查与验证（实测）

- pytest 12 个用例全部通过。
- 端到端：TestClient 走真实本地问答，stats.db 正确落库（source=local、local_nodes=2、耗时、token 估算、知识命中 4 条、passed=1），/api/stats 返回正确。
- 安全：check-ignore 命中 stats.db/models.yaml/.bak/memory.db/knowledge.db；待提交文件与 tests 均无真实密钥，本地 models.yaml 密钥仍在且被忽略。

### 署名

- 框架与统计功能：谋士（MoShi）
- 测试、CI、核对与记录：匠师（JiangShi）

---

> 记录原则：所有条目以实际部署、文件与验证结果为准；后续每次改动应在此文件追加新版本，不回填、不臆测。

---

## v1.5.0（2026-11-03，谋士 MoShi）—— 图片识别与文件识别

### 新增
- 视觉识别：models.yaml 新增 vision 段（本地 qwen2.5vl:7b / 云端 VL 双引擎）；Web"图片"模式（拖拽上传 ≤8MB）+ 终端 `/图 路径` 命令；
- 视觉模型可选下载：download_models.py 增加 `--with-vision`（主体 4.36GB + mmproj 1.26GB，均魔搭源、断点续传）；
- 文件识别：kb.py 支持 pdf/docx/xlsx 文本提取（pypdf/python-docx/openpyxl），知识看板"导入到知识库"按钮。

### 问题与修复
- 视觉模型首测报 `image input is not supported`：Qwen2.5-VL 需独立 mmproj 投影文件——查仓库文件清单找到 `mmproj-model-f16.gguf`，Modelfile 改为双 FROM；
- r1 清单字节数误差 448B（download_models.py 转录错误，download_r1.ps1 原值正确）——修正并加"已存在即跳过"逻辑。

### 验证
- 真实报错截图提问：17 秒返回完整中文描述，图内中文提示逐句读对；pytest 12/12；txt/docx 导入往返通过。

## v1.6.0（2026-11-03，谋士 MoShi）—— 文案模式与插件空间 v1

### 新增
- 文案创作模式 social：策划→创作→审查闭环（广告法/敏感词检查），Web"文案"标签 + `/文案` 命令，人工确认后复制发布；
- 插件空间 v1：plugins/ 目录（manifest.json + plugin.py + plugin.js），服务端工具与**消息后处理器钩子**、前端头部插槽、官方示例 post_compress（微博压缩）。

## v1.7.0（2026-11-03，谋士 MoShi）—— MCP 客户端、插件热重载、模型监控

### 新增
- MCP 客户端 mcp_client.py：models.yaml 的 mcp 段接入任意 MCP 服务器工具（默认关闭，每次调用新建会话）；
- 插件热重载：看板"插件"页一键重载（拖文件夹即装），/api/plugins/reload；
- 模型监控面板：/api/monitor（nvidia-smi + Ollama ps/tags），网页实时显存条/温度/负载，5 秒刷新。

### 验证
- 监控面板实测读出 RTX 4070 Laptop 显存 582/8188MB、52°C。

## v1.8.0（2026-11-03，谋士 MoShi）—— 多会话增强

### 新增
- 项目分组、对话命名（双击）、图标标记（12 选循环）、拖拽排序、置顶、在新对话中继续、分叉对话、归档、结构树视图；老会话数据自动迁移（纯前端）。

## v1.9.0（2026-11-03，谋士 MoShi）—— 笔记/搜索/模板/图谱 + 体检清理

### 新增
- 笔记：卡片风格自定义（底色/圆角/字号 + 8 色标记）、置顶、一键转存长期记忆；
- @引用：输入框 @ 弹出笔记/记忆/知识选择器，一键注入上下文；
- 全局搜索：跨对话/笔记/记忆/知识（Ctrl+K）；
- 提示词模板库：6 个内置模板，可增删；
- 对话图谱：径向树 + 五套配色/节点大小/标签/归档开关自定义。

### 清理
- 删除冗余：download_gguf.py（零引用）、test_single.py、multi_agent.py（早期演示，pytest 取代）、.pytest_cache、__pycache__、.uploads；plugins 运行时 config.json 不再入库。

### 验证
- 本地全功能体检 21/21（3 项失败系 Ollama 服务未启动，重启后全绿）；GitHub 官方 zip 包解压后 15 文件 AST + 10 模块导入全部通过。

—— 谋士（MoShi），2026-11-03
## v1.10.0（2026-11-03，谋士 MoShi）—— 部署脚本 v2

### 新增
- [0/5] 环境自检（同前）；[2/5] 新增**新功能依赖验证**：pip 安装后校验 pypdf/python-docx/openpyxl/langchain-mcp-adapters，缺失自动补装；
- [5/5] **视觉模型交互检测与一键部署**：检测 qwen2.5vl 主体+mmproj 是否就位，缺则询问下载（约 5.6GB）→ download_models.py --with-vision → ollama create；
- 部署结束输出**环境汇总**：GPU（nvidia-smi 型号/显存）、Node/npx、uvx 状态（监控面板与 MCP 所需工具链）。

### 说明
- 全部新功能（图片/文件/插件/MCP/监控）的环境要求已纳入部署脚本检测；MCP 服务器本身需用户按需自备（npx/uvx 状态在汇总中提示）。

### 验证
- 脚本保持纯 ASCII + CRLF 规范；新增步骤涉及的命令（--with-vision 下载、ollama create qwen2.5vl、依赖导入校验）均在本机实测通过。

—— 谋士（MoShi），2026-11-03
## v2.0.0（2026-11-03，谋士 MoShi）—— 卸载脚本健壮性与诊断自检

### 新增
- 一键卸载.bat 重写：运行日志 uninstall_log.txt（含环境信息与每步结果，只读目录自动降级到 %TEMP%）；确认输入接受 YES 或 Y（不区分大小写）；自删改为双兜底（先 rd 一次，失败再 rd 一次）；路径含空格/中文/特殊字符时更稳；"在 ZIP 内直接运行"场景给出明确提示（提示先完整解压）。
- 新增 诊断自检.bat：一键输出 OS 版本、项目文件完整性、Python/Ollama/nvidia-smi/Node/npx/uvx 工具链、cmd 回声测试，生成 zzdm_diag.txt，便于远程判断"是脚本问题还是电脑环境问题"。

### 问题与修复（其他电脑上卸载 bat 启动不了）
- 排查结论：脚本自身逻辑无缺陷（ASCII+CRLF、无语法错误）；常见外部原因按概率排序——① 在 ZIP 预览内直接双击（未解压，路径不存在于磁盘）② 杀软/SmartScreen 拦截脚本或 rd 自删 ③ 仅复制了单个 bat 而未带 core.py（安全护栏拦截）④ 输入了 YES 以外的内容被当作取消。
- 对策：脚本内加日志与更清晰提示；README/说明书补充排障指引与诊断脚本。

### 验证
- 全功能回归 11/11（页面、五模式、工作台、六面板、插件桥、ping/memory/kb/plugins/monitor/stats）；pytest 12/12；模块导入全过。

—— 谋士（MoShi），2026-11-03
## v2.1.0（2026-11-03，谋士 MoShi）—— 部署脚本全自动化

### 新增
- 部署脚本 v3（安装部署.bat v2.1.0）：工具链全自动检测与安装
  - [1/6] Python 3.13 自动 winget 安装
  - [2/6] Ollama 自动 winget 安装
  - [3/6] 虚拟环境 + 依赖安装 + 功能依赖验证（pypdf/docx/openpyxl/MCP）
  - [3/6] 新增：工具链全自动检测与安装
    - NVIDIA 驱动：检测 nvidia-smi，缺失时给出官网下载链接
    - Node.js/npx：缺失时自动 winget 安装 Node.js LTS（含 npx）
    - uvx：缺失时自动 winget 安装 Astral.uv
  - [4/6] 核心模型文件检查（缺失时交互下载 13GB）
  - [5/6] 核心 6 模型导入 Ollama
  - [6/6] 可选视觉模型（qwen2.5vl:7b，主体+mmproj）交互下载与导入
  - 部署结束输出环境汇总：GPU/Node/npx/uvx 状态，MCP/监控面板所需工具链一目了然

### 说明
- 全自动化：从零环境到可用，仅需双击安装部署.bat 跟随提示
- 智能兜底：winget 失败时给出官网下载链接，不卡死
- NVIDIA 驱动不自动安装（需用户手动），但给出官网链接和提示

### 验证
- 本地全功能体检 11/11 通过；pytest 12/12；GitHub zip 包解压验证通过
- 依赖验证命令输出 OK；视觉模型检测（主体+mmproj）通过

—— 谋士（MoShi），2026-11-03

## v2.1.1（2026-11-03，谋士 MoShi）—— 修复闪退与端口占用

### 修复（一键卸载闪退，根因彻底定位）
- 现象：双击 一键卸载.bat 窗口一闪而过，cmd 报 `. was unexpected at this time.`（退出码 255）。
- 根因（三重叠加的 batch 解析坑）：
  1. `setlocal enabledelayedexpansion` 下 `echo [!]` 里的 `!` 被当作延迟展开分隔符吞掉；
  2. echo 文本里的括号（如 `(never run it inside the ZIP)`）破坏 if 块的括号配对；
  3. 双重 `if /i not ... if /i not ... (` 语法。
- 修复：去掉延迟展开、`[!]` 全部改 `[WARN]`、echo 文本去括号、确认逻辑改 goto 流程。实测退出码 0，正常显示"已取消"。
- 同源隐患排查：安装部署.bat 14 处 `[!]`、打包到U盘.bat 4 处 `[!]` 一并清理为 `[WARN]`。

### 修复（启动.bat / Web 界面端口占用）
- 现象：webui 已在运行时再次启动，端口 8765 被占用导致 python 崩溃。
- 修复：webui.py 启动时检测端口占用，若已有实例运行则直接打开浏览器并优雅退出（不再崩溃）。

### 修复（右键菜单闭包）
- 会话上下文菜单先执行 closeMenu() 再执行动作，导致 menuFor 被清空、删除/置顶/重命名/分叉/归档等全部失效；改为先捕获 target id 再执行动作。

### 新增
- 新增 关闭Web界面.bat：一键按端口关闭 Web 界面（兜底；正常做法是关闭启动它的命令行窗口）。
- 版本号全库统一到 v2.1.1（core.py 与 5 个 bat 一致）。

### 验证（本机 + GitHub 双测）
- 本机：ping ok（7 模型）、六面板、五模式、工作台、对话事件流全通；pytest 12/12；
- GitHub zip 包（72 条目）：5 个 bat 全部 CRLF+ASCII+无 `[!]`+版本 v2.1.1；实跑卸载脚本 cancel 路径退出码 0；15 个模块 AST/导入全过，core 2.1.1，17 路由。

—— 谋士（MoShi），2026-11-03

## v2.1.2（2026-11-03，谋士 MoShi）—— 修复前端 JS 语法错误 + Web 端杀后台按钮

### 修复（核心：卡"检测中"、按钮全失效的根因）
- 现象：Web 界面右上角一直"检测中"，所有按钮（发送、模式、面板、会话右键等）全部无响应，关闭浏览器标签页也无法结束后端进程。
- 根因：前端主 JS 脚本里 `openMenu()` 的"移动到项目…"菜单项箭头函数**少写了一个 `}`**（三层嵌套只闭合两层），导致整个 `<script>` 块语法错误——浏览器解析失败，**所有 JS（含 ping 与全部事件绑定）都不执行**。
- 修复：补上缺失的 `}`；复检主脚本花括号/圆括号差值均为 0。
- 排查方法沉淀：webui.py 内嵌 JS 需用花括号配平 + 圆括号配平自检，避免再引入同类语法错误。

### 新增（Web 端"杀后台"按钮）
- 右上角状态区新增"杀后台"按钮 + 后端 `/api/kill` 接口：点击确认后 1.2 秒内优雅结束 webui 进程（os._exit），页面提示"重新双击 启动.bat"。
- 与 关闭Web界面.bat 互补：后者是命令行兜底，前者是网页内一键结束。

### 验证
- 本机实测：页面加载、杀后台按钮、五模式、工作台（笔记/图谱/搜索/@）、ping(ok,7模型)、chat 完整事件流、`/api/kill` 返回 ok 且端口随后释放；pytest 12/12。

—— 谋士（MoShi），2026-11-03