# ManualSearch

## 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [前提条件と要件](#前提条件と要件)
3. [インストール手順](#インストール手順)
4. [使用方法](#使用方法)
5. [プロジェクト構造](#プロジェクト構造)
6. [機能説明](#機能説明)
7. [設定](#設定)
8. [開発者向け情報](#開発者向け情報)
9. [パフォーマンス最適化](#パフォーマンス最適化)
10. [Adobe Acrobat連携詳細ガイド](#adobe-acrobat連携詳細ガイド)
11. [コントリビューション](#コントリビューション)
12. [トラブルシューティング詳細ガイド](#トラブルシューティング詳細ガイド)
13. [依存ライブラリ](#依存ライブラリ)
14. [最新の変更履歴](#最新の変更履歴)
15. [バージョン情報](#バージョン情報)
16. [ライセンス](#ライセンス)

---

## プロジェクト概要

**ManualSearch**は、PDF、テキスト、Markdownファイルで作成されたマニュアルを効率的に検索するためのデスクトップアプリケーションです。

### 主要な機能

- **複数ファイル形式対応**: PDF、TXT、Markdownファイルの横断検索
- **高速インデックス検索**: 事前にインデックスを作成して高速検索を実現
- **フォルダ横断検索**: 複数フォルダを横断したインデックス検索に対応
- **PDF連携**: Adobe Acrobat Readerと連携し、検索語をハイライト表示
- **柔軟な検索条件**: AND/OR検索、サブフォルダ検索対応
- **視覚的な結果表示**: 検索結果をハイライト表示で見やすく提示

### 対象ユーザー

- 大量の文書やマニュアルを管理する方
- 複数のPDFファイルから情報を効率的に検索したい方

### 解決する問題

- 複数のPDFファイルにまたがる情報検索の効率化
- 検索結果の視覚的な確認とファイルへの直接アクセス
- 大量ファイルに対する高速検索の実現

## 前提条件と要件

### システム要件

- **OS**: Windows 10/11
- **Python**: 3.11以降推奨 (32bit版に対応)
- **Adobe Acrobat Reader DC**: PDF表示機能に必要

### ハードウェア要件

- **RAM**: 4GB以上推奨
- **ストレージ**: インデックスファイル用に追加容量が必要

## インストール手順

### 1. Pythonのインストール

Python 3.11以降をインストールしてください。
```bash
# Pythonバージョン確認
python --version
```

### 2. リポジトリのクローン

```bash
git clone <repository-url>
cd ManualSearch
```

### 3. 仮想環境の作成（推奨）

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 4. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 5. Adobe Acrobat Reader DCのインストール

PDF機能を使用するには、Adobe Acrobat Reader DCが必要です：
- [Adobe公式サイト](https://get.adobe.com/jp/reader/)からダウンロード
- デフォルトパス: `C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe`

### 6. 設定ファイルの準備

初回起動時に`utils/config.ini`が自動作成されます。必要に応じて設定を変更してください。

## 使用方法

### 基本的な使い方

1. **アプリケーション起動**
   ```bash
   python main.py
   ```

2. **検索対象フォルダの設定**
   - 「追加」ボタンでフォルダを選択
   - 複数フォルダの登録が可能

3. **検索の実行**
   - 検索語を入力（カンマ区切りで複数語可能）
   - AND/OR検索を選択
   - 「検索」ボタンをクリック

4. **結果の確認**
   - 検索結果リストから項目を選択
   - ダブルクリックでファイルを開く

### インデックス機能の使用

高速検索のためのインデックス機能：

1. **インデックス管理画面を開く**
   - 「インデックス設定」ボタンをクリック

2. **インデックス作成**
   - 「インデックス作成」ボタンで初回作成
   - 「インデックス更新」で差分更新

3. **インデックス検索の有効化**
   - 「インデックス検索」チェックボックスを有効にする
   - **フォルダ横断検索**: 「フォルダ横断検索」を有効にして複数フォルダ横断検索が可能

### 検索のコツ

- **AND検索**: すべての語を含むページを検索
- **OR検索**: いずれかの語を含むページを検索
- **サブフォルダ検索**: 指定フォルダ以下を再帰的に検索
- **フォルダ横断検索**: 登録されたすべてのフォルダを対象にした横断検索

## プロジェクト構造

```
ManualSearch/
├── main.py                     # アプリケーションエントリーポイント
├── constants.py                # 定数定義
├── requirements.txt            # 依存関係
├── app/
│   ├── __init__.py
│   └── main_window.py          # メインウィンドウ
├── service/
│   ├── file_opener.py          # ファイル開く機能
│   ├── file_searcher.py        # ファイル検索エンジン
│   ├── indexed_file_searcher.py # インデックス検索
│   ├── search_indexer.py       # インデックス作成・管理
│   ├── content_extractor.py    # コンテンツ抽出処理
│   ├── index_storage.py        # インデックス保存管理
│   ├── pdf_handler.py          # PDF処理
│   ├── pdf_search_strategy.py  # PDF検索戦略
│   ├── search_matcher.py       # 検索マッチング処理
│   ├── text_handler.py         # テキスト処理
│   └── text_search_strategy.py # テキスト検索戦略
├── widgets/
│   ├── search_widget.py        # 検索UI
│   ├── results_widget.py       # 結果表示UI
│   ├── directory_widget.py     # フォルダ選択UI
│   └── index_management_widget.py # インデックス管理UI
├── utils/
│   ├── config_manager.py       # 設定管理
│   └── helpers.py              # ヘルパー関数
└── templates/
    └── text_viewer.html        # テキスト表示テンプレート
```

### 主要ファイルの役割

- **main.py**: アプリケーションの起動とQtアプリケーションの初期化
- **main_window.py**: メインUIとコンポーネント間の連携
- **file_searcher.py**: ファイル内容の検索処理
- **indexed_file_searcher.py**: インデックスを使用した高速検索
- **search_indexer.py**: 検索インデックスの作成と管理
- **content_extractor.py**: PDF/テキストからのコンテンツ抽出
- **index_storage.py**: インデックスデータの保存・読み込み管理
- **pdf_search_strategy.py**: PDF検索の戦略実装
- **text_search_strategy.py**: テキスト検索の戦略実装
- **search_matcher.py**: 検索条件マッチング処理
- **config_manager.py**: 設定ファイルの読み書き

## 機能説明

### 検索エンジン

#### FileSearcher クラス
通常の全文検索を実行します。

```python
# 基本的な使用例
searcher = FileSearcher(
    directory="C:/Documents",
    search_terms=["検索語1", "検索語2"],
    include_subdirs=True,
    search_type="AND",
    file_extensions=['.pdf', '.txt', '.md'],
    context_length=100
)
```

#### IndexedFileSearcher クラス
インデックスを活用した高速検索を実行します。フォルダ横断検索にも対応しています。

```python
# インデックス検索の使用例
indexed_searcher = IndexedFileSearcher(
    directory="C:/Documents",
    search_terms=["検索語"],
    use_index=True,
    index_file_path="search_index.json",
    cross_folder_search=True  # 複数フォルダ横断検索
)
```

### PDF処理機能

#### PDF ハイライト機能
検索語をPDFにハイライト表示します。

```python
# PDFハイライトの例
highlighted_path = highlight_pdf(
    pdf_path="document.pdf",
    search_terms=["重要", "確認"]
)
```

### インデックス管理

#### SearchIndexer クラス
検索用インデックスの作成と管理を行います。

```python
# インデックス作成の例
indexer = SearchIndexer("search_index.json")
indexer.create_index(
    directories=["C:/Documents", "C:/Manuals"],
    include_subdirs=True
)
```

## 設定

### config.ini の主要設定項目

```ini
[WindowSettings]
window_width = 1150
window_height = 800
font_size = 14

[Paths]
acrobat_path = C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe

[IndexSettings]
index_file_path = C:\search_index.json
use_index_search = True

[SearchSettings]
context_length = 100
```

### 設定のカスタマイズ

- **フォントサイズ**: UIの文字サイズを調整
- **Acrobatパス**: Adobe Acrobat Readerのインストールパスを指定
- **インデックスパス**: インデックスファイルの保存場所を指定
- **コンテキスト長**: 検索結果表示時の前後文字数

## 開発者向け情報

### 開発環境のセットアップ

```bash
# リポジトリのクローン
git clone <repository-url>
cd ManualSearch

# 仮想環境の作成
python -m venv venv
venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

### テスト実行

プロジェクトではpytest + pytest-qtを使用しています。

```bash
# すべてのテストを実行
python -m pytest tests/ -v

# テストタイプ別実行
python -m pytest -m unit -v               # ユニットテストのみ
python -m pytest -m integration -v        # 統合テストのみ
python -m pytest -m gui -v                # GUIテストのみ（ディスプレイ必須）

# カバレッジレポート生成
python -m pytest --cov=. --cov-report=html

# 特定のテストを実行
python -m pytest tests/service/test_file_searcher.py::TestFileSearcher::test_search_functionality -v
```

### テスト構成

```
tests/
├── conftest.py                    # pytest共通設定
├── test_integration.py            # エンドツーエンドテスト
├── test_runner.py                 # テスト実行支援
├── service/
│   ├── test_file_searcher.py      # FileSearcherテスト
│   ├── test_indexed_file_searcher.py # IndexedFileSearcherテスト
│   ├── test_search_indexer.py     # SearchIndexerテスト
│   ├── test_pdf_handler.py        # PDF処理テスト
│   ├── test_text_handler.py       # テキスト処理テスト
│   ├── test_file_opener.py        # ファイルオープナーテスト
│   └── test_handlers.py           # ハンドラ統合テスト
├── utils/
│   ├── test_config_manager.py     # 設定管理テスト
│   └── test_helpers.py            # ヘルパー関数テスト
└── widgets/
    └── test_search_widget.py      # UIウィジェットテスト
```

### テストマーカー

pytest.iniで定義されたマーカーで効率的にテストを選別できます：

- `@pytest.mark.unit`: ユニットテスト
- `@pytest.mark.integration`: 統合テスト
- `@pytest.mark.gui`: GUIテスト
- `@pytest.mark.performance`: パフォーマンステスト
- `@pytest.mark.memory`: メモリ使用量テスト
- `@pytest.mark.large_dataset`: 大規模データセットテスト
- `@pytest.mark.slow`: 時間がかかるテスト

### ビルド方法

実行可能ファイルをビルドする場合：

```bash
# 標準ビルド
python build.py

# PyInstallerを手動実行
pyinstaller --name=マニュアル検索 --windowed --icon=assets/ManualSearch.ico main.py
```

ビルド処理は以下を含みます：
- PyInstallerによる実行可能ファイル生成
- アイコン設定
- リソースの埋め込み（テンプレート、設定ファイル）
- バージョン管理の自動更新

### コード品質チェック

```bash
# 型チェック（Pyright）
pyright

# テストカバレッジ確認
pytest --cov=. --cov-report=term-missing
```

### アーキテクチャ

### 全体設計

**ManualSearch**は以下の設計原則に基づいています：

- **MVCパターン**: モデル（Service層）、ビュー（Widgets）、コントローラー（MainWindow）
- **Qt Signalシステム**: コンポーネント間の疎結合な通信
- **設定管理**: INIファイルベースの設定永続化

### コアコンポーネント

#### 検索エンジン

**FileSearcher**（マルチスレッド全文検索）
- ThreadPoolExecutorを使用した並列ファイル処理
- 複数ファイル形式の統一的な検索インターフェース
- キャンセル機能とプログレス報告
- AND/OR検索の両方に対応

```python
searcher = FileSearcher(
    directory="C:/Documents",
    search_terms=["検索語1", "検索語2"],
    include_subdirs=True,
    search_type="AND",
    file_extensions=['.pdf', '.txt', '.md'],
    context_length=100
)
```

**IndexedFileSearcher**（インデックス利用検索）
- 事前に作成したインデックスを活用
- フォルダ横断検索対応
- 高速検索を実現

```python
indexed_searcher = IndexedFileSearcher(
    directory="C:/Documents",
    search_terms=["検索語"],
    use_index=True,
    index_file_path="search_index.json",
    cross_folder_search=True
)
```

**SmartFileSearcher**（インテリジェント検索ルータ）
- インデックス利用可否を自動判断
- インデックス破損時の自動フォールバック
- 最適な検索方法を選択

#### ファイル処理パイプライン

1. **ファイル検出**: os.walk()による階層的ファイルスキャン
2. **コンテンツ抽出**: ContentExtractorによる形式別処理
   - PDF: PyMuPDF (fitz)でのテキスト抽出
   - TEXT: chardet自動エンコーディング検出
   - MARKDOWN: テキストファイルとして処理
3. **マッチング**: SearchMatcherによる検索条件評価
   - AND検索: すべての検索語を含む
   - OR検索: いずれかの検索語を含む
4. **コンテキスト抽出**: 検索結果の前後文脈を自動抽出
5. **結果集約**: 結果ウィジェットへの表示

#### インデックスシステム

**SearchIndexer**（インデックス作成・管理）
```python
indexer = SearchIndexer("search_index.json")
indexer.create_index(
    directories=["C:/Documents"],
    include_subdirs=True,
    progress_callback=lambda p, t: print(f"{p}/{t}")
)
```

**インデックス機能**
- ファイル修正時刻ベースの差分更新
- ハッシュ値によるファイル変更検出
- JSON形式での永続化
- インデックス統計情報提供

#### PDF処理・Adobe連携

**PDFハイライト機能**
- 検索語の自動ハイライト
- 複数語のカラーコーディング
- Adobe Acrobat Reader DCとの統合
- UNCパス対応

**プロセス管理**
- Acrobatプロセスの生存確認
- 一時ファイルの自動クリーンアップ
- リソースリーク防止

#### UI層（Widgets）

- **SearchWidget**: 検索条件入力とオプション設定
- **DirectoryWidget**: 検索対象フォルダ管理
- **ResultsWidget**: 検索結果表示とハイライト
- **IndexManagementWidget**: インデックス作成・更新UI

#### スレッドモデル

```
┌─────────────────────────────────────────┐
│         UI Thread (Qt Main Loop)        │
│  - Widget操作とイベント処理             │
│  - ユーザーインタラクション             │
└─────────────────────────────────────────┘
         ▲              ▼
    (Signals)      (Signals)
         │              │
    ┌────┴──────────────┴────┐
    │                         │
┌───▼────────────────┐  ┌───▼────────────────┐
│ FileSearcher       │  │  SearchIndexer     │
│ QThread Instance   │  │  QThread Instance  │
│                    │  │                    │
│ ・ファイル検索      │  │ ・インデックス作成 │
│ ・コンテンツ抽出    │  │ ・ファイル処理     │
└────────────────────┘  └────────────────────┘
```

#### 設定管理システム

**ConfigManager**
- INI形式での設定永続化
- ウィンドウジオメトリの自動保存
- フォントサイズの管理
- パス設定（Acrobat、インデックス）
- 検索設定（コンテキスト長、タイムアウト）

```python
config = ConfigManager()
acrobat_path = config.get_acrobat_path()
font_size = config.get_font_size()
index_file_path = config.get_index_file_path()
```

### 拡張可能設計

#### 新しいファイル形式の追加

1. **constants.py** に拡張子を登録
```python
SUPPORTED_FILE_EXTENSIONS = ['.pdf', '.txt', '.md', '.docx']
```

2. **service/** に形式別ハンドラを作成
```python
class DocxHandler:
    def extract_content(self, file_path):
        # .docxからのコンテンツ抽出実装
        pass
```

3. **search_strategy.py** に検索戦略を実装
```python
class DocxSearchStrategy:
    def search(self, file_path, search_terms, search_type):
        # .docx内の検索実装
        pass
```

4. **constants.py** にマッピングを追加
```python
FILE_HANDLER_MAPPING = {
    '.docx': 'DocxHandler',
    # ...
}

SEARCH_METHODS_MAPPING = {
    '.docx': 'search_docx',
    # ...
}
```

#### 新しいUIウィジェットの追加

1. **widgets/** に新規ウィジェットクラスを作成
2. **main_window.py** で統合
3. シグナル/スロット接続でメインウィンドウと連携

### 拡張方法

1. **新しいファイル形式の追加**
   - `constants.py`に拡張子を追加
   - `file_searcher.py`に対応する検索メソッドを実装

2. **UI機能の追加**
   - `widgets/`に新しいウィジェットクラスを作成
   - `main_window.py`で統合

## トラブルシューティング

### よくある問題と解決方法

#### Q: Adobe Acrobat Readerが起動しない
**A**: 
- Acrobatのインストールパスを確認してください
- 設定ファイルの`acrobat_path`を正しいパスに変更してください
- 管理者権限で実行してみてください

#### Q: 検索が遅い
**A**:
- インデックス機能を有効にしてください
- インデックスが古い場合は「インデックス更新」を実行してください
- 検索対象ファイル数を確認し、必要に応じて範囲を絞ってください

#### Q: 日本語ファイルが正しく検索されない
**A**:
- ファイルのエンコーディングを確認してください
- UTF-8またはShift_JISで保存されているファイルを推奨します

#### Q: インデックス作成に時間がかかる
**A**:
- 大量のファイルを処理する場合は時間がかかります
- バックグラウンド処理なので、他の作業を続けることができます
- 進行状況バーで進捗を確認してください

#### Q: メモリ使用量が多い
**A**:
- 一度に検索する対象を減らしてください
- 古いインデックスファイルをクリーンアップしてください
- アプリケーションを再起動してください

### エラーログの確認

アプリケーションの動作に問題がある場合：
1. コンソール出力を確認してください
2. 設定ファイル（config.ini）の内容を確認してください
3. 一時ファイルが正しく削除されているか確認してください

### パフォーマンス最適化

- 定期的なインデックスクリーンアップ
- 不要な一時ファイルの削除
- 検索対象フォルダの適切な選択

## Adobe Acrobat連携詳細ガイド

### 機能概要

ManualSearchはAdobe Acrobat Reader DCと統合して、検索語を自動的にハイライト表示できます。

### セットアップ

#### 1. Adobe Acrobat Reader DCのインストール

```bash
# 公式サイトからダウンロード
# https://get.adobe.com/jp/reader/

# インストール後、パスを確認
"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe" --version
```

#### 2. 設定ファイルでパスを指定

```ini
[Paths]
# デフォルトパス（自動検出）
acrobat_path = C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe

# 別インストール位置の場合（例：32bit版）
acrobat_path = C:\Program Files (x86)\Adobe\Reader 11.0\Reader\AcroRd32.exe
```

### 動作原理

```
1. PDFファイル検出
   |
2. ハイライト処理
   ├─ PyMuPDFで検索語位置を特定
   ├─ ハイライト色を適用（複数語で色分け）
   └─ 一時ファイル生成
   |
3. Acrobat起動
   ├─ プロセスマネージャーで制御
   ├─ 一時PDFを自動表示
   └─ ページ位置を自動調整
   |
4. クリーンアップ
   └─ アプリケーション終了時に一時ファイル削除
```

### ハイライト色設定

```python
# constants.py
HIGHLIGHT_COLORS = ['yellow', 'lightgreen', 'lightblue', 'lightsalmon', 'lightpink']

# 複数検索語の場合、順番に色を適用
# 最初の語 → yellow
# 2番目の語 → lightgreen
# 3番目の語 → lightblue
```

### トラブルシューティング

#### Acrobatが起動しない場合

```bash
# 1. 既存プロセスをクリア
taskkill /IM Acrobat.exe /F
taskkill /IM AcroRd32.exe /F

# 2. 一時ファイルを確認
dir %TEMP% | findstr "pdf_temp"

# 3. パスを再確認
where Acrobat.exe
```

#### ハイライト表示されない場合

```python
# ログで検索語が正しく抽出されたか確認
import logging
logging.basicConfig(level=logging.DEBUG)

# デバッグ実行
searcher = FileSearcher(...)
results = searcher.search_pdf("test.pdf", ["検索語"])
```

#### 複数PDF同時表示

Acrobatはシングルインスタンスなため、複数PDFの同時表示が必要な場合：

```bash
# 各PDFファイルを個別に開く
start "C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe" file1.pdf
start "C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe" file2.pdf
```

### ネットワークパス対応

UNCパスでのPDF参照に対応：

```ini
[Paths]
# ネットワークパス設定例
acrobat_path = C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe

# 自動変換例
# C:\Users\yokam\Documents\file.pdf
# \\server\share\Documents\file.pdf に変換可能
```

## コントリビューション

### ベストプラクティス

プロジェクト開発に参加する際の推奨事項：

#### コード改善の提案

1. **フォークとブランチ作成**
```bash
git clone https://github.com/your-username/ManualSearch.git
cd ManualSearch
git checkout -b feature/your-feature-name
```

2. **コーディング規約**
   - Python: PEP 8に準拠
   - import文: 標準 > サードパーティ > カスタムモジュールの順
   - type hints: 全関数に型アノテーションを記載
   - docstring: Google形式で記載

3. **コミットメッセージ**
```
型(スコープ): 簡潔な説明

詳細な説明（必要に応じて）
- 変更内容1
- 変更内容2

関連Issue: #123
```

型の例: `feat` (機能), `fix` (修正), `refactor` (リファクタリング), `test` (テスト), `docs` (ドキュメント)

4. **テスト追加**
```bash
# 新機能に対してテストを追加
pytest tests/ -v --cov=. --cov-report=html
```

5. **プルリクエスト提出**
   - テスト全て合格確認
   - カバレッジ低下なし
   - ドキュメント更新済み

### 機能拡張の例

#### 新ファイル形式対応（DOCX例）

1. **ハンドラ作成**
```python
# service/docx_handler.py
from docx import Document

class DocxContentExtractor:
    @staticmethod
    def extract(file_path):
        doc = Document(file_path)
        return '\n'.join([p.text for p in doc.paragraphs])
```

2. **検索戦略実装**
```python
# service/docx_search_strategy.py
class DocxSearchStrategy:
    def search(self, file_path, search_terms, search_type):
        content = DocxContentExtractor.extract(file_path)
        # 検索処理実装
        return results
```

3. **定数更新**
```python
# utils/constants.py に追加
SUPPORTED_FILE_EXTENSIONS.append('.docx')
FILE_HANDLER_MAPPING['.docx'] = DocxContentExtractor
SEARCH_METHODS_MAPPING['.docx'] = 'search_docx'
```

### バグ報告

バグを発見した場合、以下の情報を含めてIssueを作成してください：

- OS: Windows 10/11
- Python: バージョン
- 再現手順
- 期待される動作
- 実際の動作
- スクリーンショット（必要に応じて）
- エラーログ（logs/ディレクトリ）

## 最新の変更履歴

### 2025年10月20日
- 🐞 **統計情報表示修正**: インデックスファイルパスの属性アクセスを修正（`widgets/index_management_widget.py:99`）
- 🐞 **完全再構築バグ修正**: 存在しないメソッド呼び出しを修正し、アプリクラッシュを解決（`widgets/index_management_widget.py:145-146`）

### 2025年10月18日
- ✨ **検索戦略の分離**: PDF/テキスト検索戦略を別ファイルに分割
- 🔧 **インデックス管理改善**: ContentExtractor、IndexStorageクラスで処理を分離
- 🎯 **検索マッチング最適化**: SearchMatcherクラスで検索条件マッチング処理を統一
- 🐞 **インデックス再構築修正**: index_file_path参照とリセット処理の改善
- 📝 **テスト強化**: content_extractorモック参照修正とインデックス統計検証

### 2025年09月2日
- 🔧 **警告対策**: テスト環境での警告抑制とSwig警告の対処
- 📝 **テスト整理**: テストファイルの構造を整理し、importの順序を改善
- 📖 **ドキュメント**: READMEにフォルダ横断検索機能の説明を追加・更新

### 2025年09月1日
- ✨ **検索機能強化**: グローバル検索をインデックス検索に切り替え可能に改善
- 🔧 **フォルダ横断検索**: 複数フォルダを横断したインデックス検索機能を追加
- ⚙️ **検索オプション拡張**: 柔軟な検索設定を可能にするオプションを導入
- 🛠️ **UI改善**: 検索結果表示の処理効率化を実現

### 2025年08月30日
- ✨ **UI改善**: 「フォルダ横断検索」チェックボックスを「サブフォルダ含む」の右側に移動
- 🔧 **設定変更**: 「フォルダ横断検索」をデフォルトでオンに設定
- 🛠️ **新機能**: インデックス完全再構築スクリプト (`scripts/rebuild_index.py`) を追加
  - 確認プロンプトなしで自動実行
  - コマンドライン引数対応 (`--index-file`, `--config-file`, `--no-subdirs`)
  - 進捗バー表示とインデックス統計情報の表示

## バージョン情報

- **現在のバージョン**: 1.2.3
- **最終更新日**: 2025年10月20日

## 依存ライブラリ

### 主要依存関係

| ライブラリ | バージョン | 用途 |
|-----------|-----------|------|
| PyQt5 | 5.15.11 | GUI フレームワーク |
| PyMuPDF (fitz) | 1.26.3 | PDF テキスト抽出 |
| chardet | 5.2.0 | 文字エンコーディング自動検出 |
| Jinja2 | 3.1.6 | HTML テンプレートレンダリング |
| psutil | 7.0.0 | プロセス監視管理 |
| PyAutoGUI | 0.9.54 | Acrobat自動制御 |
| pytest | 8.4.1 | テストフレームワーク |
| pytest-qt | 4.5.0 | Qt テスト支援 |
| pytest-cov | 6.2.1 | カバレッジ測定 |
| pyinstaller | 6.14.2 | 実行可能ファイル生成 |
| Markdown | 3.8.2 | Markdownパーサ |
| colorama | 0.4.6 | カラー出力（Windows対応） |

### 最小要件バージョン

- Python 3.11以上
- PyQt5 5.15以上
- PyMuPDF 1.24以上

## パフォーマンス最適化

### 検索パフォーマンス

#### インデックス機能の活用

大規模なドキュメント群を検索する場合、インデックス機能を有効にすることで検索時間を大幅に短縮できます。

**オンデマンド検索** vs **インデックス検索**:
- 1,000 PDFファイル検索: 約5分 → 約5秒（60倍高速化）
- 10,000テキストファイル検索: 約10分 → 約10秒（60倍高速化）

#### インデックス最適化のコツ

```python
# 差分更新を活用（全体再構築より高速）
indexer.create_index(
    directories=["C:/Documents"],
    include_subdirs=True
)

# 不要なファイル形式を除外
# constants.py で SUPPORTED_FILE_EXTENSIONS を制限

# インデックス統計を確認
stats = indexer.get_index_stats()
print(f"インデックスサイズ: {stats['total_size']} bytes")
print(f"対象ファイル数: {stats['file_count']}")
```

### メモリ使用量管理

#### インデックスメモリ最適化

```ini
[IndexSettings]
# インデックスファイルパスをSSD上に配置
index_file_path = C:\SSD\search_index.json

# 大規模インデックスの場合、ストレージを分散
# directory_index_path_1 = C:\index_part1.json
# directory_index_path_2 = C:\index_part2.json
```

#### 検索中のメモリ使用量削減

- 検索対象フォルダの選別（不要なフォルダを除外）
- 古いインデックスの定期的なクリーンアップ
- 結果ウィジェット表示の制限（`MAX_SEARCH_RESULTS_PER_FILE = 100`）

### I/O パフォーマンス

#### ディスク読み取り最適化

```bash
# インデックス作成時に外部ディスクI/Oを最小化
# ローカルドライブへの配置を推奨

# Windows Defender の除外設定
# %USERPROFILE%\AppData\Local\ManualSearch を除外に追加
```

#### PDF抽出パフォーマンス

```python
# PyMuPDF 使用時の最適設定
import fitz

# テキスト抽出を高速化
pdf_doc = fitz.open("document.pdf")
for page_num in range(len(pdf_doc)):
    page = pdf_doc[page_num]
    text = page.get_text("text")  # "dict"より高速
```

### スレッド処理最適化

```python
# FileSearcher のスレッドプール設定（constants.py相当）
MAX_WORKERS = os.cpu_count() or 4  # CPU コア数に合わせる

# 検索タイムアウト設定で無限待機を防止
DEFAULT_PDF_TIMEOUT = 30  # 秒

# キャンセル機能の活用
searcher.cancel_search()  # 長時間検索を中断
```

## トラブルシューティング詳細ガイド

### デバッグモード有効化

```python
# main.py での設定
log_level = config.config.get('LOGGING', 'log_level', fallback='DEBUG')
```

ログファイルは `logs/` ディレクトリに自動生成されます。

### 一般的なエラーと対処

#### 1. "Cannot find Adobe Acrobat Reader" エラー

```bash
# Acrobatのインストール確認
"C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe" --version

# 設定ファイルで手動指定
[Paths]
acrobat_path = C:\Program Files\Adobe\Acrobat DC\Acrobat\Acrobat.exe
```

#### 2. インデックス作成がハング

```bash
# 一時ファイルのクリーンアップ
cd ManualSearch
python -c "from service.pdf_handler import cleanup_temp_files; cleanup_temp_files()"

# インデックスファイルの再初期化
del search_index.json
```

#### 3. PDF抽出でエラー

```python
# 破損したPDFは自動スキップ（エラーログに記録）
# 手動確認の場合
import fitz
try:
    doc = fitz.open("document.pdf")
    print("PDFは正常です")
except Exception as e:
    print(f"PDF破損: {e}")
```

#### 4. メモリリーク/プロセスハング

```bash
# Acrobatプロセス強制終了
taskkill /IM Acrobat.exe /F

# 一時ファイル確認
dir %TEMP% | findstr "pdf_temp"

# アプリケーション再起動
python main.py
```

#### 5. 日本語検索が機能しない

```ini
# config.ini で文字エンコーディング確認
[SearchSettings]
# テキストファイルはUTF-8保存を推奨
```

### パフォーマンス診断

#### スロー検索の診断

```bash
# 詳細ログで時間計測
python -m pytest tests/service/test_file_searcher.py -v --durations=5

# プロファイリング実行
python -m cProfile -s cumtime main.py
```

#### メモリ使用量監視

```python
# メモリプロファイリング
import tracemalloc
tracemalloc.start()
# ... 処理 ...
current, peak = tracemalloc.get_traced_memory()
print(f"現在: {current / 1024**2:.1f} MB, ピーク: {peak / 1024**2:.1f} MB")
```

## ライセンス

このプロジェクトのライセンス情報については、LICENSEファイルを参照してください。