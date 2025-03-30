#!/bin/bash

# 設定（必要に応じて変更してください）
SCRIPT_DIR="$(dirname "$(realpath "$0")")" 
SPEAKER_ID=10  # 話者ID（10=玄野武宏）

# 引数の処理
SCRIPT_FILE="${1:-script.txt}"
OUTPUT_DIR="${2:-.}"
BACKGROUND_VIDEO="${3:-}"

# 出力ファイル名の生成
OUTPUT_FILE="${OUTPUT_DIR}/output_$(date +%Y%m%d_%H%M%S).mp4"

# 話者IDを設定
sed -i.bak "s/SPEAKER_ID = [0-9]\+/SPEAKER_ID = ${SPEAKER_ID}/" "${SCRIPT_DIR}/main_loop_fixed.py"

# 実行
if [ -n "$BACKGROUND_VIDEO" ]; then
    echo "背景動画を使用して実行します: $BACKGROUND_VIDEO"
    python3 "${SCRIPT_DIR}/main_loop_fixed.py" "$SCRIPT_FILE" "$OUTPUT_FILE" "$BACKGROUND_VIDEO"
else
    echo "背景動画なしで実行します"
    python3 "${SCRIPT_DIR}/main_loop_fixed.py" "$SCRIPT_FILE" "$OUTPUT_FILE"
fi

# バックアップファイルの削除
rm -f "${SCRIPT_DIR}/main_loop_fixed.py.bak"

echo "処理が完了しました。出力ファイル: $OUTPUT_FILE"