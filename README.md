# notion_ext

查询 **Notion 数据库**（今日 todo + 本周任务）和 **macOS 提醒事项**，汇总后发送到钉钉。可选 Mac 本地通知「当前任务 + 剩余时间」。

## 安装

```bash
cd /path/to/notion_ext
pip install -r requirements.txt
```

## 使用

```bash
# 确保环境变量已设置（或 source env.sh）
python -m notion_ext
```

## 项目结构

```
notion_ext/
├── pyproject.toml          # 项目元数据 + 依赖
├── requirements.txt
├── env.sh                  # 定时任务用环境变量
├── run_cron.sh             # cron 包装脚本
├── read_reminders.jxa      # macOS 提醒事项 JXA 脚本
└── notion_ext/             # Python 包
    ├── __main__.py         # CLI 入口 (python -m notion_ext)
    ├── config.py           # 配置常量
    ├── models.py           # 数据模型 (dataclass)
    ├── notion_client.py    # Notion API 查询
    ├── dingtalk.py         # 钉钉消息发送
    ├── reminders.py        # macOS 提醒事项读取
    ├── formatter.py        # 日报消息格式化
    └── notify.py           # macOS 系统通知
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `DINGTALK_WEBHOOK` | 钉钉机器人 webhook URL |
| `DINGTALK_SECRET` | 钉钉加签密钥（可选） |
| `NOTION_TOKEN` | Notion API token（必填） |
| `NOTION_TODAY_DB_ID` | 今日 todo 数据库 ID（必填） |
| `NOTION_WEEK_DB_ID` | 本周任务数据库 ID（必填） |

## 定时任务 (cron)

```bash
chmod +x run_cron.sh

# crontab -e 添加（每半小时，10:00-22:30）：
0,30 10-22 * * * /path/to/notion_ext/run_cron.sh >> /path/to/notion_ext/cron.log 2>&1
```
