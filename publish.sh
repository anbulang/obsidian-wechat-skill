#!/bin/bash
# 使用虚拟环境中的 Python 运行发布脚本
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
"$DIR/.venv/bin/python" "$DIR/publish_to_wechat.py" "$@"
