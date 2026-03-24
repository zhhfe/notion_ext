#!/bin/bash
# 供 crontab 调用：设置代理等环境变量后执行 python -m notion_ext

cd "$(dirname "$0")"

export TZ="${TZ:-Asia/Shanghai}"
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export HTTPS_PROXY="${HTTPS_PROXY:-http://127.0.0.1:7890}"
export HTTP_PROXY="${HTTP_PROXY:-http://127.0.0.1:7890}"
export ALL_PROXY="${ALL_PROXY:-socks5://127.0.0.1:7891}"

[ -f env.sh ] && source env.sh

exec python3 -m notion_ext
