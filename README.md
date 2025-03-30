# VoiceVox 字幕同期ツール

このツールは、テキスト台本をVoiceVoxで音声合成し、その読み上げ時間に**完全に同期した**字幕付き動画を生成します。

## 機能

- テキストファイルから行単位で音声合成
- 音声の長さに基づく**厳密に同期された**字幕タイミング生成
- 任意の背景動画への字幕追加（または黒背景の生成）
- バッチ処理による一括変換機能

## 必要なもの

- Python 3.6以上
- FFmpeg (コマンドラインから実行可能なように環境変数PATHに追加されていること)
- VoiceVox Engine (ローカルで起動しておく必要があります)

## インストール方法

```bash
# リポジトリをクローン
git clone https://github.com/mayu119/voicevox-subtitle-sync.git
cd voicevox-subtitle-sync

# 必要に応じて実行権限を付与
chmod +x run.sh
```

## 使い方

### 1. 準備

- [VoiceVox](https://voicevox.hiroshiba.jp/)をダウンロードしてインストールします
- VoiceVox Engineを起動します
- [FFmpeg](https://ffmpeg.org/download.html)をインストールします

### 2. 台本ファイルを作成

`script.txt`というファイル名で、1行ごとに字幕として表示したいテキストを書きます。

### 3. 実行

```bash
# 基本的な使い方
./run.sh

# 引数を指定した使い方
./run.sh [台本ファイルのパス] [出力ディレクトリ] [背景動画のパス(オプション)]

# 例
./run.sh my_script.txt ./output ./backgrounds/beach.mp4
```

## 詳細設定

`main_loop_fixed.py`の冒頭にある以下の変数を編集することで、生成される動画のスタイルを調整できます:

```python
# VoiceVox関連の設定
VOICEVOX_URL = "http://localhost:50021"  # VoiceVoxのデフォルトURL
SPEAKER_ID = 10  # 話者ID（デフォルト: 玄野武宏）

# FFmpeg関連の設定
FONT_SIZE = 28  # 字幕のフォントサイズ
FONT_COLOR = "white"  # 字幕の色
MARGIN_BOTTOM = 60  # 画面下端からの余白
```

## 話者IDについて

VoiceVoxの主な話者ID:
- 0: 四国めたん（ノーマル）
- 1: ずんだもん（ノーマル）
- 3: ずんだもん（あまあま）
- 8: 春日部つむぎ
- 10: 玄野武宏（標準的な男性声、同期に最適）
- 13: 青山龍星
- 14: 冥鳴ひまり
- 16: ナースロボ＿タイプＴ
- 20: もち子(cv 明日葉よもぎ)

詳細は[VoiceVoxのドキュメント](https://github.com/VOICEVOX/voicevox_engine/blob/master/docs/api.md)を参照してください。

## 注意点

- VoiceVox Engineが起動していない場合、エラーが発生します
- 長い台本の場合、処理に時間がかかる場合があります
- 話者によって音声と字幕の同期精度が異なる場合があります。ID 10（玄野武宏）が最も安定しています

## 同期問題のトラブルシューティング

字幕と音声が同期しない場合：

1. 話者IDを変更してみてください（ID 10: 玄野武宏が最も安定）
2. スクリプトの各行を短くしてみてください
3. FFmpegのバージョンが最新であることを確認してください

## 貢献

バグ報告や機能追加のリクエストは、GitHubのIssueにてお願いします。