# ManualSearch

PyQt5ベースのデスクトップアプリケーション。PDF、テキスト、Markdownファイルの全文検索、マルチスレッド検索エンジン、インデックスベースの高速検索、Adobe Acrobat連携による検索語ハイライト表示を実現します。



## 目次

1. [主要機能](#主要機能)
2. [前提条件と要件](#前提条件と要件)
3. [インストール手順](#インストール手順)
4. [使用方法](#使用方法)
5. [プロジェクト構造](#プロジェクト構造)
6. [主要コンポーネント](#主要コンポーネント)
7. [設定](#設定)
8. [開発者向け情報](#開発者向け情報)
9. [トラブルシューティング](#トラブルシューティング)
10. [バージョン情報](#バージョン情報)
11. [ライセンス](#ライセンス)

---

## 主要機能

- **複数ファイル形式対応**: PDF、TXT、Markdownファイルの横断検索
- **マルチスレッド全文検索**: ThreadPoolExecutorを使用した並列検索
- **インデックスベース高速検索**: 事前にインデックスを作成して高速検索を実現
- **フォルダ横断検索**: 複数フォルダを対象とした横断検索対応
- **Adobe Acrobat連携**: 検索語を自動ハイライト表示
- **柔軟な検索条件**: AND/OR検索、サブフォルダ検索対応
- **ハイライト表示**: 検索結果を視覚的に強調表示

---

## 前提条件と要件

### システム要件

- **OS**: Windows 10/11
- **Python**: 3.11以上（推奨: 3.12）
- **Adobe Acrobat Reader DC**: PDF表示機能に必要

### 最小要件

- RAM: 4GB以上推奨
- ストレージ: インデックスファイル用に追加容量が必要

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

---

## 使用方法

### 基本的な検索フロー

1. **検索対象フォルダの設定**
   - 「追加」ボタンでフォルダを選択
   - 複数フォルダの登録が可能

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
- **インデックス検索**: 大規模データセットで60倍の高速化を実現

---

## プロジェクト構造

```
ManualSearch/
├── main.py                          # アプリケーションエントリーポイント
├── constants.py                     # グローバル定数とマッピング
├── requirements.txt                 # 依存関係
├── app/
│   ├── __init__.py
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
│   ├── directory_widget.py          # フォルダ選択管理
│   ├── index_management_widget.py   # インデックス管理UI
│   └── auto_close_message_widget.py # 自動クローズメッセージ
├── utils/
│   ├── config_manager.py            # INI設定管理
│   ├── helpers.py                   # ユーティリティ関数
│   └── log_rotation.py              # ログローテーション
├── templates/
│   └── text_viewer.html             # テキスト表示テンプレート
├── tests/                           # テストコード
├── logs/                            # ログディレクトリ
└── docs/
    ├── README.md                    # このファイル
    ├── CHANGELOG.md                 # バージョン履歴
    └── LICENSE                      # ライセンス情報
```

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
- インデックスベースの高速検索（最大60倍高速化）
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

### PDF処理・Adobe連携

```python
# PDFハイライト
highlighted_path = highlight_pdf(
    pdf_path="document.pdf",
    search_terms=["重要", "確認"]
)
```

**機能**:
- 検索語の自動ハイライト
- 複数語のカラーコーディング
- Adobe Acrobat Reader DC統合
- UNCパス対応
- 一時ファイル自動クリーンアップ

### UI層（Widgets）

- **SearchWidget**: 検索語入力、AND/OR選択、検索オプション
- **DirectoryWidget**: フォルダ管理（追加・削除・リスト表示）
- **ResultsWidget**: 検索結果表示、ハイライト表示、ファイルオープン
- **IndexManagementWidget**: インデックス作成・更新・管理UI

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

[LOGGING]
log_level = INFO
log_directory = logs
log_retention_days = 7
```

### 設定項目の説明

| 設定項目 | 説明 | デフォルト値 |
|---------|------|-----------|
| window_width | ウィンドウ幅（ピクセル） | 1150 |
| window_height | ウィンドウ高さ（ピクセル） | 800 |
| font_size | UI文字サイズ | 14 |
| acrobat_path | Adobe Acrobatの実行ファイルパス | 自動検出 |
| index_file_path | インデックスファイルの保存先 | search_index.json |
| use_index_search | インデックス検索の有効化 | False |
| context_length | 検索結果の前後文字数 | 100 |
| log_level | ログレベル (DEBUG/INFO/WARNING/ERROR) | INFO |

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

# テストタイプ別実行
python -m pytest -m unit -v               # ユニットテストのみ
python -m pytest -m integration -v        # 統合テストのみ
python -m pytest -m gui -v                # GUIテストのみ

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

ビルド処理は以下を含みます：
- PyInstallerによる実行可能ファイル生成
- アイコン設定
- リソースの埋め込み（テンプレート、設定ファイル）
- バージョン情報の自動更新

### コード品質チェック

```bash
# 型チェック（Pyright）
pyright

# テストカバレッジ確認
pytest --cov=. --cov-report=term-missing
```

### コーディング規約（CLAUDE.md参照）

- **Python**: PEP 8に準拠
- **Import順序**: 標準ライブラリ → サードパーティ → カスタムモジュール（各セクション内でアルファベット順）
- **命名規則**:
  - クラス名: PascalCase（例: `FileSearcher`）
  - 関数/変数: snake_case（例: `search_files`）
- **型ヒント**: すべての関数に型アノテーション記載
- **Docstring**: Google形式で簡潔に記載
- **コメント**: 日本語で必要最小限に

### テスト構成

```
tests/
├── conftest.py                    # pytest共通設定
├── test_integration.py            # エンドツーエンドテスト
├── service/
│   ├── test_file_searcher.py      # FileSearcherテスト
│   ├── test_indexed_file_searcher.py
│   ├── test_search_indexer.py
│   ├── test_pdf_handler.py
│   └── test_handlers.py
├── utils/
│   ├── test_config_manager.py
│   └── test_helpers.py
└── widgets/
    └── test_search_widget.py
```

### 主要な開発タスク

```bash
# ログの確認
tail -f logs/manual_search.log

# デバッグログレベルで実行
LOG_LEVEL=DEBUG python main.py
```

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

---

## 主要依存ライブラリ

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| PyQt5 | 5.15.11 | GUIフレームワーク |
| PyMuPDF (fitz) | 1.26.3 | PDFテキスト抽出 |
| chardet | 5.2.0 | 文字エンコーディング自動検出 |
| Jinja2 | 3.1.6 | HTMLテンプレートレンダリング |
| psutil | 7.0.0 | プロセス監視管理 |
| pytest | 8.4.1 | テストフレームワーク |
| pytest-qt | 4.5.0 | Qtテスト支援 |
| pytest-cov | 6.2.1 | カバレッジ測定 |
| pyinstaller | 6.14.2 | 実行可能ファイル生成 |

詳細は `requirements.txt` を参照してください。

---

## バージョン情報

- **現在のバージョン**: 1.3.3
- **最終更新日**: 2025年11月29日

## ライセンス

このプロジェクトのライセンス情報については、`docs/LICENSE`を参照してください。
