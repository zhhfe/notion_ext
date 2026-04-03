#!/usr/bin/env bash
# notion_ext LaunchAgent：安装 / 重载 / 启停（路径随本脚本所在目录自动解析）
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
LABEL="com.zhouhuaifeng.notion-ext"
PLIST_NAME="${LABEL}.plist"
PLIST_SRC="${ROOT}/${PLIST_NAME}"
PLIST_DST="${HOME}/Library/LaunchAgents/${PLIST_NAME}"
GUI_DOMAIN="gui/$(id -u)"

usage() {
    echo "用法: $(basename "$0") <命令>"
    echo ""
    echo "  install   链 plist 到 ~/Library/LaunchAgents 并 load（已加载则先 unload）"
    echo "  reload    unload 再 load（改 plist 后用这个）"
    echo "  unload    从 launchd 卸载（不删 LaunchAgents 里的链接）"
    echo "  kickstart 强制重启任务（等价于 README 里的 kickstart）"
    echo "  status    launchctl list 里筛 notion-ext"
    echo ""
    echo "项目 plist: ${PLIST_SRC}"
}

ensure_plist() {
    if [[ ! -f "${PLIST_SRC}" ]]; then
        echo "错误: 找不到 ${PLIST_SRC}" >&2
        exit 1
    fi
}

cmd_install() {
    ensure_plist
    mkdir -p "${HOME}/Library/LaunchAgents"
    launchctl unload "${PLIST_DST}" 2>/dev/null || true
    ln -sf "${PLIST_SRC}" "${PLIST_DST}"
    launchctl load "${PLIST_DST}"
    launchctl kickstart -k "${GUI_DOMAIN}/${LABEL}" 2>/dev/null || true
    echo "已安装并加载: ${PLIST_DST}"
}

cmd_reload() {
    ensure_plist
    if [[ ! -L "${PLIST_DST}" && ! -f "${PLIST_DST}" ]]; then
        echo "未找到 ${PLIST_DST}，请先执行: $0 install" >&2
        exit 1
    fi
    launchctl unload "${PLIST_DST}" 2>/dev/null || true
    ln -sf "${PLIST_SRC}" "${PLIST_DST}"
    launchctl load "${PLIST_DST}"
    launchctl kickstart -k "${GUI_DOMAIN}/${LABEL}" 2>/dev/null || true
    echo "已重载: ${LABEL}"
}

cmd_unload() {
    launchctl unload "${PLIST_DST}" 2>/dev/null || true
    echo "已 unload（若此前未加载则无影响）"
}

cmd_kickstart() {
    launchctl kickstart -k "${GUI_DOMAIN}/${LABEL}"
    echo "已 kickstart: ${LABEL}"
}

cmd_status() {
    launchctl list | grep -i notion-ext || echo "（无匹配项，可能未加载）"
}

case "${1:-install}" in
    install)   cmd_install ;;
    reload)    cmd_reload ;;
    unload)    cmd_unload ;;
    kickstart) cmd_kickstart ;;
    status)    cmd_status ;;
    -h|--help|help)
        usage
        ;;
    *)
        echo "未知命令: $1" >&2
        usage >&2
        exit 1
        ;;
esac
