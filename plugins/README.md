# 足智多谋 插件规范 v1（v1.6.0）

插件 = 本机信任代码。**只安装你信任来源的插件**；插件拥有与系统同级的 Python/JS 权限。

## 一、目录结构

```
plugins/<插件id>/
    manifest.json   声明（必填）
    plugin.py       服务端（可选）：工具 + 文本后处理器
    plugin.js       前端（可选）：通过 window.ZZDM 挂载 UI
    config.json     运行时配置（自动生成，如 {"enabled": true}）
```

安装方式：把插件文件夹放进 plugins/，重启 Web 界面即生效（工具类需重启，后处理器动态读取配置）。

## 二、manifest.json

| 字段 | 说明 |
|---|---|
| id | 目录同名，唯一 |
| name / version / description | 展示信息 |

## 三、服务端 plugin.py

```python
POST_PROCESSORS = [
    {"id": "xxx", "name": "显示名", "fn": lambda text: text},  # text -> text
]
PLUGIN_TOOLS = []   # langchain @tool 装饰的函数，自动进入 Agent 工具集
```

- 后处理器链：按启用状态依次作用于**每条最终回答**（压缩/翻译/格式转换等）；
- 工具：与 my_tools.py 同规范（docstring 即模型说明书）。

## 四、前端 plugin.js 与插槽

浏览器全局桥 `window.ZZDM`：

```js
ZZDM.addHeaderButton('按钮名', onclick)   // 头部按钮插槽
ZZDM.api(url, opts)                       // fetch 封装（返回 json）
```

插槽清单（v1.6.0）：
- 头部按钮区（addHeaderButton）；
- 消息操作区（每条回答下方，系统自带"复制"按钮；后续版本开放追加 API）。

钩子清单：
- 文本后处理器（服务端，见上）；
- Agent 工具（服务端）。

不开放：流式渲染内部、会话引擎内部（保证系统稳定）。

## 五、API

- `GET /api/plugins`：清单 + 后处理器启用状态；
- `POST /api/plugins/<id>`：`{"enabled": true/false}` 切换开关（写入 config.json）。

## 六、"迂回空间"与安全红线（运营/建号不做功能，只留接口）

- 内容创作：系统内置"文案"模式（起草 → 人工确认 → 复制发布）；
- 平台操作（发帖/回复/私信）：**系统不做**。你可用插件接入①平台官方 API（自备开发者 key，合规）②浏览器自动化（playwright 模板，自带封号风险，须人工监督）；
- 建号/批量运营：**系统不做、不建议做**（实名制法规 + 平台风控 + 验证码不可解）；
- 插件红线：控制电脑/删文件/花钱/自动发布类插件必须自带白名单与人工确认。

## 七、官方示例

`post_compress/`：把回答压缩到约 140 字（后处理器 + 头部开关按钮），完整演示后端钩子、前端插槽与配置读写。
