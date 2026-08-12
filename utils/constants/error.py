"""
エラーメッセージ関連の定数
"""

# ============================================================================
# エラーメッセージ
# ============================================================================

ERROR_MESSAGES = {
    'FILE_NOT_FOUND': 'ファイルが見つかりません',
    'FILE_NOT_ACCESSIBLE': 'ファイルにアクセスできません',
    'UNSUPPORTED_FORMAT': 'サポートされていないファイル形式です',
    'PDF_ACCESS_FAILED': 'PDFファイルにアクセスできません',
    'ACROBAT_NOT_FOUND': 'Adobe Acrobat Readerが見つかりません',
    'ALL_ACROBAT_PATHS_NOT_FOUND': '設定されたパスをすべて確認しましたが、Adobe Acrobat/Readerの実行ファイルが見つかりませんでした。',
    'ACROBAT_START_FAILED': 'Acrobatの起動に失敗しました',
    'FOLDER_NOT_FOUND': '指定されたフォルダが見つかりません',
    'FOLDER_OPEN_FAILED': 'フォルダを開けませんでした',
    'ENCODING_DETECTION_FAILED': 'エンコーディングの検出に失敗しました',
    'FILE_DECODE_FAILED': 'ファイルのデコードに失敗しました'
}


# ============================================================================
# ログメッセージテンプレート
# ============================================================================

LOG_MESSAGE_TEMPLATES = {
    'SEARCH_START': '検索開始: 検索語={search_terms}, タイプ={search_type}, グローバル検索={is_global_search}',
    'INDEX_CONFIG_LOAD_ERROR': 'インデックス設定の読み込みに失敗: {error}',
    'INDEX_TOGGLE': 'インデックス検索を{status}にしました',
    'SEARCH_ERROR': '検索中にエラーが発生しました: {error}',
    'FILE_NOT_FOUND': 'ファイルが見つかりません',
    'FOLDER_NOT_FOUND': 'フォルダが見つかりません',
    'FOLDER_OPEN_ERROR': 'フォルダを開く際にエラーが発生しました: {error}',
    'APP_EXIT': 'アプリケーションを終了します',
    'NO_ACROBAT_PROCESSES': '既存のAcrobatプロセスは見つかりませんでした',
    'FOUND_ACROBAT_PROCESSES': '既存のAcrobatプロセスが{count}個見つかりました',
    'PROCESS_TERMINATING': 'プロセス終了中: {process_name} (PID: {pid})',
    'PROCESS_TERMINATED': 'Acrobatプロセス (PID: {pid}) を正常に終了しました',
    'PROCESS_FORCE_KILLED': 'Acrobatプロセス (PID: {pid}) を強制終了しました',
    'ACROBAT_WAIT_ERROR': 'Acrobat待機中にエラー: {error}',
    'ACROBAT_TIMEOUT': 'Acrobat起動のタイムアウト（{timeout}秒）',
    'UNSUPPORTED_FILE_TYPE': 'サポートされていないファイル形式: {extension}',
    'SEARCH_ERROR_DETAIL': '検索エラー: {path} - {error}',
    'INDEX_OPERATION_START': 'インデックス{operation_name}を開始します...',
    'INDEX_OPERATION_ERROR': 'インデックス{operation_name}中にエラーが発生しました: {error}',
    'LOG_FORMAT': '[{timestamp}] {message}'
}


# ============================================================================
# ログ日時フォーマット
# ============================================================================

LOG_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


# ============================================================================
# インデックス操作ラベル
# ============================================================================

INDEX_OPERATION_LABELS = {
    'CREATE': '初回作成',
    'ADD': 'ファイル追加更新',
    'DELETE': 'ファイル削除更新',
    'REBUILD': '完全再構築'
}


# ============================================================================
# ディレクトリアクセスエラー
# ============================================================================

ERROR_DIRECTORY_ACCESS = 'ディレクトリアクセスエラー: {directory} - {error}'
ERROR_DIRECTORY_SEARCH = 'ディレクトリ検索エラー: {directory} - {error}'


# ============================================================================
# インデックス検索ステータスメッセージ（UI表示）
# ============================================================================

INDEX_STATUS_MESSAGES = {
    'FILE_NOT_FOUND': 'インデックスファイルが見つかりません',
    'EMPTY': 'インデックスが空です',
    'SEARCHING_WITHOUT_INDEX': 'インデックスなしで検索中...',
    'SEARCH_ERROR': 'インデックス検索でエラーが発生しました',
    'CREATING': 'インデックスを作成中...',
    'UNAVAILABLE': 'インデックスが利用できません',
    'CREATING_NEW': 'インデックスを新規作成します...',
}

INDEX_STATUS_TEMPLATES = {
    'CREATE_COMPLETE': 'インデックス作成完了: {files_count} ファイル, {size_mb:.1f}MB',
    'CREATE_ERROR': 'インデックス作成エラー: {error}',
    'CLEANUP_COMPLETE': 'インデックスクリーンアップ完了: {count} ファイルを削除',
    'CLEANUP_ERROR': 'インデックスクリーンアップエラー: {error}',
    'REBUILD_ERROR': 'インデックス再構築エラー: {error}',
}


# ============================================================================
# ファイルオープン時のエラーメッセージテンプレート（UI表示）
# ============================================================================

PDF_HANDLER_ERROR_TEMPLATES = {
    'HIGHLIGHT_FAILED': 'PDFのハイライト処理中にエラー: {error}',
    'FILE_NOT_FOUND': '指定されたファイルが見つかりません: {file_path}',
    'ACROBAT_START_FAILED': 'Acrobat Readerの起動に失敗しました: {error}',
    'UNEXPECTED_ERROR': 'PDFを開く際に予期せぬエラーが発生しました: {error}',
}

FILE_OPEN_ERROR_TEMPLATES = {
    'PDF_PROCESS_FAILED': 'PDFの処理に失敗しました: {error}',
    'ACROBAT_START_FAILED': '{message}: {error}',
    'PDF_OPERATION_ERROR': 'PDFの操作中にエラーが発生しました: {error}',
    'TEXT_READ_FAILED': 'テキストファイルの読み込みに失敗しました: {error}',
    'TEXT_PROCESS_ERROR': 'テキストファイルの処理中にエラーが発生しました: {error}',
    'FOLDER_OPEN_FAILED': '{message}: {error}',
    'FOLDER_OPEN_ERROR': 'フォルダを開く際にエラーが発生しました: {error}',
    'FILE_OPEN_ERROR': 'ファイルを開く際にエラーが発生しました: {error}',
}


# ============================================================================
# テキストビューア印刷時のエラーメッセージテンプレート（UI表示）
# ============================================================================

TEXT_VIEWER_PRINT_ERROR_TEMPLATES = {
    'PRINTER_NOT_FOUND': 'プリンタが見つかりません。プリンタの接続と設定を確認してください',
    'PRINT_FAILED': '印刷中にエラーが発生しました: {error}',
}
