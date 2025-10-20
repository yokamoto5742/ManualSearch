# ManualSearch

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
   pip install -r requirements.txt
   pip install pytest pytest-qt  # テスト用（必要に応じて）
   ```

### アーキテクチャ

- **MVCパターン**: モデル（Service層）、ビュー（Widgets）、コントローラー（MainWindow）
- **Qt Signalシステム**: コンポーネント間の疎結合な通信
- **設定管理**: INIファイルベースの設定永続化

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

- **現在のバージョン**: 1.2.2
- **最終更新日**: 2025年10月20日

## ライセンス

このプロジェクトのライセンス情報については、LICENSEファイルを参照してください。