#!/bin/bash
# LogMaster Pro 快速启动

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# 优先使用安装版本，否则使用本地版本
if [ -d "/Applications/LogMaster.app" ]; then
    echo "启动已安装的应用..."
    open "/Applications/LogMaster.app"
else
    echo "启动本地应用..."
    python3 LogMasterPro.py
fi
