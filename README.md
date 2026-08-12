# ManualSearch

ManualSearch は、PDF・テキスト・Markdownを横断して全文検索し、PDFは該当箇所までAdobe Acrobat上で自動ハイライト表示するWindowsデスクトップアプリです。共有フォルダを指定すれば、チーム全員が同じ資料を自分の端末から検索できます。


## 目次

1. [特徴](#特徴)
2. [活用シーン](#活用シーン)
3. [主な機能](#主な機能)
4. [前提条件と要件](#前提条件と要件)
5. [インストール手順](#インストール手順)
6. [使用方法](#使用方法)
7. [プロジェクト構造](#プロジェクト構造)
8. [主要コンポーネント](#主要コンポーネント)
9. [設定](#設定)
10. [開発者向け情報](#開発者向け情報)
11. [トラブルシューティング](#トラブルシューティング)
12. [ライセンス](#ライセンス)
13. [更新履歴](#更新履歴)

---

## 特徴

「業務マニュアルのあの部分、どこにあったっけ」と探すことは、なかなかなくなりません。ManualSearch はこの手間を一つずつ解消します。

| 既存ツール                            | ManualSearch |
|----------------------------------|---|
| **Acrobat Reader**：1ファイルずつしか探せない | 複数フォルダを横断検索し、該当箇所を自動ハイライト |
| **Windows検索**：遅い         | インデックスで高速 |

そして**共有フォルダ**を検索対象に指定すれば、チームメンバー全員が同じ資料を自分の端末から探せるようになります。

> 「あの人に聞かないとわからない」が「だれでもいつでも検索できる」に変わります。

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## 活用シーン

- **大量の業務マニュアルから記載箇所を一発で探す** — 数百のPDF・手順書を横断し、該当ページを開いた瞬間にハイライトで該当箇所が分かる
- **共有ドライブの資料を新人が自力で検索・自己解決** — ベテランに聞かなくても過去の手順や事例を引けるため、属人化した引継ぎコストを下げる
- **Shift_JIS混在の現場ファイルでも文字化けせず検索** — エンコーディングを自動判定し、日本語環境の「検索できない」を防ぐ

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## 主な機能

- **Adobe Acrobat連携（PDF自動ハイライト）**: PDFの検索語を該当箇所まで自動ハイライト表示
- **インデックスベース高速検索**: 事前にインデックスを作成し、大量ファイルでも待たされない検索を実現
- **複数ファイル形式対応**: PDF、TXT、Markdownファイルの横断検索
- **フォルダ横断検索**: 複数フォルダ（共有フォルダ含む）を対象とした横断検索対応
- **マルチスレッド全文検索**: ThreadPoolExecutorを使用した並列検索
- **テキストビューア機能**: テキスト・Markdownファイルを独立ウィンドウで表示、検索語をハイライト、印刷機能搭載
- **柔軟な検索条件**: AND/OR検索、サブフォルダ検索対応
- **日本語エンコーディング自動判定**: chardetによりShift_JIS/UTF-8を自動検出

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## 前提条件と要件

### システム要件

- **OS**: Windows 10/11
- **Python**: 3.12以上
- **Adobe Acrobat Reader DC**: PDF表示機能に必要

### 最小要件

- RAM: 4GB以上推奨
- ストレージ: インデックスファイル用に追加容量が必要

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## インストール手順

### 1. Pythonのインストール確認

```bash
python --version
```

### 2. リポジトリのクローン

```bash
git clone <repository-url>
cd ManualSearch
```

### 3. 仮想環境の作成

```bash
python -m venv venv
venv\Scripts\activate
```

### 4. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 5. アプリケーション起動

```bash
python main.py
```

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## 使用方法

### 基本的な検索フロー

1. **検索対象フォルダの設定**
   - 「追加」ボタンでフォルダを選択
   - 複数フォルダの登録が可能
   - **共有フォルダ（社内サーバー・共有ドライブ）を指定すれば、チーム全員が同じ資料を検索できます**

2. **検索の実行**
   - 検索語を入力（カンマ区切りで複数語可能）
   - AND/OR検索を選択
   - 「検索」ボタンをクリック

3. **結果の確認**
   - 検索結果リストから項目を選択
   - ダブルクリックでファイルを開く

### インデックス機能の使用

```python
# インデックス作成（初回のみ）
indexer = SearchIndexer("search_index.json")
indexer.create_index(
    directories=["C:/Documents"],
    include_subdirs=True
)

# インデックス検索
indexed_searcher = IndexedFileSearcher(
    directory="C:/Documents",
    search_terms=["検索語"],
    use_index=True,
    index_file_path="search_index.json"
)
results = indexed_searcher.search()
```

### 検索のコツ

- **AND検索**: すべての語を含むページを検索
- **OR検索**: いずれかの語を含むページを検索
- **サブフォルダ検索**: 指定フォルダ以下を再帰的に検索
- **インデックス検索**: 大規模データセットでの高速化を実現

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## プロジェクト構造

```
ManualSearch/
├── main.py                          # アプリケーションエントリーポイント
├── app/
│   └── main_window.py               # メインウィンドウとUI統制
├── service/                         # コアビジネスロジック
│   ├── file_searcher.py             # マルチスレッド検索エンジン
│   ├── indexed_file_searcher.py     # インデックス活用検索
│   ├── search_indexer.py            # インデックス作成・管理
│   ├── file_opener.py               # ファイルオープン機能
│   ├── pdf_handler.py               # PDF処理とハイライト
│   ├── text_handler.py              # テキスト処理
│   ├── content_extractor.py         # コンテンツ抽出
│   ├── index_storage.py             # インデックス永続化
│   ├── search_matcher.py            # 検索マッチング処理
│   ├── pdf_search_strategy.py       # PDF検索戦略
│   └── text_search_strategy.py      # テキスト検索戦略
├── widgets/                         # UIコンポーネント
│   ├── search_widget.py             # 検索入力とコントロール
│   ├── results_widget.py            # 検索結果表示
│   ├── directory_widget.py          # 検索対象フォルダの状態表示と検索オプション
│   ├── directory_management_widget.py # フォルダ設定ダイアログ
│   ├── index_management_widget.py   # インデックス管理UI
│   ├── text_viewer_widget.py        # テキストビューアウィンドウ
│   └── auto_close_message_widget.py # 自動クローズメッセージ
├── utils/
│   ├── config_manager.py            # INI設定管理
│   ├── helpers.py                   # ユーティリティ関数
│   └── log_rotation.py              # ログローテーション
├── tests/                           # テストコード

```

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## 主要コンポーネント

### 検索エンジン層

#### FileSearcher（マルチスレッド検索）

ファイルを並列処理して全文検索を実行します。

```python
searcher = FileSearcher(
    directory="C:/Documents",
    search_terms=["検索語1", "検索語2"],
    include_subdirs=True,
    search_type="AND",  # または "OR"
    file_extensions=['.pdf', '.txt', '.md'],
    context_length=100
)
results = searcher.search()
```

**特徴**:
- ThreadPoolExecutorによる並列処理
- キャンセル機能
- 進捗報告コールバック
- AND/OR検索両対応

#### IndexedFileSearcher（インデックス検索）

事前に作成したインデックスを活用した高速検索。

```python
indexed_searcher = IndexedFileSearcher(
    directory="C:/Documents",
    search_terms=["検索語"],
    use_index=True,
    index_file_path="search_index.json",
    cross_folder_search=True
)
results = indexed_searcher.search()
```

**特徴**:
- インデックスベースの高速検索
- 複数フォルダ横断検索対応
- インデックス破損時の自動フォールバック

### ファイル処理パイプライン

1. **ファイル検出**: os.walk()による階層的スキャン
2. **コンテンツ抽出**: ContentExtractorによる形式別処理
   - PDF: PyMuPDFでのテキスト抽出
   - TEXT: chardetによる自動エンコーディング検出
   - MARKDOWN: テキストとして処理
3. **マッチング**: SearchMatcherによる検索条件評価
4. **コンテキスト抽出**: 検索結果の前後文脈を自動抽出
5. **結果集約**: UI表示へ

### インデックスシステム

```python
# インデックス作成
indexer = SearchIndexer("search_index.json")
indexer.create_index(
    directories=["C:/Documents"],
    include_subdirs=True,
    progress_callback=lambda progress, total: print(f"{progress}/{total}")
)

# インデックス更新（差分更新）
indexer.update_index(
    directories=["C:/Documents"],
    include_subdirs=True
)
```

**機能**:
- ファイル修正時刻ベースの差分更新
- ハッシュ値によるファイル変更検出
- JSON形式での永続化
- インデックス統計情報提供

### テキスト処理・ビューア機能

```python
# テキストファイルを別ウィンドウで開く
from service.text_handler import open_text_file

open_text_file(
    file_path="document.txt",
    search_terms=["重要", "確認"],
    html_font_size=16,
    position=0,
    width=1000,
    height=600
)
```

**テキストビューア機能**:
- テキスト・Markdownファイルを独立ウィンドウで表示
- 検索語のカラーハイライト表示
- ズームイン/ズームアウト機能
- 印刷機能（プレビュー対応）

### PDF処理・Adobe連携

```python
# PDFハイライト
highlighted_path = highlight_pdf(
    pdf_path="document.pdf",
    search_terms=["重要", "確認"]
)
```

**機能**:
- 検索語の自動ハイライト（画面表示のみ、印刷対象外）
- Adobe Acrobat Reader DC統合
- 一時ファイル自動クリーンアップ

### UI層（Widgets）

- **SearchWidget**: 検索語入力、AND/OR選択、検索オプション
- **DirectoryWidget**: 検索対象フォルダ数の表示、サブフォルダ検索の切替、フォルダ設定ダイアログの起動
- **DirectoryManagementDialog**: 検索対象フォルダの追加・編集・削除
- **ResultsWidget**: 検索結果表示、ハイライト表示、ファイルオープン
- **IndexManagementWidget**: インデックス作成・更新・管理UI
- **TextViewerWindow**: テキスト・Markdownファイル表示、検索語ハイライト、ズーム機能、ファイルを開く・印刷・閉じるボタン（印刷プレビュー対応）

### スレッドモデル

```
UI Thread (Qt Main Loop)
  ├─ Widget操作とイベント処理
  └─ ユーザーインタラクション
        ▲              ▼
   (Signals)      (Signals)
        │              │
    ┌───┴──────────────┴───┐
    │                      │
FileSearcher Thread   SearchIndexer Thread
 ・ファイル検索       ・インデックス作成
 ・コンテンツ抽出     ・ファイル処理
 ・マッチング処理     ・統計情報生成
```

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## 設定

### config.ini の主要設定

アプリケーション初回起動時に自動作成されます。

```ini
[WindowSettings]
window_width = 1150
window_height = 800
font_size = 14

[Paths]
acrobat_path = C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe

[IndexSettings]
index_file_path = C:\search_index.json
use_index_search = False

[SearchSettings]
context_length = 100

[TextViewer]
window_width = 1000
window_height = 600
html_font_size = 16

[LOGGING]
log_level = INFO
log_directory = logs
log_retention_days = 7
```

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## 開発者向け情報

### 開発環境のセットアップ

```bash
# リポジトリクローン
git clone <repository-url>
cd ManualSearch

# 仮想環境作成と有効化
python -m venv venv
venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt
```

### テスト実行

```bash
# すべてのテスト実行
python -m pytest tests/ -v

# カバレッジレポート生成
python -m pytest --cov=. --cov-report=html

# 特定のテスト実行
python -m pytest tests/service/test_file_searcher.py::TestFileSearcher::test_search_functionality -v
```

### ビルド方法

```bash
# 実行可能ファイルをビルド
python build.py
```

### コード品質チェック

```bash
# 型チェック（Pyright）
pyright

# テストカバレッジ確認
pytest --cov=. --cov-report=term-missing
```

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## トラブルシューティング

### よくある問題と対処法

#### Q: Adobe Acrobat Readerが起動しない
**A**:
- Acrobatのインストールパスを確認してください
- 設定ファイルの`acrobat_path`を正しいパスに変更してください
- 管理者権限で実行してみてください

```bash
# インストール確認
"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe" --version
```

#### Q: 検索が遅い
**A**:
- インデックス機能を有効にしてください
- インデックスが古い場合は「インデックス更新」を実行してください

```ini
[IndexSettings]
use_index_search = True
```

#### Q: 日本語検索が機能しない
**A**:
- ファイルがUTF-8またはShift_JISで保存されているか確認してください
- エンコーディング自動検出がchardetで行われています

#### Q: インデックス作成に時間がかかる
**A**:
- 大量のファイルを処理する場合は時間がかかります
- バックグラウンド処理が進行中なので他の作業を続けられます
- 進行状況バーで進捗を確認してください

#### Q: メモリ使用量が多い
**A**:
- 検索対象を減らしてください
- 古いインデックスファイルをクリーンアップしてください
- アプリケーションを再起動してください

### ログファイルの確認

```bash
# ログディレクトリ
logs/manual_search.log
```

ログレベルをDEBUGに設定することで詳細情報を確認できます。

### パフォーマンス診断

```bash
# スロー検索の診断
python -m pytest tests/service/test_file_searcher.py -v --durations=5

# メモリ使用量監視
python -m cProfile -s cumtime main.py
```

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## 主要依存ライブラリ

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| PyQt5 | 5.15.11 | GUIフレームワーク |
| PyMuPDF (fitz) | 1.26.3 | PDFテキスト抽出 |
| chardet | 5.2.0 | 文字エンコーディング自動検出 |

詳細は `requirements.txt` を参照してください。

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>

---

## ライセンス

このプロジェクトのライセンス情報については、 [LICENSE](docs/LICENSE) を参照してください。

## 更新履歴

更新履歴は [CHANGELOG.md](docs/CHANGELOG.md) を参照してください。

<div align="right"><a href="#目次">▲ 目次へ戻る</a></div>
