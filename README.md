# notion_ext

Notion 扩展工具，一个常驻服务：

- **HTTP 服务** — 提供 `/calendar.ics` 端点，供 Apple Calendar 订阅 Notion 任务
- **定时日报** — 按配置的 cron 时间，自动查询 Notion + macOS 提醒事项，发送钉钉日报

## 安装

```bash
cd /path/to/notion_ext
pip install -r requirements.txt
cp .env.example .env   # 编辑填入你的配置
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
- 定时任务按 cron 配置自动执行日报（默认每半小时，10:00-22:30）

### macOS 开机自启（LaunchAgent）

将服务注册为 LaunchAgent，登录后自动启动、崩溃自动重启：

```bash
# 安装
ln -sf /path/to/notion_ext/com.notion-ext.plist \
       ~/Library/LaunchAgents/com.notion-ext.plist
launchctl load ~/Library/LaunchAgents/com.notion-ext.plist
```

常用管理命令：

```bash
launchctl start com.notion-ext    # 启动
launchctl stop com.notion-ext     # 停止
launchctl unload ~/Library/LaunchAgents/com.notion-ext.plist  # 卸载
launchctl list | grep notion-ext               # 查看状态
```

```bash
launchctl kickstart -k gui/$(id -u)/com.zhouhuaifeng.notion-ext
````

## 项目结构

```
notion_ext/
├── .env / .env.example       # 环境变量配置
├── pyproject.toml             # 项目元数据 + 依赖
├── requirements.txt
├── run_cron.sh                # 启动脚本（设置代理等环境变量）
├── read_reminders.jxa         # macOS 提醒事项 JXA 脚本
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
| `ICS_OUTPUT_PATH` | ICS 文件保存目录 | |
| `ICS_AUTO_PUSH_GIT` | 自动 git push | `false` |
