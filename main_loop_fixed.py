#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import requests
import json
import wave
import tempfile
import subprocess
import time
from urllib.parse import urljoin
import datetime
import sys

# VoiceVox関連の設定
VOICEVOX_URL = "http://localhost:50021"  # VoiceVoxのデフォルトURL
SPEAKER_ID = 10  # 話者ID

# FFmpeg関連の設定
FONT_SIZE = 28  # 字幕サイズを大きく
FONT_COLOR = "white"
MARGIN_BOTTOM = 60  # 画面下端からの余白を増やす

class VoiceVoxSubtitleGenerator:
    def __init__(self, script_path, output_path, background_video=None):
        """初期化"""
        self.script_path = os.path.abspath(script_path)
        self.output_path = os.path.abspath(output_path)
        self.background_video = os.path.abspath(background_video) if background_video else None
        self.temp_dir = tempfile.mkdtemp()
        self.audio_files = []
        self.subtitle_data = []
        
        print(f"台本パス: {self.script_path}")
        print(f"出力パス: {self.output_path}")
        print(f"背景動画パス: {self.background_video}")
        print(f"一時ディレクトリ: {self.temp_dir}")
        
        # VoiceVoxが起動しているか確認
        try:
            requests.get(VOICEVOX_URL)
            print("VoiceVox Engineに接続しました")
        except requests.exceptions.ConnectionError:
            print("エラー: VoiceVox Engineに接続できません")
            print("VoiceVoxを起動してから再度実行してください")
            sys.exit(1)
    
    def read_script(self):
        """台本を読み込む"""
        with open(self.script_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        return lines
    
    def generate_audio_for_line(self, line, index):
        """1行のテキストから音声を生成"""
        # 音声合成クエリの作成
        query_url = urljoin(VOICEVOX_URL, "audio_query")
        query_params = {"text": line, "speaker": SPEAKER_ID}
        query_response = requests.post(query_url, params=query_params)
        
        if query_response.status_code != 200:
            print(f"エラー: 音声合成クエリの作成に失敗しました (行 {index+1})")
            return None, 0
        
        query_data = query_response.json()
        
        # 音声合成
        synthesis_url = urljoin(VOICEVOX_URL, "synthesis")
        synthesis_params = {"speaker": SPEAKER_ID}
        synthesis_response = requests.post(
            synthesis_url, 
            params=synthesis_params,
            data=json.dumps(query_data),
            headers={"Content-Type": "application/json"}
        )
        
        if synthesis_response.status_code != 200:
            print(f"エラー: 音声合成に失敗しました (行 {index+1})")
            return None, 0
        
        # 一時ファイルに保存
        audio_path = os.path.join(self.temp_dir, f"audio_{index:03d}.wav")
        with open(audio_path, "wb") as f:
            f.write(synthesis_response.content)
        
        # 音声の長さを取得
        with wave.open(audio_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
        
        return audio_path, duration
    
    def process_script(self):
        """台本を処理して音声とタイミング情報を生成"""
        lines = self.read_script()
        current_time = 0.0
        
        for i, line in enumerate(lines):
            print(f"処理中 ({i+1}/{len(lines)}): {line}")
            
            # 音声生成
            audio_path, duration = self.generate_audio_for_line(line, i)
            if not audio_path:
                continue
                
            self.audio_files.append(audio_path)
            
            # 字幕データの作成（SRT形式用）
            # 音声の時間と字幕の表示時間を完全に一致させる
            start_time = current_time
            end_time = start_time + duration  # 音声の長さと完全に同期
            
            # SRTファイル用のタイムコード形式に変換
            start_str = self._format_time_srt(start_time)
            end_str = self._format_time_srt(end_time)
            
            self.subtitle_data.append({
                'index': i + 1,
                'start': start_time,
                'end': end_time,
                'start_str': start_str,
                'end_str': end_str,
                'text': line
            })
            
            # 次の行の開始時間 - 音声が終わった直後から開始
            # 音声と音声の間に小さな間隔を設ける（0.05秒）
            current_time = end_time + 0.05
    
    def _format_time_srt(self, seconds):
        """秒数をSRT形式のタイムコード（00:00:00,000）に変換"""
        ms = int((seconds % 1) * 1000)
        s = int(seconds % 60)
        m = int((seconds / 60) % 60)
        h = int(seconds / 3600)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
    
    def create_srt_file(self):
        """SRT形式の字幕ファイルを作成"""
        srt_path = os.path.join(self.temp_dir, "subtitles.srt")
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            for item in self.subtitle_data:
                f.write(f"{item['index']}\n")
                f.write(f"{item['start_str']} --> {item['end_str']}\n")
                f.write(f"{item['text']}\n\n")
        
        return srt_path
    
    def concatenate_audio(self):
        """全ての音声ファイルを結合"""
        concat_list_path = os.path.join(self.temp_dir, "concat_list.txt")
        final_audio_path = os.path.join(self.temp_dir, "final_audio.wav")
        
        # 結合リストファイルの作成
        with open(concat_list_path, 'w', encoding='utf-8') as f:
            for audio_file in self.audio_files:
                f.write(f"file '{audio_file}'\n")
        
        # FFmpegを使用して音声ファイルを結合
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_list_path, "-c", "copy", final_audio_path
        ]
        
        subprocess.run(cmd, check=True)
        return final_audio_path
    
    def get_video_duration(self, video_path):
        """動画の長さを取得"""
        cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", video_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    
    def get_audio_duration(self, audio_path):
        """音声の長さを取得"""
        with wave.open(audio_path, 'rb') as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            duration = frames / float(rate)
        return duration
    
    def create_looped_video(self, video_path, target_duration):
        """背景動画をループして指定した長さの動画を作成"""
        video_duration = self.get_video_duration(video_path)
        loops_needed = int(target_duration / video_duration) + 1
        
        print(f"背景動画の長さ: {video_duration:.2f}秒")
        print(f"必要な長さ: {target_duration:.2f}秒")
        print(f"必要なループ回数: {loops_needed}")
        
        # 背景動画を一時ディレクトリにコピー
        video_copy_path = os.path.join(self.temp_dir, "background.mp4")
        subprocess.run(["cp", video_path, video_copy_path], check=True)
        
        # ループリストファイルを作成
        loop_list_path = os.path.join(self.temp_dir, "loop_list.txt")
        with open(loop_list_path, 'w', encoding='utf-8') as f:
            for _ in range(loops_needed):
                f.write(f"file '{video_copy_path}'\n")
        
        # ループ動画を作成
        looped_video_path = os.path.join(self.temp_dir, "looped_background.mp4")
        cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", loop_list_path, "-c", "copy", looped_video_path
        ]
        
        subprocess.run(cmd, check=True)
        return looped_video_path
    
    def create_video(self, audio_path, srt_path):
        """最終的な動画を作成（背景動画ループあり）"""
        if not self.background_video:
            # 背景動画がない場合は黒背景の動画を作成
            total_duration = self.subtitle_data[-1]['end'] + 1.0
            
            # 黒背景動画の作成
            blank_video_path = os.path.join(self.temp_dir, "blank.mp4")
            cmd_blank = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c=black:s=1280x720:d={total_duration}",
                "-c:v", "libx264", "-pix_fmt", "yuv420p", blank_video_path
            ]
            subprocess.run(cmd_blank, check=True)
            video_input = blank_video_path
        else:
            # 背景動画がある場合
            audio_duration = self.get_audio_duration(audio_path)
            
            # 必要な長さの動画を作成（ループ処理）
            video_input = self.create_looped_video(self.background_video, audio_duration)
        
        # 動画と音声の合成、字幕の追加
        cmd = [
            "ffmpeg", "-y",
            "-i", video_input,
            "-i", audio_path,
            "-vf", f"subtitles={srt_path}:force_style='FontSize={FONT_SIZE},Alignment=2,OutlineColour=&H000000&,BorderStyle=3,"
                  f"Outline=1,Shadow=0,MarginV={MARGIN_BOTTOM},Bold=1'",
            "-map", "0:v:0", "-map", "1:a:0",
            "-c:v", "libx264", "-c:a", "aac", "-shortest",
            "-vsync", "cfr", "-async", "1", 
            self.output_path
        ]
        
        subprocess.run(cmd, check=True)
    
    def generate(self):
        """メイン処理：動画生成の全プロセスを実行"""
        try:
            print("台本を処理しています...")
            self.process_script()
            
            print("SRTファイルを作成しています...")
            srt_path = self.create_srt_file()
            
            print("音声ファイルを結合しています...")
            audio_path = self.concatenate_audio()
            
            print("動画を生成しています...")
            self.create_video(audio_path, srt_path)
            
            print(f"完了！動画が保存されました: {self.output_path}")
            return True
            
        except Exception as e:
            print(f"エラーが発生しました: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 一時ファイルの削除（必要に応じてコメントアウト）
            # import shutil
            # shutil.rmtree(self.temp_dir)
            pass

if __name__ == "__main__":
    script_path = "script.txt"
    output_path = "output_video.mp4"
    
    # コマンドライン引数の処理（オプション）
    if len(sys.argv) > 1:
        script_path = sys.argv[1]
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    # 背景動画の指定（オプション）
    background_video = None
    if len(sys.argv) > 3:
        background_video = sys.argv[3]
    
    generator = VoiceVoxSubtitleGenerator(script_path, output_path, background_video)
    generator.generate()