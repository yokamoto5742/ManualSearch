# 変更履歴

このプロジェクトの注目すべき変更はすべてこのファイルに記録されます。

このファイルは [Keep a Changelog](https://keepachangelog.com/ja/1.0.0/) のフォーマットに従い、
バージョニングは [Semantic Versioning](https://semver.org/lang/ja/) に準拠しています。

## [Unreleased]

### 追加
- PDFハイライト機能：日本語ラベル「ハイライト付きPDF」をUI選択肢に追加
- ディレクトリウィジェットにPDFハイライト設定用チェックボックスを追加
- PDFハイライト設定の状態保存機能：ユーザーの設定を永続化

### 変更
- PDFハンドラー（pdf_handler.py）：ハイライトの有無に応じたPDFパス設定ロジックを改善
- ディレクトリウィジェット（directory_widget.py）：PDFハイライト設定をUIに反映するよう修正
- テスト設定（pytest.ini）：パフォーマンス設定のdurations値を10から5に変更

### 修正
- エンドツーエンド検索テスト（test_integration.py）：コメントと関数定義の整合性を修正

### セキュリティ
- 開発環境設定（.gitignore）：__pycache__と.ideaディレクトリをGit追跡対象外に設定

## [1.2.3] - 2025-10-20

### 変更
- 依存関係を更新：nodeenv と pyright を requirements.txt に追加
- pyright を Python 3.12 対応で設定（pyrightconfig.json 作成）

### 修正
- バージョン番号を 1.2.3 に統一し、ドキュメント内の日付を 2025-10-20 に修正

## [1.2.2] - 2025-10-19

### 追加
- インデックス管理ウィジェット：UI から直接インデックスファイルパスを表示・管理可能に
- CLAUDE.md に「パッチ差分を返す」ルール追加

### 変更
- インデックスファイルパス：設定ファイルとUIに正しいパスを設定
- インデックス更新処理（index_management_widget.py）：新しいインデックスを作成して保存するよう簡素化

### 削除
- 自動インデックス更新機能：UI から自動インデックス更新チェックボックスを削除
- 関連するメソッドを削除し、手動インデックス管理に統一

## [1.2.1] - 2025-10-18

### 追加
- 検索戦略パターン：PDF とテキストの検索方法を分離し、拡張性を向上
- フルテキストインデックス機能：SearchIndexer で全文検索インデックスを作成・管理
- スマート検索機能：IndexedFileSearcher でインデックスを活用し、フォールバック検索に対応

### 変更
- 検索エンジン：複数の検索戦略を条件に応じて選択できるよう改善
- インデックス再構築：修正と検証を強化

### 修正
- IndexedFileSearcher：index_file_path の参照を修正し、インデックス再構築時の初期化処理を改善
- SearchIndexer：content_extractor のモック参照を修正
- テスト（test_indexed_file_searcher.py）：rebuild_index の包括的なテストケースを追加
- テスト（test_search_indexer.py）：content_extractor モック参照を修正し、インデックス統計取得を検証

## [1.2.0] - 2025-10-15

### 追加
- フルテキストサーチインデックス機能：SearchIndexer で大規模文書集合の検索性能を向上
- インデックス管理ウィジェット：UI からインデックスの構築・更新・削除が可能に
- マルチスレッド対応のファイル検索エンジン（FileSearcher）：ThreadPoolExecutor で並列処理

### 変更
- 検索システム全体：インデックスベースの高速検索と直接ファイル検索の併用に改善
- Adobe Acrobat 連携：プロセス管理とハイライト機能の信頼性を向上

## [1.1.0] - 2025-09-01

### 追加
- Adobe Acrobat 統合機能：PDF にハイライト表示して Adobe Acrobat で開く機能を実装
- ファイルオープナー（file_opener.py）：クロスプラットフォーム対応でファイルを開く機能
- 設定管理システム（config_manager.py）：INI ファイルベースの設定保存・復元機能

### 変更
- PDF ハンドラー（pdf_handler.py）：PyMuPDF を使用した高速テキスト抽出に改善
- テキストハンドラー（text_handler.py）：自動エンコーディング検出で多言語対応を向上

### 修正
- ウィンドウジオメトリ：起動時と終了時の位置・サイズが正しく保存・復元されるよう修正

## [1.0.0] - 2025-08-01

### 追加
- 基本的なマルチスレッド全文検索機能：複数形式（PDF、テキスト、マークダウン）に対応
- 検索結果表示ウィジェット：ハイライト表示と文脈表示に対応
- ディレクトリ選択ウィジェット：複数ディレクトリの並列検索に対応
- 検索パラメータ設定ウィジェット：AND/OR 検索ロジック選択が可能

### 変更
- UI デザイン：PyQt5 を使用した直感的なインターフェース設計

[Unreleased]: https://github.com/yokam-oss/ManualSearch/compare/v1.2.3...HEAD
[1.2.3]: https://github.com/yokam-oss/ManualSearch/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/yokam-oss/ManualSearch/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/yokam-oss/ManualSearch/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/yokam-oss/ManualSearch/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/yokam-oss/ManualSearch/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/yokam-oss/ManualSearch/releases/tag/v1.0.0
