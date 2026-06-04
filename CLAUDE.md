# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

PDF・テキスト・Markdownファイルの全文検索を行うPyQt5デスクトップアプリ（Windows専用）。マルチスレッド検索エンジンとインデックスベースの高速検索を搭載し、Adobe Acrobat DCとの連携によるPDFハイライト機能を持つ。

## コマンド

```bash
# 起動
python main.py

# テスト（詳細は .claude/rules/testing.md 参照）
python -m pytest tests/ -v --tb=short

# 型チェック
pyright

# 実行ファイルビルド（PyInstaller）
python build.py
```

## 設定

`utils/config.ini` は事前設定済み。Acrobatパス・インデックスパス・ウィンドウ設定などが含まれる。新規環境では `[Paths] acrobat_path` を実際のAcrobatインストール先に更新する。

## アーキテクチャ

| ディレクトリ | 役割 |
|---|---|
| `app/` | メインウィンドウ（PyQt5 QMainWindow） |
| `service/` | 検索・インデックス・PDF処理などのビジネスロジック |
| `widgets/` | PyQt5 UIコンポーネント |
| `utils/constants/` | 全UI文字列・エラーメッセージ・定数（magic string禁止） |

- `FileSearcher` / `IndexedFileSearcher` はQThreadベースの非同期検索
- PDF検索はPyMuPDFでテキスト抽出、ハイライトはAcrobat DCプロセス経由

## 注意事項

- **Windows専用**：pyautogui/pywin32依存、Adobe Acrobat DC必須（PDFハイライト機能）
- UI表示文字列はすべて `utils/constants/` で管理。直接文字列を書かない
- コーディング規約・コミット形式・テスト方法は `.claude/rules/` 参照
