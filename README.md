# notion_ext

Notion 扩展工具，一个常驻服务：

- **HTTP 服务** — 提供 `/calendar.ics` 端点，供 Apple Calendar 订阅 Notion 任务
- **客户端数据接口** — 提供 `/report/overlay` 和 `/report/text`，供本地 macOS 悬浮窗客户端读取
- **定时日报** — 按配置的 cron 时间，自动查询 Notion + macOS 提醒事项，发送钉钉日报

## 安装

```bash
cd /path/to/notion_ext
pip install -r requirements.txt
cp .env.example .env   # 编辑填入你的配置

# macOS：编译提醒事项读取工具（EventKit，不会在程序坞拉起「提醒事项」应用）
(cd read_reminders_cli && swift build -c release)
```

## 使用

```bash
# 启动服务（HTTP + 定时日报）
python -m notion_ext

# 手动执行一次日报（调试用）
python -m notion_ext report
```

启动后：
- HTTP 服务监听端口（默认 33189），Apple Calendar 订阅 `http://IP:33189/calendar.ics`
- 本机客户端可读取 `http://127.0.0.1:33189/report/overlay`
- 定时任务按 cron 配置自动执行日报（默认每半小时，10:00-22:30）

### macOS 悬浮窗客户端

仓库新增了一个原生 macOS 客户端包：`notion_overlay_app/`

```bash
cd notion_overlay_app
swift run
```

客户端特性：

- 毛玻璃悬浮窗，支持拖拽移动和窗口缩放
- 全局快捷键切换显示/隐藏
- 全局快捷键切换“所有桌面置顶”
- 菜单栏入口、设置页、透明度和材质调节
- 自动轮询 `/report/overlay` 展示与钉钉一致的日报内容

说明：

- 推荐在 Xcode 中打开 `Package.swift` 作为 macOS App 包进行调试与归档。
- 登录自启动依赖 `.app` 形态；若直接通过 `swift run` 运行，设置页会给出提示。

### macOS 开机自启（LaunchAgent）

将服务注册为 LaunchAgent，登录后自动启动、崩溃自动重启：

```bash
# 推荐：使用项目自带脚本一键安装/重载（会自动 kickstart 立即生效）
cd /path/to/notion_ext
./notion_ext_launchagent.sh
```

常用管理命令（脚本版）：

```bash
./notion_ext_launchagent.sh reload     # 改了 plist 后重载并 kickstart
./notion_ext_launchagent.sh unload     # 卸载（不删除 ~/Library/LaunchAgents 下的链接）
./notion_ext_launchagent.sh disable    # 彻底停掉并禁止自动拉起（推荐用于排障/停用）
./notion_ext_launchagent.sh kickstart  # 强制重启任务
./notion_ext_launchagent.sh status     # 查看状态
./notion_ext_launchagent.sh help       # 帮助
```

如果你遇到“kill 之后马上又起来”的情况，通常是 LaunchAgent 的 `KeepAlive` 在拉起。直接执行：

```bash
cd /path/to/notion_ext
./notion_ext_launchagent.sh disable
```

执行后会做三件事：`bootout` 当前任务、`disable` 该 Label、删除 `~/Library/LaunchAgents` 下的链接，从而彻底停止自动重启。

说明：

- `notion_ext_launchagent.sh` 会自动解析当前项目路径（基于脚本所在目录），避免项目移动/改名后 plist 仍指向旧路径导致启动失败。
- 如需手工排障，可直接使用 `launchctl`，脚本内部等价于执行 `ln -sf`、`launchctl unload/load` 和 `launchctl kickstart` 等操作。
- 对外发布仓库时建议仅保留 `com.zhouhuaifeng.notion-ext.plist.example`，并在本机复制为 `com.zhouhuaifeng.notion-ext.plist` 后将 `__PROJECT_ROOT__` 替换为实际项目路径。

## 项目结构

```
notion_ext/
├── .env / .env.example       # 环境变量配置
├── pyproject.toml             # 项目元数据 + 依赖
├── requirements.txt
├── notion_ext_launchagent.sh   # macOS LaunchAgent 管理脚本
├── run_cron.sh                # 启动脚本（设置代理等环境变量）
├── read_reminders_cli/        # macOS 提醒事项 Swift CLI（EventKit）
└── notion_ext/                # Python 包
    ├── __main__.py            # 入口：启动 HTTP 服务 + 定时任务
    ├── config.py              # 共享配置
    ├── models.py              # 数据模型
    ├── notion_api.py          # Notion API 共享基础
    ├── report/                # 日报功能
    │   ├── queries.py         # Notion 查询（今日 + 本周）
    │   ├── dingtalk.py        # 钉钉消息发送
    │   ├── formatter.py       # 日报消息格式化
    │   ├── reminders.py       # macOS 提醒事项读取
    │   └── notify.py          # macOS 系统通知
    └── calendar/              # 日历同步功能
        ├── queries.py         # Notion 查询（最近一个月）
        ├── ics_generator.py   # 生成 .ics 文件
        ├── git_push.py        # Git 自动推送
        ├── notion_updater.py  # 更新默认页面时间
        └── server.py          # HTTP 服务器
```

## 环境变量

在 `.env` 中配置（参考 `.env.example`）：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NOTION_TOKEN` | Notion API token（必填） | |
| `NOTION_TODAY_DB_ID` | 今日 todo 数据库 ID（必填） | |
| `NOTION_WEEK_DB_ID` | 本周任务数据库 ID（必填） | |
| `NOTION_DEFAULT_PAGE_ID` | 默认页面 ID，心跳更新 | |
| `DINGTALK_WEBHOOK` | 钉钉 webhook URL | |
| `DINGTALK_SECRET` | 钉钉加签密钥 | |
| `CALENDAR_SERVER_PORT` | HTTP 端口 | `33189` |
| `REPORT_CRON_MINUTE` | 日报执行分钟 | `0,30` |
| `REPORT_CRON_HOUR` | 日报执行小时 | `10-22` |
| `TZ` | 时区 | `Asia/Shanghai` |
| `NOTION_EXT_REMINDERS_CLI` | 提醒事项 CLI 可执行文件路径（可选，默认用 `read_reminders_cli` 编译产物） | |
| `ICS_OUTPUT_PATH` | ICS 文件保存目录 | |
| `ICS_AUTO_PUSH_GIT` | 自动 git push | `false` |
